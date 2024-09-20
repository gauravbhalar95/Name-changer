import os
import telebot
import requests

# Get environment variables (API keys, tokens, and channel ID)
bot_token = os.getenv('TELEGRAM_BOT_TOKEN')  # Store in Render environment
tmdb_api_key = os.getenv('TMDB_API_KEY')    # Store in Render environment
channel_id = os.getenv('CHANNEL_ID')        # Store in Render environment

# Initialize the Telegram bot
bot = telebot.TeleBot(bot_token)

# Function to get the titles of the 3 latest upcoming Hindi movies
def get_latest_hindi_movies():
    url = f"https://api.themoviedb.org/3/movie/upcoming?api_key={tmdb_api_key}&language=hi-IN&page=1"
    response = requests.get(url)
    data = response.json()

    if 'results' in data and len(data['results']) > 0:
        # Extract the titles of the first 3 movies
        movies = data['results'][:3]  # Get only the first 3 results
        movie_titles = [movie['title'] for movie in movies]
        return ', '.join(movie_titles)  # Join the titles with commas
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
    movie_names = get_latest_hindi_movies()
    if movie_names:
        change_channel_name(movie_names)
    else:
        print("No upcoming Hindi movies found.")

# Call the function to update the channel name
if __name__ == "__main__":
    update_channel_name()
