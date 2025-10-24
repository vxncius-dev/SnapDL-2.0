import flet as ft

def settings_page(self, w: int):
    return ft.Container(
        width=w,
        padding=ft.padding.all(20),
        content=ft.Column(
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Text(
                    "Configurações",
                    color=self.colors["text"],
                    size=22,
                    weight=ft.FontWeight.BOLD,
                ),
                ft.Text(
                    "Placeholder — em breve mais opções aqui.",
                    color=self.colors["hint"],
                    size=14,
                    italic=True,
                ),
            ],
            expand=True,
        ),
    )
