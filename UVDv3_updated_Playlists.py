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

def format_size_str(mb_value):
    """Formats megabytes into a human-readable MB or GB string."""
    if mb_value <= 0:
        return "Size Unknown"
    if mb_value >= 1024:
        return f"~{mb_value / 1024:.2f} GB (est.)"
    return f"~{mb_value:.1f} MB (est.)"


# --- HISTORY UI WINDOW ---
class HistoryWindow(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Download History")
        self.geometry("750x450")
        self.parent = parent
        
        self.transient(parent)
        self.grab_set()

        self.title_label = ctk.CTkLabel(self, text="Download History", font=ctk.CTkFont(size=18, weight="bold"))
        self.title_label.pack(pady=10)

        self.scroll_frame = ctk.CTkScrollableFrame(self)
        self.scroll_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.clear_btn = ctk.CTkButton(self, text="Clear All History", fg_color="#C62828", hover_color="#B71C1C", command=self.clear_all)
        self.clear_btn.pack(pady=10)
        
        self.load_items()

    def load_items(self):
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
        
        title_entry = ctk.CTkEntry(frame, textvariable=title_var)
        title_entry.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        
        url_entry = ctk.CTkEntry(frame, textvariable=url_var)
        url_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        
        save_btn = ctk.CTkButton(frame, text="Save Edit", width=60, command=lambda: self.update_item(index, title_var.get(), url_var.get()))
        save_btn.grid(row=0, column=2, padx=5, pady=5)
        
        load_btn = ctk.CTkButton(frame, text="Load", width=60, fg_color="#2E7D32", hover_color="#1B5E20", command=lambda: self.load_to_main(url_var.get(), title_var.get()))
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
        self.load_items()

    def clear_all(self):
        if messagebox.askyesno("Clear All", "Are you sure you want to permanently delete all history?", parent=self):
            save_history([])
            self.load_items()

    def load_to_main(self, url, title):
        self.parent.url_entry.delete(0, tk.END)
        self.parent.url_entry.insert(0, url)
        
        if "[Playlist]" in title:
            self.parent.playlist_var.set(True)
        else:
            self.parent.playlist_var.set(False)

        self.destroy()
        self.parent.start_fetch_info()


# --- MAIN APP ---
class VideoDownloaderApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Universal Video Downloader")
        self.geometry("600x520")
        self.resizable(False, False)

        icon_path = os.path.join(BASE_DIR, "icon.ico")
        if os.path.exists("icon.ico"):
            self.iconbitmap("icon.ico")

        self.download_path = os.path.join(os.path.expanduser("~"), "Downloads")
        self.formats_dict = {}
        self.current_is_playlist = False

        self.create_widgets()

    def create_widgets(self):
        self.title_label = ctk.CTkLabel(
            self, text="Universal Video Downloader", font=ctk.CTkFont(size=22, weight="bold")
        )
        self.title_label.pack(pady=(20, 10))

        # --- URL & Playlist Input Frame ---
        self.url_frame = ctk.CTkFrame(self)
        self.url_frame.pack(fill="x", padx=20, pady=10)

        self.url_entry = ctk.CTkEntry(
            self.url_frame, placeholder_text="Paste video or playlist link...", width=310
        )
        self.url_entry.pack(side="left", padx=(10, 5), pady=10)

        self.playlist_var = ctk.BooleanVar(value=False)
        self.playlist_checkbox = ctk.CTkCheckBox(
            self.url_frame, text="Playlist", variable=self.playlist_var, width=70
        )
        self.playlist_checkbox.pack(side="left", padx=(5, 5), pady=10)

        self.fetch_btn = ctk.CTkButton(self.url_frame, text="Fetch", width=90, command=self.start_fetch_info)
        self.fetch_btn.pack(side="right", padx=(5, 10), pady=10)

        # --- Video Information Frame ---
        self.info_frame = ctk.CTkFrame(self)
        self.info_frame.pack(fill="x", padx=20, pady=10)

        self.video_title_label = ctk.CTkLabel(
            self.info_frame, text="Title: N/A", font=ctk.CTkFont(size=13), wraplength=540, justify="left"
        )
        self.video_title_label.pack(anchor="w", padx=10, pady=(10, 5))

        self.quality_label = ctk.CTkLabel(self.info_frame, text="Select Quality / Format:")
        self.quality_label.pack(anchor="w", padx=10, pady=(5, 0))

        self.quality_option = ctk.CTkOptionMenu(self.info_frame, values=["Fetch a media link first"])
        self.quality_option.pack(fill="x", padx=10, pady=(0, 10))

        # --- Output Folder Selection ---
        self.path_frame = ctk.CTkFrame(self)
        self.path_frame.pack(fill="x", padx=20, pady=10)

        self.path_entry = ctk.CTkEntry(self.path_frame, width=420)
        self.path_entry.insert(0, self.download_path)
        self.path_entry.pack(side="left", padx=(10, 5), pady=10)

        self.browse_btn = ctk.CTkButton(self.path_frame, text="Browse", width=100, command=self.browse_folder)
        self.browse_btn.pack(side="right", padx=(5, 10), pady=10)

        # --- Download Controls ---
        self.download_btn = ctk.CTkButton(
            self, text="Download", fg_color="green", hover_color="darkgreen", font=ctk.CTkFont(size=15, weight="bold"), command=self.start_download
        )
        self.download_btn.pack(pady=(10, 5))

        self.progress_bar = ctk.CTkProgressBar(self, width=540)
        self.progress_bar.set(0)
        self.progress_bar.pack(pady=5)
        
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
            messagebox.showwarning("Input Error", "Please paste a URL.")
            return

        is_playlist_checked = self.playlist_var.get()
        self.status_label.configure(text="Fetching media details...")
        self.fetch_btn.configure(state="disabled")
        
        threading.Thread(target=self.fetch_info_thread, args=(url, is_playlist_checked), daemon=True).start()

    def fetch_info_thread(self, url, is_playlist_mode):
        ydl_opts = {
            'quiet': True, 
            'no_warnings': True,
            'socket_timeout': 15,
            'ignoreerrors': True 
        }

        if is_playlist_mode:
            ydl_opts['extract_flat'] = 'in_playlist' 
            ydl_opts['noplaylist'] = False
        else:
            ydl_opts['noplaylist'] = True
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)

            if not info:
                self.after(0, self._handle_fetch_error, "Could not extract info. Check URL or privacy.")
                return

            self.formats_dict = {}
            options = []
            is_actual_playlist = False
            
            # --- PLAYLIST LOGIC ---
            if info.get('_type') in ['playlist', 'multi_video']:
                is_actual_playlist = True
                
                raw_entries = info.get('entries', [])
                entries = [e for e in raw_entries if isinstance(e, dict)] if raw_entries else []
                
                p_count = info.get('playlist_count') or len(entries) or "Unknown"
                
                # Sum total duration across playlist entries
                total_seconds = sum(e.get('duration', 0) for e in entries if e.get('duration'))
                
                # Format total time display
                if total_seconds > 0:
                    hrs = int(total_seconds // 3600)
                    mins = int((total_seconds % 3600) // 60)
                    time_str = f", {hrs}h {mins}m" if hrs > 0 else f", {mins}m"
                else:
                    time_str = ""

                title = f"[Playlist] {info.get('title', 'Unknown Playlist')} ({p_count} videos{time_str})"
                
                # Estimate total playlist sizes based on average bitrates per minute:
                # ~35 MB/min for Best Quality, ~30 MB/min for 1080p, ~15 MB/min for 720p, ~1.5 MB/min for Audio
                if total_seconds > 0:
                    total_min = total_seconds / 60.0
                    est_best = format_size_str(total_min * 35)
                    est_1080 = format_size_str(total_min * 30)
                    est_720 = format_size_str(total_min * 15)
                    est_audio = format_size_str(total_min * 1.5)
                else:
                    est_best = est_1080 = est_720 = est_audio = "Size Unknown"

                label_best = f"Best Available Quality - {est_best}"
                label_1080 = f"1080p Video - {est_1080}"
                label_720 = f"720p Video - {est_720}"
                label_audio = f"Audio Only (mp3) - {est_audio}"

                self.formats_dict[label_best] = {
                    'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best', 'type': 'video'
                }
                self.formats_dict[label_1080] = {
                    'format': 'bestvideo[ext=mp4][height<=1080]+bestaudio[ext=m4a]/best[ext=mp4][height<=1080]/best', 'type': 'video'
                }
                self.formats_dict[label_720] = {
                    'format': 'bestvideo[ext=mp4][height<=720]+bestaudio[ext=m4a]/best[ext=mp4][height<=720]/best', 'type': 'video'
                }
                self.formats_dict[label_audio] = {
                    'format': 'bestaudio/best', 'type': 'audio'
                }
                options = [label_best, label_1080, label_720, label_audio]

            # --- SINGLE VIDEO LOGIC ---
            else:
                title = info.get('title', 'Unknown Title')
                formats = info.get('formats', [])
                
                best_audio_size = 0
                for f in formats:
                    if f.get('vcodec') == 'none' and f.get('acodec') != 'none':
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
                    size_str = format_size_str(size_mb) if size_mb > 0 else "Size Unknown"
                    label = f"{height}p ({data['ext']}) - {size_str}"
                    
                    self.formats_dict[label] = {
                        'format': f"bestvideo[ext=mp4][height<={height}]+bestaudio[ext=m4a]/best[ext=mp4][height<={height}]/best",
                        'type': 'video'
                    }
                    options.append(label)

                if not options:
                    options = ["Best Available Video Quality"]
                    self.formats_dict["Best Available Video Quality"] = {
                        'format': "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best", 'type': 'video'
                    }

                audio_mb = best_audio_size / (1024 * 1024)
                audio_str = format_size_str(audio_mb) if audio_mb > 0 else "Size Unknown"
                audio_label = f"Audio Only (mp3) - {audio_str}"
                
                self.formats_dict[audio_label] = {
                    'format': 'bestaudio/best', 'type': 'audio'
                }
                options.append(audio_label) 

            # Pass to main thread safely
            self.after(0, self._finalize_fetch, url, title, options, is_actual_playlist)
                
        except Exception as e:
            self.after(0, self._handle_fetch_error, str(e))


    # --- GUI Update Helpers (Fetch) ---
    def _finalize_fetch(self, url, title, options, is_actual_playlist):
        self.current_is_playlist = is_actual_playlist
        self.video_title_label.configure(text=f"Title: {title}")
        self.quality_option.configure(values=options)
        self.quality_option.set(options[0])
        self.status_label.configure(text="Media details loaded successfully.")
        self.fetch_btn.configure(state="normal")

        history = load_history()
        found = False
        for h in history:
            if h['url'] == url:
                h['title'] = title  
                found = True
                break
        if not found:
            history.insert(0, {'title': title, 'url': url}) 
        save_history(history)

    def _handle_fetch_error(self, error_msg):
        self.status_label.configure(text="Error fetching media details.")
        self.fetch_btn.configure(state="normal")
        messagebox.showerror("Error", f"Failed to fetch details:\n{error_msg}")


    # --------------------------------------------
    def start_download(self):
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showwarning("Input Error", "Please paste a URL.")
            return

        selected_quality = self.quality_option.get()
        selection_data = self.formats_dict.get(selected_quality)

        self.download_btn.configure(state="disabled")
        self.progress_bar.set(0)
        self.status_label.configure(text="Starting download...")

        threading.Thread(
            target=self.download_thread, args=(url, selection_data, self.current_is_playlist), daemon=True
        ).start()

    def download_thread(self, url, selection_data, is_playlist):
        def progress_hook(d):
            playlist_index = d.get('info_dict', {}).get('playlist_index')
            playlist_count = d.get('info_dict', {}).get('playlist_count')

            if is_playlist and playlist_index and playlist_count:
                prefix = f"[{playlist_index}/{playlist_count}] "
            else:
                prefix = ""

            if d['status'] == 'downloading':
                total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
                downloaded = d.get('downloaded_bytes', 0)
                if total > 0:
                    percent = downloaded / total
                    speed = d.get('_speed_str', '').strip()
                    self.after(0, self._update_download_progress, percent, f"{prefix}Downloading: {int(percent * 100)}% ({speed})")
            elif d['status'] == 'finished':
                self.after(0, self._update_download_finished, prefix)

        format_spec = selection_data['format'] if selection_data else 'best'
        is_audio = selection_data['type'] == 'audio' if selection_data else False

        ydl_opts = {
            'format': format_spec,
            'progress_hooks': [progress_hook],
            'ffmpeg_location': r"C:\ffmpeg\bin\ffmpeg.exe", 
            'ignoreerrors': True 
        }

        if is_playlist:
            ydl_opts['outtmpl'] = os.path.join(self.download_path, '%(playlist_title)s', '%(playlist_index)s - %(title)s.%(ext)s')
            ydl_opts['noplaylist'] = False
        else:
            ydl_opts['outtmpl'] = os.path.join(self.download_path, '%(title)s.%(ext)s')
            ydl_opts['noplaylist'] = True

        if is_audio:
            ydl_opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }]
        else:
            ydl_opts['merge_output_format'] = 'mp4'

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            self.after(0, self._finalize_download, True, "")
        except Exception as e:
            self.after(0, self._finalize_download, False, str(e))


    # --- GUI Update Helpers (Download) ---
    def _update_download_progress(self, percent, text):
        self.progress_bar.set(percent)
        self.status_label.configure(text=text)

    def _update_download_finished(self, prefix=""):
        self.progress_bar.set(1.0)
        self.status_label.configure(text=f"{prefix}Processing / Converting format...")

    def _finalize_download(self, success, error_msg):
        self.download_btn.configure(state="normal")
        if success:
            self.status_label.configure(text="Download Complete!")
            messagebox.showinfo("Success", "Media downloaded successfully!")
        else:
            self.status_label.configure(text="Download failed.")
            messagebox.showerror("Download Error", f"An error occurred during download:\n{error_msg}")


if __name__ == "__main__":
    app = VideoDownloaderApp()
    app.mainloop()