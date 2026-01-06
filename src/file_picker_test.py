import flet as ft
import os
from pathlib import Path
from tinytag import TinyTag
import base64
import re

def main(page: ft.Page):
    PLAYLIST = []
    CURRENT_PLAYLIST_INDEX = -1
    CURRENT_TRACK = None
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


    async def handle_pick_files(e: ft.Event[ft.Button]):
        tracks = await ft.FilePicker(
        ).pick_files(allow_multiple=True)
        if tracks and len(tracks) > 0:
            for track in tracks:
                PLAYLIST.append(extract_metadata(Path(track.path).as_posix()))
        print(PLAYLIST)

        lv = ft.ListView(expand=True, spacing=10)
        for i, track in enumerate(PLAYLIST):
            lv.controls.append(ft.Text(f"{i+1}: {track}"))
        page.add(lv)

    async def handle_pick_folder(e: ft.Event[ft.Button]):
        nonlocal PLAYLIST, CURRENT_PLAYLIST_INDEX
        folder = await ft.FilePicker(
        ).get_directory_path()
        print("Folder:", folder)
        if folder:
            supported_ext = ('.mp3', '.flac', '.wav', '.m4a', '.alac')
            new_playlist = []
            try:
                for root, dirs, files in os.walk(folder):
                    for file in files:
                        if file.lower().endswith(supported_ext):
                            full_path = os.path.join(root, file)
                            new_playlist.append(extract_metadata(Path(full_path).as_posix()))
                
                if new_playlist:
                    # Apply current sort
                    if current_sort_key == "Title":
                         new_playlist.sort(key=lambda x: natural_sort_key(x.get('title', '')))
                    elif current_sort_key == "Track Number":
                         new_playlist.sort(key=lambda x: (x.get('track', 0), natural_sort_key(x.get('title', ''))))
                    else:
                         new_playlist.sort(key=lambda x: natural_sort_key(x.get('filename', '')))
                         
                    PLAYLIST = new_playlist
                    CURRENT_PLAYLIST_INDEX = 0
                    print(f"Loaded {len(PLAYLIST)} tracks.")
                else:
                    print("No audio files found in folder.")
            except Exception as err:
                print(f"Error scanning folder: {err}")

        lv = ft.ListView(expand=True, spacing=10)
        for i, track in enumerate(PLAYLIST):
            lv.controls.append(ft.Text(f"{i+1}: {track}"))
        page.add(lv)

    page.add(
        ft.Row(
            spacing=50,
            controls=[
                ft.Button(
                    content="Pick files",
                    icon=ft.Icons.UPLOAD_FILE,
                    on_click=handle_pick_files
                ),
                ft.Button(
                    content="Pick folder",
                    icon=ft.Icons.FOLDER_OPEN,
                    on_click=handle_pick_folder
                )
            ]
        )
    )



# ft.run(main, view=ft.AppView.WEB_BROWSER)
ft.run(main)