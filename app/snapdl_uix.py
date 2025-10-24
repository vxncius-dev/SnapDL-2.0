from os import path
from platform import system
from json import dumps, load
from time import sleep
import flet as ft
from flet_permission_handler import PermissionHandler, PermissionType, PermissionStatus
from .search import SearchManager
from .downloader import DownloadManager
from .ffmpeg_helper import FFmpegHelper
from .homepage import homepage
from .results_page import results_page
from .downloads_page import downloads_page
from .settings_page import settings_page
from types import MethodType

# system().lower() == "linux" and path.exists("/storage/emulated/0")


class SnapDL:
    def __init__(self):
        self.DEBUG_MODE = False
        self.IS_MOBILE = 1
        self.page = None
        self.base_dir = path.dirname(path.abspath(__file__))
        self.seach_mananger = SearchManager()
        self.donwload_mananger = DownloadManager()
        self.ffmpeg_setup = FFmpegHelper()
        self.homepage = MethodType(homepage, self)
        self.results_page = MethodType(results_page, self)
        self.downloads_page = MethodType(downloads_page, self)
        self.settings_page = MethodType(settings_page, self)
        # self.video_player_page = MethodType(video_player_page, self)
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
        if self.DEBUG_MODE:
            try:
                placeholder_path = path.join(
                    self.base_dir, "..", "assets", "result_placeholder.json"
                )
                if path.exists(placeholder_path):
                    with open(placeholder_path, "r", encoding="utf-8") as f:
                        self.search_result = load(f)
                else:
                    self.log(
                        f"result_placeholder.json não encontrado em {placeholder_path}"
                    )
            except Exception as e:
                self.log(f"Erro ao carregar result_placeholder.json: {e}")

        ft.app(target=self.main)

    def log(self, mesage):
        print(f"[DEBUG] {str(mesage)}")

    def download_video(
        self,
        url: str,
        title: str,
        uploader: str,
        thumbnail: str = "",
        only_audio: bool = False,
    ):
        download_id = self.donwload_mananger.add_download(
            url, title, uploader, thumbnail, only_audio=only_audio
        )
        self.log(
            f"Iniciando download ({'AUDIO' if only_audio else 'VIDEO'}) ID {download_id}: {title} from {url}"
        )

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
                mouse_cursor=ft.MouseCursor.CLICK,
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
                        if not self.IS_MOBILE
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

        if self.IS_MOBILE:
            return ft.SafeArea(content=content_base, expand=True)
        else:
            return ft.WindowDragArea(content_base, expand=True, maximizable=False)

    def navigator(self, route="/", w=800):
        self.current_route = route
        if route == "/":
            return self.setup_window(self.page, w, self.height, self.homepage(w))
        elif route == "/results":
            return self.setup_window(self.page, w, self.height, self.results_page(w))
        elif route == "/downloads":
            return self.setup_window(self.page, w, self.height, self.downloads_page(w))
        elif route == "/settings":
            return self.setup_window(self.page, w, self.height, self.settings_page(w))
        else:
            self.log(f"Rota desconhecida: {route}, redirecionando para homepage")
            return self.setup_window(self.page, w, self.height, self.homepage(w))

        # elif route.startswith("/video"):
        #     params = dict(
        #         param.split("=")
        #         for param in route.split("?")[1].split("&")
        #         if "?" in route
        #     )
        #     return self.setup_window(
        #         self.page, w, self.height, self.video_player_page(w, params)
        #     )

    def aspect_ratio_from_page(self, page, fmt: str = "wide", percent: float = 0.9):
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
        custom_overlay_style = ft.SystemOverlayStyle(
            status_bar_color=self.colors["bg"],
            status_bar_icon_brightness=ft.Brightness.LIGHT,
            system_navigation_bar_color=self.colors["bg"],
            system_navigation_bar_icon_brightness=ft.Brightness.LIGHT,
            system_navigation_bar_divider_color=self.colors["bg"],
        )
        page.theme = ft.Theme(system_overlay_style=custom_overlay_style)
        page.fonts = {
            "Poppins-Bold": path.join(self.base_dir, "..", "fonts", "Poppins-Bold.ttf"),
            "Poppins-Regular": path.join(
                self.base_dir, "..", "fonts", "Poppins-Regular.ttf"
            ),
        }
        self.scren_format = "wide"  # if not self.IS_MOBILE else "portrait"
        self.width, self.height = self.aspect_ratio_from_page(page, self.scren_format)
        page.window.width = self.width
        page.window.height = self.height
        page.bgcolor = self.colors["bg"]
        page.window.icon = path.join(self.base_dir, "..", "assets", "favicon.ico")
        page.window.title_bar_hidden = True
        page.window.center()
        page.padding = 0
        if self.IS_MOBILE:

            def go_back(e):
                self.page.controls.clear()
                self.current_route = "/"
                self.current_page = self.navigator(self.current_route, self.width)
                self.page.add(self.current_page)
                self.page.update()

            def list_downloads(e):
                self.page.controls.clear()
                self.current_route = "/downloads"
                self.current_page = self.navigator(self.current_route, self.width)
                self.page.add(self.current_page)
                self.page.update()

            def settings(e):
                self.page.controls.clear()
                self.current_route = "/settings"
                self.current_page = self.navigator(self.current_route, self.width)
                self.page.add(self.current_page)
                self.page.update()

            page.bottom_appbar = ft.BottomAppBar(
                bgcolor=self.colors["bg"],
                shape=ft.NotchShape.CIRCULAR,
                content=ft.Row(
                    controls=[
                        ft.Container(expand=True),
                        ft.IconButton(
                            icon=ft.Icons.SEARCH,
                            icon_color=ft.Colors.WHITE,
                            on_click=go_back,
                        ),
                        ft.Container(
                            expand=True, margin=ft.margin.symmetric(horizontal=5)
                        ),
                        ft.IconButton(
                            icon=ft.Icons.VIDEO_LIBRARY,
                            icon_color=ft.Colors.WHITE,
                            on_click=list_downloads,
                        ),
                        ft.Container(
                            expand=True, margin=ft.margin.symmetric(horizontal=5)
                        ),
                        ft.IconButton(
                            icon=ft.Icons.SETTINGS,
                            icon_color=ft.Colors.WHITE,
                            on_click=settings,
                        ),
                        ft.Container(expand=True),
                    ]
                ),
            )

        self.permission_handler = PermissionHandler()
        page.overlay.append(self.permission_handler)

        def request_permissions():
            try:
                storage_status = self.permission_handler.request_permission(
                    PermissionType.STORAGE
                )
                notif_status = self.permission_handler.request_permission(
                    PermissionType.NOTIFICATION
                )
                self.log(f"Storage: {storage_status}, Notifications: {notif_status}")
                if storage_status != PermissionStatus.GRANTED:
                    self.log(
                        "Permissão de armazenamento negada, abrindo configurações..."
                    )
                    self.permission_handler.open_app_settings()

            except Exception as e:
                self.log(f"Erro ao solicitar permissões: {e}")

        def on_ready(e):
            sleep(0.5)
            request_permissions()

        page.on_resume = on_ready
        self.current_page = self.navigator("/", self.width)
        page.add(self.current_page)

        def on_resize(e):
            w = page.window.width
            h = page.window.height
            self.width, self.height = w, h
            page.controls.clear()
            self.current_page = self.navigator(self.current_route, w)
            page.add(self.current_page)
            page.update()

        page.on_resized = on_resize
        if self.DEBUG_MODE:
            self.fake_search()

    def fake_search(self):
        # self.log(dumps(self.search_result, indent=4))
        self.page.controls.clear()
        self.current_route = "/results"
        self.current_page = self.navigator(self.current_route, self.width)
        self.page.add(self.current_page)
        self.page.update()
