import os
import platform
import subprocess
import shutil
import threading
from typing import Callable, List, Optional


class FFmpegHelper:
    """
    Classe utilitária independente para gerenciar e usar FFmpeg.
    Detecta binário automaticamente, copia se necessário (Android),
    e oferece métodos seguros para geração de thumbnails e execução de comandos.
    """

    def __init__(
        self,
        base_dir: Optional[str] = None,
        app_data_dir: Optional[str] = None,
        binaries_subdir: str = "binaries",
        on_ready: Optional[Callable[[str], None]] = None,
        on_error: Optional[Callable[[str], None]] = None,
    ):
        """
        Args:
            base_dir: Diretório base onde ficam os binários (ex: pasta do projeto)
            app_data_dir: Diretório local da aplicação (Android/Windows/macOS)
            binaries_subdir: Nome da subpasta onde fica o FFmpeg local
            on_ready: Callback opcional chamado quando o FFmpeg está pronto
            on_error: Callback opcional chamado em caso de falha
        """
        self.base_dir = base_dir or os.getcwd()
        self.app_data_dir = app_data_dir or os.getcwd()
        self.binaries_subdir = binaries_subdir
        self.ffmpeg_path = None
        self.on_ready = on_ready
        self.on_error = on_error

        self.ffmpeg_path = self._detect_ffmpeg_path()
        self.ensure_ffmpeg_ready()

    # ===============================================================
    # Inicialização e detecção
    # ===============================================================

    def _detect_ffmpeg_path(self) -> Optional[str]:
        """Detecta caminho do binário do FFmpeg conforme o sistema."""
        binaries_dir = os.path.join(self.base_dir, self.binaries_subdir)
        system = platform.system().lower()

        # Android → copia para sandbox
        if "android" in system:
            return os.path.join(self.app_data_dir, "ffmpeg")

        # Verifica se o ffmpeg está disponível no PATH
        try:
            subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
            return "ffmpeg"
        except Exception:
            pass

        # Tenta encontrar localmente (projeto/binaries/ffmpeg)
        local_ffmpeg = os.path.join(binaries_dir, "ffmpeg")
        return local_ffmpeg if os.path.exists(local_ffmpeg) else None

    def ensure_ffmpeg_ready(self):
        """Verifica se o FFmpeg está disponível e executável."""
        if not self.ffmpeg_path:
            if self.on_error:
                self.on_error("FFmpeg não encontrado.")
            return

        system = platform.system().lower()
        local_ffmpeg = os.path.join(self.base_dir, self.binaries_subdir, "ffmpeg")

        try:
            # Android → copia para sandbox do app
            if "android" in system:
                if not os.path.exists(self.ffmpeg_path) and os.path.exists(local_ffmpeg):
                    shutil.copy(local_ffmpeg, self.ffmpeg_path)
                    os.chmod(self.ffmpeg_path, 0o755)
                elif os.path.exists(self.ffmpeg_path):
                    os.chmod(self.ffmpeg_path, 0o755)

            # Testa execução
            if os.path.exists(self.ffmpeg_path) or self.ffmpeg_path == "ffmpeg":
                subprocess.run([self.ffmpeg_path, "-version"], capture_output=True, check=True)
                if self.on_ready:
                    self.on_ready(self.ffmpeg_path)
        except Exception as e:
            self.ffmpeg_path = None
            if self.on_error:
                self.on_error(f"Erro ao preparar FFmpeg: {e}")

    # ===============================================================
    # Execução e utilitários
    # ===============================================================

    def run(self, cmd: List[str]) -> subprocess.CompletedProcess:
        """Executa um comando FFmpeg e retorna o resultado."""
        if not self.ffmpeg_path:
            raise RuntimeError("FFmpeg não disponível.")
        full_cmd = [self.ffmpeg_path] + cmd
        return subprocess.run(full_cmd, capture_output=True, text=True)

    def generate_thumbnail(self, video_path: str, output_dir: Optional[str] = None) -> Optional[str]:
        """Gera thumbnail do vídeo de forma síncrona."""
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
        """Gera thumbnail em thread separada e retorna via callback."""
        def worker():
            thumb = self.generate_thumbnail(video_path)
            try:
                callback(thumb)
            except Exception:
                pass

        threading.Thread(target=worker, daemon=True).start()
