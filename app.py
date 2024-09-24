from flask import Flask, request, jsonify
import telebot
import requests
import os

# Your Telegram bot token
bot_token = os.getenv('BOT_TOKEN')
bot = telebot.TeleBot(bot_token)

# Your TMDb API key
tmdb_api_key = os.getenv('TMDB_API_KEY')

# The ID of the Telegram channel you want to rename
channel_id = os.getenv('CHANNEL_ID')

# Flask app to keep the bot alive
app = Flask(__name__)

# Function to get the names of the first 3 upcoming movies
def get_upcoming_movies():
    try:
        url = f"https://api.themoviedb.org/3/movie/upcoming?api_key={tmdb_api_key}&language=hi-IN&page=1"
        response = requests.get(url)
        data = response.json()

        if 'results' in data and len(data['results']) > 0:
            upcoming_movies = [movie['title'] for movie in data['results'][:3]]
            print(f"Upcoming movies: {upcoming_movies}")
            return ', '.join(upcoming_movies)
        print("No upcoming movies found in the TMDb response.")
        return None
    except Exception as e:
        print(f"Error fetching upcoming movies: {e}")
        return None

# Function to change the channel name
def change_channel_name(new_name):
    try:
        bot.set_chat_title(chat_id=channel_id, title=new_name)
        print(f"Channel name changed to: {new_name}")
        return True
    except Exception as e:
        print(f"Failed to change channel name: {e}")
        return False

# Set webhook
@app.route('/setwebhook', methods=['GET', 'POST'])
def set_webhook():
    webhook_url = os.getenv('WEBHOOK_URL')  # Your HTTPS webhook URL (e.g., https://yourdomain.com/webhook)
    s = bot.set_webhook(url=webhook_url)
    if s:
        return jsonify({"status": "success", "message": "Webhook set successfully"})
    else:
        return jsonify({"status": "error", "message": "Failed to set webhook"}), 500

# Webhook to receive updates
@app.route('/webhook', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_str = request.get_data().decode('UTF-8')
        update = telebot.types.Update.de_json(json_str)
        bot.process_new_updates([update])
        return 'OK', 200
    else:
        return 'Unsupported Media Type', 415

# Command handler
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "Welcome to the Movie Channel Bot! Use /update to rename the channel.")

# Command to trigger channel update
@bot.message_handler(commands=['update'])
def update_channel_name_handler(message):
    movie_names = get_upcoming_movies()
    if movie_names:
        success = change_channel_name(movie_names)
        if success:
            bot.reply_to(message, f"Channel name updated to: {movie_names}")
        else:
            bot.reply_to(message, "Failed to change channel name.")
    else:
        bot.reply_to(message, "No upcoming movies found.")

# Flask route to check if the app is running
@app.route('/')
def home():
    return "Bot is running!"

if __name__ == "__main__":
    # Bind Flask app to port 5000 or any other port
    app.run(host='0.0.0.0', port=5000)
