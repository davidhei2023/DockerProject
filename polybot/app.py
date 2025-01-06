import os
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from loguru import logger
from bot import ObjectDetectionBot  # Correct import for the bot

# Load environment variables
load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_APP_URL = os.getenv("TELEGRAM_APP_URL")

if not TELEGRAM_TOKEN or not TELEGRAM_APP_URL:
    raise ValueError("TELEGRAM_TOKEN and TELEGRAM_APP_URL must be set in the environment or .env file.")

app = Flask(__name__)
logger.add("app.log", rotation="500 MB", level="DEBUG")

# Initialize bot
bot = ObjectDetectionBot(TELEGRAM_TOKEN, TELEGRAM_APP_URL)


@app.route("/", methods=["GET"])
def index():
    return "Bot is running!", 200


@app.route(f"/{TELEGRAM_TOKEN}/", methods=["POST"])
def webhook():
    req = request.get_json()
    if not req or "message" not in req:
        logger.warning("Invalid request received.")
        return jsonify({"error": "Invalid request"}), 400

    logger.info(f"Incoming message: {req['message']}")
    bot.handle_message(req["message"])
    return "Ok", 200


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8443))  # Default to port 8443 if not set
    app.run(host="0.0.0.0", port=port)
