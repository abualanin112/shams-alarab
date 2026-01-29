# Video Processing Desktop App

A production-ready Python desktop application for batch video processing.

## Features

- **Batch Processing**: Select multiple video files.
- **Subtitle Burn-in**: Automatically finds matching `.srt` files or assumes specific file.
- **Watermark**: Adds a logo (PNG) with transparency and adjustable opacity.
- **Compression**: High-efficiency H.265 (HEVC) encoding with CRF mode.
- **Background Processing**: UI remains responsive during rendering.

## Architecture

The application uses a **Hybrid Pipeline Architecture**:

- **Logical Modules**: Segregated classes for Subtitles, Watermarking, and Compression.
- **Single-Pass Execution**: All transformations are compiled into a complex FFmpeg filter graph to prevent generation loss (only one encoding pass).

## Installation

1. Install Python 3.10+
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. **FFmpeg**: Ensure `ffmpeg.exe` is placed in `video_app/ffmpeg/` folder OR is in your system PATH.

## Usage

Run the application:

- **Option 1 (Normal)**: `python main.py`
- **Option 2 (Stealth/No Console)**: Double-click `start.bat`

1. Click **Add Videos** to select files.
2. (Optional) Click **Select Logo** to add a watermark.
3. Click **START PROCESSING**.

## Testing

Run the automated test suite:

```bash
pytest tests/
```

## Bundling (PyInstaller)

To create a standalone executable:

```bash
pyinstaller --name "VideoProcessor" --windowed --add-binary "ffmpeg/ffmpeg.exe;ffmpeg" --add-data "assets/fonts;assets/fonts" main.py
```

_(Note: requires `ffmpeg` folder to exist)_

## License

MIT
