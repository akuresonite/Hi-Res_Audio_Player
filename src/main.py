import flet as ft
from tinytag import TinyTag
import os
import base64
import re

def main(page: ft.Page):
    # 1. Page Configuration
    page.title = "Hi-Res Player"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 0
    page.spacing = 0
    page.bgcolor = "#000000"

    # State variables
    current_track = None # Dictionary
    is_playing = False
    duration = 0  # in milliseconds
    playlist = [] # List of dicts: {path, title, artist, duration, ext, filename}
    current_playlist_index = -1
    playback_rate = 1.0
    current_sort_key = "File Name"

    # --- HELPER FUNCTIONS ---
    def format_time(milliseconds):
        if not milliseconds: return "0:00"
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

    def extract_metadata(file_path):
        filename = os.path.basename(file_path)
        ext = os.path.splitext(filename)[1].replace('.', '').upper()
        
        try:
            tag = TinyTag.get(file_path, image=False) # Image loaded on demand
            title = tag.title if tag.title else filename
            artist = tag.artist if tag.artist else "Unknown Artist"
            dur = tag.duration * 1000 if tag.duration else 0
            return {
                "path": file_path,
                "title": title,
                "artist": artist,
                "duration": dur,
                "ext": ext,
                "filename": filename
            }
        except Exception as e:
            print(f"Error reading {filename}: {e}")
            return {
                "path": file_path,
                "title": filename,
                "artist": "Unknown",
                "duration": 0,
                "ext": ext,
                "filename": filename
            }

    def natural_sort_key(s):
        # Splits string into list of strings and integers: "foo20bar" -> ["foo", 20, "bar"]
        return [int(text) if text.isdigit() else text.lower()
                for text in re.split('([0-9]+)', str(s))]

    # --- EVENT HANDLERS ---
    
    def on_file_picked(e):
        nonlocal current_track, playlist, current_playlist_index
        if e.files and len(e.files) > 0:
            new_tracks = []
            for f in e.files:
                new_tracks.append(extract_metadata(f.path))
            
            playlist = new_tracks
            current_playlist_index = 0
            if playlist:
                load_track(playlist[0])
            update_main_view()

    def on_folder_picked(e):
        nonlocal playlist, current_playlist_index
        if e.path:
            supported_ext = ('.mp3', '.flac', '.wav', '.m4a', '.alac')
            new_playlist = []
            try:
                # Show loading? (Blocking for now, simpler)
                for root, dirs, files in os.walk(e.path):
                    for file in files:
                        if file.lower().endswith(supported_ext):
                            full_path = os.path.join(root, file)
                            new_playlist.append(extract_metadata(full_path))
                
                if new_playlist:
                    # Apply current sort
                    if current_sort_key == "Title":
                         new_playlist.sort(key=lambda x: natural_sort_key(x.get('title', '')))
                    else:
                         new_playlist.sort(key=lambda x: natural_sort_key(x.get('filename', '')))
                         
                    playlist = new_playlist
                    current_playlist_index = 0
                    load_track(playlist[0])
                    print(f"Loaded {len(playlist)} tracks.")
                else:
                    print("No audio files found in folder.")
            except Exception as err:
                print(f"Error scanning folder: {err}")
            
            update_main_view()

    def sort_playlist(sort_key):
        nonlocal playlist, current_playlist_index, current_sort_key
        if not playlist: return
        
        current_sort_key = sort_key
        print(f"DEBUG: Request to sort by '{sort_key}' (Natural)")
        print(f"DEBUG: Before Sort (First 3): {[t.get('title') for t in playlist[:3]]}")
        
        # Store current playing path to restore index
        current_path = playlist[current_playlist_index]['path'] if current_playlist_index >= 0 and current_playlist_index < len(playlist) else None
        
        if sort_key == "Title":
            playlist.sort(key=lambda x: natural_sort_key(x.get('title', '')))
        elif sort_key == "File Name":
            playlist.sort(key=lambda x: natural_sort_key(x.get('filename', '')))
            
        print(f"DEBUG: After Sort (First 3): {[t.get('title') for t in playlist[:3]]}")

        # Restore index
        if current_path:
            for i, track in enumerate(playlist):
                if track['path'] == current_path:
                    current_playlist_index = i
                    break
        
        update_main_view()

    # Re-renders the entire scrollable view (Header + Queue items)
    def update_main_view():
        # Clear existing controls
        main_list_view.controls.clear()

        # 1. THE PLAYER HEADER
        # We rebuild ALL controls here to ensure they are fresh and correctly attached.
        
        # Speed Controls
        speed_row = ft.Row([
            ft.Text("Speed:", color=ft.colors.GREY_400, size=12),
            ft.IconButton(ft.icons.REMOVE_CIRCLE_OUTLINE, icon_color=ft.colors.GREY_300, icon_size=20, on_click=lambda e: change_speed(-0.25)),
            ft.Text(f"{playback_rate}x", color=ft.colors.WHITE, size=12, weight="bold"),
            ft.IconButton(ft.icons.ADD_CIRCLE_OUTLINE, icon_color=ft.colors.GREY_300, icon_size=20, on_click=lambda e: change_speed(0.25)),
        ], alignment=ft.MainAxisAlignment.CENTER, spacing=5)

        # Play/Pause Button
        current_icon = ft.icons.PAUSE_ROUNDED if is_playing else ft.icons.PLAY_ARROW_ROUNDED
        play_btn = ft.Container(
            content=ft.IconButton(
                icon=current_icon,
                icon_color=ft.colors.BLACK,
                icon_size=40,
                bgcolor=ft.colors.WHITE,
                on_click=toggle_play_pause
            ),
            border_radius=50, 
            bgcolor=ft.colors.WHITE, 
            padding=5
        )

        current_controls_row = ft.Row(
            [
                ft.IconButton(ft.icons.SHUFFLE, icon_color=ft.colors.GREY_500),
                ft.IconButton(ft.icons.SKIP_PREVIOUS_ROUNDED, icon_color=ft.colors.WHITE, icon_size=30, on_click=play_prev),
                play_btn,
                ft.IconButton(ft.icons.SKIP_NEXT_ROUNDED, icon_color=ft.colors.WHITE, icon_size=30, on_click=play_next),
                ft.IconButton(ft.icons.REPEAT, icon_color=ft.colors.GREY_500),
            ],
            alignment=ft.MainAxisAlignment.SPACE_EVENLY,
            vertical_alignment=ft.CrossAxisAlignment.CENTER
        )

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
                
                # Speed Controls
                speed_row,

                ft.Container(height=10),
                
                # Controls
                current_controls_row,
                
                ft.Container(height=20),
                library_actions,
                
                ft.Container(height=20),
                
                # Queue Header & Sort
                ft.Row([
                    ft.Text("Up Next", size=18, weight="bold", color=ft.colors.WHITE),
                    ft.Dropdown(
                        options=[
                            ft.dropdown.Option("File Name"),
                            ft.dropdown.Option("Title"),
                        ],
                        value=current_sort_key,
                        width=120,
                        text_size=12,
                        height=40,
                        content_padding=10,
                        on_change=lambda e: sort_playlist(e.data),
                        bgcolor=ft.colors.GREY_900,
                        color=ft.colors.WHITE,
                        border_color=ft.colors.GREY_700,
                    )
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                
                ft.Container(height=10),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            padding=20
        )
        
        main_list_view.controls.append(header_container)

        # 2. QUEUE ITEMS
        for i, track in enumerate(playlist):
            is_active = (i == current_playlist_index)
            
            def play_clicked_track(e, index=i):
                 nonlocal current_playlist_index
                 current_playlist_index = index
                 load_track(playlist[current_playlist_index])

            tile = ft.Container(
                content=ft.Row([
                    ft.Text(f"{i+1}", color=ft.colors.GREY_500, width=30, size=12),
                    
                    # Title
                    ft.Column([
                        ft.Text(track.get('title', 'Unknown'), 
                               color=ft.colors.CYAN_400 if is_active else ft.colors.WHITE, 
                               weight="bold" if is_active else "normal",
                               size=14, overflow=ft.TextOverflow.ELLIPSIS),
                    ], expand=True),
                    
                    # Metadata (Time | Type)
                    ft.Row([
                       ft.Text(format_time(track.get('duration', 0)), color=ft.colors.GREY_500, size=11, font_family="monospace"),
                       ft.Container(
                           content=ft.Text(track.get('ext', ''), size=9, weight="bold", color=ft.colors.BLACK),
                           bgcolor=ft.colors.GREY_400,
                           padding=ft.padding.symmetric(horizontal=4, vertical=2),
                           border_radius=4
                       )
                    ], spacing=10, alignment=ft.MainAxisAlignment.END)
                    
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                padding=ft.padding.symmetric(vertical=8, horizontal=15),
                border_radius=8,
                bgcolor=ft.colors.with_opacity(0.1, ft.colors.WHITE) if is_active else None,
                on_click=play_clicked_track,
                ink=True
            )
            main_list_view.controls.append(tile)

        # Update the list view
        page.update()

    def load_track(track_data):
        nonlocal current_track, duration, is_playing
        current_track = track_data
        file_path = track_data['path']
        
        # Reset UI Values
        current_time.value = "0:00"
        progress_slider.value = 0
        
        # Images Defaults
        default_img = "https://loremflickr.com/500/500/abstract,music"
        img_bg.src = default_img
        img_bg.src_base64 = None
        album_art_image_control.src = default_img
        album_art_image_control.src_base64 = None
        
        # Metadata Display
        track_title.value = track_data.get('title', 'Unknown')
        artist_name.value = track_data.get('artist', 'Unknown Artist')
        
        if track_data.get('duration'):
            duration = track_data['duration']
            total_duration.value = format_time(duration)
            progress_slider.max = duration
        
        # Art extraction (On demand to save memory in list)
        art_b64 = get_album_art_base64(file_path)
        if art_b64:
            img_bg.src_base64 = art_b64
            img_bg.src = ""
            album_art_image_control.src_base64 = art_b64
            album_art_image_control.src = ""
            
        # Audio Player
        # Ensure player stops before loading new src to avoid overlap issues
        audio_player.pause() 
        audio_player.src = file_path
        audio_player.playback_rate = playback_rate
        audio_player.autoplay = True
        
        is_playing = True
        
        # Refresh the whole view to highlight current track and update Play/Pause button
        update_main_view()
        
    def toggle_play_pause(e):
        nonlocal is_playing
        if not current_track:
            return
            
        if is_playing:
            audio_player.pause()
            is_playing = False
        else:
            audio_player.resume()
            is_playing = True
        
        # Declarative Update
        update_main_view()

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
        if not current_track:
            return
        audio_player.seek(int(progress_slider.value))

    def on_position_changed(e):
        try:
            curr_pos = int(e.data)
            progress_slider.value = curr_pos
            current_time.value = format_time(curr_pos)
            progress_slider.update()
            current_time.update()
        except Exception:
            # Control might be detached during view update; ignore safe frame drop
            pass

    def on_duration_changed(e):
        nonlocal duration
        try:
            duration = int(e.data)
            progress_slider.max = duration
            total_duration.value = format_time(duration)
            progress_slider.update()
            total_duration.update()
        except Exception:
            pass

    def on_audiostate_changed(e):
        if e.data == "completed":
            play_next(None)

    def change_speed(delta):
        nonlocal playback_rate
        playback_rate = max(0.25, min(2.0, playback_rate + delta))
        audio_player.playback_rate = playback_rate
        audio_player.update()
        
        # Declarative Update
        update_main_view()

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
    
    # -- UI COMPONENTS --
    
    # Background Image
    img_bg = ft.Image(
        src="https://loremflickr.com/500/500/abstract,music",
        fit=ft.ImageFit.COVER,
        opacity=0.4,
    )
    
    # Foreground Album Art
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
    
    # NOTE: play_button_icon, speed_text etc are now LOCAL inside update_main_view to prevent detachment issues.
    # We remove their global definitions or just ignore them.
    
    library_actions = ft.Row([
        ft.OutlinedButton("File", icon=ft.icons.AUDIO_FILE, style=ft.ButtonStyle(color=ft.colors.GREY_300), on_click=lambda _: file_picker.pick_files(allow_multiple=True, allowed_extensions=["mp3", "flac", "wav", "m4a", "alac"])),
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
    
    # Initialize View
    update_main_view()

ft.app(target=main)