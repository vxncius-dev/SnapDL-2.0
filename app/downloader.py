import os
import re
import uuid
import time
import shutil
import threading
import subprocess
from typing import Any, Dict, List, Optional, Callable
from threading import Lock


class DownloadManager:
    """
    Gerenciador de downloads com yt-dlp, independente de UI.
    Permite callbacks para atualização de progresso, conclusão e erros.
    """

    def __init__(
        self,
        yt_dlp_bin: str = "yt-dlp",
        download_dir: Optional[str] = None,
        temp_dir: Optional[str] = None,
        on_progress: Optional[Callable[[Dict[str, Any]], None]] = None,
        on_complete: Optional[Callable[[Dict[str, Any]], None]] = None,
        on_error: Optional[Callable[[Dict[str, Any]], None]] = None,
        on_status: Optional[Callable[[Dict[str, Any]], None]] = None,
    ):
        self.yt_dlp_bin = yt_dlp_bin
        self.download_dir = download_dir or os.path.join(os.getcwd(), "downloads")
        self.temp_dir = temp_dir or self.download_dir

        os.makedirs(self.download_dir, exist_ok=True)
        os.makedirs(self.temp_dir, exist_ok=True)

        self.items: Dict[str, Dict[str, Any]] = {}
        self.lock = Lock()
        self._pct_re = re.compile(r"(?P<pct>\d{1,3}(?:\.\d+)?)%")

        # Callbacks
        self.on_progress = on_progress
        self.on_complete = on_complete
        self.on_error = on_error
        self.on_status = on_status

    # ==============================================================
    # Público
    # ==============================================================

    def add_download(
        self,
        url: str,
        title: str,
        uploader: str,
        thumbnail: str = "",
        only_audio: bool = False,
    ) -> str:
        """Adiciona um novo download à fila e inicia automaticamente."""
        download_id = str(uuid.uuid4())
        safe_title = "".join(c for c in title if c.isalnum() or c in " ._-").strip() or download_id
        out_template = os.path.join(self.temp_dir, f"{safe_title}.%(ext)s")

        entry = {
            "id": download_id,
            "url": url,
            "title": title,
            "uploader": uploader,
            "thumbnail": thumbnail,
            "only_audio": only_audio,
            "status": "queued",
            "progress": 0.0,
            "process": None,
            "thread": None,
            "output_template": out_template,
            "temp_dir": self.temp_dir,
            "error": None,
            "final_path": None,
            "final_dir": self.download_dir,
        }

        with self.lock:
            self.items[download_id] = entry

        self.start_download(download_id)
        return download_id

    def start_download(self, download_id: str) -> None:
        with self.lock:
            entry = self.items.get(download_id)
            if not entry or entry["status"] in ("downloading", "completed"):
                return
            entry["status"] = "downloading"

        self._emit_status(entry)
        t = threading.Thread(target=self._download_worker, args=(download_id,), daemon=True)
        entry["thread"] = t
        t.start()

    def pause_download(self, download_id: str) -> bool:
        with self.lock:
            entry = self.items.get(download_id)
            if not entry:
                return False
            proc = entry.get("process")
            if not proc:
                return False
            try:
                proc.terminate()
            except Exception:
                try:
                    proc.kill()
                except Exception:
                    pass
            entry["status"] = "paused"
            entry["process"] = None
        self._emit_status(entry)
        return True

    def stop_download(self, download_id: str, clean_partial: bool = False) -> bool:
        with self.lock:
            entry = self.items.get(download_id)
            if not entry:
                return False
            proc = entry.get("process")
            entry["status"] = "stopped"
            entry["process"] = None
        if proc:
            try:
                proc.terminate()
            except Exception:
                try:
                    proc.kill()
                except Exception:
                    pass
        if clean_partial:
            base = entry["output_template"].replace("%(ext)s", "")
            for fname in os.listdir(self.download_dir):
                if fname.startswith(os.path.basename(base)):
                    try:
                        os.remove(os.path.join(self.download_dir, fname))
                    except Exception:
                        pass
        self._emit_status(entry)
        return True

    def resume_download(self, download_id: str) -> None:
        with self.lock:
            entry = self.items.get(download_id)
            if not entry or entry["status"] not in ("paused", "stopped", "error"):
                return
            entry["status"] = "queued"
        self.start_download(download_id)

    def remove_entry(self, download_id: str) -> None:
        with self.lock:
            entry = self.items.pop(download_id, None)
        if not entry:
            return
        proc = entry.get("process")
        if proc:
            try:
                proc.terminate()
            except Exception:
                pass

    def get_all(self) -> List[Dict[str, Any]]:
        with self.lock:
            return [dict(v) for v in self.items.values()]

    # ==============================================================
    # Interno
    # ==============================================================

    def _download_worker(self, download_id: str) -> None:
        with self.lock:
            entry = self.items.get(download_id)
            if not entry:
                return
            url = entry["url"]
            only_audio = entry["only_audio"]
            out_template = entry["output_template"]

        cmd = [self.yt_dlp_bin]
        if only_audio:
            cmd += ["-f", "bestaudio", "-x", "--audio-format", "mp3", "--no-mtime"]
        else:
            cmd += ["-f", "best", "--no-mtime"]
        cmd += ["-o", out_template, url]

        try:
            p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
            with self.lock:
                entry["process"] = p

            while True:
                line = p.stdout.readline()
                if line == "" and p.poll() is not None:
                    break
                if not line:
                    continue

                m = self._pct_re.search(line)
                if m:
                    try:
                        pct = float(m.group("pct"))
                        with self.lock:
                            entry["progress"] = max(0.0, min(100.0, pct))
                        self._emit_progress(entry)
                    except Exception:
                        pass

            ret = p.wait()
            with self.lock:
                entry["process"] = None
                if ret == 0:
                    entry["final_path"] = self._find_output(out_template)
                    entry["status"] = "completed"
                    entry["progress"] = 100.0
                    self._emit_complete(entry)
                else:
                    entry["status"] = "error"
                    entry["error"] = f"yt-dlp exit {ret}"
                    self._emit_error(entry)

        except Exception as exc:
            with self.lock:
                entry["process"] = None
                entry["status"] = "error"
                entry["error"] = str(exc)
            self._emit_error(entry)

    def _find_output(self, out_template: str) -> Optional[str]:
        base = out_template.replace("%(ext)s", "")
        for ext_try in ("mp4", "mkv", "webm", "mp3", "m4a"):
            candidate = f"{base}{ext_try}"
            if os.path.exists(candidate):
                return candidate
        return None

    # ==============================================================
    # Callbacks
    # ==============================================================

    def _emit_progress(self, entry: Dict[str, Any]):
        if callable(self.on_progress):
            try:
                self.on_progress(dict(entry))
            except Exception:
                pass

    def _emit_complete(self, entry: Dict[str, Any]):
        if callable(self.on_complete):
            try:
                self.on_complete(dict(entry))
            except Exception:
                pass

    def _emit_error(self, entry: Dict[str, Any]):
        if callable(self.on_error):
            try:
                self.on_error(dict(entry))
            except Exception:
                pass

    def _emit_status(self, entry: Dict[str, Any]):
        if callable(self.on_status):
            try:
                self.on_status(dict(entry))
            except Exception:
                pass
