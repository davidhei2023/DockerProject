import os
import time
import telebot
from loguru import logger
from telebot.types import InputFile


class Bot:
    def __init__(self, token, telegram_chat_url):
        self.telegram_bot_client = telebot.TeleBot(token)
        self.telegram_bot_client.remove_webhook()
        time.sleep(0.5)
        self.telegram_bot_client.set_webhook(url=f"{telegram_chat_url}/{token}/", timeout=60)
        logger.info(f"Telegram Bot information\n\n{self.telegram_bot_client.get_me()}")

    def send_text(self, chat_id, text):
        self.telegram_bot_client.send_message(chat_id, text)

    def is_current_msg_photo(self, msg):
        return "photo" in msg

    def download_user_photo(self, msg):
        if not self.is_current_msg_photo(msg):
            raise RuntimeError("Message content of type 'photo' expected.")

        file_info = self.telegram_bot_client.get_file(msg["photo"][-1]["file_id"])
        file_path = f"photos/{file_info.file_path.split('/')[-1]}"

        os.makedirs("photos", exist_ok=True)

        data = self.telegram_bot_client.download_file(file_info.file_path)
        with open(file_path, "wb") as photo:
            photo.write(data)

        logger.info(f"Photo saved locally to: {file_path}")
        return file_path

    def send_photo(self, chat_id, img_path):
        if not os.path.exists(img_path):
            raise RuntimeError("Image path doesn't exist")

        self.telegram_bot_client.send_photo(chat_id, InputFile(img_path))


class ObjectDetectionBot(Bot):
    def handle_message(self, msg):
        logger.info(f"Incoming message: {msg}")

        if self.is_current_msg_photo(msg):
            try:
                # Handle photo message
                photo_path = self.download_user_photo(msg)
                logger.info(f"Photo downloaded to: {photo_path}")
                self.send_text(msg["chat"]["id"], "Photo received! Processing...")
            except Exception as e:
                logger.error(f"Error in handling message: {str(e)}")
                self.send_text(msg["chat"]["id"], "An error occurred while processing your image.")
        else:
            self.send_text(msg["chat"]["id"], "Please send a photo for object detection.")
