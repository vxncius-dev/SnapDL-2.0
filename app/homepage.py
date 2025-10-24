import flet as ft
from json import dumps


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
            # self.log(dumps(self.search_result, indent=4))
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
        padding=ft.padding.only(bottom=0 if self.IS_MOBILE else 50),
        bgcolor=self.colors["bg"],
        image=decoration(False),
        expand=True,
    )
