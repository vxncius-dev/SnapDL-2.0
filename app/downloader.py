import os
import re
import uuid
import threading
import subprocess
import shutil
from typing import Any, Dict, List, Optional, Callable
from threading import Lock


class DownloadManager:
    def __init__(
        self,
        yt_dlp_bin: Optional[str] = None,
        base_dir: Optional[str] = None,
        binaries_subdir: str = "binaries",
        download_dir: Optional[str] = None,
        temp_dir: Optional[str] = None,
        on_progress: Optional[Callable[[Dict[str, Any]], None]] = None,
        on_complete: Optional[Callable[[Dict[str, Any]], None]] = None,
        on_error: Optional[Callable[[Dict[str, Any]], None]] = None,
        on_status: Optional[Callable[[Dict[str, Any]], None]] = None,
    ):
        self.base_dir = base_dir or os.getcwd()
        self.binaries_subdir = binaries_subdir

        # Detecta ambiente
        self.is_android = self._is_android()
        self.app_bin_dir = self._resolve_app_bin_dir()

        # Resolve yt-dlp correto
        self.yt_dlp_bin = yt_dlp_bin or self._detect_yt_dlp_path()

        # Diretórios de download
        self.download_dir = download_dir or self._resolve_download_dir()
        self.temp_dir = temp_dir or self._resolve_temp_dir()
        os.makedirs(self.download_dir, exist_ok=True)
        os.makedirs(self.temp_dir, exist_ok=True)

        # Controle e eventos
        self.items: Dict[str, Dict[str, Any]] = {}
        self.lock = Lock()
        self._pct_re = re.compile(r"(?P<pct>\d{1,3}(?:\.\d+)?)%")
        self.on_progress = on_progress
        self.on_complete = on_complete
        self.on_error = on_error
        self.on_status = on_status

    # ==============================================================
    # DETECÇÃO DE AMBIENTE E BINÁRIO
    # ==============================================================

    def _is_android(self) -> bool:
        return os.path.exists("/storage/emulated/0")

    def _resolve_app_bin_dir(self) -> str:
        if self._is_android():
            path = "/storage/emulated/0/Android/data/com.vxncius.snapdl/files/bin"
            os.makedirs(path, exist_ok=True)
            return path
        return os.path.join(self.base_dir, self.binaries_subdir)

    def _detect_yt_dlp_path(self) -> str:
        """Tenta encontrar o yt-dlp funcional no sistema ou embutido."""
        embedded_path = os.path.join(self.base_dir, self.binaries_subdir, "yt-dlp")

        # Android usa o binário embutido copiado para pasta executável
        if self._is_android():
            android_bin = os.path.join(self.app_bin_dir, "yt-dlp")
            if not os.path.exists(android_bin) and os.path.exists(embedded_path):
                shutil.copy(embedded_path, android_bin)
                os.chmod(android_bin, 0o755)
            return android_bin

        # Desktop: tenta no PATH
        try:
            subprocess.run(["yt-dlp", "--version"], capture_output=True, check=True)
            return "yt-dlp"
        except Exception:
            pass

        # Se falhar, tenta o embutido
        if os.path.exists(embedded_path):
            os.chmod(embedded_path, 0o755)
            return embedded_path

        raise FileNotFoundError(
            "yt-dlp não encontrado nem no PATH nem nos binários locais."
        )

    # ==============================================================
    # RESOLUÇÃO DE DIRETÓRIOS
    # ==============================================================

    def _resolve_download_dir(self) -> str:
        """Define o diretório padrão de download."""
        if self._is_android():
            base = "/storage/emulated/0/Download/SnapDL"
        else:
            base = os.path.join(os.path.expanduser("~"), "Downloads", "SnapDL")
        os.makedirs(base, exist_ok=True)
        return base

    def _resolve_temp_dir(self) -> str:
        """Usa o mesmo diretório de download no desktop, e pasta app no Android."""
        if self._is_android():
            tmp = os.path.join(self.app_bin_dir, "temp")
            os.makedirs(tmp, exist_ok=True)
            return tmp
        return self._resolve_download_dir()

    # ==============================================================
    # CORE DE DOWNLOADS
    # ==============================================================

    def add_download(
        self,
        url: str,
        title: str,
        uploader: str,
        thumbnail: str = "",
        only_audio: bool = False,
    ) -> str:
        download_id = str(uuid.uuid4())
        safe_title = (
            "".join(c for c in title if c.isalnum() or c in " ._-").strip()
            or download_id
        )
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
        t = threading.Thread(
            target=self._download_worker, args=(download_id,), daemon=True
        )
        entry["thread"] = t
        t.start()

    # ==============================================================
    # WORKER
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
            p = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )
            with self.lock:
                entry["process"] = p

            for line in p.stdout:
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
                final_path = self._find_output(out_template)
                if final_path:
                    # Se Android e não puder gravar direto, move o arquivo
                    if self._is_android() and not os.access(self.download_dir, os.W_OK):
                        dest = os.path.join(
                            self.download_dir, os.path.basename(final_path)
                        )
                        shutil.move(final_path, dest)
                        final_path = dest

                    entry["final_path"] = final_path
                    entry["status"] = "completed"
                    entry["progress"] = 100.0
                    self._emit_complete(entry)
                else:
                    entry["status"] = "error"
                    entry["error"] = "Arquivo final não encontrado"
                    self._emit_error(entry)
            else:
                entry["status"] = "error"
                entry["error"] = f"yt-dlp exit {ret}"
                self._emit_error(entry)

        except Exception as exc:
            with self.lock:
                entry["status"] = "error"
                entry["error"] = str(exc)
            self._emit_error(entry)

    # ==============================================================
    # AUXILIARES
    # ==============================================================

    def _find_output(self, out_template: str) -> Optional[str]:
        base = out_template.replace("%(ext)s", "")
        for ext_try in ("mp4", "mkv", "webm", "mp3", "m4a"):
            candidate = f"{base}{ext_try}"
            if os.path.exists(candidate):
                return candidate
        return None

    # ==============================================================
    # CALLBACKS
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
