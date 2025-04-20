import logging
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
import os
from datetime import datetime
import whisper
from notion_client import Client
import secrets_txt as secrets  # Ensure you have a secrets.py file with your tokens
from PIL import Image
import pytesseract
import numpy as np
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderUnavailable


# Ensure ffmpeg is in PATH (adjust path to where ffmpeg.exe is located)
os.environ["PATH"] += os.pathsep + r"C:\Program Files\ffmpeg\bin"  # Replace with actual path

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.DEBUG
)
logger = logging.getLogger(__name__)

# Create Downloads folder if it doesn't exist
DOWNLOADS_DIR = r"./downloads"
if not os.path.exists(DOWNLOADS_DIR):
    os.makedirs(DOWNLOADS_DIR)

# Notion configuration
NOTION_TOKEN = secrets.Notion_secret  # Use your Notion secret token
NOTION_DATABASE_ID = secrets.database_id  # Use your Notion database ID

# Validate Notion configuration
if not NOTION_TOKEN or not NOTION_DATABASE_ID:
    logger.error("NOTION_TOKEN or NOTION_DATABASE_ID not set in .env file")
    raise ValueError("Missing Notion configuration")



# Initialize Notion client
notion = Client(auth=NOTION_TOKEN)

# Test Notion connection
try:
    notion.databases.retrieve(database_id=NOTION_DATABASE_ID)
    logger.info("Notion database connection successful")
except Exception as e:
    logger.error(f"Failed to connect to Notion database: {e}")
    raise

# Load Whisper model (tiny for speed and low resource usage)
try:
    whisper_model = whisper.load_model("tiny")
    logger.info("Whisper model loaded successfully")
except Exception as e:
    logger.error(f"Failed to load Whisper model: {e}")
    whisper_model = None

# Define Tesseract path explicitly
TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"  # Adjust if installed elsewhere
pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH

# Verify Tesseract installation
try:
    if os.path.exists(TESSERACT_PATH):
        version = pytesseract.get_tesseract_version()
        logger.info(f"Tesseract OCR found at {TESSERACT_PATH}, version: {version}")
    else:
        raise FileNotFoundError(f"Tesseract executable not found at {TESSERACT_PATH}")
except Exception as e:
    logger.error(f"Failed to initialize Tesseract OCR: {e}")
    pytesseract.pytesseract.tesseract_cmd = None

# Initialize geocoder for reverse geocoding
geolocator = Nominatim(user_agent="telegram_life_logging_bot")

# Function to append to Notion database
async def append_to_notion(timestamp: str, msg_type: str, content: str, file_path: str = None, tag: str = None) -> None:
    try:
        properties = {
            "Timestamp": {
                "date": {"start": timestamp}
            },
            "Type": {
                "select": {"name": msg_type}
            },
            "Content": {
                "rich_text": [{"text": {"content": content}}]
            }
        }
        # Add the Tag field if a tag is present
        if tag:
            properties["Tag"] = {
                "select": {"name": tag}
            }
        # if file_path:
        #     with open(file_path, "rb") as f:
        #         properties["Uploaded File"] = {
        #             "files": [
        #                 {
        #                     "name": os.path.basename(file_path),
        #                     "type": "file",
        #                     "file": {
        #                         "url": f"file://{file_path}"  # Notion will handle the upload
        #                     }
        #                 }
        #             ]
        #         }
        response = notion.pages.create(
            parent={"database_id": NOTION_DATABASE_ID},
            properties=properties
        )
        logger.info(f"Successfully appended to Notion: {timestamp} | {msg_type} | {content} (Page ID: {response['id']})")
    except Exception as e:
        logger.error(f"Error appending to Notion: {e}")
        raise

# Handler for text messages
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        message = update.message
        text = message.text
        if ":" in text:
            tag = text.split(":")[0].strip()
            text = text.split(":", 1)[1].strip()
        else:
            tag = None
            content = text
        timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")  # ISO format for Notion
        content = text
        await append_to_notion(timestamp, "message", content,tag=tag)
        await message.reply_text(f"Text message saved to Notion: {timestamp}: message : {content}")
    except Exception as e:
        logger.error(f"Error handling text message: {e}")
        await message.reply_text(f"Failed to process text message: {str(e)}")

# # Handler for location messages
# async def handle_location(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
#     try:
#         message = update.message
#         location = message.location
#         timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")  # ISO format for Notion
#         content = f"Latitude: {location.latitude}, Longitude: {location.longitude}"
#         await append_to_notion(timestamp, "location", content)
#         await message.reply_text(f"Location saved to Notion: {timestamp}: location : {content}")
#     except Exception as e:
#         logger.error(f"Error handling location message: {e}")
#         await message.reply_text(f"Failed to process location message: {str(e)}")

# Handler for location messages
async def handle_location(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        message = update.message
        location = message.location
        timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")  # ISO format for Notion
        
        # Initialize default values
        place_name = "Unknown"
        city = "Unknown"
        country = "Unknown"
        lat = location.latitude
        long = location.longitude

        # Try reverse geocoding with geopy
        try:
            location_data = geolocator.reverse((lat, long), language='en', timeout=5)
            if location_data and location_data.raw.get('address'):
                address = location_data.raw['address']
                place_name = address.get('amenity', '') or address.get('shop', '') or address.get('tourism', '') or address.get('highway', '') or "Unknown"
                city = address.get('city', '') or address.get('town', '') or address.get('village', '') or "Unknown"
                country = address.get('country', "Unknown")
        except (GeocoderTimedOut, GeocoderUnavailable) as e:
            logger.warning(f"Geocoding failed: {e}, falling back to coordinates and venue data")

        # Check for venue data
        if message.venue:
            place_name = message.venue.title or place_name
            if message.venue.address:
                # Use venue address as fallback for city/country if geocoding failed
                if city == "Unknown":
                    city = message.venue.address.split(',')[-2].strip() if ',' in message.venue.address else "Unknown"
                if country == "Unknown":
                    country = message.venue.address.split(',')[-1].strip() if ',' in message.venue.address else "Unknown"

        # Format content
        if place_name != "Unknown":
            content = f"Place Name: {place_name}\nCity: {city}\nCountry: {country}\nLatitude: {lat}\nLongitude: {long}"
        else:
            content = f"City: {city}\nCountry: {country}\nLatitude: {lat}\nLongitude: {long}"
        
        await append_to_notion(timestamp, "location", content)
        await message.reply_text(f"Location saved to Notion: {timestamp}: location : {content}")
    except Exception as e:
        logger.error(f"Error handling location message: {e}")
        await message.reply_text(f"Failed to process location message: {str(e)}")

# Handler for documents, voice messages, images, and videos
async def download_media(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        message = update.message
        file_path = None
        file_name = "downloaded_file"
        file_ext = ""
        save_path = None
        timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")  # ISO format for Notion
        msg_type = "doc"
        content = ""

        # Handle documents
        if message.document:
            file_name = message.document.file_name or f"document_{message.document.file_id}"
            file = await context.bot.get_file(message.document.file_id)
            file_path = file.file_path
            file_ext = os.path.splitext(file_name)[1] or ".bin"
            file_name = os.path.splitext(file_name)[0]
            content = file_name
            logger.info(f"Received document: {file_name}")

        # Handle voice messages
        elif message.voice:
            file_name = f"voice_{message.voice.file_id}"
            file_ext = ".ogg"
            file = await context.bot.get_file(message.voice.file_id)
            file_path = file.file_path
            msg_type = "voice"
            logger.info(f"Received voice message: {file_name}")

        # # Handle images
        # elif message.photo:
        #     file_name = f"image_{message.message_id}"
        #     file = await context.bot.get_file(message.photo[-1].file_id)  # Get highest resolution
        #     file_path = file.file_path
        #     file_ext = ".jpg"
        #     msg_type = "image"
        #     content = message.caption if message.caption else "No caption"
        #     logger.info(f"Received image: {file_name}")

        # Handle images
        elif message.photo:
            file_name = f"image_{message.message_id}"
            file = await context.bot.get_file(message.photo[-1].file_id)  # Get highest resolution
            file_path = file.file_path
            file_ext = ".jpg"
            msg_type = "image"  # Use image_ocr for OCR processing
            tag = "OCR"
            content = message.caption if message.caption else "No caption"
            logger.info(f"Received image: {file_name}")

        # Handle videos (treat as documents for simplicity)
        elif message.video:
            file_name = f"video_{message.message_id}"
            file = await context.bot.get_file(message.video.file_id)
            file_path = file.file_path
            file_ext = ".mp4"
            content = file_name
            logger.info(f"Received video: {file_name}")

        # Download the file if it exists
        if file_path:
            # Construct filename with timestamp
            safe_file_name = f"{file_name}_{timestamp.replace(':', '')}{file_ext}"
            # Ensure the filename is safe
            safe_file_name = "".join(c for c in safe_file_name if c.isalnum() or c in ('.', '_', '-'))
            # Full path to save the file
            save_path = os.path.join(DOWNLOADS_DIR, safe_file_name)
            # Download file
            await file.download_to_drive(custom_path=save_path)
            await message.reply_text(f"File '{safe_file_name}' downloaded successfully to Downloads folder!")

            # Process voice messages
            if message.voice and whisper_model:
                try:
                    logger.debug(f"Attempting to transcribe: {save_path}")
                    # Transcribe the audio file
                    result = whisper_model.transcribe(save_path)
                    transcription = result["text"].strip()
                    logger.debug(f"Transcription result: {transcription}")
                    if transcription:
                        content = transcription
                        await append_to_notion(timestamp, msg_type, content, save_path,tag=None)
                        await message.reply_text(f"Transcription: {transcription}\nSaved to Notion: {timestamp}: voice : {content}")
                    else:
                        await message.reply_text("Transcription failed: No text detected.")
                    logger.info(f"Transcription completed for {safe_file_name}")
                except Exception as e:
                    logger.error(f"Error transcribing voice message: {e}")
                    await message.reply_text(f"Failed to transcribe the voice message: {str(e)}")
            elif message.voice and not whisper_model:
                await message.reply_text("Transcription unavailable: Whisper model not loaded.")

            # Process images with Tesseract OCR
            elif message.photo and pytesseract.pytesseract.tesseract_cmd:
                try:
                    logger.debug(f"Attempting OCR on image: {save_path}")
                    # Preprocess image for better OCR accuracy
                    # processed_image = preprocess_image(save_path)
                    processed_image = save_path
                    # Perform OCR with Tesseract, specifying Urdu and English
                    ocr_text = pytesseract.image_to_string(processed_image).strip()
                    logger.debug(f"OCR result: {ocr_text}")
                    if ocr_text:
                        content = ocr_text
                        await append_to_notion(timestamp, msg_type, content, save_path,tag="OCR")
                        await message.reply_text(f"OCR Text: {ocr_text}\nSaved to Notion: {timestamp}: image_ocr : {content}")
                    else:
                        # Fall back to caption or default message
                        content = message.caption if message.caption else "No text detected"
                        # await append_to_notion(timestamp, msg_type, content, save_path)
                        await message.reply_text(f"No text detected in image. Saved to Notion: {timestamp}: image_ocr : {content}")
                    logger.info(f"OCR completed for {safe_file_name}")
                except Exception as e:
                    logger.error(f"Error performing OCR on image: {e}")
                    await message.reply_text(f"Failed to perform OCR on image: {str(e)}")
                    # Still save the image with caption or default
                    # await append_to_notion(timestamp, msg_type, content, save_path)
                    await message.reply_text(f"Saved to Notion: {timestamp}: image_ocr : {content}")
            elif message.photo and not pytesseract.pytesseract.tesseract_cmd:
                await message.reply_text("OCR unavailable: Tesseract not installed.")
                # Still save the image with caption or default
                await append_to_notion(timestamp, msg_type, content, save_path)
                await message.reply_text(f"Saved to Notion: {timestamp}: image_ocr : {content}")

            # Process images or documents
            else:
                await append_to_notion(timestamp, msg_type, content, save_path,tag=None)
                await message.reply_text(f"Saved to Notion: {timestamp}: {msg_type} : {content}")

        else:
            await message.reply_text("No downloadable file found in the message.")

    except Exception as e:
        logger.error(f"Error downloading file: {e}")
        await message.reply_text(f"An error occurred while downloading the file: {str(e)}")

def main() -> None:
    # Get Telegram bot token from environment
    bot_token = secrets.bot_token  # Use your bot token from secrets.py
    if not bot_token:
        logger.error("TELEGRAM_BOT_TOKEN not set in .env file")
        raise ValueError("Missing TELEGRAM_BOT_TOKEN")

    # Create the Application and pass the bot's token
    application = Application.builder().token(bot_token).build()

    # Add handlers
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    application.add_handler(MessageHandler(filters.LOCATION, handle_location))
    application.add_handler(MessageHandler(
        filters.Document.ALL | filters.VOICE | filters.PHOTO | filters.VIDEO,
        download_media
    ))

    # Start the Bot
    logger.info("Starting bot...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
