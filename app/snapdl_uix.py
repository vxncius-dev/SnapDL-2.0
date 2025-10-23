from os import path
from platform import system
from json import dumps, load
import flet as ft
from .search import SearchManager
from .downloader import DownloadManager
from .ffmepg_helper import FFmpegHelper

DEBUG_MODE = True
IS_MOBILE = False
# system().lower() == "linux" and path.exists("/storage/emulated/0")


class SnapDL:
    def __init__(self):
        self.page = None
        self.base_dir = path.dirname(path.abspath(__file__))
        self.seach_mananger = SearchManager()
        self.donwload_mananger = DownloadManager()
        self.ffmpeg_setup = FFmpegHelper()
        self.colors = {
            "bg": "#0D0D0D",
            "text": "#FFFFFF",
            "primary": "#DBDBDB",
            "secondary": "#3E3E3E",
            "border": "#3B3B3B",
            "icon": "#FFFFFF",
            "hint": "#AAAAAA",
            "search_bg": "#1E1E1E",
            "search_border": "#3B3B3B",
        }
        self.search_result = {}
        self.current_page = None
        self.current_route = "/"

        if DEBUG_MODE:
            try:
                placeholder_path = path.join(
                    self.base_dir, "..", "assets", "result_placeholder.json"
                )
                if path.exists(placeholder_path):
                    with open(placeholder_path, "r", encoding="utf-8") as f:
                        self.search_result = load(f)
                    self.log(f"Carregado: {placeholder_path}")
                else:
                    self.log(
                        f"result_placeholder.json não encontrado em {placeholder_path}"
                    )
            except Exception as e:
                self.log(f"Erro ao carregar result_placeholder.json: {e}")

        ft.app(target=self.main)

    def log(self, mesage):
        print(f"[DEBUG] {str(mesage)}")

    def homepage(self, w):
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
                # Navega para results após busca
                self.page.controls.clear()
                self.current_route = "/results"
                self.current_page = self.navigator(self.current_route, w)
                self.page.add(self.current_page)
                self.page.update()

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
                    ft.Icon(name=ft.Icons.DOWNLOAD, color=self.colors["icon"], size=20),
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
            "SnapDL", color=self.colors["text"], size=45, font_family="Poppins-Bold"
        )

        return ft.Container(
            content=ft.Column(
                [title, search_bar],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=10,
                width=w,
            ),
            padding=ft.padding.only(bottom=50),
            bgcolor=self.colors["bg"],
            image=decoration(False),
            expand=True,
        )

    def results_page(self, w):
        def go_back(e):
            self.page.controls.clear()
            self.current_route = "/"
            self.current_page = self.navigator(self.current_route, w)
            self.page.add(self.current_page)
            self.page.update()

        back_button = ft.IconButton(
            icon=ft.Icons.ARROW_BACK,
            icon_color=self.colors["icon"],
            icon_size=24,
            on_click=go_back,
        )

        if not self.search_result.get("success", False):
            content = ft.Column(
                [
                    back_button,
                    ft.Text(
                        "No results found or error occurred.",
                        color=self.colors["text"],
                        size=20,
                        text_align=ft.TextAlign.CENTER,
                    ),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=20,
                expand=True,
            )
        else:
            results = self.search_result.get("results", [])
            query = self.search_result.get("query", "")

            header = ft.Row(
                [
                    back_button,
                    ft.Container(
                        content=ft.Text(
                            f"Results for: {query}",
                            color=self.colors["text"],
                            size=24,
                            font_family="Poppins-Bold",
                        ),
                        expand=True,
                        alignment=ft.alignment.center_left,
                        padding=ft.padding.only(left=10),
                    ),
                ],
                alignment=ft.MainAxisAlignment.START,
            )

            result_list = ft.ListView(
                controls=[],
                spacing=10,
                padding=ft.padding.all(20),
                expand=True,
            )

            for result in results:
                title = result.get("title", "")
                uploader = result.get("uploader", "")
                thumb = result.get("thumbnail", "")
                duration = result.get("duration", "")
                views = result.get("views", "0")
                url = result.get("url", "")
                video_card = ft.Card(
                    content=ft.Container(
                        content=ft.Row(
                            [
                                ft.Image(
                                    src=thumb,
                                    width=100,
                                    height=60,
                                    fit=ft.ImageFit.COVER,
                                    border_radius=8,
                                ),
                                ft.Container(
                                    expand=True,
                                    padding=ft.padding.only(left=10),
                                    content=ft.Column(
                                        [
                                            ft.Text(
                                                title,
                                                color=self.colors["text"],
                                                size=16,
                                                weight=ft.FontWeight.BOLD,
                                                max_lines=2,
                                                overflow=ft.TextOverflow.ELLIPSIS,
                                            ),
                                            ft.Text(
                                                uploader,
                                                color=self.colors["hint"],
                                                size=14,
                                            ),
                                            ft.Text(
                                                duration,
                                                color=self.colors["hint"],
                                                size=12,
                                            ),
                                        ],
                                        spacing=5,
                                    ),
                                ),
                                ft.IconButton(
                                    icon=ft.Icons.DOWNLOAD,
                                    icon_color=self.colors["primary"],
                                    icon_size=24,
                                    tooltip="Download",
                                    on_click=lambda e, url=url, title=title, uploader=uploader, thumb=thumb: self.download_video(
                                        url, title, uploader, thumb
                                    ),
                                ),
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        padding=ft.padding.all(5),
                    ),
                    color=self.colors["bg"],
                    elevation=0,
                )
                result_list.controls.append(video_card)
            content = ft.Column([header, result_list], expand=True)

        return ft.Container(
            content=content,
            bgcolor=self.colors["bg"],
            width=w,
            expand=True,
        )

    def download_video(self, url: str, title: str, uploader: str, thumbnail: str = ""):
        download_id = self.donwload_mananger.add_download(
            url, title, uploader, thumbnail
        )
        self.log(f"Iniciando download ID {download_id}: {title} from {url}")

    def setup_window(self, page, w, h, screen):
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
                    bgcolor="#666666",
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
        )

        content_base = ft.Container(
            content=ft.Column(
                controls=[
                    (
                        ft.Container(
                            content=window_controls,
                            alignment=ft.alignment.top_left,
                            padding=ft.padding.only(left=12, top=10),
                        )
                        if not IS_MOBILE
                        else ft.Container()
                    ),
                    screen,
                ],
                expand=True,
            ),
            bgcolor=self.colors["bg"],
            width=w,
            height=h,
        )

        if IS_MOBILE:
            return ft.SafeArea(content=content_base, expand=True)
        else:
            return ft.WindowDragArea(content_base, expand=True, maximizable=False)

    def navigator(self, route="/", w=800):
        self.current_route = route
        if route == "/":
            return self.setup_window(self.page, w, self.height, self.homepage(w))
        elif route == "/results":
            return self.setup_window(self.page, w, self.height, self.results_page(w))
        else:
            return self.setup_window(self.page, w, self.height, self.homepage(w))

    def aspect_ratio_from_page(self, page, fmt: str = "wide", percent: float = 0.8):
        presets = {
            "square": (1, 1),
            "wide": (16, 9),
            "portrait": (9, 16),
            "ultrawide": (21, 9),
        }

        if fmt in presets:
            w_ratio, h_ratio = presets[fmt]
        else:
            sep = "x" if "x" in fmt else ":"
            w_ratio, h_ratio = map(float, fmt.split(sep))

        target_ratio = w_ratio / h_ratio
        win_w = page.window.width or 1280
        win_h = page.window.height or 720
        if win_w == 0 or win_h == 0:
            win_w, win_h = 1280, 720
        max_w = win_w * percent
        max_h = win_h * percent
        if target_ratio > (win_w / win_h):
            width = max_w
            height = width / target_ratio
            if height > max_h:
                height = max_h
                width = height * target_ratio
        else:
            height = max_h
            width = height * target_ratio
            if width > max_w:
                width = max_w
                height = width / target_ratio

        return int(width), int(height)

    def main(self, page: ft.Page):
        self.page = page
        page.title = "SnapDL"
        page.fonts = {
            "Poppins-Bold": path.join(self.base_dir, "..", "fonts", "Poppins-Bold.ttf"),
            "Poppins-Regular": path.join(
                self.base_dir, "..", "fonts", "Poppins-Regular.ttf"
            ),
        }

        self.scren_format = "portrait" if IS_MOBILE else "wide"
        self.width, self.height = self.aspect_ratio_from_page(page, self.scren_format)
        page.window.width = self.width
        page.window.height = self.height
        page.bgcolor = self.colors["bg"]
        page.window.icon = path.join(self.base_dir, "..", "assets", "favicon.png")
        page.window.title_bar_hidden = True
        page.window.center()
        page.padding = 0

        # render inicial
        self.current_page = self.navigator("/", self.width)
        page.add(self.current_page)

        # atualização ao redimensionar
        def on_resize(e):
            w = page.window.width
            h = page.window.height
            self.width, self.height = w, h
            page.controls.clear()
            self.current_page = self.navigator(self.current_route, w)
            page.add(self.current_page)
            page.update()

        page.on_resized = on_resize
