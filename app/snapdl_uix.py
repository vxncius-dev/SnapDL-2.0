from os import path
from platform import system
from json import dumps, load
import flet as ft
from .search import SearchManager
from .downloader import DownloadManager
from .ffmepg_helper import FFmpegHelper
from .screen_config import ScreenConfig


DEBUG_MODE = True
IS_MOBILE = False
# system().lower() == "linux" and path.exists("/storage/emulated/0")


class SnapDL:
    def __init__(self):
        self.page = None
        self.base_dir = path.dirname(path.abspath(__file__))
        self.scren_format = "portrait" if IS_MOBILE else "wide"
        self.screen_config = ScreenConfig()
        self.seach_mananger = SearchManager()
        self.donwload_mananger = DownloadManager()
        self.ffmpeg_setup = FFmpegHelper()
        self.light_colors = {
            "bg": "#F5F5F5",
            "text": "#212121",
            "primary": "#1976D2",
            "secondary": "#03A9F4",
            "border": "#CCCCCC",
            "icon": "#212121",
            "hint": "#757575",
            "search_bg": "#FFFFFF",
            "search_border": "#B0B0B0",
        }
        self.dark_colors = {
            "bg": "#0D0D0D",
            "text": "#FFFFFF",
            "primary": "#90CAF9",
            "secondary": "#64B5F6",
            "border": "#3B3B3B",
            "icon": "#FFFFFF",
            "hint": "#AAAAAA",
            "search_bg": "#1E1E1E",
            "search_border": "#3B3B3B",
        }
        self.colors = self.dark_colors if ft.ThemeMode == ft.ThemeMode.DARK else self.light_colors
        self.search_result = {}
        if DEBUG_MODE:
            try:
                placeholder_path = path.join(self.base_dir, "result_placeholder.json")
                if path.exists(placeholder_path):
                    with open(placeholder_path, "r", encoding="utf-8") as f:
                        self.search_result = load(f)
                    self.log(f"Carregado: {placeholder_path}")
                else:
                    self.log(f"result_placeholder.json não encontrado em {placeholder_path}")
            except Exception as e:
                self.log(f"Erro ao carregar result_placeholder.json: {e}")
        ft.app(self.main)

    def log(self, mesage):
        print(f"[DEBUG] {str(mesage)}")

    def build_content(self, w):
        def on_focus(e):
            search_bar.border = ft.border.all(1, self.colors["primary"])
            search_bar.update()

        def on_blur(e):
            search_bar.border = ft.border.all(1, self.colors["search_border"])
            search_bar.update()

        def on_search(e=None):
            value = search_input.value.strip()
            if value:
                self.search_result = self.seach_mananger.search_youtube(value)
                self.log(dumps(self.search_result, indent=4))

        search_input = ft.TextField(
            hint_text="Search",
            border=ft.InputBorder.NONE,
            hover_color=ft.Colors.TRANSPARENT,
            bgcolor=self.colors["search_bg"],
            cursor_color=self.colors["primary"],
            text_style=ft.TextStyle(color=self.colors["text"], size=17),
            hint_style=ft.TextStyle(color=self.colors["hint"]),
            expand=True,
            on_submit=on_search,
            on_focus=on_focus,
            on_blur=on_blur,
        )

        search_bar = ft.Container(
            content=ft.Row(
                [
                    ft.Icon(name=ft.Icons.DOWNLOAD,
                            color=self.colors["icon"],
                            size=20
                    ),
                    search_input,
                    ft.IconButton(
                        icon=ft.Icons.SEARCH,
                        icon_color=self.colors["icon"],
                        icon_size=20,
                        tooltip="Search",
                        on_click=on_search,
                    ),
                ],
                alignment=ft.MainAxisAlignment.START,
            ),
            bgcolor=self.colors["search_bg"],
            border=ft.border.all(1, self.colors["search_border"]),
            border_radius=50,
            padding=ft.padding.symmetric(horizontal=15, vertical=0),
            margin=ft.margin.symmetric(horizontal=20),
            width=400,
        )

        def decoration(state):
            if state:
                return ft.DecorationImage(
                    src="assets/background2.jpg",
                    fit=ft.ImageFit.CONTAIN,
                    repeat=ft.ImageRepeat.REPEAT_X,
                )

        title = ft.Text(
            "SnapDL",
            color=self.colors["text"],
            size=45,
            font_family="Poppins-Bold"
        )

        return ft.Container(
            content=ft.Column(
                [
                    title,
                    search_bar,
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=10,
                width=w
            ),
            bgcolor=self.colors["bg"],
            image=decoration(False),
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
                    bgcolor=self.colors["border"],
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
                bgcolor=self.colors["bg"],
                padding=0,
                width=w,
                height=h,
            ),
            expand=True,
            maximizable=False
        )

    def main(self, page: ft.Page):
        self.page = page
        page.title = "SnapDL"
        page.fonts = {
            "Poppins-Bold": path.join(self.base_dir, "fonts", "Poppins-Bold.ttf"),
            "Poppins-Regular": path.join(self.base_dir, "fonts", "Poppins-Regular.ttf"),
        }
        width, height = self.screen_config.aspect_ratio(self.scren_format)
        page.bgcolor = self.colors["bg"]
        page.window.title_bar_hidden = True
        page.window.width = width
        page.window.height = height
        page.window.center()
        page.padding = 0
        content = self.setup_window(page, width, height)
        page.add(content)

        def on_resize(e):
            new_w = page.window.width
            new_h = page.window.height
            page.controls.clear()
            page.add(self.setup_window(page, new_w, new_h))
            page.update()

        page.on_resized = on_resize
