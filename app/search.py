import time
import traceback
import uyts
import re
from yt_dlp import YoutubeDL
from yt_dlp.utils import ExtractorError, DownloadError

class SearchManager:
    def __init__(self):
        pass

    def normalize_title(self, title: str) -> str:
        return title.strip().lower()

    def is_url(self, query: str) -> bool:
        # Regex robusta para detectar URLs
        url_pattern = r'^(https?://)?([a-zA-Z0-9-]+\.)+[a-zA-Z0-9-]+(/.*)?$'
        try:
            return bool(re.match(url_pattern, query.strip()))
        except re.error as e:
            print(f"[SearchManager] Erro na regex: {e}")
            return False

    def extract_video_metadata(self, url: str) -> dict:
        try:
            ydl_opts = {
                'format': 'best',
                'noplaylist': True,
                'quiet': True,
            }
            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                return {
                    "title": info.get('title', 'Título desconhecido'),
                    "uploader": info.get('uploader', 'Canal desconhecido') or info.get('channel', 'Canal desconhecido'),
                    "url": url,
                    "thumbnail": info.get('thumbnail', ''),
                    "duration": info.get('duration_string', 'N/A'),
                    "views": str(info.get('view_count', '0')),
                }
        except ExtractorError as e:
            print(f"[SearchManager] Erro de extração do vídeo {url}: {e}")
            traceback.print_exc()
            error_msg = "Autenticação necessária (cookies ou login) para acessar este vídeo." if "login required" in str(e).lower() else str(e)
            return {
                "title": "Título desconhecido",
                "uploader": "Canal desconhecido",
                "url": url,
                "thumbnail": "",
                "duration": "N/A",
                "views": "0",
                "error": error_msg
            }
        except Exception as e:
            print(f"[SearchManager] Erro geral ao extrair metadados do vídeo {url}: {e}")
            traceback.print_exc()
            return {
                "title": "Título desconhecido",
                "uploader": "Canal desconhecido",
                "url": url,
                "thumbnail": "",
                "duration": "N/A",
                "views": "0",
                "error": str(e)
            }

    def search_youtube(self, query: str, total_pages: int = 1) -> dict:
        result_data = {
            "query": query,
            "success": False,
            "error": None,
            "results": [],
        }

        if not query or not query.strip():
            result_data["error"] = "Consulta vazia."
            return result_data

        print(f"[SearchManager] Processando query: {query}")

        # Verifica se a query é um URL
        if self.is_url(query):
            try:
                video = self.extract_video_metadata(query)
                result_data["results"] = [video]
                result_data["success"] = True
                if video.get("error"):
                    result_data["error"] = video["error"]
            except Exception as e:
                result_data["error"] = f"Erro ao processar o link: {str(e)}"
                traceback.print_exc()
            return result_data

        # Busca no YouTube com uyts
        added_titles = set()
        all_results = []

        def load_page(page_index: int):
            term = f"{query} page {page_index + 1}" if page_index > 0 else query
            try:
                print(f"[SearchManager] Buscando: {term}")
                search = uyts.Search(term)
                results = getattr(search, "results", [])
                print(f"[SearchManager] Resultados brutos da página {page_index + 1}: {len(results)} itens")
                for r in results:
                    if getattr(r, "resultType", "") != "video":
                        continue

                    title = getattr(r, "title", "Título desconhecido")
                    normalized = self.normalize_title(title)
                    if normalized in added_titles:
                        continue
                    added_titles.add(normalized)

                    video = {
                        "title": title,
                        "uploader": getattr(r, "author", "Canal desconhecido"),
                        "url": f"https://www.youtube.com/watch?v={getattr(r, 'id', '')}",
                        "thumbnail": getattr(r, "thumbnail_src", ""),
                        "duration": getattr(r, "duration", "N/A"),
                        "views": getattr(r, "view_count", "0"),
                    }
                    all_results.append(video)
                    print(f"[SearchManager] Vídeo adicionado: {title}")

            except Exception as e:
                print(f"[SearchManager] Erro ao buscar página {page_index + 1}: {e}")
                traceback.print_exc()

        try:
            # Carrega todas as páginas de forma síncrona
            for i in range(total_pages):
                load_page(i)
                if i < total_pages - 1:
                    time.sleep(0.5)  # Pausa entre páginas

            result_data["results"] = all_results
            result_data["success"] = True
            print(f"[SearchManager] Resultados finais: {len(all_results)} vídeos")

        except Exception as e:
            result_data["error"] = str(e)
            traceback.print_exc()

        return result_data