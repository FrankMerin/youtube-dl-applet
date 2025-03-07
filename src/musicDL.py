import tkinter as tk
from tkinter import ttk, filedialog
import re
from PIL import Image, ImageTk
import os
import random
import json
import sys
import yt_dlp
from threading import Thread


from helpersDL import (
    load_config,
    count_png_files,
    extract_frames_from_gif,
    clean_youtube_url,
    calculate_time_difference,
    is_valid_time
)


base_path = getattr(sys, '_MEIPASS', os.getcwd())


ffmpeg_path = os.path.join(base_path, "ffmpeg.exe")

config_directory = os.path.join(os.path.expanduser("~"), ".musicDL")

file_types = ["M4A", "MP3", 'MP4']
CONFIG_FILE = os.path.join(config_directory, "config.json")
IMAGE_FOLDER = os.path.join(base_path, "frames")

configs = load_config()
output_directory = configs["output_directory"]
continue_animation = True
random_delay = random.randint(10, 130)

def select_directory():
    """Open a dialog to select output directory"""
    directory = filedialog.askdirectory()
    if directory:
        output_directory_entry.delete(0, tk.END)
        output_directory_entry.insert(0, directory)

def set_custom_paths():
    global output_directory

    custom_output_directory = output_directory_entry.get()

    if custom_output_directory:
        if not custom_output_directory.endswith('\\'):
            # Handle cross-platform path separator
            custom_output_directory = os.path.join(custom_output_directory, '')
        output_directory = custom_output_directory
    config = {
        "output_directory": output_directory
    }
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f)

def download_content():
    try:
        start_time = start_time_entry.get()
        end_time = end_time_entry.get()
        global output_directory, continue_animation, ffmpeg_path
        download_button.config(state=tk.DISABLED)
        status_label.config(text="")
        continue_animation = True
        animate_spinner()
        set_custom_paths()

        youtube_url = url_entry.get()

        if not os.path.exists(output_directory):
            os.makedirs(output_directory)

        if not re.search(r'(youtube\.com|youtu\.be)', youtube_url):
            raise ValueError("Invalid YouTube URL")
        
        clean_url = clean_youtube_url(youtube_url)
        file_type = selected_file_type.get()

        ydl_opts = {
            'format': f'bestaudio/best' if file_type in ('M4A', 'MP3') else f'bestvideo[ext={file_type.lower()}]+bestaudio[ext={file_type.lower()}]/best[ext={file_type.lower()}]/best',
            'outtmpl': os.path.join(output_directory, '%(title)s.%(ext)s'),
            'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': file_type.lower(), 'preferredquality': '0'}] if file_type in ('M4A', 'MP3') else [],
            'ffmpeg_location': ffmpeg_path
        }
        if trim_checkbox_var.get():
            valid_time = is_valid_time(start_time, end_time)
            if not valid_time[0]:
                raise ValueError(valid_time[1])
            diff_time = calculate_time_difference(start_time,end_time)
            ydl_opts['postprocessor_args'] = ['-ss', start_time, '-t', diff_time]

        def run_download():
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([clean_url])
                root.after(0, lambda: update_status("Download Complete!"))
            except yt_dlp.DownloadError as e:
                root.after(0, lambda e=e: update_status(f"Error: {e}"))

        Thread(target=run_download).start()
    except ValueError as e:
        root.after(0, lambda e=e: update_status(f"Error: {e}"))

def update_status(message):
    global continue_animation
    download_button.config(state=tk.NORMAL)
    status_label.config(text=message)
    spinner_label.grid_forget()
    continue_animation = False

def animate_spinner():
    spinner_label.grid(row=6, column=0, columnspan=2, padx=10, pady=10)

    global spinner_index
    spinner_index = 1
    animate()

def animate():
    global spinner_index, png_count, random_delay
    frame_path = os.path.join(IMAGE_FOLDER, f'frame{spinner_index}.png')
    image = Image.open(frame_path)
    spinner_image = ImageTk.PhotoImage(image)

    spinner_label.config(image=spinner_image)
    spinner_label.image = spinner_image

    spinner_index = (spinner_index % png_count) + 1
    if spinner_index == 2:
        random_delay = random.randint(5, 100)
    if continue_animation:
        root.after(random_delay, animate)

png_count = count_png_files(IMAGE_FOLDER)
if png_count == 0:
    png_count = extract_frames_from_gif(os.path.join(base_path, "assets", "loading.gif"), IMAGE_FOLDER)
def toggle_trim():
    if trim_checkbox_var.get():
        start_time_label.grid(row=3, column=0, padx=10, pady=10, sticky="w")
        start_time_entry.grid(row=3, column=1, padx=10, pady=10)
        end_time_label.grid(row=4, column=0, padx=10, pady=10, sticky="w")
        end_time_entry.grid(row=4, column=1, padx=10, pady=10)
    else:
        start_time_label.grid_remove()
        start_time_entry.grid_remove()
        end_time_label.grid_remove()
        end_time_entry.grid_remove()

root = tk.Tk()
root.title("YouTube Downloader")
root.iconbitmap(os.path.join(base_path, "assets", "logo.ico"))

selected_file_type = tk.StringVar(root)
trim_checkbox_var = tk.BooleanVar(root)
spinner_label = ttk.Label(root)

file_type_label = ttk.Label(root, text="Select File Type:")
file_type_combobox = ttk.Combobox(root, textvariable=selected_file_type, values=file_types, width=6)
file_type_combobox.set(file_types[0])

url_label = ttk.Label(root, text="YouTube Video or Playlist URL:")
url_entry = ttk.Entry(root, width=40)

button_style = ttk.Style()
button_style.configure("Download.TButton", font=("Arial", 10, "bold"))
download_button = ttk.Button(root, 
                           text="↓ Download", 
                           command=download_content,
                           style="Download.TButton")
status_label = ttk.Label(root, text="")


trim_checkbox = ttk.Checkbutton(root, text="Trim", variable=trim_checkbox_var, command=toggle_trim)
start_time_label = ttk.Label(root, text="Start Time (hh:mm:ss):")
start_time_entry = ttk.Entry(root, width=15)
start_time_entry.insert(0, "00:00:00") 
end_time_label = ttk.Label(root, text="End Time (hh:mm:ss):")
end_time_entry = ttk.Entry(root, width=15)
end_time_entry.insert(0, "00:00:00") 

output_directory_label = ttk.Label(root, text="Output Directory:")
output_directory_entry = ttk.Entry(root, width=30)
browse_button = ttk.Button(root, text="Browse...", command=select_directory)

url_label.grid(row=0, column=0, padx=10, pady=10)
url_entry.grid(row=0, column=1, padx=10, pady=10)
file_type_label.grid(row=1, column=0, padx=10, pady=10, sticky="w") 
file_type_combobox.grid(row=1, column=1, padx=10, pady=10, sticky="w")  
download_button.grid(row=1, column=1, padx=100, pady=10, sticky="w")
status_label.grid(row=2, column=0, columnspan=2, padx=10, pady=5)
trim_checkbox.grid(row=1, column=2, padx=10, pady=10, sticky="w")

output_directory_label.grid(row=5, column=0, padx=10, pady=10)
output_directory_entry.grid(row=5, column=1, padx=10, pady=10, sticky="w")
browse_button.grid(row=5, column=1, padx=(210, 0), pady=10, sticky="w")  # Position the button next to the entry field

output_directory_entry.insert(0, output_directory)

root.mainloop()