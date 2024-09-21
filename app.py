import os
import telebot
import requests
import json
from flask import Flask, request

# Initialize Flask app
app = Flask(__name__)

# Use environment variables for bot token and API key
bot_token = os.getenv('BOT_TOKEN', 'your_default_bot_token')
tmdb_api_key = os.getenv('TMDB_API_KEY', 'your_default_tmdb_api_key')
channel_id = os.getenv('CHANNEL_ID', 'your_default_channel_id')
webhook_url = os.getenv('WEBHOOK_URL', 'your_default_webhook_url')

bot = telebot.TeleBot(bot_token)

# Function to get the name of the latest upcoming movie
def get_latest_movie():
    url = f"https://api.themoviedb.org/3/movie/upcoming?api_key={tmdb_api_key}&language=hi-IN&page=1"
    response = requests.get(url)
    data = response.json()

    if 'results' in data and len(data['results']) > 0:
        latest_movie = data['results'][0]
        movie_title = latest_movie['title']
        print(f"Latest movie found: {movie_title}")
        return movie_title
    print("No upcoming movies found.")
    return None

# Function to get the current channel name
def get_channel_name():
    try:
        chat = bot.get_chat(chat_id=channel_id)
        print(f"Current channel name: {chat.title}")
        return chat.title
    except Exception as e:
        print(f"Failed to get channel name: {e}")
        return None

# Function to change the channel name to append the latest movie, separated by commas
def update_channel_name_with_movie():
    movie_name = get_latest_movie()
    if movie_name:
        current_name = get_channel_name()
        if current_name:
            # Check if movie name is already in the channel title, to avoid duplicates
            if movie_name not in current_name:
                new_name = f"{current_name}, {movie_name}" if current_name else movie_name
                print(f"Updating channel name to: {new_name}")
                change_channel_name(new_name)
            else:
                print(f"The movie '{movie_name}' is already in the channel name.")
        else:
            change_channel_name(movie_name)
    else:
        print("No upcoming movie found.")

# Function to change the channel name
def change_channel_name(new_name):
    try:
        bot.set_chat_title(chat_id=channel_id, title=new_name)
        print(f"Channel name changed to: {new_name}")
    except Exception as e:
        print(f"Failed to change channel name: {e}")

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
    update_channel_name_with_movie()
    return "Channel name update triggered!", 200

# Start the Flask server and set webhook before the first request
if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    
    # Remove existing webhook and set the new one
    bot.remove_webhook()
    bot.set_webhook(url=f"{webhook_url}/{bot_token}")
    
    # Start the Flask server
    app.run(host='0.0.0.0', port=port)
