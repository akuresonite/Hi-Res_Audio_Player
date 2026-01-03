import flet as ft
from tinytag import TinyTag
import os
import base64

def main(page: ft.Page):
    # 1. Page Configuration
    page.title = "Hi-Res Player"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 0
    page.spacing = 0
    page.bgcolor = "#000000"

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
            load_track(playlist[0])

    def on_folder_picked(e):
        nonlocal playlist, current_playlist_index
        if e.path:
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
                    load_track(playlist[0])
                    print(f"Loaded {len(playlist)} tracks.")
                else:
                    print("No audio files found in folder.")
            except Exception as err:
                print(f"Error scanning folder: {err}")

    # Re-renders the entire scrollable view (Header + Queue items)
    def update_main_view():
        # Clear existing controls
        main_list_view.controls.clear()

        # 1. THE PLAYER HEADER (Art, Info, Controls)
        # This is the first item in the list
        
        # Determine current track info (safe access)
        title = "No Track Selected"
        artist = "Select a file to play"
        has_track = current_track_path is not None
        
        # We need to construct these dynamically or update their values?
        # Flet controls are objects. We can keep the objects and just put them in the list.
        # But we need to make sure their values are updated before adding.
        # Actually, since we clear list_view.controls, we are re-attaching the SAME control objects.
        # This works if we update the control properties separately.
        
        # Build the Header Container
        header_container = ft.Container(
            content=ft.Column([
                ft.Container(height=60), # Top spacing for the Fixed AppBar
                
                # Album Art (Foreground)
                ft.Container(
                    content=album_art_foreground,
                    alignment=ft.alignment.center,
                    padding=ft.padding.symmetric(vertical=20)
                ),
                
                # Track Info
                track_title,
                artist_name,
                
                ft.Container(height=20),
                
                # Progress
                ft.Row([current_time, ft.Container(expand=True), total_duration], width=320),
                progress_slider,
                
                ft.Container(height=10),
                
                # Controls
                controls_row,
                
                ft.Container(height=20),
                library_actions,
                
                ft.Container(height=20),
                ft.Text("Up Next", size=18, weight="bold", color=ft.colors.WHITE),
                ft.Container(height=10),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            padding=20
        )
        
        main_list_view.controls.append(header_container)

        # 2. QUEUE ITEMS
        for i, track_path in enumerate(playlist):
            fname = os.path.basename(track_path)
            is_active = (i == current_playlist_index)
            
            def play_clicked_track(e, index=i):
                 nonlocal current_playlist_index
                 current_playlist_index = index
                 load_track(playlist[current_playlist_index])

            tile = ft.Container(
                content=ft.Row([
                    ft.Text(f"{i+1}", color=ft.colors.GREY_500, width=30),
                    ft.Column([
                        ft.Text(fname, color=ft.colors.CYAN_400 if is_active else ft.colors.WHITE, 
                               weight="bold" if is_active else "normal",
                               size=16, overflow=ft.TextOverflow.ELLIPSIS),
                       # ft.Text("Artist Name", color=ft.colors.GREY_600, size=12) 
                    ], expand=True),
                    ft.Icon(ft.icons.GRAPHIC_EQ if is_active else None, color=ft.colors.CYAN_400, size=20)
                ]),
                padding=ft.padding.symmetric(vertical=10, horizontal=20),
                border_radius=10,
                bgcolor=ft.colors.with_opacity(0.1, ft.colors.WHITE) if is_active else None,
                on_click=play_clicked_track
            )
            main_list_view.controls.append(tile)

        # Update the list view
        main_list_view.update()

    def load_track(file_path):
        nonlocal current_track_path, duration, is_playing
        current_track_path = file_path
        
        # Reset UI Values
        current_time.value = "0:00"
        progress_slider.value = 0
        play_button_icon.icon = ft.icons.PLAY_ARROW_ROUNDED
        
        # Images Defaults
        default_img = "https://loremflickr.com/500/500/abstract,music"
        img_bg.src = default_img
        img_bg.src_base64 = None
        album_art_image_control.src = default_img
        album_art_image_control.src_base64 = None

        # Metadata extraction
        try:
            tag = TinyTag.get(file_path, image=True)
            track_title.value = tag.title if tag.title else os.path.basename(file_path)
            artist_name.value = tag.artist if tag.artist else "Unknown Artist"
            
            if tag.duration:
                duration = tag.duration * 1000 
                total_duration.value = format_time(duration)
                progress_slider.max = duration
            
            # Art extraction
            art_b64 = get_album_art_base64(file_path)
            if art_b64:
                img_bg.src_base64 = art_b64
                img_bg.src = ""
                album_art_image_control.src_base64 = art_b64
                album_art_image_control.src = ""
            
        except Exception as err:
            print(f"Error loading metadata: {err}")
            track_title.value = os.path.basename(file_path)

        # Audio Player
        audio_player.src = file_path
        audio_player.autoplay = True
        audio_player.update()
        
        is_playing = True
        play_button_icon.icon = ft.icons.PAUSE_ROUNDED
        
        # Refresh the whole view to prevent stale state and update highlighting
        update_main_view()
        
        # We need to update individual components that might have changed if update_main_view() doesn't force redraw of them
        # (It re-adds them, so it usually refreshes, but for safety updating values first is good)
        img_bg.update()
        # No need to call page.update() if we update main_list_view and img_bg
        
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
        # Note: We don't need full page update here, just the slider/text
        progress_slider.update()
        total_duration.update()

    def on_audiostate_changed(e):
        if e.data == "completed":
            play_next(None)

    # --- CONTROLS INSTANCES ---
    
    # Audio
    audio_player = ft.Audio(
        src="https://loremflickr.com/audio.mp3",
        autoplay=False,
        on_position_changed=on_position_changed,
        on_duration_changed=on_duration_changed,
        on_state_changed=on_audiostate_changed,
    )
    page.overlay.append(audio_player)

    # Pickers
    file_picker = ft.FilePicker(on_result=on_file_picked)
    folder_picker = ft.FilePicker(on_result=on_folder_picked)
    page.overlay.extend([file_picker, folder_picker])
    
    # -- UI COMPONENTS (Defined once, re-used in loop) --
    
    # Background Image
    img_bg = ft.Image(
        src="https://loremflickr.com/500/500/abstract,music",
        fit=ft.ImageFit.COVER,
        opacity=0.4,
    )
    
    # Foreground Album Art
    # ft.Image does not support shadow directly in some versions. Wrap in Container.
    album_art_image_control = ft.Image(
        src="https://loremflickr.com/500/500/abstract,music",
        width=250, height=250,
        fit=ft.ImageFit.COVER,
        border_radius=20,
    )
    
    album_art_foreground = ft.Container(
        content=album_art_image_control,
        shadow=ft.BoxShadow(blur_radius=20, color=ft.colors.BLACK),
        border_radius=20
    )
    
    track_title = ft.Text("No Track", size=24, weight="bold", color=ft.colors.WHITE, text_align="center")
    artist_name = ft.Text("Select a folder...", size=16, color=ft.colors.GREY_400)
    
    current_time = ft.Text("0:00", size=12, color=ft.colors.GREY_300)
    total_duration = ft.Text("0:00", size=12, color=ft.colors.GREY_300)
    progress_slider = ft.Slider(value=0, min=0, max=100, active_color=ft.colors.WHITE, thumb_color=ft.colors.WHITE, on_change_end=on_seek)
    
    # Buttons
    play_button_icon = ft.IconButton(
        icon=ft.icons.PLAY_ARROW_ROUNDED,
        icon_color=ft.colors.BLACK,
        icon_size=40,
        bgcolor=ft.colors.WHITE,
        on_click=toggle_play_pause
    )
    play_btn_container = ft.Container(content=play_button_icon, border_radius=50, bgcolor=ft.colors.WHITE, padding=5)
    
    controls_row = ft.Row(
        [
            ft.IconButton(ft.icons.SHUFFLE, icon_color=ft.colors.GREY_500),
            ft.IconButton(ft.icons.SKIP_PREVIOUS_ROUNDED, icon_color=ft.colors.WHITE, icon_size=30, on_click=play_prev),
            play_btn_container,
            ft.IconButton(ft.icons.SKIP_NEXT_ROUNDED, icon_color=ft.colors.WHITE, icon_size=30, on_click=play_next),
            ft.IconButton(ft.icons.REPEAT, icon_color=ft.colors.GREY_500),
        ],
        alignment=ft.MainAxisAlignment.SPACE_EVENLY,
        vertical_alignment=ft.CrossAxisAlignment.CENTER
    )
    
    library_actions = ft.Row([
        ft.OutlinedButton("File", icon=ft.icons.AUDIO_FILE, style=ft.ButtonStyle(color=ft.colors.GREY_300), on_click=lambda _: file_picker.pick_files(allow_multiple=False, allowed_extensions=["mp3", "flac"])),
        ft.OutlinedButton("Folder", icon=ft.icons.CREATE_NEW_FOLDER, style=ft.ButtonStyle(color=ft.colors.GREY_300), on_click=lambda _: folder_picker.get_directory_path())
    ], alignment=ft.MainAxisAlignment.CENTER)

    # Main Scrollable View
    main_list_view = ft.ListView(
        expand=True,
        padding=0,
        spacing=0
    )

    # AppBar (Fixed Overlay)
    app_bar_row = ft.Row(
        [
            ft.IconButton(ft.icons.KEYBOARD_ARROW_DOWN, icon_color=ft.colors.WHITE),
            ft.Text("NOW PLAYING", size=12, weight="bold", color=ft.colors.GREY_400),
            ft.IconButton(ft.icons.MORE_HORIZ, icon_color=ft.colors.WHITE),
        ],
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN
    )



    # --- FINAL COMPOSITION ---
    stack = ft.Stack(
        [
            # Layer 1: Background
            ft.Container(content=img_bg, expand=True, alignment=ft.alignment.center),
            
            # Layer 2: Gradient
            ft.Container(
                gradient=ft.LinearGradient(
                    begin=ft.alignment.top_center,
                    end=ft.alignment.bottom_center,
                    colors=[ft.colors.with_opacity(0.5, ft.colors.BLACK), ft.colors.BLACK],
                    stops=[0.0, 1.0]
                ),
                expand=True
            ),
            
            # Layer 3: Scrollable Content
            main_list_view,
            
            # Layer 4: Fixed Header (App Bar)
            ft.Container(content=app_bar_row, padding=ft.padding.symmetric(horizontal=10, vertical=5), bgcolor=ft.colors.TRANSPARENT, height=60),
        ],
        expand=True
    )

    page.add(stack)
    
    # Initialize View after adding to page
    update_main_view()

ft.app(target=main)