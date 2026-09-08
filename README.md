Markdown
# 📥 Universal Video Downloader

A modern, lightweight Windows desktop application built with Python that allows you to download videos from thousands of websites (including YouTube, Instagram, and more) with support for quality selection, live file-size previews, and built-in history management.

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![GUI](https://img.shields.io/badge/GUI-CustomTkinter-green)
![Downloader](https://img.shields.io/badge/Core-yt--dlp-red)

---

## ✨ Features

* **Universal Support:** Powered by `yt-dlp`, supporting downloads from YouTube, Instagram, Vimeo, and thousands of other platforms.
* **Quality & Size Preview:** Automatically calculates and displays the estimated file size (in MB) for each resolution option before you download.
* **Smart History Tracking:** Automatically logs fetched links and video titles into a local `download_history.json` file.
* **In-App History Manager:** View, edit, delete, or reload past video links directly from a dedicated window inside the app.
* **Modern Dark UI:** Clean, responsive user interface built using **CustomTkinter** with multithreading to prevent UI freezing during downloads.
* **Automatic Stream Merging:** Automatically stitches high-definition video and audio streams together using FFmpeg into a universally playable `.mp4` file.

---

## 🛠️ Prerequisites & Requirements

Before running or compiling the application, ensure you have the following ready:

### 1. Python (Version 3.8 or higher)
Make sure Python is installed on your system and added to your environment variables (PATH).

### 2. Python Dependencies
Open your terminal or command prompt and install the required UI and downloading libraries:
```bash
pip install customtkinter yt-dlp pillow pyinstaller
3. FFmpeg (Crucial for High Definition & Merging)
Because platforms like YouTube separate high-definition video and audio streams, FFmpeg is required to merge them.

Download FFmpeg for Windows (e.g., from Gyan.dev or official builds).

Extract ffmpeg.exe from the download archive's bin folder.

Place ffmpeg.exe directly into the same folder where your app.py script is saved.

🚀 Step-by-Step Installation & Running Guide
Clone or Download the Repository:

Bash
git clone [https://github.com/YourUsername/your-repo-name.git](https://github.com/YourUsername/your-repo-name.git)
Navigate to the Project Folder:

Bash
cd your-repo-name
Ensure FFmpeg is Present:
Verify that ffmpeg.exe is sitting right next to app.py.

Run the Script:

Bash
python app.py
📦 Building into a Standalone Windows .exe
If you want to package this application into an executable file that can run on any Windows machine without requiring Python installed:

Open your command prompt in the project directory.

Run the PyInstaller bundling command:

Bash
pyinstaller --noconsole --onefile --collect-all customtkinter app.py
Once the compilation finishes, open the newly generated dist folder.

Important: Copy your ffmpeg.exe file and paste it directly into the dist folder right next to your new app.exe.

You can now zip the dist folder contents and share your application anywhere!

📂 Project Structure
Plaintext
├── app.py                   # Main application source code
├── ffmpeg.exe               # Required media merging binary
├── download_history.json    # Auto-generated history storage file
└── dist/                    # Contains the compiled .exe (after building)
📄 License
This project is open-source and available under the MIT License.
