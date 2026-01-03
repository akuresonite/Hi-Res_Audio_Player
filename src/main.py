import flet as ft

def main(page: ft.Page):
    # 1. Page Configuration for Mobile Feel
    page.title = "Hi-Res Player"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 20
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    # Set a dark background color specific to music apps
    page.bgcolor = "#121212" 

    # --- UI COMPONENTS ---

    # A. AppBar (Top header)
    app_bar = ft.AppBar(
        leading=ft.Icon(ft.Icons.KEYBOARD_ARROW_DOWN), # Changed 'icons' to 'Icons'
        leading_width=40,
        title=ft.Text("Now Playing", weight="bold", size=16),
        center_title=True,
        bgcolor=ft.colors.TRANSPARENT,
        actions=[
            ft.IconButton(ft.Icons.CAST), # Use ft.Icons
            ft.IconButton(ft.Icons.MORE_VERT),
        ],
    )

    # B. Album Art Placeholder
    # In a real app, the 'src' would be the path to the album cover image
    album_art = ft.Container(
        content=ft.Image(
            src="https://loremflickr.com/500/500/abstract,music", # Placeholder image
            fit=ft.ImageFit.COVER,
            border_radius=ft.border_radius.all(20),
        ),
        width=350,
        height=350,
        # Add shadow for depth
        shadow=ft.BoxShadow(
            spread_radius=1,
            blur_radius=25,
            color=ft.colors.with_opacity(0.3, ft.colors.BLACK),
            offset=ft.Offset(0, 10),
        ),
        alignment=ft.alignment.center,
    )

    # C. Track Info & Audiophile Badge
    track_title = ft.Text("Geralt of Rivia (Theme)", size=24, weight="bold", text_align="center")
    artist_name = ft.Text("Sonya Belousova, Giona Ostinelli", size=16, color=ft.colors.GREY_400)
    
    # The "Hi-Res" indicator badge
    audio_specs_badge = ft.Container(
        content=ft.Row(
            [
                ft.Icon(ft.icons.audiotrack, color=ft.colors.CYAN_400, size=16),
                ft.Text("FLAC  |  24-BIT  |  96 KHZ", color=ft.colors.CYAN_400, weight="bold", size=12),
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

    # D. Progress Bar (Slider & Timestamps)
    current_time = ft.Text("1:24", size=12)
    total_duration = ft.Text("4:12", size=12)
    
    progress_slider = ft.Slider(
        value=30, # Dummy value for visualization
        min=0,
        max=100,
        active_color=ft.colors.WHITE,
        inactive_color=ft.colors.GREY_800,
        thumb_color=ft.colors.WHITE,
    )
    
    progress_container = ft.Column([
        progress_slider,
        ft.Row([current_time, total_duration], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
    ])


    # E. Playback Controls
    play_button = ft.Container(
        content=ft.IconButton(
            icon=ft.Icons.PLAY_ARROW_ROUNDED, # Standardize here
            icon_color=ft.colors.BLACK,
            icon_size=40,
            bgcolor=ft.colors.WHITE, # White circle background for play button
            # In real app: on_click=lambda e: audio.resume()
        ),
        border_radius=ft.border_radius.all(50), # Makes the container circular
        padding=5,
        bgcolor=ft.colors.WHITE
    )

    controls_row = ft.Row(
        [
            ft.IconButton(ft.icons.SHUFFLE, icon_color=ft.colors.GREY_500),
            ft.IconButton(ft.icons.SKIP_PREVIOUS_ROUNDED, icon_size=35),
            play_button, # The big central button
            ft.IconButton(ft.icons.SKIP_NEXT_ROUNDED, icon_size=35),
            ft.IconButton(ft.icons.REPEAT, icon_color=ft.colors.GREY_500),
        ],
        alignment=ft.MainAxisAlignment.SPACE_EVENLY,
        vertical_alignment=ft.CrossAxisAlignment.CENTER
    )

    # F. Bottom File Picker Button
    library_button = ft.TextButton(
        "Open Library / Pick File",
        icon=ft.icons.FOLDER_OPEN,
        style=ft.ButtonStyle(color=ft.colors.CYAN_200),
        # In real app: on_click=lambda _: file_picker.pick_files()
    )


    # --- ASSEMBLING THE PAGE ---
    # Use a Column to stack elements vertically
    layout_column = ft.Column(
        [
            app_bar,
            ft.Container(height=20), # Spacer
            album_art,
            ft.Container(height=30), # Spacer
            track_info_column,
            ft.Container(height=30), # Spacer
            progress_container,
            ft.Container(height=10), # Spacer
            controls_row,
            ft.Divider(color=ft.colors.TRANSPARENT), # Spacer that pushes bottom element down
            library_button
        ],
        # Distribute space nicely on tall screens
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN, 
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
    )

    page.add(layout_column)

ft.app(target=main)