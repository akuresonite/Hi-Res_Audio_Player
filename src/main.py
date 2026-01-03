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
    page.bgcolor = "#000000" # Black background behind everything
    # We will handle scrolling inside the bottom sheet, not the page

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
            
            def play_clicked_track(e, index=i):
                 nonlocal current_playlist_index
                 current_playlist_index = index
                 load_track(playlist[current_playlist_index])

            # In the dark redesign, list items should be subtle
            tile = ft.Container(
                content=ft.Row([
                    # Visualizer bar or simple icon
                    ft.Icon(ft.icons.EQUALIZER if is_active else ft.icons.MUSIC_NOTE, 
                           color=ft.colors.WHITE if is_active else ft.colors.GREY_500, size=20),
                    ft.Column([
                        ft.Text(fname, color=ft.colors.WHITE if is_active else ft.colors.GREY_300, 
                               weight="bold" if is_active else "normal",
                               size=14, overflow=ft.TextOverflow.ELLIPSIS),
                        ft.Text(f"Track {i+1}", color=ft.colors.GREY_600, size=12)
                    ], spacing=2, expand=True)
                ]),
                padding=10,
                border_radius=10,
                bgcolor=ft.colors.with_opacity(0.1, ft.colors.WHITE) if is_active else None,
                on_click=play_clicked_track
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
        
        # Reset Art
        img_bg.src = "https://loremflickr.com/500/500/abstract,music"
        img_bg.src_base64 = None

        # Get Metadata
        try:
            tag = TinyTag.get(file_path, image=True)
            track_title.value = tag.title if tag.title else os.path.basename(file_path)
            artist_name.value = tag.artist if tag.artist else "Unknown"
            
            # Badge info
            sample_rate = f"{tag.samplerate} Hz" if tag.samplerate else ""
            # bitrate = f"{tag.bitrate} kbits/s" if tag.bitrate else "" # Removed to cleaner look requested
            # audio_specs_text.value = f"{bitrate} | {sample_rate}" # Maybe keep minimal
            
            # Load duration
            if tag.duration:
                duration = tag.duration * 1000 # convert to ms
                total_duration.value = format_time(duration)
                progress_slider.max = duration
            
            # Album Art
            art_b64 = get_album_art_base64(file_path)
            if art_b64:
                img_bg.src_base64 = art_b64
                img_bg.src = "" 
            
        except Exception as err:
            print(f"Error loading metadata: {err}")
            track_title.value = os.path.basename(file_path)

        audio_player.src = file_path
        audio_player.autoplay = True
        audio_player.update()
        
        # Auto play state
        is_playing = True
        play_button_icon.icon = ft.icons.PAUSE_ROUNDED
        play_button_icon.update()
        
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

    # --- UI LAYOUT ---

    # 1. Background Image (The "Galaxy" look)
    img_bg = ft.Image(
        src="https://loremflickr.com/500/500/abstract,music",
        fit=ft.ImageFit.COVER,
        opacity=0.6, # Darken it a bit
    )
    
    # 2. Header (Back Button, Menu)
    header = ft.Row(
        [
            ft.IconButton(ft.icons.KEYBOARD_ARROW_DOWN, icon_color=ft.colors.WHITE, bgcolor=ft.colors.with_opacity(0.2, ft.colors.WHITE)),
            ft.IconButton(ft.icons.MORE_HORIZ, icon_color=ft.colors.WHITE, bgcolor=ft.colors.with_opacity(0.2, ft.colors.WHITE)),
        ],
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN
    )

    # 3. Bottom Card Components
    
    track_title = ft.Text("No Track Selected", size=28, weight="bold", color=ft.colors.WHITE, text_align="center")
    artist_name = ft.Text("Select a file to play", size=16, color=ft.colors.GREY_400)
    
    # Waveform placeholder (Visual only, simple bars)
    waveform = ft.Row(
        controls=[
            ft.Container(width=4, height=30, bgcolor=ft.colors.WHITE, border_radius=2),
            ft.Container(width=4, height=50, bgcolor=ft.colors.WHITE, border_radius=2),
            ft.Container(width=4, height=40, bgcolor=ft.colors.WHITE, border_radius=2),
            ft.Container(width=4, height=20, bgcolor=ft.colors.WHITE, border_radius=2),
            ft.Container(width=4, height=45, bgcolor=ft.colors.WHITE, border_radius=2),
             ft.Container(width=4, height=30, bgcolor=ft.colors.WHITE, border_radius=2),
            ft.Container(width=4, height=50, bgcolor=ft.colors.WHITE, border_radius=2),
        ],
        alignment=ft.MainAxisAlignment.CENTER,
        opacity=0.5
    )

    # Sliders
    current_time = ft.Text("0:00", size=12, color=ft.colors.GREY_400)
    total_duration = ft.Text("0:00", size=12, color=ft.colors.GREY_400)
    progress_slider = ft.Slider(value=0, min=0, max=100, active_color=ft.colors.WHITE, thumb_color=ft.colors.WHITE, on_change_end=on_seek)
    
    # Controls Row
    play_button_icon = ft.IconButton(
        icon=ft.icons.PLAY_ARROW_ROUNDED,
        icon_color=ft.colors.BLACK,
        icon_size=40,
        bgcolor=ft.colors.WHITE, # White circle
        on_click=toggle_play_pause
    )
    play_btn_container = ft.Container(content=play_button_icon, border_radius=50, bgcolor=ft.colors.WHITE, padding=10)
    
    controls = ft.Row(
        [
            ft.IconButton(ft.icons.SHUFFLE, icon_color=ft.colors.GREY_500),
            ft.IconButton(ft.icons.SKIP_PREVIOUS_ROUNDED, icon_color=ft.colors.GREY_300, icon_size=30, bgcolor=ft.colors.with_opacity(0.1, ft.colors.WHITE), on_click=play_prev),
            play_btn_container,
            ft.IconButton(ft.icons.SKIP_NEXT_ROUNDED, icon_color=ft.colors.GREY_300, icon_size=30, bgcolor=ft.colors.with_opacity(0.1, ft.colors.WHITE), on_click=play_next),
            ft.IconButton(ft.icons.REPEAT, icon_color=ft.colors.GREY_500),
        ],
        alignment=ft.MainAxisAlignment.SPACE_EVENLY,
        vertical_alignment=ft.CrossAxisAlignment.CENTER
    )

    # Playlist View (Queue)
    playlist_view = ft.ListView(
        expand=True,
        spacing=5,
        padding=10,
        height=200 # Fixed height to allow scrolling within the card
    )

    # Library Actions
    library_actions = ft.Row([
        ft.ElevatedButton("File", icon=ft.icons.AUDIO_FILE, color=ft.colors.WHITE, bgcolor=ft.colors.GREY_900, on_click=lambda _: file_picker.pick_files(allow_multiple=False, allowed_extensions=["mp3", "flac"])),
        ft.ElevatedButton("Folder", icon=ft.icons.CREATE_NEW_FOLDER, color=ft.colors.WHITE, bgcolor=ft.colors.GREY_900, on_click=lambda _: folder_picker.get_directory_path())
    ], alignment=ft.MainAxisAlignment.CENTER)

    # Bottom Sheet Content
    bottom_sheet_content = ft.Column(
        [
            ft.Container(height=10),
            track_title,
            artist_name,
            ft.Container(height=20),
            waveform,
            ft.Container(height=10),
            ft.Row([current_time, ft.Container(expand=True), total_duration], width=300), 
            progress_slider,
            ft.Container(height=10),
            controls,
            ft.Container(height=20),
            ft.Divider(color=ft.colors.GREY_800),
            library_actions,
            ft.Container(height=10),
            playlist_view
        ],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        scroll=ft.ScrollMode.AUTO # Enable scrolling so buttons aren't cut off
    )

    # The Glassmorphic/Card Container
    bottom_card = ft.Container(
        content=bottom_sheet_content,
        bgcolor=ft.colors.BLACK, # Solid black or very dark grey
        border_radius=ft.border_radius.only(top_left=40, top_right=40),
        padding=20,
        expand=True, # Expand to fill bottom area
        shadow=ft.BoxShadow(blur_radius=50, color=ft.colors.BLACK) 
    )

    # Main Stack
    stack = ft.Stack(
        [
            # Layer 1: Background Image (Full Screen)
            ft.Container(content=img_bg, expand=True, alignment=ft.alignment.top_center),
            
            # Layer 2: Gradient Overlay (make top art readable but bottom dark)
            ft.Container(
                gradient=ft.LinearGradient(
                    begin=ft.alignment.top_center,
                    end=ft.alignment.bottom_center,
                    colors=[ft.colors.TRANSPARENT, ft.colors.BLACK],
                    stops=[0.0, 0.6]
                ),
                expand=True
            ),
            
            # Layer 3: Header
            ft.Container(content=header, padding=20, top=0, left=0, right=0),

            # Layer 4: Bottom Card (Positioned at bottom)
            # We use a Column to push the card to the bottom
            ft.Column(
                [
                    ft.Container(expand=True), # Spacer to push card down
                    bottom_card
                ],
                expand=True
            )
        ],
        expand=True
    )

    page.add(stack)

ft.app(target=main)