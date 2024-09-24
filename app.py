import os
import telebot
import requests
from flask import Flask

# Load environment variables
bot_token = os.getenv('BOT_TOKEN')  # Store your bot token in an environment variable
tmdb_api_key = os.getenv('TMDB_API_KEY')  # Store your TMDB API key in an environment variable
channel_id = os.getenv('CHANNEL_ID')  # Store your channel ID in an environment variable
port = int(os.getenv('PORT', 5000))  # Use environment variable for the port (default is 5000)
webhook_url = os.getenv('WEBHOOK_URL')  # Webhook URL for the bot

bot = telebot.TeleBot(bot_token)
app = Flask(__name__)

# Function to get the names of the first 3 upcoming movies
def get_latest_movies():
    url = f"https://api.themoviedb.org/3/movie/upcoming?api_key={tmdb_api_key}&language=hi-IN&page=1"
    response = requests.get(url)
    data = response.json()

    if 'results' in data and len(data['results']) > 0:
        # Get the first 3 movies
        upcoming_movies = [movie['title'] for movie in data['results'][:3]]
        return ', '.join(upcoming_movies)  # Join movie titles with a comma
    return None

# Function to change the channel name
def change_channel_name(new_name):
    try:
        bot.set_chat_title(chat_id=channel_id, title=new_name)
        print(f"Channel name changed to: {new_name}")
    except Exception as e:
        print(f"Failed to change channel name: {e}")

# Main function to update the channel name
def update_channel_name():
    movie_names = get_latest_movies()
    if movie_names:
        change_channel_name(movie_names)
    else:
        print("No upcoming movies found.")

# Set webhook route for Telegram
@app.route('/webhook', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_str = request.get_data().decode('UTF-8')
        update = telebot.types.Update.de_json(json_str)
        bot.process_new_updates([update])
        return 'OK', 200
    else:
        return 'Unsupported Media Type', 415

# Bind Flask app to the provided port
@app.route('/')
def home():
    return "Bot is running!"

# Start Flask app
if __name__ == "__main__":
    update_channel_name()  # Update the channel name on startup
    app.run(host='0.0.0.0', port=port)  # Bind to the environment variable port
