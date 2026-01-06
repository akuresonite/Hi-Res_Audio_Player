import flet as ft
import flet_audio as fta
import os
from pathlib import Path


def main(page: ft.Page):

    page.window_width = 100
    page.window_height = 300
    page.window_resizable = True

    PLAYLIST = []
    CURRENT_TRACK = 0

    url = "../assets/viper.mp3"
    audio = fta.Audio(
        src=url,
        autoplay=False,
        volume=1,
        balance=0,
        on_loaded=lambda _: print("Loaded", ">"*20),
        on_duration_change=lambda e: print("Duration changed:", e.duration),
        on_position_change=lambda e: print("Position changed:", e.position),
        on_state_change=lambda e: print("State changed:", e.state),
        on_seek_complete=lambda _: print("Seek complete"),
    )
    # page.overlay.append(audio)

    async def handle_pick_files(e: ft.Event[ft.Button]):
        nonlocal CURRENT_TRACK

        files = await ft.FilePicker().pick_files(allow_multiple=True)
        if not files:
            selected_files.value = "Cancelled!"
            page.update()
            return

        PLAYLIST.clear()
        CURRENT_TRACK = 0

        for file in files:
            PLAYLIST.append(Path(file.path).as_posix())

        selected_files.value = ", ".join(PLAYLIST)

        audio.src = PLAYLIST[CURRENT_TRACK]
        audio.autoplay = True
        audio.update()
        page.update()


    
    async def previous(e: ft.Event[ft.Button]):
        nonlocal CURRENT_TRACK

        if not PLAYLIST:
            return

        if CURRENT_TRACK > 0:
            CURRENT_TRACK -= 1
            await audio.pause()
            audio.src = PLAYLIST[CURRENT_TRACK]
            print("-"*30, "\n", "Previous track:", audio.src, "\n", "-"*30)
            audio.autoplay = True
            audio.update()


    async def next(e: ft.Event[ft.Button]):
        nonlocal CURRENT_TRACK

        if not PLAYLIST:
            return

        if CURRENT_TRACK < len(PLAYLIST) - 1:
            CURRENT_TRACK += 1
            await audio.pause()
            audio.src = PLAYLIST[CURRENT_TRACK]
            print("-"*30, "\n", "Next track:", audio.src, "\n", "-"*30)
            audio.autoplay = True
            audio.update()


    async def play(e: ft.Event[ft.Button]):
        if not PLAYLIST:
            return

        await audio.pause()
        audio.src = PLAYLIST[CURRENT_TRACK]
        print("-"*30, "\n", "Playing track:", audio.src, "\n", "-"*30)
        audio.update()
        await audio.play()


    async def pause(e: ft.Event[ft.Button]):
        await audio.pause()

    async def resume(e: ft.Event[ft.Button]):
        await audio.resume()

    async def release(e: ft.Event[ft.Button]):
        await audio.release()

    def set_volume(value: float):
        audio.volume += value

    def set_balance(value: float):
        audio.balance += value

    async def seek_2s(e: ft.Event[ft.Button]):
        await audio.seek(ft.Duration(seconds=2))

    async def get_duration(e: ft.Event[ft.Button]):
        duration = await audio.get_duration()
        print("Duration:", duration)

    async def on_get_current_position(e: ft.Event[ft.Button]):
        position = await audio.get_current_position()
        print("Current position:", position)

    # def on_seek(e: ft.Event[ft.Button]):
    #     if not current_track:
    #         return
    #     audio_player.seek(int(progress_slider.value))

    
    # --- PAGE ---
    page.add(
        ft.Column(
            spacing=50,
            controls=[
                ft.Column(
                controls=[
                    ft.Button(
                        content="Pick files",
                        icon=ft.Icons.UPLOAD_FILE,
                        on_click=handle_pick_files,
                    ),
                    selected_files := ft.Text(),
                ]
                ),
                ft.Row(
                    controls=[
                        ft.Button("Play", on_click=play),
                        ft.Button("Pause", on_click=pause),
                        ft.Button("Resume", on_click=resume),
                    ]
                ),
                ft.Row(
                    controls=[
                        ft.Button("Previous", on_click=previous),
                        ft.Button("Next", on_click=next),
                    ]
                ),
                ft.Row(
                    controls=[
                        ft.Button("Volume down", on_click=lambda _: set_volume(-0.1)),
                        ft.Button("Volume up", on_click=lambda _: set_volume(0.1)),
                    ]
                ),
                ft.Row(
                    controls=[
                        ft.Button("Release", on_click=release),
                        ft.Button("Seek 2s", on_click=seek_2s),
                    ]
                ),
                ft.Row(
                    controls=[
                        ft.Button("Balance left", on_click=lambda _: set_balance(-0.1)),
                        ft.Button("Balance right", on_click=lambda _: set_balance(0.1)),
                    ]
                ),
                ft.Row(
                    controls=[
                        ft.Button("Get duration", on_click=get_duration),
                        ft.Button("Get current position", on_click=on_get_current_position),
                    ]
                ),
            ],
        )
    )


ft.run(main)
