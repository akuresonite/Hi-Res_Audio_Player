import flet as ft
import os
from pathlib import Path


def main(page: ft.Page):
    PLAYLIST = []

    async def handle_pick_files(e: ft.Event[ft.Button]):
        files = await ft.FilePicker().pick_files(allow_multiple=True)
        for file in files:
            PLAYLIST.append(Path(file.path).as_posix())
        print(PLAYLIST)

        lv = ft.ListView(expand=True, spacing=10)
        for i, track in enumerate(PLAYLIST):
            lv.controls.append(ft.Text(f"{i+1}: {track}"))
        page.add(lv)

    page.add(
        ft.Button(
                content="Pick files",
                icon=ft.Icons.UPLOAD_FILE,
                on_click=handle_pick_files,
                    )
    )



# ft.run(main, view=ft.AppView.WEB_BROWSER)
ft.run(main)