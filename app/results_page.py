import flet as ft


class ResultsPage(ft.View):
    def __init__(self, search_result: dict, on_back):
        super().__init__(route="/results")
        self.search_result = search_result
        self.on_back = on_back
        self.controls = [
            ft.AppBar(
                title=ft.Text(f"Resultados para: {search_result.get('query', '')}"),
                leading=ft.IconButton(ft.icons.ARROW_BACK, on_click=lambda _: on_back()),
            ),
            self._build_results_list()
        ]

    def _build_results_list(self):
        results = self.search_result.get("results", [])
        if not results:
            return ft.Text("Nenhum resultado encontrado.")

        return ft.ListView(
            expand=True,
            spacing=10,
            padding=10,
            controls=[
                ft.Container(
                    bgcolor=ft.colors.with_opacity(0.05, ft.colors.ON_SURFACE),
                    border_radius=8,
                    padding=10,
                    content=ft.Row([
                        ft.Image(r.get("thumbnail"), width=80, height=80),
                        ft.Column([
                            ft.Text(r.get("title", "Sem título"), weight="bold"),
                            ft.Text(r.get("uploader", "Desconhecido")),
                            ft.Text(r.get("url", ""), color=ft.colors.BLUE_400),
                        ], expand=True)
                    ])
                )
                for r in results
            ]
        )
