import flet as ft
import flet_audio as fta
from tinytag import TinyTag
import os
import base64
import re
import asyncio
from pathlib import Path

def main(page: ft.Page):
    # Page Configuration
    page.title = "Hi-Res Player" 
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 0
    page.spacing = 0
    page.bgcolor = "#000000"
    
    # mobile aspect ratio
    page.window_width = 390
    page.window_height = 844

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
            image_data = tag.images.any
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
            
            # Extract Track Number
            track_num = 0
            if tag.track:
                try:
                    # Handle "1/12" format
                    t_str = str(tag.track).split('/')[0]
                    track_num = int(t_str) if t_str.isdigit() else 0
                except:
                    track_num = 0
            
            return {
                "path": file_path,
                "title": title,
                "artist": artist,
                "duration": dur,
                "ext": ext,
                "filename": filename,
                "track": track_num
            }
        except Exception as e:
            print(f"Error reading {filename}: {e}")
            return {
                "path": file_path,
                "title": filename,
                "artist": "Unknown",
                "duration": 0,
                "ext": ext,
                "filename": filename,
                "track": 0
            }

    def natural_sort_key(s):
        # Splits string into list of strings and integers: "foo20bar" -> ["foo", 20, "bar"]
        return [int(text) if text.isdigit() else text.lower()
                for text in re.split('([0-9]+)', str(s))]

    # --- EVENT HANDLERS ---
    
    def on_file_picked(files):
        nonlocal current_track, playlist, current_playlist_index
        if files and len(files) > 0:
            new_tracks = []
            for f in files:
                new_tracks.append(extract_metadata(f.path))
            
            playlist = new_tracks
            current_playlist_index = 0
            if playlist:
                load_track(playlist[0])
            update_main_view()

    def on_folder_picked(path):
        nonlocal playlist, current_playlist_index
        if path:
            supported_ext = ('.mp3', '.flac', '.wav', '.m4a', '.alac')
            new_playlist = []
            try:
                # Show loading? (Blocking for now, simpler)
                for root, dirs, files in os.walk(path):
                    for file in files:
                        if file.lower().endswith(supported_ext):
                            full_path = os.path.join(root, file)
                            new_playlist.append(extract_metadata(full_path))
                
                if new_playlist:
                    # Apply current sort
                    if current_sort_key == "Title":
                         new_playlist.sort(key=lambda x: natural_sort_key(x.get('title', '')))
                    elif current_sort_key == "Track Number":
                         new_playlist.sort(key=lambda x: (x.get('track', 0), natural_sort_key(x.get('title', ''))))
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
        print(f"DEBUG: Request to sort by '{sort_key}' (Natural/Track)")
        
        # Store current playing path to restore index
        current_path = playlist[current_playlist_index]['path'] if current_playlist_index >= 0 and current_playlist_index < len(playlist) else None
        
        if sort_key == "Title":
            playlist.sort(key=lambda x: natural_sort_key(x.get('title', '')))
        elif sort_key == "File Name":
            playlist.sort(key=lambda x: natural_sort_key(x.get('filename', '')))
        elif sort_key == "Track Number":
             # Primary sort: Track Number, Secondary: Title
            playlist.sort(key=lambda x: (x.get('track', 0), natural_sort_key(x.get('title', ''))))
            
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
        nonlocal progress_slider, current_time, total_duration
        
        # Clear existing controls
        main_list_view.controls.clear()

        # 1. THE PLAYER HEADER
        
        # Recreation of Controls to ensure valid attachment
        # We preserve current values from the existing objects (or state)
        current_time_val = current_time.value if hasattr(current_time, 'value') else "0:00"
        total_duration_val = total_duration.value if hasattr(total_duration, 'value') else "0:00"
        slider_val = progress_slider.value if hasattr(progress_slider, 'value') else 0
        slider_max = progress_slider.max if hasattr(progress_slider, 'max') else 100

        current_time = ft.Text(current_time_val, size=12, color=ft.Colors.GREY_300)
        total_duration = ft.Text(total_duration_val, size=12, color=ft.Colors.GREY_300)
        # progress_slider = ft.Slider(value=slider_val, min=0, max=slider_max, active_color=ft.Colors.WHITE, thumb_color=ft.Colors.WHITE)
        progress_slider.value = slider_val
        progress_slider.max = slider_max
        progress_slider.active_color = ft.Colors.WHITE
        progress_slider.thumb_color = ft.Colors.WHITE
        progress_slider.on_change_end = on_seek
        
        # Speed Controls
        btn_speed_down = ft.IconButton(ft.Icons.REMOVE_CIRCLE_OUTLINE, icon_color=ft.Colors.GREY_300, icon_size=20)
        btn_speed_down.on_click = lambda e: change_speed(-0.01)
        btn_speed_up = ft.IconButton(ft.Icons.ADD_CIRCLE_OUTLINE, icon_color=ft.Colors.GREY_300, icon_size=20)
        btn_speed_up.on_click = lambda e: change_speed(0.01)

        speed_row = ft.Row([
            ft.Text("Speed:", color=ft.Colors.GREY_400, size=12),
            btn_speed_down,
            ft.Text(f"{playback_rate:.2f}x", color=ft.Colors.WHITE, size=12, weight="bold"),
            btn_speed_up,
        ], alignment=ft.MainAxisAlignment.CENTER, spacing=5)

        # Play/Pause Button
        current_icon = ft.Icons.PAUSE_ROUNDED if is_playing else ft.Icons.PLAY_ARROW_ROUNDED
        btn_play_inner = ft.IconButton(
                icon=current_icon,
                icon_color=ft.Colors.BLACK,
                icon_size=40,
                bgcolor=ft.Colors.WHITE
            )
        btn_play_inner.on_click = toggle_play_pause

        play_btn = ft.Container(
            content=btn_play_inner,
            border_radius=50, 
            bgcolor=ft.Colors.WHITE, 
            padding=5
        )

        btn_prev = ft.IconButton(ft.Icons.SKIP_PREVIOUS_ROUNDED, icon_color=ft.Colors.WHITE, icon_size=30)
        btn_prev.on_click = play_prev
        btn_next = ft.IconButton(ft.Icons.SKIP_NEXT_ROUNDED, icon_color=ft.Colors.WHITE, icon_size=30)
        btn_next.on_click = play_next

        current_controls_row = ft.Row(
            [
                ft.IconButton(ft.Icons.SHUFFLE, icon_color=ft.Colors.GREY_500),
                btn_prev,
                play_btn,
                btn_next,
                ft.IconButton(ft.Icons.REPEAT, icon_color=ft.Colors.GREY_500),
            ],
            alignment=ft.MainAxisAlignment.SPACE_EVENLY,
            vertical_alignment=ft.CrossAxisAlignment.CENTER
        )

        sort_dd = ft.Dropdown(
                        options=[
                            ft.dropdown.Option("File Name"),
                            ft.dropdown.Option("Title"),
                            ft.dropdown.Option("Track Number"),
                        ],
                        value=current_sort_key,
                        width=140, # Slightly wider
                        text_size=12,
                        height=40,
                        content_padding=10,
                        bgcolor=ft.Colors.GREY_900,
                        color=ft.Colors.WHITE,
                        border_color=ft.Colors.GREY_700,
                    )
        sort_dd.on_change = lambda e: sort_playlist(e.data)

        queue_header_row = ft.Row([
            ft.Text("Up Next", size=18, weight="bold", color=ft.Colors.WHITE),
            sort_dd
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

        # Build the Header Container
        header_container = ft.Container(
            content=ft.Column([
                ft.Container(height=60), # Top spacing for the Fixed AppBar
                
                # Album Art (Foreground)
                ft.Container(
                    content=album_art_foreground,   
                    alignment=ft.Alignment(0, 0),
                    padding=ft.Padding(top=20, bottom=20, left=0, right=0)
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
                
                queue_header_row,
                
                ft.Container(height=10),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            padding=20
        )
        
        main_list_view.controls.append(header_container)

        # 2. QUEUE ITEMS
        for i, track in enumerate(playlist):
            is_active = (i == current_playlist_index)
            # print(track)

            async def play_clicked_track(e, index=i):
                 nonlocal current_playlist_index
                 current_playlist_index = index
                 await load_track(playlist[current_playlist_index])

            tile = ft.Container(
                content=ft.Row([
                    ft.Text(f"{i+1}", color=ft.Colors.GREY_500, width=30, size=12),
                    
                    # Title
                    ft.Column([
                        ft.Text(track.get('title', 'Unknown'), 
                               color=ft.Colors.CYAN_400 if is_active else ft.Colors.WHITE, 
                               weight="bold" if is_active else "normal",
                               size=14, overflow=ft.TextOverflow.ELLIPSIS),
                    ], expand=True),
                    
                    # Metadata (Time | Type)
                    ft.Row([
                       ft.Text(format_time(track.get('duration', 0)), color=ft.Colors.GREY_500, size=11, font_family="monospace"),
                       ft.Container(
                           content=ft.Text(track.get('ext', ''), size=9, weight="bold", color=ft.Colors.BLACK),
                           bgcolor=ft.Colors.GREY_400,
                           padding=ft.Padding(top=2, bottom=2, left=4, right=4),
                           border_radius=4
                       )
                    ], spacing=10, alignment=ft.MainAxisAlignment.END)
                    
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                padding=ft.Padding(top=8, bottom=8, left=15, right=15),
                border_radius=8,
                bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.WHITE) if is_active else None,
                ink=True
            )
            tile.on_click = play_clicked_track
            main_list_view.controls.append(tile)

        # Update the list view
        page.update()

    async def load_track(track_data):
        nonlocal current_track, duration, is_playing
        current_track = track_data
        file_path = track_data['path']
        
        # Reset UI Values
        current_time.value = "0:00"
        progress_slider.value = 0
        
        # Images Defaults
        default_img = "../assets/bg.jpg"
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
        await audio_player.pause() 
        audio_player.src = file_path
        audio_player.playback_rate = playback_rate
        audio_player.autoplay = True
        
        is_playing = True
        
        # Refresh the whole view to highlight current track and update Play/Pause button
        update_main_view()
        
    async def toggle_play_pause(e):
        nonlocal is_playing
        if not current_track:
            return
            
        if is_playing:
            await audio_player.pause()
            is_playing = False
        else:
            await audio_player.resume()
            is_playing = True
        
        # Declarative Update
        update_main_view()

    async def play_next(e):
        nonlocal current_playlist_index
        if playlist and len(playlist) > 0:
            current_playlist_index = (current_playlist_index + 1) % len(playlist)
            await load_track(playlist[current_playlist_index])

    async def play_prev(e):
        nonlocal current_playlist_index
        if playlist and len(playlist) > 0:
            current_playlist_index = (current_playlist_index - 1) % len(playlist)
            await load_track(playlist[current_playlist_index])

    async def on_seek(e):
        if not current_track:
            return
        if progress_slider.value is None:
            return
        await audio_player.seek(int(progress_slider.value))

    async def on_position_change(e):
        if e.data is None:
            return

        curr_pos = int(e.data)
        progress_slider.value = curr_pos
        current_time.value = format_time(curr_pos)
        progress_slider.update()
        current_time.update()


    async def on_duration_change(e):
        nonlocal duration
        try:
            duration = int(e.data)
            progress_slider.max = duration
            total_duration.value = format_time(duration)
            progress_slider.update()
            total_duration.update()
        except Exception:
            pass

    def on_audiostate_change(e):
        if e.data == "completed":
            play_next(None)

    async def change_speed(delta):
        nonlocal playback_rate
        playback_rate = max(0.25, min(2.0, playback_rate + delta))
        audio_player.playback_rate = playback_rate
        await audio_player.update()
        
        # Declarative Update
        update_main_view()

    # --- CONTROLS INSTANCES ---
    
    # Audio
    audio_player = fta.Audio(
        src="../assets/outfoxing.mp3",
        autoplay=False,
        volume=1,
        balance=0,
        on_loaded=lambda _: print("Loaded", ">"*20),
        on_duration_change = on_duration_change,
        on_position_change = on_position_change,
        on_state_change = on_audiostate_change,
    )
    
    # page.overlay.append(audio_player)


    
    # -- UI COMPONENTS --
    
    # Background Image
    img_bg = ft.Image(
        src="../assets/bg.jpg",
        fit=ft.BoxFit.COVER,
        opacity=0.4,
    )
    
    # Foreground Album Art
    album_art_image_control = ft.Image(
        src="../assets/tulips.jpg",
        width=250, 
        height=250,
        fit=ft.BoxFit.COVER,
        border_radius=20,
    )
    
    album_art_foreground = ft.Container(
        content=album_art_image_control,
        shadow=ft.BoxShadow(blur_radius=20, color=ft.Colors.BLACK),
        border_radius=20
    )
    
    track_title = ft.Text("No Track", size=24, weight="bold", color=ft.Colors.WHITE, text_align="center")
    artist_name = ft.Text("Select a folder...", size=16, color=ft.Colors.GREY_400)
    
    current_time = ft.Text("0:00", size=12, color=ft.Colors.GREY_300)
    total_duration = ft.Text("0:00", size=12, color=ft.Colors.GREY_300)
    progress_slider = ft.Slider(value=0, min=0, max=100, active_color=ft.Colors.WHITE, thumb_color=ft.Colors.WHITE)
    progress_slider.on_change_end = on_seek
        
    
    # File Picker -----------------------------    
    async def handle_pick_files(e: ft.Event[ft.Button]):
        nonlocal current_track, playlist, current_playlist_index
        tracks = await ft.FilePicker().pick_files(
            allow_multiple=True, 
            allowed_extensions=["mp3", "flac", "wav", "m4a", "alac"]
        )
        if tracks and len(tracks) > 0:
            for track in tracks:
                playlist.append(extract_metadata(Path(track.path).as_posix()))
            
            # print(playlist)
            current_playlist_index = 0
            if playlist:
                load_track(playlist[0])
            update_main_view()

    btn_lib_file = ft.OutlinedButton("File", icon=ft.Icons.AUDIO_FILE, style=ft.ButtonStyle(color=ft.Colors.GREY_300))
    btn_lib_file.on_click = handle_pick_files
    
    # Folder Picker --------------------------
    async def handle_pick_folder(e: ft.Event[ft.Button]):
        nonlocal playlist, current_playlist_index
        path = await ft.FilePicker(
        ).get_directory_path()
        if path:
            supported_ext = ('.mp3', '.flac', '.wav', '.m4a', '.alac')
            new_playlist = []
            try:
                # Show loading? (Blocking for now, simpler)
                for root, dirs, files in os.walk(path):
                    for file in files:
                        if file.lower().endswith(supported_ext):
                            full_path = os.path.join(root, file)
                            new_playlist.append(extract_metadata(full_path))
                
                if new_playlist:
                    # Apply current sort
                    if current_sort_key == "Title":
                         new_playlist.sort(key=lambda x: natural_sort_key(x.get('title', '')))
                    elif current_sort_key == "Track Number":
                         new_playlist.sort(key=lambda x: (x.get('track', 0), natural_sort_key(x.get('title', ''))))
                    else:
                         new_playlist.sort(key=lambda x: natural_sort_key(x.get('filename', '')))
                         
                    playlist = new_playlist
                    current_playlist_index = 0
                    await load_track(playlist[0])
                    print(f"Loaded {len(playlist)} tracks.")
                else:
                    print("No audio files found in folder.")
            except Exception as err:
                print(f"Error scanning folder: {err}")
            
            update_main_view()    
    
    btn_lib_folder = ft.OutlinedButton("Folder", icon=ft.Icons.CREATE_NEW_FOLDER, style=ft.ButtonStyle(color=ft.Colors.GREY_300))
    btn_lib_folder.on_click = handle_pick_folder

    # Library Actions -----------------------
    library_actions = ft.Row([
        btn_lib_file,
        btn_lib_folder
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
            ft.IconButton(ft.Icons.KEYBOARD_ARROW_DOWN, icon_color=ft.Colors.WHITE),
            ft.Text("NOW PLAYING", size=12, weight="bold", color=ft.Colors.GREY_400),
            ft.IconButton(ft.Icons.MORE_HORIZ, icon_color=ft.Colors.WHITE),
        ],
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN
    )

    # --- FINAL COMPOSITION ---
    stack = ft.Stack(
        controls=[
            # Layer 1: Background
            ft.Container(content=img_bg, expand=True, alignment=ft.Alignment(0, 0)),
            
            # Layer 2: Gradient
            ft.Container(
                gradient=ft.LinearGradient(
                    begin=ft.Alignment(0, -1),
                    end=ft.Alignment(0, 1),
                    colors=[ft.Colors.with_opacity(0.5, ft.Colors.BLACK), ft.Colors.BLACK],
                    stops=[0.0, 1.0]
                ),
                expand=True
            ),
            
            # Layer 3: Scrollable Content
            main_list_view,
            
            # Layer 4: Fixed Header (App Bar)
            ft.Container(content=app_bar_row, padding=ft.Padding(top=5, bottom=5, left=10, right=10), bgcolor=ft.Colors.TRANSPARENT, height=60),
        ],
        expand=True
    )

    page.add(stack)
    
    # Initialize View
    update_main_view()

ft.run(main)