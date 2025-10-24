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
        self.ffmpeg_path: Optional[str] = None
        self.on_ready = on_ready
        self.on_error = on_error

        self._setup_android_storage()
        self.ffmpeg_path = self._detect_ffmpeg_path()
        self.ensure_ffmpeg_ready()

    # ============================================================
    # DETECÇÃO DE AMBIENTE
    # ============================================================
    def _is_android(self) -> bool:
        return os.path.exists("/storage/emulated/0")

    def _setup_android_storage(self):
        """
        Garante um local de execução acessível no Android.
        Usa /storage/emulated/0/Android/data/com.vxncius.snapdl/files/bin
        """
        if self._is_android():
            target_dir = "/storage/emulated/0/Android/data/com.vxncius.snapdl/files/bin"
            try:
                os.makedirs(target_dir, exist_ok=True)
                self.app_data_dir = target_dir
            except Exception:
                # fallback
                self.app_data_dir = "/storage/emulated/0/Download/SnapDL"
                os.makedirs(self.app_data_dir, exist_ok=True)

    # ============================================================
    # DETECÇÃO E ESCOLHA DO FFMPEG
    # ============================================================
    def _detect_ffmpeg_path(self) -> Optional[str]:
        """
        Retorna o caminho do ffmpeg conforme a prioridade:
        1. ffmpeg no PATH do sistema
        2. ffmpeg embutido em binaries/
        3. (Android) ffmpeg copiado para app_data_dir
        """
        system = platform.system().lower()
        binaries_dir = os.path.join(self.base_dir, self.binaries_subdir)
        embedded_ffmpeg = os.path.join(binaries_dir, "ffmpeg")

        # Android usa o binário embutido, mas copiado pro app_data_dir
        if self._is_android():
            return os.path.join(self.app_data_dir, "ffmpeg")

        # Se o ffmpeg estiver disponível no PATH, usa ele
        try:
            subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
            return "ffmpeg"
        except Exception:
            pass

        # Caso contrário, tenta usar o binário embutido
        if os.path.exists(embedded_ffmpeg):
            return embedded_ffmpeg

        return None

    # ============================================================
    # PREPARO DO BINÁRIO
    # ============================================================
    def ensure_ffmpeg_ready(self):
        """
        Garante que o ffmpeg pode ser executado:
          - copia pro local correto se for Android
          - aplica permissão de execução (chmod)
          - verifica se responde a `-version`
        """
        if not self.ffmpeg_path:
            if self.on_error:
                self.on_error("FFmpeg não encontrado.")
            return

        local_ffmpeg = os.path.join(self.base_dir, self.binaries_subdir, "ffmpeg")

        try:
            # Android: copia pra pasta segura se necessário
            if self._is_android():
                if not os.path.exists(self.ffmpeg_path) and os.path.exists(
                    local_ffmpeg
                ):
                    shutil.copy(local_ffmpeg, self.ffmpeg_path)
                    os.chmod(self.ffmpeg_path, 0o755)
                else:
                    os.chmod(self.ffmpeg_path, 0o755)
            else:
                # macOS/Linux/Windows: garante permissão se embutido
                if self.ffmpeg_path != "ffmpeg" and os.path.exists(self.ffmpeg_path):
                    os.chmod(self.ffmpeg_path, 0o755)

            # Testa execução
            subprocess.run(
                [self.ffmpeg_path, "-version"], capture_output=True, check=True
            )
            if self.on_ready:
                self.on_ready(self.ffmpeg_path)

        except Exception as e:
            self.ffmpeg_path = None
            if self.on_error:
                self.on_error(f"Erro ao preparar FFmpeg: {e}")

    # ============================================================
    # UTILITÁRIOS
    # ============================================================
    def run(self, cmd: List[str]) -> subprocess.CompletedProcess:
        if not self.ffmpeg_path:
            raise RuntimeError("FFmpeg não disponível.")
        full_cmd = [self.ffmpeg_path] + cmd
        return subprocess.run(full_cmd, capture_output=True, text=True)

    def generate_thumbnail(
        self, video_path: str, output_dir: Optional[str] = None
    ) -> Optional[str]:
        try:
            if not os.path.exists(video_path):
                return None
            output_dir = output_dir or self.app_data_dir
            thumb_path = os.path.join(
                output_dir, f"thumb_{os.path.basename(video_path)}.jpg"
            )
            cmd = [
                "-y",
                "-i",
                video_path,
                "-ss",
                "00:00:01",
                "-vframes",
                "1",
                thumb_path,
            ]
            self.run(cmd)
            return thumb_path if os.path.exists(thumb_path) else None
        except Exception:
            return None

    def generate_thumbnail_async(
        self, video_path: str, callback: Callable[[Optional[str]], None]
    ) -> None:
        def worker():
            thumb = self.generate_thumbnail(video_path)
            try:
                callback(thumb)
            except Exception:
                pass

        threading.Thread(target=worker, daemon=True).start()
