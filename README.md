﻿# LifeLogger

## Overview
This is a Telegram bot designed to log various types of messages (text, location, documents, voice messages, images, and videos) into a Notion database. It uses the Whisper model for transcribing voice messages, Tesseract OCR for extracting text from images, and reverse geocoding for location data. The bot saves media files to a local `downloads` folder and logs metadata to Notion.

## Features
- **Text Logging**: Saves text messages to Notion with optional tagging.
- **Location Logging**: Logs location data with reverse geocoded place names, city, and country.
- **Media Handling**: Downloads and processes documents, voice messages, images, and videos.
- **Voice Transcription**: Transcribes voice messages using the Whisper `tiny` model.
- **Image OCR**: Extracts text from images using Tesseract OCR.
- **Notion Integration**: Stores all data in a specified Notion database with timestamps, message types, and content.

## Prerequisites
- **Python**: Version 3.8 or higher.
- **Dependencies**: Install required Python packages:
  ```bash
  pip install python-telegram-bot==20.0 whisper notion-client pillow pytesseract opencv-python numpy geopy
  ```
- **FFmpeg**: Required for Whisper audio processing. Add to system PATH (e.g., `C:\Program Files\ffmpeg\bin` on Windows).
- **Tesseract OCR**: Required for image text extraction. Install and set the path (e.g., `C:\Program Files\Tesseract-OCR\tesseract.exe` on Windows).
- **Notion Account**: A Notion database with an integration token.
- **Telegram Bot**: A Telegram bot token from BotFather.

## Setup
1. **Clone the Repository**:
   ```bash
   git clone <repository-url>
   cd <repository-directory>
   ```

2. **Create a Secrets File**:
   Create a `secrets_txt.py` file in the project root with the following:
   ```python
   bot_token = "YOUR_TELEGRAM_BOT_TOKEN"
   Notion_secret = "YOUR_NOTION_INTEGRATION_TOKEN"
   database_id = "YOUR_NOTION_DATABASE_ID"
   ```

3. **Configure Notion Database**:
   - Create a Notion database with the following properties:
     - `Timestamp` (Date)
     - `Type` (Select)
     - `Content` (Rich Text)
     - `Tag` (Select, optional)
     - `Uploaded File` (Files & Media, optional)
   - Share the database with your Notion integration and note the database ID.

4. **Install FFmpeg and Tesseract**:
   - Download and install FFmpeg: [FFmpeg Official Site](https://ffmpeg.org/download.html)
   - Download and install Tesseract: [Tesseract OCR](https://github.com/tesseract-ocr/tesseract)
   - Update the paths in `bot.py` for FFmpeg and Tesseract if different from defaults.

5. **Set Up Downloads Folder**:
   - The bot creates a `downloads` folder in the project directory to store media files. Ensure write permissions.

## Usage
1. **Run the Bot**:
   ```bash
   python bot.py
   ```
2. **Interact with the Bot**:
   - Send text messages (e.g., `Tag: Message content` for tagged messages).
   - Share locations to log place details.
   - Send documents, voice messages, images, or videos to download and process.
   - Voice messages are transcribed, and images are processed for OCR.

3. **Check Notion**:
   - All messages and media metadata are saved to the specified Notion database.

## File Structure
- `bot.py`: Main bot script.
- `secrets.py`: Stores sensitive tokens (not tracked by Git).
- `downloads/`: Folder for storing downloaded media files (contains `.gitkeep` for Git tracking).
- `README.md`: This file.

## Notes
- **Whisper Model**: Uses the `tiny` model for speed. Upgrade to `base`, `small`, `medium`, or `large` for better transcription accuracy (requires more resources).
- **Tesseract OCR**: Supports English and Urdu by default. Modify `bot.py` to support other languages.
- **Geocoding**: Uses Nominatim for reverse geocoding. Ensure a stable internet connection.
- **Error Handling**: Logs errors to the console and notifies users via Telegram.
- **Notion File Uploads**: File upload to Notion is commented out due to API limitations. Uncomment and adjust if needed.

## Troubleshooting
- **FFmpeg/Tesseract Not Found**: Verify paths in `bot.py` and ensure executables are in PATH.
- **Notion Errors**: Check `NOTION_TOKEN` and `NOTION_DATABASE_ID` in `secrets.py`.
- **Transcription/OCR Failures**: Ensure Whisper and Tesseract are properly installed.
- **Geocoding Timeouts**: Check internet connectivity or increase timeout in `bot.py`.

## Contributing
Feel free to submit issues or pull requests to improve the bot. Ensure changes are well-documented and tested.

## License
This project is licensed under the MIT License.
