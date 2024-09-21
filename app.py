from flask import Flask
import telebot
import requests

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
    url = f"https://api.themoviedb.org/3/movie/upcoming?api_key={tmdb_api_key}&language=hi-IN&page=1"
    response = requests.get(url)
    data = response.json()

    if 'results' in data and len(data['results']) > 0:
        # Get the titles of the first 3 movies
        upcoming_movies = [movie['title'] for movie in data['results'][:3]]
        return ', '.join(upcoming_movies)  # Combine movie names with a comma separator
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
    movie_names = get_upcoming_movies()
    if movie_names:
        change_channel_name(movie_names)
    else:
        print("No upcoming movies found.")

# Flask route to bind the app to a port
@app.route('/')
def home():
    return "Bot is running!"

if __name__ == "__main__":
    update_channel_name()  # Update the channel name on startup
    # Bind Flask app to port 5000 or any other port
    app.run(host='0.0.0.0', port=5000)
