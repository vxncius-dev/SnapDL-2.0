import flet as ft
import flet_video as fv
from yt_dlp import YoutubeDL
import threading


def get_streaming_url(youtube_url):
    try:
        ydl_opts = {
            "format": "best[ext=mp4]",
            "noplaylist": True,
            "quiet": True,
        }
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(youtube_url, download=False)
            streaming_url = info.get("url", youtube_url)
            # print(f"URL de streaming obtida: {streaming_url}")
            return streaming_url
    except Exception as e:
        print(f"Erro ao obter URL de streaming: {e}")
        return None


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
                    "Nenhum resultado encontrado ou ocorreu um erro.",
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
        result_list = ft.Column(
            controls=[],
            spacing=10,
            scroll=ft.ScrollMode.AUTO,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            expand=True,
        )

        def create_video_card(result):
            title = result.get("title", "")
            uploader = result.get("uploader", "")
            thumb = result.get("thumbnail", "")
            duration = result.get("duration", "")
            url = result.get("url", "")
            thumb_size_w = w * 0.5 if not self.IS_MOBILE else w * 0.85
            thumb_size_h = thumb_size_w * 9 / 16
            card_content_ref = ft.Ref[ft.Container]()
            is_video = False

            def create_thumbnail():
                return ft.GestureDetector(
                    content=ft.Stack(
                        [
                            ft.Image(
                                src=thumb,
                                width=thumb_size_w,
                                height=thumb_size_h,
                                fit=ft.ImageFit.COVER,
                                border_radius=8,
                            ),
                            ft.Container(
                                content=ft.Text(
                                    duration,
                                    color=ft.Colors.WHITE,
                                    size=10,
                                    weight=ft.FontWeight.BOLD,
                                    text_align=ft.TextAlign.CENTER,
                                ),
                                bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.BLACK),
                                padding=ft.padding.symmetric(horizontal=5, vertical=2),
                                border_radius=4,
                                alignment=ft.alignment.bottom_right,
                                width=thumb_size_w,
                                height=thumb_size_h,
                            ),
                        ],
                        width=thumb_size_w,
                        height=thumb_size_h,
                    ),
                    on_tap=lambda e, u=url, t=title: handle_card_click(e, u, t),
                )

            def create_video_player(streaming_url):
                return ft.Container(
                    content=fv.Video(
                        playlist=[fv.VideoMedia(streaming_url)],
                        playlist_mode=fv.PlaylistMode.SINGLE,
                        show_controls=True,
                        autoplay=True,
                        fill_color=ft.Colors.BLACK,
                        filter_quality=ft.FilterQuality.HIGH,
                        volume=100.0,
                        muted=False,
                        fit=ft.ImageFit.CONTAIN,
                        wakelock=True,
                        on_loaded=lambda e: self.log(
                            f"[DEBUG] Vídeo '{title}' carregado com sucesso!"
                        ),
                        on_completed=lambda e: self.log(
                            f"[DEBUG] Reprodução do vídeo '{title}' concluída!"
                        ),
                        on_error=lambda e: self.log(f"[DEBUG] Erro no vídeo: {e.data}"),
                        on_enter_fullscreen=lambda e: self.log(
                            f"[DEBUG] Vídeo entrou em tela cheia!"
                        ),
                        on_exit_fullscreen=lambda e: self.log(
                            f"[DEBUG] Vídeo saiu de tela cheia!"
                        ),
                    ),
                    width=thumb_size_w,
                    height=thumb_size_h,
                    clip_behavior=ft.ClipBehavior.HARD_EDGE,
                    alignment=ft.alignment.center,
                )

            def toggle_content(to_video, streaming_url=None):
                nonlocal is_video
                if not card_content_ref.current:
                    self.log("Erro: card_content_ref.current é None")
                    return
                self.log(f"Alterando para {'vídeo' if to_video else 'thumbnail'}")
                card_content_ref.current.content.controls[0] = (
                    create_video_player(streaming_url)
                    if to_video and streaming_url
                    else (
                        ft.Text("Erro ao carregar vídeo", color=ft.Colors.RED, size=14)
                        if to_video
                        else create_thumbnail()
                    )
                )
                is_video = to_video
                card_content_ref.current.update()
                self.page.update()

            def load_streaming_url(video_url, video_title):
                self.log(f"Iniciando carregamento da URL para {video_title}")
                streaming_url = get_streaming_url(video_url)
                if streaming_url:
                    # self.log(f"URL válida obtida: {streaming_url}")
                    toggle_content(True, streaming_url)
                else:
                    self.log(f"Falha ao obter URL de streaming")
                    toggle_content(True, None)
                self.page.update()

            def handle_card_click(e, video_url, video_title):
                nonlocal is_video
                if not is_video:
                    card_content_ref.current.content.controls[0] = ft.Column(
                        [
                            ft.Text(
                                "Carregando vídeo...",
                                color=self.colors["text"],
                                size=14,
                                text_align=ft.TextAlign.CENTER,
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        height=thumb_size_h,
                    )
                    card_content_ref.current.update()
                    threading.Thread(
                        target=lambda: load_streaming_url(video_url, video_title),
                        daemon=True,
                    ).start()

            def open_download_sheet(url, title, uploader, thumb):
                def handle_choice(e, only_audio=False):
                    self.page.close(bottom_sheet)
                    self.download_video(
                        url, title, uploader, thumb, only_audio=only_audio
                    )

                bottom_sheet = ft.BottomSheet(
                    ft.Container(
                        bgcolor=self.colors["bg"],
                        padding=ft.padding.all(20),
                        content=ft.Column(
                            alignment=ft.MainAxisAlignment.CENTER,
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            spacing=15,
                            controls=[
                                ft.Text(
                                    title,
                                    color=self.colors["hint"],
                                    size=14,
                                    max_lines=2,
                                    overflow=ft.TextOverflow.ELLIPSIS,
                                    text_align=ft.TextAlign.CENTER,
                                ),
                                ft.ElevatedButton(
                                    text="Baixar como Vídeo (MP4)",
                                    icon=ft.Icons.VIDEO_LIBRARY,
                                    on_click=lambda e: handle_choice(
                                        e, only_audio=False
                                    ),
                                    bgcolor=self.colors["secondary"],
                                    color=self.colors["text"],
                                ),
                                ft.ElevatedButton(
                                    text="Baixar como Áudio (MP3)",
                                    icon=ft.Icons.AUDIO_FILE,
                                    on_click=lambda e: handle_choice(
                                        e, only_audio=True
                                    ),
                                    bgcolor=self.colors["secondary"],
                                    color=self.colors["text"],
                                ),
                            ],
                        ),
                    ),
                    bgcolor=self.colors["bg"],
                    open=True,
                    show_drag_handle=True,
                    enable_drag=True,
                )
                self.page.overlay.append(bottom_sheet)
                self.page.update()

            return ft.Card(
                content=ft.Container(
                    ref=card_content_ref,
                    content=ft.Column(
                        controls=[
                            create_thumbnail(),
                            ft.Container(
                                padding=ft.padding.only(left=10, top=5),
                                content=ft.Row(
                                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                    controls=[
                                        ft.Container(
                                            content=ft.Column(
                                                spacing=3,
                                                alignment=ft.MainAxisAlignment.CENTER,
                                                controls=[
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
                                                        max_lines=1,
                                                        overflow=ft.TextOverflow.ELLIPSIS,
                                                        color=self.colors["hint"],
                                                        size=14,
                                                    ),
                                                ],
                                            ),
                                            expand=True,
                                        ),
                                        ft.IconButton(
                                            icon=ft.Icons.DOWNLOAD,
                                            icon_color=self.colors["primary"],
                                            icon_size=24,
                                            tooltip="Download",
                                            on_click=lambda e, u=url, t=title, up=uploader, th=thumb: open_download_sheet(
                                                u, t, up, th
                                            ),
                                        ),
                                    ],
                                ),
                                width=thumb_size_w,
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    padding=ft.padding.all(5),
                    width=thumb_size_w,
                ),
                color=self.colors["bg"],
                elevation=0,
            )

        for result in results:
            result_list.controls.append(create_video_card(result))

        list_content = [result_list]
        if not self.IS_MOBILE:
            list_content = [back_button, result_list]

        content = ft.Column(
            list_content,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            expand=True,
        )

    return ft.Container(
        content=content,
        bgcolor=self.colors["bg"],
        # padding=ft.padding.symmetric(horizontal=0 if self.IS_MOBILE else 40),
        width=w,
        expand=True,
    )
