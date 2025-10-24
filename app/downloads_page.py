import os
import flet as ft

def downloads_page(self, w: int):
    downloads_dir = os.path.join(os.path.expanduser("~"), "Downloads", "SnapDL")
    if os.path.exists("/storage/emulated/0/Download/SnapDL"):  # Android
        downloads_dir = "/storage/emulated/0/Download/SnapDL"

    os.makedirs(downloads_dir, exist_ok=True)
    files = os.listdir(downloads_dir)

    items = []
    if not files:
        items.append(
            ft.Text("Nenhum arquivo encontrado.", color=self.colors["hint"], size=14)
        )
    else:
        for f in files:
            full_path = os.path.join(downloads_dir, f)
            size_mb = os.path.getsize(full_path) / (1024 * 1024)
            items.append(
                ft.Container(
                    padding=ft.padding.symmetric(vertical=8, horizontal=10),
                    content=ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Text(
                                f,
                                color=self.colors["text"],
                                size=14,
                                max_lines=1,
                                overflow=ft.TextOverflow.ELLIPSIS,
                            ),
                            ft.Text(
                                f"{size_mb:.1f} MB",
                                color=self.colors["hint"],
                                size=12,
                            ),
                        ],
                    ),
                    border=ft.border.all(1, self.colors["border"]),
                    border_radius=6,
                )
            )

    return ft.Container(
        width=w,
        padding=ft.padding.all(15),
        content=ft.Column(
            controls=[
                ft.Text("Downloads", color=self.colors["text"], size=22, weight=ft.FontWeight.BOLD),
                ft.Divider(height=10, color=self.colors["border"]),
                ft.ListView(expand=True, spacing=8, controls=items),
            ],
            expand=True,
        ),
    )
