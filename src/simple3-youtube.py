import flet as ft


class Song(object):
    def __init__(self, song_name: str, artist_name: str, audio_path: str, img_path: str) -> None:
        super(Song, self).__init__()
        self.song_name: str = song_name
        self.artist_name: str = artist_name
        self.audio_path: str = audio_path
        self.img_path: str = img_path

    @property
    def name(self) -> str:
        return self.song_name

    @property
    def artist(self) -> str:
        return self.artist_name

    @property
    def path(self) -> str:
        return self.audio_path

    @property
    def path_img(self) -> str:
        return self.img_path


class AudioDirectory(object):
    playlist: list = [
        Song(
            song_name="Hungarian Rhapsody No. 2",
            artist_name="liszt",
            audio_path="0.mp3",
            img_path="img0.jpg",
        ),
        Song(
            song_name="Seasons",
            artist_name="Telecasted",
            audio_path="1.mp3",
            img_path="img1.jpg",
        ),
    ]




class Playlist(ft.View):
    def __init__(self) -> None:
        super().__init__(
            route="/playlist",
            horizontal_alignment="center"
        )

        self.playlist: list[Song] = AudioDirectory.playlist

        self.controls = [
            ft.Row(
                [ft.Text("PLAYLIST", size=21, weight="bold")],
                alignment="center",
            ),
            ft.Divider(height=10, color="transparent"),
        ]



def main(page: ft.Page) -> None:
    page.theme_mode = ft.ThemeMode.LIGHT

    def router(route) -> None:
        page.views.clear()

        if page.route == "/playlist":
            page.views.append(Playlist())


        page.update()

    page.on_route_change = router
    page.go("/playlist")

ft.run(main=main, assets_dir='assets', view=ft.AppView.FLET_APP_WEB)