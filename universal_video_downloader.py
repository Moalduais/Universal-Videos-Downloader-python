import os
import sys
import json
import threading
import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk
import yt_dlp

# Set appearance and theme
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

# --- PATH & HISTORY MANAGEMENT ---
def get_base_path():
    """Ensures the app looks in the correct folder whether run as .py or .exe"""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

BASE_DIR = get_base_path()
HISTORY_FILE = os.path.join(BASE_DIR, "download_history.json")

def load_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return []
    return []

def save_history(history_list):
    with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(history_list, f, indent=4)


# --- HISTORY UI WINDOW ---
class HistoryWindow(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Download History")
        self.geometry("750x450")
        self.parent = parent
        
        # Focus this window
        self.transient(parent)
        self.grab_set()

        self.title_label = ctk.CTkLabel(self, text="Download History", font=ctk.CTkFont(size=18, weight="bold"))
        self.title_label.pack(pady=10)

        # Scrollable list area
        self.scroll_frame = ctk.CTkScrollableFrame(self)
        self.scroll_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.clear_btn = ctk.CTkButton(self, text="Clear All History", fg_color="#C62828", hover_color="#B71C1C", command=self.clear_all)
        self.clear_btn.pack(pady=10)
        
        self.load_items()

    def load_items(self):
        # Clear existing visual items
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()
            
        history = load_history()
        if not history:
            no_data = ctk.CTkLabel(self.scroll_frame, text="Your history is empty.")
            no_data.pack(pady=20)
            return

        for idx, item in enumerate(history):
            self.create_item_frame(idx, item)
            
    def create_item_frame(self, index, item):
        frame = ctk.CTkFrame(self.scroll_frame)
        frame.pack(fill="x", pady=5, padx=5)
        
        frame.columnconfigure(0, weight=1)
        frame.columnconfigure(1, weight=1)
        
        title_var = tk.StringVar(value=item.get('title', 'Unknown'))
        url_var = tk.StringVar(value=item.get('url', ''))
        
        # Editable Entry Boxes
        title_entry = ctk.CTkEntry(frame, textvariable=title_var)
        title_entry.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        
        url_entry = ctk.CTkEntry(frame, textvariable=url_var)
        url_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        
        # Action Buttons
        save_btn = ctk.CTkButton(frame, text="Save Edit", width=60, command=lambda: self.update_item(index, title_var.get(), url_var.get()))
        save_btn.grid(row=0, column=2, padx=5, pady=5)
        
        load_btn = ctk.CTkButton(frame, text="Load", width=60, fg_color="#2E7D32", hover_color="#1B5E20", command=lambda: self.load_to_main(url_var.get()))
        load_btn.grid(row=0, column=3, padx=5, pady=5)

        del_btn = ctk.CTkButton(frame, text="Delete", width=60, fg_color="#C62828", hover_color="#B71C1C", command=lambda: self.delete_item(index))
        del_btn.grid(row=0, column=4, padx=5, pady=5)

    def update_item(self, index, new_title, new_url):
        history = load_history()
        history[index]['title'] = new_title
        history[index]['url'] = new_url
        save_history(history)
        messagebox.showinfo("Saved", "History entry updated successfully!", parent=self)

    def delete_item(self, index):
        history = load_history()
        history.pop(index)
        save_history(history)
        self.load_items() # Refresh list

    def clear_all(self):
        if messagebox.askyesno("Clear All", "Are you sure you want to permanently delete all history?", parent=self):
            save_history([])
            self.load_items()

    def load_to_main(self, url):
        self.parent.url_entry.delete(0, tk.END)
        self.parent.url_entry.insert(0, url)
        self.destroy() # Close history window
        self.parent.start_fetch_info() # Automatically start fetching


# --- MAIN APP ---
class VideoDownloaderApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Universal Video Downloader")
        self.geometry("600x520")  # Slightly taller to fit the history button
        self.resizable(False, False)

        self.download_path = os.path.join(os.path.expanduser("~"), "Downloads")
        self.formats_dict = {}

        self.create_widgets()

    def create_widgets(self):
        # App Header
        self.title_label = ctk.CTkLabel(
            self, text="Universal Video Downloader", font=ctk.CTkFont(size=22, weight="bold")
        )
        self.title_label.pack(pady=(20, 10))

        # URL Input
        self.url_frame = ctk.CTkFrame(self)
        self.url_frame.pack(fill="x", padx=20, pady=10)

        self.url_entry = ctk.CTkEntry(
            self.url_frame, placeholder_text="Paste video link here...", width=420
        )
        self.url_entry.pack(side="left", padx=(10, 5), pady=10)

        self.fetch_btn = ctk.CTkButton(self.url_frame, text="Fetch", width=100, command=self.start_fetch_info)
        self.fetch_btn.pack(side="right", padx=(5, 10), pady=10)

        # Video Information Frame
        self.info_frame = ctk.CTkFrame(self)
        self.info_frame.pack(fill="x", padx=20, pady=10)

        self.video_title_label = ctk.CTkLabel(
            self.info_frame, text="Title: N/A", font=ctk.CTkFont(size=13), wraplength=540, justify="left"
        )
        self.video_title_label.pack(anchor="w", padx=10, pady=(10, 5))

        # Quality Selection OptionMenu
        self.quality_label = ctk.CTkLabel(self.info_frame, text="Select Quality (Size included):")
        self.quality_label.pack(anchor="w", padx=10, pady=(5, 0))

        self.quality_option = ctk.CTkOptionMenu(self.info_frame, values=["Fetch a video link first"])
        self.quality_option.pack(fill="x", padx=10, pady=(0, 10))

        # Output Folder Selection
        self.path_frame = ctk.CTkFrame(self)
        self.path_frame.pack(fill="x", padx=20, pady=10)

        self.path_entry = ctk.CTkEntry(self.path_frame, width=420)
        self.path_entry.insert(0, self.download_path)
        self.path_entry.pack(side="left", padx=(10, 5), pady=10)

        self.browse_btn = ctk.CTkButton(self.path_frame, text="Browse", width=100, command=self.browse_folder)
        self.browse_btn.pack(side="right", padx=(5, 10), pady=10)

        # Download Button & Progress Bar
        self.download_btn = ctk.CTkButton(
            self, text="Download Video", fg_color="green", hover_color="darkgreen", font=ctk.CTkFont(size=15, weight="bold"), command=self.start_download
        )
        self.download_btn.pack(pady=(10, 5))

        self.progress_bar = ctk.CTkProgressBar(self, width=540)
        self.progress_bar.set(0)
        self.progress_bar.pack(pady=5)
        
        # History Button
        self.history_btn = ctk.CTkButton(
            self, text="View History", fg_color="gray30", hover_color="gray40", command=self.open_history
        )
        self.history_btn.pack(pady=5)

        self.status_label = ctk.CTkLabel(self, text="Ready", font=ctk.CTkFont(size=12))
        self.status_label.pack(pady=5)

    def browse_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.download_path = folder
            self.path_entry.delete(0, tk.END)
            self.path_entry.insert(0, self.download_path)

    def open_history(self):
        HistoryWindow(self)

    def start_fetch_info(self):
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showwarning("Input Error", "Please paste a video URL.")
            return

        self.status_label.configure(text="Fetching video details...")
        self.fetch_btn.configure(state="disabled")
        threading.Thread(target=self.fetch_info_thread, args=(url,), daemon=True).start()

    def fetch_info_thread(self, url):
        ydl_opts = {'quiet': True, 'no_warnings': True}
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                title = info.get('title', 'Unknown Title')

                self.formats_dict = {}
                formats = info.get('formats', [])
                
                # Extract file sizes and map by resolution
                best_audio_size = 0
                for f in formats:
                    if f.get('vcodec') == 'none' and f.get('ext') == 'm4a':
                        size = f.get('filesize') or f.get('filesize_approx') or 0
                        if size > best_audio_size:
                            best_audio_size = size
                
                temp_resolutions = {}
                for f in formats:
                    height = f.get('height')
                    ext = f.get('ext', 'mp4')
                    if height and f.get('vcodec') != 'none' and ext == 'mp4':
                        video_size = f.get('filesize') or f.get('filesize_approx') or 0
                        total_bytes = video_size + best_audio_size
                        if height not in temp_resolutions or total_bytes > temp_resolutions[height]['bytes']:
                            temp_resolutions[height] = {'bytes': total_bytes, 'ext': ext}

                for height, data in sorted(temp_resolutions.items(), reverse=True):
                    size_mb = data['bytes'] / (1024 * 1024)
                    size_str = f"~{size_mb:.1f} MB" if size_mb > 0 else "Size Unknown"
                    label = f"{height}p ({data['ext']}) - {size_str}"
                    self.formats_dict[label] = f"bestvideo[ext=mp4][height<={height}]+bestaudio[ext=m4a]/best[ext=mp4][height<={height}]/best"

                options = list(self.formats_dict.keys())
                if not options:
                    options = ["Best Available Quality"]
                    self.formats_dict["Best Available Quality"] = "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best"

                # Update UI
                self.video_title_label.configure(text=f"Title: {title}")
                self.quality_option.configure(values=options)
                self.quality_option.set(options[0])
                self.status_label.configure(text="Video details loaded successfully.")

                # SAVE TO HISTORY
                history = load_history()
                found = False
                for h in history:
                    if h['url'] == url:
                        h['title'] = title  # Update title if it changed
                        found = True
                        break
                if not found:
                    history.insert(0, {'title': title, 'url': url}) # Insert at the top of the list
                save_history(history)
                
        except Exception as e:
            self.status_label.configure(text="Error fetching video details.")
            messagebox.showerror("Error", f"Failed to fetch video details:\n{str(e)}")
        finally:
            self.fetch_btn.configure(state="normal")

    def start_download(self):
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showwarning("Input Error", "Please paste a video URL.")
            return

        selected_quality = self.quality_option.get()
        format_spec = self.formats_dict.get(selected_quality, "best")

        self.download_btn.configure(state="disabled")
        self.progress_bar.set(0)
        self.status_label.configure(text="Starting download...")

        threading.Thread(
            target=self.download_thread, args=(url, format_spec), daemon=True
        ).start()

    def download_thread(self, url, format_spec):
        def progress_hook(d):
            if d['status'] == 'downloading':
                total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
                downloaded = d.get('downloaded_bytes', 0)
                if total > 0:
                    percent = downloaded / total
                    self.progress_bar.set(percent)
                    self.status_label.configure(
                        text=f"Downloading: {int(percent * 100)}% ({d.get('_speed_str', '').strip()})"
                    )
            elif d['status'] == 'finished':
                self.progress_bar.set(1.0)
                self.status_label.configure(text="Processing / Merging audio & video...")

        ydl_opts = {
            'format': format_spec,
            'outtmpl': os.path.join(self.download_path, '%(title)s.%(ext)s'),
            'progress_hooks': [progress_hook],
            'merge_output_format': 'mp4',
            'ffmpeg_location': r"C:\ffmpeg\bin\ffmpeg.exe" # Force it to look in the app's folder
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            self.status_label.configure(text="Download Complete!")
            messagebox.showinfo("Success", "Video downloaded successfully!")
        except Exception as e:
            self.status_label.configure(text="Download failed.")
            messagebox.showerror("Download Error", f"An error occurred during download:\n{str(e)}")
        finally:
            self.download_btn.configure(state="normal")


if __name__ == "__main__":
    app = VideoDownloaderApp()
    app.mainloop()