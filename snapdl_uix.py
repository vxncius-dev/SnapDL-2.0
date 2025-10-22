import flet as ft
from search import SearchManager
from downloader import DownloadManager
from ffmepg_helper import FFMPEGSetup
from screen_config import ScreenConfig

class SnapDL:
    def __init__(self):
        self.scren_format = "portrait" # "wide" "portrait"
        self.screen_config = ScreenConfig()
        self.seach_mananger = SearchManager()
        self.donwload_mananger = DownloadManager()
        self.ffmpeg_setup = FFMPEGSetup()
        ft.app(self.main)

    def build_content(self, w):
        search_bar = ft.Container(
                        content=ft.Row(
                            [
                                ft.Icon(name=ft.Icons.DOWNLOAD_OUTLINED, color=ft.Colors.WHITE, size=20),
                                ft.TextField(
                                    hint_text="Search",
                                    border=ft.InputBorder.NONE,
                                    hover_color=ft.Colors.TRANSPARENT,
                                    bgcolor=ft.Colors.TRANSPARENT,
                                    cursor_color=ft.Colors.WHITE,
                                    text_style=ft.TextStyle(color=ft.Colors.WHITE, size=17),
                                    expand=True,
                                    on_submit=lambda e: self.seach_mananger.seach(e.control.value),
                                ),
                                ft.Icon(name=ft.Icons.SEARCH, color=ft.Colors.WHITE, size=20),
                            ],
                            alignment=ft.MainAxisAlignment.START,
                        ),
                        border=ft.border.all(1, ft.Colors.WHITE24),
                        border_radius=50,
                        padding=ft.padding.symmetric(horizontal=15, vertical=0),
                        margin=ft.margin.symmetric(horizontal=20),
                        width=400,
                    )

        return ft.Container(
            content=ft.Column(
                [
                    ft.Text("SnapDL", size=35, font_family="Poppins-Bold"),
                    search_bar,
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=15,
                width=w
            ),
            bgcolor=ft.Colors.TRANSPARENT,
            image=ft.DecorationImage(
                src="assets/background2.jpg",
                fit=ft.ImageFit.CONTAIN,
                repeat=ft.ImageRepeat.REPEAT_X,
            ),
            expand=True
        )

    def setup_window(self, page, w, h):
        def handle_minimize(e):
            page.window.minimized = True
            page.update()

        def handle_maximize(e):
            page.window.maximized = not page.window.maximized
            page.update()

        def handle_close(e):
            page.window.close()

        def window_button(action):
            return ft.GestureDetector(
                on_tap=action,
                content=ft.Container(
                    width=17,
                    height=17,
                    bgcolor="#212121",
                    border_radius=10,
                ),
            )
        
        window_controls = ft.Container(
            content=ft.Row(
                [
                    window_button(handle_minimize),
                    window_button(handle_maximize),
                    window_button(handle_close),
                ],
                spacing=10,
            ),
            padding=ft.padding.only(left=12, top=10)
        )
        
        return ft.WindowDragArea(
                    ft.Container(
                        ft.Column(
                            [
                                (
                                    window_controls if self.scren_format != "portrait"
                                    else ft.Container(width=0, height=0)
                                ),
                                self.build_content(w)
                            ],
                            spacing=5,
                        ),
                        bgcolor=ft.Colors.BLACK,
                        padding=0,
                        width=w,
                        height=h,
                    ),
                    expand=True,
                    maximizable=False
                )

    def main(self, page: ft.Page):
        page.fonts = {
            "Poppins-Bold": "fonts/Poppins-Bold.ttf",
            "Poppins-Regular": "fonts/Poppins-Regular.ttf",
        }
        width, height = self.screen_config.aspect_ratio(self.scren_format)
        page.bgcolor = ft.Colors.BLACK
        page.window.title_bar_hidden = True
        page.window.width = width
        page.window.height = height
        page.window.center()
        page.padding = 0
        page.add(self.setup_window(page, width, height))