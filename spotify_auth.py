from dotenv import load_dotenv
import os
import base64
from requests import post
import json
import requests
from bs4 import BeautifulSoup
import re
import time
import sqlite3
from requests import get

load_dotenv()

client_id = os.getenv("CLIENT_ID")
client_secret = os.getenv("CLIENT_SECRET")

def get_token():
    auth_string = client_id + ":" + client_secret
    auth_bytes = auth_string.encode("utf-8")
    auth_base64 = str(base64.b64encode(auth_bytes), "utf-8")

    url = "https://accounts.spotify.com/api/token"
    headers = {
        "Authorization": "Basic " + auth_base64,
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {"grant_type": "client_credentials"}
    result = post(url, headers=headers, data=data)
    json_result = json.loads(result.content)
    token = json_result["access_token"]
    return token

def get_auth_header(token):
    return {"Authorization": "Bearer " + token}





#BUILDING UTILITIES FOR GENRES SECOND PAGES

# Funzione per cercare playlist di un genere

def search_playlists_by_genre(auth_header, genre, limit=20):
    url = f"https://api.spotify.com/v1/search?q=genre:{genre}&type=playlist&limit={limit}"
    response = requests.get(url, headers=auth_header)
    response.raise_for_status()
    data = response.json()

    if not isinstance(data, dict) or 'playlists' not in data:
        return []

    playlists = data.get('playlists', {}).get('items', [])
    playlists_details = []

    for playlist in playlists:
        playlist_details = {
            'id': playlist['id'],
            'cover_image': playlist['images'][0]['url'] if playlist.get('images') else None,
            'name': playlist['name'],
            'tracks_count': playlist['tracks']['total']  # Assuming you get the track count this way
        }
        playlists_details.append(playlist_details)

    return playlists_details

def get_sorted_playlists(playlists):
    # Ordinamento delle playlist per il numero di tracce (in ordine decrescente)
    sorted_playlists = sorted(playlists, key=lambda p: p['tracks_count'], reverse=True)
    return sorted_playlists

    # FUNZIONE AUSILIARIA A QUELLA DOPO PER LA PAGINA DELLE PLAYLISTS
def get_playlist_tracks(playlist_id, auth_header):
    """Recupera tutte le tracce della playlist, gestendo la paginazione."""
    base_url = f'https://api.spotify.com/v1/playlists/{playlist_id}/tracks'
    tracks = []
    next_url = base_url

    while next_url:
        response = get(next_url, headers=auth_header)
        response.raise_for_status()
        data = response.json()
        tracks.extend(data['items'])
        next_url = data.get('next')

    return tracks
    # MAIN FUNCTION PER LA PAGINA DELLA PLAYLISTS
def get_playlist_details(playlist_id, auth_header):
    """Recupera i dettagli della playlist e le sue tracce usando l'ID della playlist."""
    playlist_url = f'https://api.spotify.com/v1/playlists/{playlist_id}'
    playlist_response = get(playlist_url, headers=auth_header)
    playlist_response.raise_for_status()
    playlist_data = playlist_response.json()

    # Recupera tutte le tracce della playlist
    tracks_data = get_playlist_tracks(playlist_id, auth_header)

    playlist_info = {
        'playlist_name': playlist_data.get('name', 'Unknown'),
        'description': playlist_data.get('description', 'No description'),
        'cover_image': playlist_data['images'][0]['url'] if 'images' in playlist_data and playlist_data['images'] else None,
        'tracks': [
            {
                'album_id': track['track']['album']['id'],
                'track_name': track['track']['name'],
                'artist_name': ', '.join(artist['name'] for artist in track['track']['artists']),
                'artist_id': ', '.join(artist['id'] for artist in track['track']['artists']),
                'album_name': track['track']['album']['name'],
                'cover_image': track['track']['album']['images'][0]['url'] if 'images' in track['track']['album'] and track['track']['album']['images'] else None,
                'duration': format_duration(track['track']['duration_ms'])
            }
            for track in tracks_data
        ]
    }
    return playlist_info



def format_duration(duration_ms):
    """Formatta la durata della traccia in minuti e secondi."""
    minutes, seconds = divmod(duration_ms // 1000, 60)
    return f"{minutes}:{seconds:02d}"

def get_available_genre_seeds(auth_header):
    url = 'https://api.spotify.com/v1/recommendations/available-genre-seeds'
    
    response = get(url, headers=auth_header)
    genres = response.json()['genres']
    return genres

def get_recommendations_by_genre(auth_header, genre):
    url = 'https://api.spotify.com/v1/recommendations'
    params = {
    'seed_genres': genre,
    'limit': 20,  # Numero di tracce raccomandate
}
    response = get(url, headers=auth_header, params=params)
    recommendations = response.json()
    tracks = recommendations['tracks']
    return tracks

def get_album_tracks(album_id, auth_header):
    """Recupera tutte le tracce dell'album, gestendo la paginazione."""
    url = f'https://api.spotify.com/v1/albums/{album_id}/tracks'
    tracks = []
    next_url = url

    while next_url:
        response = get(next_url, headers=auth_header)
        response.raise_for_status()
        data = response.json()
        tracks.extend(data['items'])
        next_url = data.get('next')

    return tracks

def get_album_details(album_id, auth_header):
    """Recupera i dettagli dell'album usando l'ID dell'album."""
    album_url = f'https://api.spotify.com/v1/albums/{album_id}'
    album_response = get(album_url, headers=auth_header)
    album_response.raise_for_status()
    album_data = album_response.json()

    # Recupera le tracce dell'album
    tracks_data = get_album_tracks(album_id, auth_header)

    # Gestisci i casi in cui le chiavi potrebbero non essere presenti
    album_info = {
        'album_name': album_data.get('name', 'Unknown'),
        'album_id': album_data.get('id', 'Unknown'),
        'artist_name': album_data['artists'][0]['name'] if 'artists' in album_data and album_data['artists'] else 'Unknown',
        'artist_id': album_data['artists'][0]['id'] if 'artists' in album_data and album_data['artists'] else 'Unknown',
        'release_date': album_data.get('release_date', 'Unknown'),
        'total_tracks': album_data['total_tracks'],
        'cover_image': album_data['images'][0]['url'] if 'images' in album_data and album_data['images'] else None,
        'album_type': album_data.get('album_type', 'unknown'),
        'genres': album_data.get('genres', []),
        'tracks': [
            {
                'track_name': track['name'],
                'duration': format_duration(track['duration_ms'])
            }
            for track in tracks_data
        ]
    }
    return album_info

def get_album_from_tracks(tracks, auth_header):
    """Recupera le informazioni sugli album a partire da una lista di tracce."""
    albums = []
    seen_albums = set()  # Usa un set per tenere traccia degli ID degli album già processati
    
    for track in tracks:
        album = track['album']
        album_id = album['id']
        
        # Salta gli album già processati
        if album_id in seen_albums:
            continue
        
        seen_albums.add(album_id)
        album_details = get_album_details(album_id, auth_header)
        
        album_info = {
            'album_name': album_details.get('album_name', 'Unknown'),
            'album_id': album_details.get('album_id', 'Unknown'),
            'artist_name': album_details.get('artist_name', 'Unknown'),
            'artist_id': album_details.get('artist_id', 'Unknown'),
            'cover_image': album_details.get('cover_image', None)
        }
        albums.append(album_info)
    
    return albums

def get_artist_details(artist_id, auth_header):
    url = f"https://api.spotify.com/v1/artists/{artist_id}"
    response = requests.get(url, headers=auth_header)
    response.raise_for_status()
    return response.json()

def get_artist_albums(artist_id, auth_header):
    url = f"https://api.spotify.com/v1/artists/{artist_id}/albums"
    params = {
        "include_groups": "album",  # Specifica che vuoi solo album di tipo 'album'
        "limit": 50  # Specifica il numero massimo di album per richiesta
    }

    albums = []
    while url:
        response = requests.get(url, headers=auth_header, params=params)
        response.raise_for_status()
        data = response.json()
        
        # Aggiungi gli album alla lista
        albums.extend(data["items"])

        # Ottieni il prossimo URL per la paginazione
        url = data.get("next")  # 'next' sarà None se non ci sono più pagine

        # Aggiorna i parametri solo per le richieste successive
        params = {}  # Non serve specificare i parametri per la paginazione successiva

    return albums

def get_artist_bio(artist_name):
    # Creazione dell'URL di ricerca per Wikipedia
    base_url = 'https://en.wikipedia.org/api/rest_v1/page/summary/'
    url = base_url + artist_name.replace(' ', '_')
    
    # Impostazione dell'user agent personalizzato
    headers = {
        'User-Agent': 'CloneRateYourMusic/1.0 (https://example.org/clonerateyourmusic/; youremail@example.com)'
    }
    
    # Effettua la richiesta HTTP a Wikipedia per la bio
    response = get(url, headers=headers)
    
    if response.status_code == 200:
        # Recupera i dati in formato JSON
        data = response.json()
        
        # Estrarre le informazioni necessarie
        biography = data.get('extract', 'Biografia non trovata')
        return biography
    else:
        return {
            'error': "Errore nella richiesta: " + str(response.status_code)
        }

def clean_date_text(date_text):
    # Trova date nel formato YYYY-MM-DD, oppure formato con mese e giorno
    match = re.search(r'\b(\d{4}-\d{2}-\d{2})\b', date_text)
    if match:
        return match.group(0)
    
    # Se non trova YYYY-MM-DD, prova a trovare date nel formato "Month Day, Year"
    match = re.search(r'\b(\w+ \d{1,2}, \d{4})\b', date_text)
    if match:
        return match.group(0)
    
    return 'Data non trovata'

def get_artist_birth_and_death_dates(artist_name, retry_attempts=3):
    url = f'https://en.wikipedia.org/wiki/{artist_name.replace(" ", "_")}'
    headers = {
        'User-Agent': 'CloneRateYourMusic/1.0 (https://example.org/clonerateyourmusic/; youremail@example.com)'
    }
    
    for attempt in range(retry_attempts):
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'lxml')
            infobox = soup.find('table', {'class': 'infobox'})
            
            birth_date = 'N/A'
            death_date = 'N/A'
            
            if infobox:
                rows = infobox.find_all('tr')
                for row in rows:
                    th = row.find('th')
                    td = row.find('td')
                    if th and td:
                        header_text = th.get_text(strip=True)
                        cell_text = td.get_text(strip=True)
                        if 'Born' in header_text:
                            birth_date = clean_date_text(cell_text)
                        elif 'Died' in header_text:
                            death_date = clean_date_text(cell_text)
                
            return {
                'birth_date': birth_date,
                'death_date': death_date
            }
        except requests.RequestException as e:
            print(f"Attempt {attempt + 1}: {e}, retrying...")
            time.sleep(1)  # Attendi un secondo prima di riprovare

    # Ritorna valori predefiniti in caso di errori
    return {
        'birth_date': 'N/A',
        'death_date': 'N/A',
        'error': "Server error after multiple attempts"
    }

# COSTRUZIONE FUNZIONI PER CONSENTIRE ALL UTENTE DI VOTARE E RECENSIRE ALBUMS

def get_db_connection():
    conn = sqlite3.connect('users.db')
    conn.row_factory = sqlite3.Row
    return conn

# FUNZIONE PER OTTENERE RECENSIONI ALBUM SPECIFICO

def get_reviews(album_id):
    conn = get_db_connection()
    query = """
    SELECT 
    users.username AS username,
    album_reviews.created_at AS review_date,
    album_reviews.review_title AS title,
    album_reviews.review_text AS text,
    album_ratings.rating AS rating
FROM album_reviews
JOIN users ON album_reviews.user_id = users.id
LEFT JOIN album_ratings ON album_reviews.album_id = album_ratings.album_id AND album_reviews.user_id = album_ratings.user_id
WHERE album_reviews.album_id = ?
    """
    reviews = conn.execute(query, (album_id,)).fetchall()
    conn.close()

    #print("Reviews fetched:", reviews)

    return [{
        'username': review['username'],
        'review_date': review['review_date'],
        'title': review['title'],
        'text': review['text'],
        'rating': review['rating']
    } for review in reviews]
# COSTRUZIONE FUNZIONI PER HOMEPAGE

def get_average_rating(album_id):
    """Calcola la valutazione media di un album."""
    conn = get_db_connection()
    avg_rating = conn.execute("""
        SELECT AVG(rating) as average_rating
        FROM album_ratings
        WHERE album_id = ?
    """, (album_id,)).fetchone()['average_rating']
    conn.close()
    
    return avg_rating if avg_rating is not None else 0




