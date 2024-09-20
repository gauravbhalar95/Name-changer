import os
import telebot
from flask import Flask, request

# Get environment variables (API keys, tokens, and channel ID)
bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
tmdb_api_key = os.getenv('TMDB_API_KEY')
channel_id = os.getenv('CHANNEL_ID')

# Initialize the Telegram bot
bot = telebot.TeleBot(bot_token)

# Create a Flask app
app = Flask(__name__)

# Webhook endpoint
@app.route(f"/{bot_token}", methods=["POST"])
def webhook():
    json_update = request.get_json()
    update = telebot.types.Update.de_json(json_update)
    bot.process_new_updates([update])
    return '', 200

# Function to get the titles of the 3 latest upcoming Hindi movies
def get_latest_hindi_movies():
    url = f"https://api.themoviedb.org/3/movie/upcoming?api_key={tmdb_api_key}&language=hi-IN&page=1"
    response = requests.get(url)
    data = response.json()

    if 'results' in data and len(data['results']) > 0:
        movies = data['results'][:3]
        movie_titles = [movie['title'] for movie in movies]
        return ', '.join(movie_titles)
    return None

# Function to change the channel name
def change_channel_name(new_name):
    try:
        bot.set_chat_title(chat_id=channel_id, title=new_name)
        print(f"Channel name changed to: {new_name}")
    except Exception as e:
        print(f"Failed to change channel name: {e}")

# Function to update the channel name
def update_channel_name():
    movie_names = get_latest_hindi_movies()
    if movie_names:
        change_channel_name(movie_names)
    else:
        print("No upcoming Hindi movies found.")

# Call the function to update the channel name at startup
@app.route('/update_channel', methods=['GET'])
def update_channel():
    update_channel_name()
    return "Channel name updated!", 200

# Set the webhook with your public URL and port
if __name__ == "__main__":
    bot.remove_webhook()
    bot.set_webhook(url=f"https://<your_render_service>.render.com/{bot_token}")
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 10000)))
