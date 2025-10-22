import threading
import time
import traceback
import uyts  # YouTube Search lib nova


class SearchManager:
    def __init__(self):
        pass

    def normalize_title(self, title: str) -> str:
        """Normaliza título pra evitar duplicados simples."""
        return title.strip().lower()

    def search_youtube(self, query: str, total_pages: int = 1) -> dict:
        """
        Faz uma busca segura no YouTube usando uyts.
        Retorna um dicionário padronizado com status e resultados.
        """
        result_data = {
            "query": query,
            "success": False,
            "error": None,
            "results": [],
        }

        if not query or not query.strip():
            result_data["error"] = "Consulta vazia."
            return result_data

        added_titles = set()
        all_results = []

        def load_page(page_index: int):
            """Carrega uma página de resultados com tratamento de erro seguro."""
            term = f"{query} page {page_index + 1}" if page_index > 0 else query
            try:
                search = uyts.Search(term)
                for r in getattr(search, "results", []):
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

            except Exception as e:
                print(f"[SearchManager] Erro ao buscar página {page_index + 1}: {e}")
                traceback.print_exc()

        try:
            # Carrega a primeira página
            load_page(0)

            # Se houver mais páginas, busca em thread separada
            def load_more():
                for i in range(1, total_pages):
                    time.sleep(0.5)
                    load_page(i)

            if total_pages > 1:
                threading.Thread(target=load_more, daemon=True).start()

            result_data["results"] = all_results
            result_data["success"] = True

        except Exception as e:
            result_data["error"] = str(e)
            traceback.print_exc()

        return result_data
