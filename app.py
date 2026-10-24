import hmac
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
CRON_SECRET = os.getenv("CRON_SECRET", "")
TMDB_LANGUAGE = os.getenv("TMDB_LANGUAGE", "hi-IN")

app = Flask(__name__)
bot = telebot.TeleBot(BOT_TOKEN, threaded=False) if BOT_TOKEN else None


def _tmdb_get(endpoint, params):
    """Request TMDB JSON with a timeout; return an empty payload on failure."""
    if not TMDB_API_KEY:
        logger.error("TMDB_API_KEY is not configured")
        return {}
    try:
        response = requests.get(
            f"https://api.themoviedb.org/3/{endpoint}",
            params={"api_key": TMDB_API_KEY, **params},
            timeout=12,
        )
        response.raise_for_status()
        return response.json()
    except (requests.RequestException, ValueError):
        logger.exception("TMDB request failed for %s", endpoint)
        return {}


def get_latest_movies(limit=3):
    """Return trending Hindi-language movie titles, with a popularity fallback."""
    movies = []
    seen_ids = set()
    seen_titles = set()

    # Trending list first; only keep films originally made in Hindi.
    trending = _tmdb_get(
        "trending/movie/day",
        {"language": TMDB_LANGUAGE, "page": 1},
    )
    for movie in trending.get("results", []):
        title = (movie.get("title") or movie.get("original_title") or "").strip()
        movie_id = movie.get("id")
        if (
            title
            and movie.get("original_language") == "hi"
            and movie_id not in seen_ids
            and title.casefold() not in seen_titles
        ):
            movies.append(title)
            seen_ids.add(movie_id)
            seen_titles.add(title.casefold())
            if len(movies) >= limit:
                return movies

    # Trending may contain fewer than three Hindi films, so fill remaining
    # slots with popular Hindi-language films rather than unrelated languages.
    popular = _tmdb_get(
        "discover/movie",
        {
            "language": TMDB_LANGUAGE,
            "with_original_language": "hi",
            "sort_by": "popularity.desc",
            "page": 1,
        },
    )
    for movie in popular.get("results", []):
        title = (movie.get("title") or movie.get("original_title") or "").strip()
        movie_id = movie.get("id")
        if (
            title
            and movie_id not in seen_ids
            and title.casefold() not in seen_titles
        ):
            movies.append(title)
            seen_ids.add(movie_id)
            seen_titles.add(title.casefold())
            if len(movies) >= limit:
                break

    return movies


def change_channel_name(new_name):
    if not bot or not CHANNEL_ID:
        logger.error("BOT_TOKEN or CHANNEL_ID is not configured")
        return False

    new_name = " ".join(new_name.split())
    # Telegram chat titles are limited to 128 characters. Prefer complete
    # movie titles and avoid cutting a later title in the middle.
    new_name = new_name[:128]
    if not new_name:
        return False

    try:
        bot.set_chat_title(chat_id=CHANNEL_ID, title=new_name)
        logger.info("Channel title updated to: %s", new_name)
        return True
    except Exception:
        logger.exception("Telegram could not update the channel title")
        return False


def update_channel_name():
    titles = get_latest_movies(limit=3)
    if not titles:
        logger.error("No trending Hindi movie titles were found; title unchanged")
        return False
    return change_channel_name(" | ".join(titles))


if bot:
    @bot.message_handler(commands=["start", "help"])
    def start_command(message):
        bot.reply_to(
            message,
            "Movie Name Changer is online. The channel title is scheduled to "
            "refresh daily with trending Hindi movie names. Admins can use /update "
            "to refresh it immediately."
        )

    @bot.message_handler(commands=["update"])
    def update_command(message):
        admin_id = os.getenv("ADMIN_USER_ID")
        if not admin_id or str(message.from_user.id) != admin_id:
            bot.reply_to(message, "This command is restricted to the configured administrator.")
            return
        success = update_channel_name()
        bot.reply_to(
            message,
            "Channel title updated with trending Hindi movies." if success else
            "Update failed. Check BOT_TOKEN, TMDB_API_KEY, CHANNEL_ID and Vercel logs."
        )


@app.get("/")
@app.get("/api/index")
def home():
    # Vercel Cron calls /api/index with Authorization: Bearer <CRON_SECRET>.
    # No automatic update occurs until CRON_SECRET is configured in Vercel.
    authorization = request.headers.get("Authorization", "")
    if CRON_SECRET and hmac.compare_digest(authorization, f"Bearer {CRON_SECRET}"):
        success = update_channel_name()
        return jsonify({
            "ok": success,
            "task": "daily-trending-hindi-movie-title-update",
        }), (200 if success else 500)

    return jsonify({
        "status": "ok",
        "service": "name-changer",
        "bot_configured": bool(BOT_TOKEN),
        "tmdb_configured": bool(TMDB_API_KEY),
        "channel_configured": bool(CHANNEL_ID),
        "daily_auto_update_configured": bool(CRON_SECRET),
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
