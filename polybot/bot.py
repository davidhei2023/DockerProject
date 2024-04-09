import telebot
from loguru import logger
import os
import time
from telebot.types import InputFile
from polybot.img_proc import Img


class Bot:

    def __init__(self, token, telegram_chat_url):
        # create a new instance of the TeleBot class.
        # all communication with Telegram servers are done using self.telegram_bot_client
        self.telegram_bot_client = telebot.TeleBot(token)

        # remove any existing webhooks configured in Telegram servers
        self.telegram_bot_client.remove_webhook()
        time.sleep(0.5)

        # set the webhook URL
        self.telegram_bot_client.set_webhook(url=f'{telegram_chat_url}/{token}/', timeout=60)

        logger.info(f'Telegram Bot information\n\n{self.telegram_bot_client.get_me()}')

    def send_text(self, chat_id, text):
        self.telegram_bot_client.send_message(chat_id, text)

    def send_text_with_quote(self, chat_id, text, quoted_msg_id):
        self.telegram_bot_client.send_message(chat_id, text, reply_to_message_id=quoted_msg_id)

    def is_current_msg_photo(self, msg):
        return 'photo' in msg

    def download_user_photo(self, msg):
        """
        Downloads the photos that sent to the Bot to `photos` directory (should be existed)
        :return:
        """
        if not self.is_current_msg_photo(msg):
            raise RuntimeError(f'Message content of type \'photo\' expected')

        file_info = self.telegram_bot_client.get_file(msg['photo'][-1]['file_id'])
        data = self.telegram_bot_client.download_file(file_info.file_path)
        folder_name = file_info.file_path.split('/')[0]

        if not os.path.exists(folder_name):
            os.makedirs(folder_name)

        with open(file_info.file_path, 'wb') as photo:
            photo.write(data)

        return file_info.file_path

    def send_photo(self, chat_id, img_path):
        if not os.path.exists(img_path):
            raise RuntimeError("Image path doesn't exist")

        self.telegram_bot_client.send_photo(
            chat_id,
            InputFile(img_path)
        )

    def handle_message(self, msg):
        """Bot Main message handler"""
        logger.info(f'Incoming message: {msg}')
        self.send_text(msg['chat']['id'], f'Your original message: {msg["text"]}')


class ImageProcessingBot(Bot):
    def __init__(self, token, telegram_chat_url):
        super().__init__(token, telegram_chat_url)

    def handle_message(self, message):
        if "text" in message:
            self.send_text(message['chat']['id'], f'Your original message: {message["text"]}')
        else:
            if "caption" in message:
                try:
                    image_path = self.download_user_photo(message)
                    caption = message["caption"].lower()  # ignore capital or lower case
                    if caption == "blur":
                        self.send_text(message['chat']['id'], "Blur filter in progress")
                        new_image = Img(image_path)
                        new_image.blur()
                        new_image_path = new_image.save_img()
                        self.send_photo(message["chat"]["id"], new_image_path)
                        self.send_text(message['chat']['id'], "Blur filter applied")
                    elif caption == "contour":
                        self.send_text(message['chat']['id'], "Contour filter in progress")
                        new_image = Img(image_path)
                        new_image.contour()
                        new_image_path = new_image.save_img()
                        self.send_photo(message["chat"]["id"], new_image_path)
                        self.send_text(message['chat']['id'], "Contour filter applied")
                    elif caption == "salt and pepper":
                        self.send_text(message['chat']['id'], "Salt and Pepper filter in progress")
                        new_image = Img(image_path)
                        new_image.salt_n_pepper()
                        new_image_path = new_image.save_img()
                        self.send_photo(message["chat"]["id"], new_image_path)
                        self.send_text(message['chat']['id'], "Salt and Pepper filter applied")
                    elif caption == "dreamy enhance":  # New filter
                        self.send_text(message['chat']['id'], "Dreamy Enhance filter in progress")
                        new_image = Img(image_path)
                        new_image.dreamy_enhance()
                        new_image_path = new_image.save_img()
                        self.send_photo(message["chat"]["id"], new_image_path)
                        self.send_text(message['chat']['id'], "Dreamy Enhance filter applied")
                    else:
                        self.send_text(message['chat']['id'], f'Error, please choose a valid caption')
                except Exception as error:
                    logger.info(f"Error {error}")
                    self.send_text(message['chat']['id'], f'Failed - Try again later')
            else:
                self.send_text(message['chat']['id'], f'Failed - Please provide caption')


class ObjectDetectionBot(Bot):
    def handle_message(self, msg):
        logger.info(f'Incoming message: {msg}')

        if self.is_current_msg_photo(msg):
            photo_path = self.download_user_photo(msg)

            # TODO upload the photo to S3
            # TODO send an HTTP request to the `yolo5` service for prediction
            # TODO send the returned results to the Telegram end-user
