import spotipy
from spotipy.oauth2 import SpotifyOAuth
import os
from dotenv import load_dotenv, find_dotenv
import random
import yt_dlp
import discord
from discord import app_commands
import re

load_dotenv(find_dotenv())


# НАСТРОЙКИ SPOTIPY
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id=str(os.getenv("SPOTIPY_CLIENT_ID")),
    client_secret=str(os.getenv("SPOTIPY_CLIENT_SECRET")),
    redirect_uri=str(os.getenv("SPOTIPY_REDIRECT_URI")),
    scope=["user-library-read", "playlist-modify-public", "user-read-private"]
))
sp._session.timeout = 10


# ОСНОВНЫЕ ФУНКЦИИ SPOTIPY
def get_user_playlists():
    playlists = sp.current_user_playlists()  
    for playlist in playlists['items']:
        print(f"Playlist: {playlist['name']} ID: {playlist['id']}")

def get_daily_playlists():
    genre = sp.recommendation_genre_seeds()
    genres = genre['genres']
    selected_genres = random.sample(genres, 5) 
    results = sp.recommendations(seed_tracks=None, seed_artists=None, seed_genres=selected_genres, limit=5)
    results_return = []
    for track in results['tracks']:
        # print(f"Трек: {track['name']} от {track['artists'][0]['name']} АЛЬБОМ: {track['album']['name']}")
        results_return.append(f"{track['name']} - {track['artists'][0]['name']}")
    return results_return
    

def get_playlist_details(playlist_id):
    playlist = sp.playlist_tracks(playlist_id)
    for track in playlist['items']:
        track_name = track['track']['name']
        artist_name = track['track']['artists'][0]['name']
        print(f"Трек: {track_name} от {artist_name}")






# print(f'Плейлисты пользователя:')
# get_user_playlists()

# print(f'Подробней о плейлисте пользователя:')
# get_playlist_details('4T7wTsUhZJaz9Kyfbszb1d')

# print(f'Рекомендуемые треки пользователя:')
# print(get_daily_playlists())