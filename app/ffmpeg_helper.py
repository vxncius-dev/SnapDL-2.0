import os
import platform
import subprocess
import shutil
import threading
from typing import Callable, List, Optional


class FFmpegHelper:
    def __init__(
        self,
        base_dir: Optional[str] = None,
        app_data_dir: Optional[str] = None,
        binaries_subdir: str = "binaries",
        on_ready: Optional[Callable[[str], None]] = None,
        on_error: Optional[Callable[[str], None]] = None,
    ):
        self.base_dir = base_dir or os.getcwd()
        self.app_data_dir = app_data_dir or os.getcwd()
        self.binaries_subdir = binaries_subdir
        self.ffmpeg_path = None
        self.on_ready = on_ready
        self.on_error = on_error

        self._setup_storage_if_linux()
        self.ffmpeg_path = self._detect_ffmpeg_path()
        self.ensure_ffmpeg_ready()

    def _setup_storage_if_linux(self):
        system = platform.system().lower()
        if "linux" in system:
            storage_root = "/storage/emulated/0"
            if os.path.exists(storage_root):
                target_dir = os.path.join(storage_root, "storage")
                try:
                    if not os.path.exists(target_dir):
                        os.makedirs(target_dir, exist_ok=True)
                    self.app_data_dir = target_dir
                except Exception:
                    pass

    def _detect_ffmpeg_path(self) -> Optional[str]:
        binaries_dir = os.path.join(self.base_dir, self.binaries_subdir)
        system = platform.system().lower()

        if "android" in system:
            return os.path.join(self.app_data_dir, "ffmpeg")

        try:
            subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
            return "ffmpeg"
        except Exception:
            pass

        local_ffmpeg = os.path.join(binaries_dir, "ffmpeg")
        return local_ffmpeg if os.path.exists(local_ffmpeg) else None

    def ensure_ffmpeg_ready(self):
        if not self.ffmpeg_path:
            if self.on_error:
                self.on_error("FFmpeg não encontrado.")
            return

        system = platform.system().lower()
        local_ffmpeg = os.path.join(self.base_dir, self.binaries_subdir, "ffmpeg")

        try:
            if "android" in system:
                if not os.path.exists(self.ffmpeg_path) and os.path.exists(local_ffmpeg):
                    shutil.copy(local_ffmpeg, self.ffmpeg_path)
                    os.chmod(self.ffmpeg_path, 0o755)
                elif os.path.exists(self.ffmpeg_path):
                    os.chmod(self.ffmpeg_path, 0o755)

            if os.path.exists(self.ffmpeg_path) or self.ffmpeg_path == "ffmpeg":
                subprocess.run([self.ffmpeg_path, "-version"], capture_output=True, check=True)
                if self.on_ready:
                    self.on_ready(self.ffmpeg_path)
        except Exception as e:
            self.ffmpeg_path = None
            if self.on_error:
                self.on_error(f"Erro ao preparar FFmpeg: {e}")

    def run(self, cmd: List[str]) -> subprocess.CompletedProcess:
        if not self.ffmpeg_path:
            raise RuntimeError("FFmpeg não disponível.")
        full_cmd = [self.ffmpeg_path] + cmd
        return subprocess.run(full_cmd, capture_output=True, text=True)

    def generate_thumbnail(self, video_path: str, output_dir: Optional[str] = None) -> Optional[str]:
        try:
            if not os.path.exists(video_path):
                return None
            output_dir = output_dir or self.app_data_dir
            thumb_path = os.path.join(output_dir, f"thumb_{os.path.basename(video_path)}.jpg")
            cmd = ["-y", "-i", video_path, "-ss", "00:00:01", "-vframes", "1", thumb_path]
            self.run(cmd)
            return thumb_path if os.path.exists(thumb_path) else None
        except Exception:
            return None

    def generate_thumbnail_async(self, video_path: str, callback: Callable[[Optional[str]], None]) -> None:
        def worker():
            thumb = self.generate_thumbnail(video_path)
            try:
                callback(thumb)
            except Exception:
                pass

        threading.Thread(target=worker, daemon=True).start()
