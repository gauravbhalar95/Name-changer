import os
import telebot
import requests
import json
from flask import Flask, request

# Initialize Flask app
app = Flask(__name__)

# Use environment variables for bot token, API key, and channel ID
bot_token = os.getenv('BOT_TOKEN', 'your_default_bot_token')
tmdb_api_key = os.getenv('TMDB_API_KEY', 'your_default_tmdb_api_key')
channel_id = os.getenv('CHANNEL_ID', 'your_default_channel_id')
webhook_url = os.getenv('WEBHOOK_URL', 'your_default_webhook_url')

bot = telebot.TeleBot(bot_token)

# Function to get the names of the top 3 latest upcoming movies
def get_latest_movies():
    url = f"https://api.themoviedb.org/3/movie/upcoming?api_key={tmdb_api_key}&language=hi-IN&page=1"
    response = requests.get(url)
    data = response.json()

    if 'results' in data and len(data['results']) > 0:
        # Get the top 3 upcoming movies (or fewer if there aren't 3)
        latest_movies = data['results'][:3]
        movie_titles = [movie['title'] for movie in latest_movies]
        movie_titles_str = ', '.join(movie_titles)
        return movie_titles_str
    return None

# Function to change the channel name
def change_channel_name(new_name):
    try:
        bot.set_chat_title(chat_id=channel_id, title=new_name)
        print(f"Channel name changed to: {new_name}")
    except Exception as e:
        print(f"Failed to change channel name: {e}")

# Main function to update the channel name with the top 3 movies
def update_channel_name():
    movies = get_latest_movies()
    if movies:
        change_channel_name(movies)
    else:
        print("No upcoming movies found.")

# Set webhook for bot deployment
@app.route('/' + bot_token, methods=['POST'])
def webhook():
    json_str = request.get_data().decode('UTF-8')
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "Webhook received!", 200

# Main route for testing the Flask app
@app.route('/')
def index():
    return "Bot is running!", 200

# Route to manually trigger channel name update
@app.route('/update_channel_name', methods=['GET'])
def trigger_update():
    update_channel_name()
    return "Channel name update triggered!", 200

# Start the Flask server and set webhook before the first request
if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    
    # Remove existing webhook and set the new one
    bot.remove_webhook()
    bot.set_webhook(url=f"{webhook_url}/{bot_token}")
    
    # Start the Flask server
    app.run(host='0.0.0.0', port=port)
