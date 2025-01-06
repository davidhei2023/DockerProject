import os
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from loguru import logger
from polybot.bot import ObjectDetectionBot
import requests


# Load environment variables
load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

if not TELEGRAM_TOKEN or not WEBHOOK_URL:
    raise ValueError("TELEGRAM_TOKEN and WEBHOOK_URL must be set in the environment or .env file.")

# Initialize bot
bot = ObjectDetectionBot(TELEGRAM_TOKEN, WEBHOOK_URL)

app = Flask(__name__)
logger.add("app.log", rotation="500 MB", level="DEBUG")


@app.route("/", methods=["GET"])
def index():
    return "Bot is running!", 200


@app.route(f"/{TELEGRAM_TOKEN}/", methods=["POST"])
def telegram_webhook():
    data = request.get_json()
    if not data or "message" not in data:
        logger.warning("Invalid webhook request received.")
        return jsonify({"error": "Invalid webhook request"}), 400

    message = data["message"]
    chat_id = message["chat"]["id"]

    if "photo" in message:
        logger.info(f"Photo received from chat {chat_id}")
        bot.handle_message(message)
        return jsonify({"message": "Photo received"}), 200
    elif "text" in message:
        logger.info(f"Text message received from chat {chat_id}: {message['text']}")
        bot.send_text(chat_id, "Thank you for your message! Please send a photo for object detection.")
        return jsonify({"message": "Text received"}), 200
    else:
        logger.info(f"Unhandled message type from chat {chat_id}: {message}")
        return jsonify({"message": "Unsupported message type"}), 200


# Set Telegram Webhook
def set_webhook():
    # Check current webhook status
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getWebhookInfo"
    response = requests.get(url)
    webhook_info = response.json()

    if webhook_info.get("ok") and webhook_info.get("result", {}).get("url") == f"{WEBHOOK_URL}/{TELEGRAM_TOKEN}/":
        logger.info("Webhook is already set correctly.")
        return

    # Clear any existing webhook
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/deleteWebhook"
    requests.get(url)

    # Set the new webhook
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/setWebhook"
    webhook_url = f"{WEBHOOK_URL}/{TELEGRAM_TOKEN}/"
    response = requests.post(url, json={"url": webhook_url})
    if response.status_code == 200:
        logger.info("Webhook set successfully.")
    else:
        logger.error(f"Failed to set webhook: {response.json()}")


def check_webhook():
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getWebhookInfo"
    response = requests.get(url)
    logger.info(f"Webhook info: {response.json()}")


if __name__ == "__main__":
    set_webhook()  # Set the webhook before starting the app
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 8081)))
