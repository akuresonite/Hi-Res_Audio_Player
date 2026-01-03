import flet as ft
from tinytag import TinyTag
import os
import base64

def main(page: ft.Page):
    # 1. Page Configuration for Mobile Feel
    page.title = "Hi-Res Player"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 20
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    # Set a dark background color specific to music apps
    page.bgcolor = "#121212"
    page.scroll = ft.ScrollMode.AUTO # Enable scrolling for smaller screens

    # State variables
    current_track_path = None
    is_playing = False
    duration = 0  # in milliseconds
    playlist = [] # List of file paths
    current_playlist_index = -1

    # --- HELPER FUNCTIONS ---
    def format_time(milliseconds):
        seconds = int(milliseconds / 1000)
        minutes = seconds // 60
        seconds = seconds % 60
        return f"{minutes}:{seconds:02d}"

    def get_album_art_base64(file_path):
        try:
            tag = TinyTag.get(file_path, image=True)
            image_data = tag.get_image()
            if image_data:
                return base64.b64encode(image_data).decode('utf-8')
        except Exception:
            pass
        return None

    # --- EVENT HANDLERS ---
    
    def on_file_picked(e):
        nonlocal current_track_path, playlist, current_playlist_index
        if e.files and len(e.files) > 0:
            playlist = [f.path for f in e.files]
            current_playlist_index = 0
            update_playlist_view()
            load_track(playlist[0])

    def on_folder_picked(e):
        nonlocal playlist, current_playlist_index
        if e.path:
            # Scan directory
            supported_ext = ('.mp3', '.flac', '.wav', '.m4a')
            new_playlist = []
            try:
                for root, dirs, files in os.walk(e.path):
                    for file in files:
                        if file.lower().endswith(supported_ext):
                            new_playlist.append(os.path.join(root, file))
                
                if new_playlist:
                    playlist = sorted(new_playlist)
                    current_playlist_index = 0
                    update_playlist_view()
                    load_track(playlist[0])
                    print(f"Loaded {len(playlist)} tracks.")
                else:
                    print("No audio files found in folder.")
            except Exception as err:
                print(f"Error scanning folder: {err}")

    def update_playlist_view():
        playlist_view.controls.clear()
        for i, track_path in enumerate(playlist):
            fname = os.path.basename(track_path)
            is_active = (i == current_playlist_index)
            
            # Create a localized closure for the click handler
            def play_clicked_track(e, index=i):
                 nonlocal current_playlist_index
                 current_playlist_index = index
                 load_track(playlist[current_playlist_index])

            tile = ft.ListTile(
                leading=ft.Icon(ft.icons.MUSIC_NOTE, color=ft.colors.CYAN_400 if is_active else ft.colors.GREY_500),
                title=ft.Text(fname, color=ft.colors.CYAN_400 if is_active else ft.colors.WHITE, weight="bold" if is_active else "normal"),
                subtitle=ft.Text(f"Track {i+1}", size=12),
                on_click=play_clicked_track,
                selected=is_active,
            )
            playlist_view.controls.append(tile)
        playlist_view.update()

    def load_track(file_path):
        nonlocal current_track_path, duration, is_playing
        current_track_path = file_path
        
        # Reset UI
        current_time.value = "0:00"
        progress_slider.value = 0
        play_button_icon.icon = ft.icons.PLAY_ARROW_ROUNDED
        
        # Determine Album Art Source
        # Default placeholder
        album_art_image.src = "https://loremflickr.com/500/500/abstract,music"
        album_art_image.src_base64 = None

        # Get Metadata
        try:
            tag = TinyTag.get(file_path, image=True)
            track_title.value = tag.title if tag.title else os.path.basename(file_path)
            artist_name.value = tag.artist if tag.artist else "Unknown Artist"
            
            # Update Audio Specs Badge
            sample_rate = f"{tag.samplerate} Hz" if tag.samplerate else ""
            bitrate = f"{tag.bitrate} kbits/s" if tag.bitrate else ""
            audio_specs_text.value = f" {os.path.splitext(file_path)[1][1:].upper()} | {bitrate} | {sample_rate}"
            
            # Load duration
            if tag.duration:
                duration = tag.duration * 1000 # convert to ms
                total_duration.value = format_time(duration)
                progress_slider.max = duration
            
            # Album Art
            art_b64 = get_album_art_base64(file_path)
            if art_b64:
                album_art_image.src_base64 = art_b64
                album_art_image.src = "" # Clear URL src when using base64
            
        except Exception as err:
            print(f"Error loading metadata: {err}")
            track_title.value = os.path.basename(file_path)
            artist_name.value = "Unknown"
            audio_specs_text.value = "Unknown Format"

        audio_player.src = file_path
        audio_player.autoplay = True
        audio_player.update()
        
        # Auto play state
        is_playing = True
        play_button_icon.icon = ft.icons.PAUSE_ROUNDED
        play_button_icon.update()
        
        # Update playlist highlighting
        update_playlist_view()
        
        page.update()

    def toggle_play_pause(e):
        nonlocal is_playing
        if not current_track_path:
            return
            
        if is_playing:
            audio_player.pause()
            play_button_icon.icon = ft.icons.PLAY_ARROW_ROUNDED
            is_playing = False
        else:
            audio_player.resume()
            play_button_icon.icon = ft.icons.PAUSE_ROUNDED
            is_playing = True
        
        play_button_icon.update()

    def play_next(e):
        nonlocal current_playlist_index
        if playlist and len(playlist) > 0:
            current_playlist_index = (current_playlist_index + 1) % len(playlist)
            load_track(playlist[current_playlist_index])

    def play_prev(e):
        nonlocal current_playlist_index
        if playlist and len(playlist) > 0:
            current_playlist_index = (current_playlist_index - 1) % len(playlist)
            load_track(playlist[current_playlist_index])

    def on_seek(e):
        if not current_track_path:
            return
        audio_player.seek(int(progress_slider.value))

    def on_position_changed(e):
        curr_pos = int(e.data)
        progress_slider.value = curr_pos
        current_time.value = format_time(curr_pos)
        progress_slider.update()
        current_time.update()

    def on_duration_changed(e):
        nonlocal duration
        duration = int(e.data)
        progress_slider.max = duration
        total_duration.value = format_time(duration)
        page.update()

    def on_audiostate_changed(e):
        if e.data == "completed":
            play_next(None)

    # --- CONTROLS ---

    # Audio Object
    audio_player = ft.Audio(
        src="https://loremflickr.com/audio.mp3", # Dummy src
        autoplay=False,
        on_position_changed=on_position_changed,
        on_duration_changed=on_duration_changed,
        on_state_changed=on_audiostate_changed,
        on_seek_complete=lambda _: print("Seek complete"),
    )
    page.overlay.append(audio_player)

    # File Pickers
    file_picker = ft.FilePicker(on_result=on_file_picked)
    folder_picker = ft.FilePicker(on_result=on_folder_picked)
    page.overlay.extend([file_picker, folder_picker])

    # UI Components
    
    # A. AppBar
    page.appbar = ft.AppBar(
        leading_width=40,
        title=ft.Text("Now Playing", weight="bold", size=16),
        center_title=True,
        bgcolor=ft.colors.TRANSPARENT,
        actions=[
            ft.IconButton(ft.icons.CAST),
            ft.IconButton(ft.icons.MORE_VERT),
        ],
    )

    # B. Album Art
    album_art_image = ft.Image(
        src="https://loremflickr.com/500/500/abstract,music",
        fit=ft.ImageFit.COVER,
        border_radius=ft.border_radius.all(20),
    )
    
    album_art = ft.Container(
        content=album_art_image,
        width=300, # Reduced size for mobile
        height=300,
        alignment=ft.alignment.center,
    )

    # C. Track Info
    track_title = ft.Text("No Track Selected", size=24, weight="bold", text_align="center")
    artist_name = ft.Text("Select a file to play", size=16, color=ft.colors.GREY_400)
    
    audio_specs_text = ft.Text("FLAC  |  24-BIT  |  96 KHZ", color=ft.colors.CYAN_400, weight="bold", size=12)
    audio_specs_badge = ft.Container(
        content=ft.Row(
            [
                ft.Icon(ft.icons.AUDIOTRACK, color=ft.colors.CYAN_400, size=16),
                audio_specs_text,
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=5
        ),
        padding=ft.padding.symmetric(horizontal=12, vertical=6),
        bgcolor=ft.colors.with_opacity(0.1, ft.colors.CYAN_400),
        border_radius=ft.border_radius.all(50),
        margin=ft.margin.only(top=10)
    )

    track_info_column = ft.Column(
        [track_title, artist_name, audio_specs_badge],
        alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=5
    )

    # D. Progress
    current_time = ft.Text("0:00", size=12)
    total_duration = ft.Text("0:00", size=12)
    
    progress_slider = ft.Slider(
        value=0,
        min=0,
        max=100,
        active_color=ft.colors.WHITE,
        inactive_color=ft.colors.GREY_800,
        thumb_color=ft.colors.WHITE,
        on_change_end=on_seek
    )
    
    progress_container = ft.Column([
        progress_slider,
        ft.Row([current_time, total_duration], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
    ])

    # E. Playback Controls
    play_button_icon = ft.IconButton(
        icon=ft.icons.PLAY_ARROW_ROUNDED,
        icon_color=ft.colors.BLACK,
        icon_size=40,
        bgcolor=ft.colors.WHITE,
        on_click=toggle_play_pause
    )
    
    play_button = ft.Container(
        content=play_button_icon,
        border_radius=ft.border_radius.all(50),
        padding=5,
        bgcolor=ft.colors.WHITE
    )

    controls_row = ft.Row(
        [
            ft.IconButton(ft.icons.SHUFFLE, icon_color=ft.colors.GREY_500),
            ft.IconButton(ft.icons.SKIP_PREVIOUS_ROUNDED, icon_size=35, on_click=play_prev), # Linked
            play_button,
            ft.IconButton(ft.icons.SKIP_NEXT_ROUNDED, icon_size=35, on_click=play_next), # Linked
            ft.IconButton(ft.icons.REPEAT, icon_color=ft.colors.GREY_500),
        ],
        alignment=ft.MainAxisAlignment.SPACE_EVENLY,
        vertical_alignment=ft.CrossAxisAlignment.CENTER
    )

    # F. Library Buttons
    file_btn = ft.ElevatedButton(
        "Add File",
        icon=ft.icons.AUDIO_FILE,
        color=ft.colors.WHITE,
        bgcolor=ft.colors.GREY_900,
        on_click=lambda _: file_picker.pick_files(allow_multiple=False, allowed_extensions=["mp3", "flac", "wav", "m4a"])
    )
    
    folder_btn = ft.ElevatedButton(
        "Add Folder",
        icon=ft.icons.CREATE_NEW_FOLDER,
        color=ft.colors.WHITE,
        bgcolor=ft.colors.GREY_900,
        on_click=lambda _: folder_picker.get_directory_path()
    )

    library_row = ft.Row(
        [file_btn, folder_btn],
        alignment=ft.MainAxisAlignment.CENTER,
        spacing=20
    )

    # G. Playlist View
    playlist_view = ft.ListView(
        expand=True,
        spacing=10,
        padding=20,
        auto_scroll=False,
        height=300 # Limit height so it doesn't take over whole screen initially
    )


    # --- ASSEMBLING THE PAGE ---
    layout_column = ft.Column(
        [
            ft.Container(height=10),
            album_art,
            ft.Container(height=20),
            track_info_column,
            ft.Container(height=20),
            progress_container,
            ft.Container(height=10),
            controls_row,
            ft.Divider(color=ft.colors.TRANSPARENT),
            library_row,
            ft.Divider(color=ft.colors.GREY_800), # Separator
            ft.Text("Playlist Queue", weight="bold", size=18),
            playlist_view
        ],
        alignment=ft.MainAxisAlignment.START, # Changed to start to allow list to flow down
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        scroll=ft.ScrollMode.AUTO # Enable scroll on the column itself
    )

    # Page scroll handles the whole page, but since we put scroll on column, 
    # we might want to disable page scroll or keep it. 
    # With a ListView inside a Column, we need to be careful.
    # best approach: Make the page scrollable, set ListView shrink_wrap=True or specific height.
    # I set height=300 for ListView.
    
    page.add(layout_column)

ft.app(target=main)