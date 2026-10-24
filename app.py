import logging
import os

import requests
import telebot
from flask import Flask, jsonify, request

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
TMDB_API_KEY = os.getenv("TMDB_API_KEY")
CHANNEL_ID = os.getenv("CHANNEL_ID")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "")
TMDB_LANGUAGE = os.getenv("TMDB_LANGUAGE", "hi-IN")

app = Flask(__name__)
bot = telebot.TeleBot(BOT_TOKEN, threaded=False) if BOT_TOKEN else None


def get_latest_movies(limit=3):
    """Return upcoming movie titles from TMDB, or an empty list on failure."""
    if not TMDB_API_KEY:
        logger.error("TMDB_API_KEY is not configured")
        return []
    try:
        response = requests.get(
            "https://api.themoviedb.org/3/movie/upcoming",
            params={"api_key": TMDB_API_KEY, "language": TMDB_LANGUAGE, "page": 1},
            timeout=12,
        )
        response.raise_for_status()
        payload = response.json()
        return [
            movie.get("title", "").strip()
            for movie in payload.get("results", [])
            if movie.get("title", "").strip()
        ][:limit]
    except (requests.RequestException, ValueError):
        logger.exception("TMDB request failed")
        return []


def change_channel_name(new_name):
    if not bot or not CHANNEL_ID:
        logger.error("BOT_TOKEN or CHANNEL_ID is not configured")
        return False
    new_name = " ".join(new_name.split())[:128]
    if not new_name:
        return False
    try:
        bot.set_chat_title(chat_id=CHANNEL_ID, title=new_name)
        logger.info("Channel title updated")
        return True
    except Exception:
        logger.exception("Telegram could not update the channel title")
        return False


def update_channel_name():
    titles = get_latest_movies()
    return change_channel_name(" | ".join(titles)) if titles else False


if bot:
    @bot.message_handler(commands=["start", "help"])
    def start_command(message):
        bot.reply_to(
            message,
            "Movie Name Changer is online. Use /update to set the channel title "
            "to the latest upcoming Hindi movie names."
        )

    @bot.message_handler(commands=["update"])
    def update_command(message):
        admin_id = os.getenv("ADMIN_USER_ID")
        if admin_id and str(message.from_user.id) != admin_id:
            bot.reply_to(message, "You are not authorized to run this command.")
            return
        success = update_channel_name()
        bot.reply_to(
            message,
            "Channel title updated." if success else
            "Update failed. Check BOT_TOKEN, TMDB_API_KEY, CHANNEL_ID and logs."
        )


@app.get("/")
@app.get("/api/index")
def home():
    return jsonify({
        "status": "ok",
        "service": "name-changer",
        "bot_configured": bool(BOT_TOKEN),
        "tmdb_configured": bool(TMDB_API_KEY),
        "channel_configured": bool(CHANNEL_ID),
    })


@app.route("/webhook", methods=["POST"])
@app.route("/api/index", methods=["POST"])
def webhook():
    if not bot:
        return jsonify({"error": "BOT_TOKEN is not configured"}), 503
    if WEBHOOK_SECRET:
        supplied_secret = request.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
        if supplied_secret != WEBHOOK_SECRET:
            return jsonify({"error": "unauthorized"}), 401
    if not request.is_json:
        return jsonify({"error": "expected application/json"}), 415
    try:
        update = telebot.types.Update.de_json(request.get_data(as_text=True))
        bot.process_new_updates([update])
    except Exception:
        logger.exception("Failed to process Telegram update")
        return jsonify({"error": "update processing failed"}), 500
    return jsonify({"ok": True}), 200


@app.get("/health")
def health():
    return jsonify({"status": "healthy"}), 200
