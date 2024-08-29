from cs50 import SQL
from flask import Flask, redirect, render_template, request, session, jsonify
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from helpers import apology
import spotify_auth
import requests
from flask import Flask, render_template, request, jsonify


# Configure application
app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///users.db")

# Obtain Spotify token and authorization header
token = spotify_auth.get_token()
auth_header = spotify_auth.get_auth_header(token)


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

@app.route("/")
def home():
    """Show homepage"""
    conn = spotify_auth.get_db_connection()
    p_reviews = conn.execute("""
        SELECT
            u.username,
            ar.rating,
            r.review_title,
            r.review_text,
            r.album_id,
            r.created_at  -- Aggiungi la colonna per la data di creazione
        FROM album_reviews r
        JOIN users u ON r.user_id = u.id
        JOIN album_ratings ar ON r.user_id = ar.user_id AND r.album_id = ar.album_id
        WHERE u.plan_type = 'premium'
        ORDER BY r.created_at DESC  -- Ordina dalla recensione più recente alla meno recente
    """).fetchall()
    conn.close()
    
    album_details = []
    for review in p_reviews:
        album_info = spotify_auth.get_album_details(review['album_id'], auth_header)
        avg_rating = spotify_auth.get_average_rating(review['album_id'])
        album_details.append({
            'username': review['username'],
            'rating': review['rating'],
            'review_title': review['review_title'],
            'review_text': review['review_text'],
            'album_id': review['album_id'],
            'album_name': album_info['album_name'],  # Modifica qui
            'album_cover': album_info['cover_image'],  # Modifica qui
            'album_genres': album_info['genres'],
            'artist_name': album_info['artist_name'],  # Aggiungi come una lista
            'artist_id': album_info['artist_id'],
            'average_rating': avg_rating  # Aggiungi come una lista
        })
    
    return render_template("home.html", reviews=album_details)

@app.route("/login", methods=["GET", "POST"])
def login():
    

    # Forget any user_id
    session.clear()

    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username")

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password")

        try:
            # Query database for username
            rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))
        except Exception as e:
            return apology(f"Database error: {e}", 500)

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["password_hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    else:
        return render_template("login.html")

@app.route("/logout")
def logout():
    

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/signup", methods=["GET", "POST"])
def signup():
    """signup"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 400)

        # Ensure password was submitted
        if not request.form.get("password"):
            return apology("must provide password", 400)

        # Ensure confirmation was submitted
        if not request.form.get("confirmation"):
            return apology("must provide password confirmation", 400)
        
        # Ensure email was submitted
        if not request.form.get("email"):
            return apology("must provide email", 400)

        # Check if password and confirmation are the same
        if request.form.get("password") != request.form.get("confirmation"):
            return apology("password and confirmation must be the same", 400)

        # Check if username is already taken
        user = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))
        if len(user) > 0:
            return apology("username already taken")
        
        # Check if email is already taken
        email = db.execute("SELECT * FROM users WHERE email = ?", request.form.get("email"))
        if len(email) > 0:
            return apology("email already taken")

        #Send info to database
        db.execute("INSERT INTO users (username, email, password_hash) VALUES (:username, :email, :hash)",
           username=request.form.get("username"),
           email=request.form.get("email"),
           hash=generate_password_hash(request.form.get("password")))

        # Get the new user's ID
        rows = db.execute("SELECT * FROM users WHERE username = :username", username=request.form.get("username"))
        user_id = rows[0]["id"]

        # Remember which user has logged in
        session["user_id"] = user_id

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("signup.html")

"""
THINGS USING THE SPOTIFY DATABASE
"""

genres = {
    "blues": {
        "description": "Originated toward the end of the 19th century in African American communities in the United States, particularly the Deep South; drew on traditional Spirituals and Work Songs; highly influential to the whole of Western popular music.",
        "images": ["blues1.jpeg", "blues2.jpeg", "blues3.jpeg"],
        "subgenres": ["r-n-b"]
    },
    "brazil": {
        "description": "Brazilian music is a diverse genre blending African, European, and indigenous influences. Key styles include Samba, with its lively Carnival beats, and Bossa Nova, which mixes samba with jazz for a more relaxed sound.",
        "images": ["brazil1.jpeg", "brazil2.jpeg", "brazil3.jpeg"],
        "subgenres": ["mpb", "pagode", "samba", "bossanova", "forro", "sertanejo"]
    },
    "classical": {
        "description": "Part of a broad generalization about the structure and function of music throughout history across the globe, describing traditions distinct from Traditional Folk Music and popular music.",
        "images": ["classical1.jpeg", "classical2.jpeg", "classical3.jpeg"],
        "subgenres": ["opera"]
    },
    "club": {
        "description": "Club music is a genre designed for dance floors, characterized by its upbeat and rhythmic beats that energize crowds. It includes various styles like House, Techno, and EDM, all of which are built around repetitive basslines and catchy hooks.",
        "images": ["club1.jpeg", "club2.jpeg", "club3.jpeg"],
        "subgenres": ["dance", "j-dance", "dancehall", "disco", "edm", "house", "hardstyle", "progressive-house", "techno", "trance", "groove"]
    },
    "country": {
        "description": "American genre derived from Southern and Appalachian forms of American Folk Music and later Rock and Pop influences, with a focus on the life and culture of rural America.",
        "images": ["country1.jpeg", "country2.jpeg", "country3.jpeg"],
        "subgenres": ["honky-tonk", "bluegrass"]
    },
    "dance": {
        "description": "Rooted in Disco and developed largely within Electronic Dance Music; emphasizes rhythm and is generally produced for play by DJs at clubs, parties, or festivals.",
        "images": ["dance1.jpeg", "dance2.jpeg", "dance3.jpeg"],
        "subgenres": ["edm", "electro"]
    },
    "dub": {
        "description": "Dub is a subgenre of reggae that focuses on remixing tracks, emphasizing deep bass, echo, and reverb effects. It's known for its instrumental versions and innovative sound manipulation.",
        "images": ["dub1.jpeg", "dub2.jpeg", "dub3.jpeg"],
        "subgenres": ["trip-hop"]
    },
    "electronic": {
        "description": "Uses non-traditional electronic instrumentation and sound manipulation technology as the primary backbone of a composition.",
        "images": ["electronic1.jpeg", "electronic2.jpeg", "electronic3.jpeg"],
        "subgenres": ["idm", "minimal-techno", "ambient", "breakbeat", "chicago-house", "deep-house", "electro", "drum-and-bass", "dubstep", "post-dubstep", "garage", "industrial", "trance", "trip-hop"]
    },
    "folk": {
        "description": "Rooted in mostly oral traditions of the peoples of the world, encompassing international Traditional Folk Music as well as Western Contemporary Folk which arose in the 1940s.",
        "images": ["folk1.jpeg", "folk2.jpeg", "folk3.jpeg"],
        "subgenres": ["acoustic", "guitar", "malay", "piano", "singer-songwriter", "songwriter"]
    },
    "funk": {
        "description": "Funk is a rhythmic genre known for its groovy basslines, syncopated beats, and strong emphasis on danceable, soulful rhythms.",
        "images": ["funk1.jpeg", "funk2.jpeg", "funk3.jpeg"],
        "subgenres": ["afrobeat", "breakbeat", "groove"]
    },
    "gospel": {
        "description": "Arising from vocal Christian tradition often featuring emotive performances, layered accompaniments, and themes of faith and salvation.",
        "images": ["gospel1.jpeg", "gospel2.jpeg", "gospel3.jpeg"],
        "subgenres": ["country", "r-n-b", "soul", "rock-n-roll"]
    },
    "hardcore": {
        "description": "Hardcore is an intense genre of punk rock known for its fast tempos, aggressive riffs, and raw, shouted vocals, often expressing themes of rebellion and resistance.",
        "images": ["hardcore1.jpeg", "hardcore2.jpeg", "hardcore3.jpeg"],
        "subgenres": ["grindcore"]
    },
    "hip-hop": {
        "description": "Emerged primarily on the United States east coast in African American communities in the late 1970s; emphasizes rhythmic beat patterns and a type of spoken vocal delivery known as rapping.",
        "images": ["hip-hop1.jpeg", "hip-hop2.jpeg", "hip-hop3.jpeg"],
        "subgenres": ["breakbeat", "chicago-house", "trip-hop"]
    },
    "house": {
        "description": "House is an electronic dance music genre characterized by steady four-on-the-floor beats, synthesized basslines, and repetitive, uplifting rhythms, often designed for nightclub and dancefloor settings.",
        "images": ["house1.jpeg", "house2.jpeg", "house3.jpeg"],
        "subgenres": ["progressive-house", "chicago-house", "deep-house"]
    },
    "industrial": {
        "description": "Umbrella encompassing Noise and Industrial, as well as later derivatives that combine the latter aesthetics with other styles and in more accessible directions which fall under Post-Industrial.",
        "images": ["industrial1.jpeg", "industrial2.jpeg", "industrial3.jpeg"],
        "subgenres": ["chicago-house", "drum-and-bass"]
    },
    "jazz": {
        "description": "Originating in African American communities in the Southern United States around the turn of the 20th century, building on New Orleans Brass Band ensemble and influences from Ragtime and Blues to become a very popular style by the emergence of Swing in the 1930s.",
        "images": ["jazz1.jpeg", "jazz2.jpeg", "jazz3.jpeg"],
        "subgenres": ["afrobeat"]
    },
    "latin": {
        "description": "Latin music encompasses diverse styles from Latin America and the Caribbean, featuring rhythmic beats, vibrant melodies, and a blend of indigenous, African, and European influences.",
        "images": ["latin1.jpeg", "latin2.jpeg", "latin3.jpeg"],
        "subgenres": ["latino", "salsa", "tango"]
    },
    "metal": {
        "description": "Driving and distorted riffs, aggressive drumming, vigorous vocals, and an all-around show of brute force in its early days, since branching into dozens of subgenres.",
        "images": ["metal1.jpeg", "metal2.jpeg", "metal3.jpeg"],
        "subgenres": ["black-metal", "death-metal", "heavy-metal", "metal-misc", "metalcore", "grindcore"]
    },
    "movies": {
        "description": "Refers to film soundtracks and scores that complement or enhance cinematic experiences. These compositions often include orchestral arrangements and thematic motifs tailored to reflect the mood, setting, and narrative of the film.",
        "images": ["movies1.jpeg", "movies2.jpeg", "movies3.jpeg"],
        "subgenres": ["soundtracks", "pop-film", "disney", "anime", "show-tunes"]
    },
    "pop": {
        "description": "Umbrella of popular styles closely tied to mass production and mass marketing, focusing on catchiness and accessibility through melody, rhythm, lyrics, and hooks.",
        "images": ["pop1.jpeg", "pop2.jpeg", "pop3.jpeg"],
        "subgenres": ["indie-pop", "pop-film", "power-pop", "j-idol", "j-pop", "k-pop", "mandopop", "synth-pop", "cantopop", "philippines-opm"]
    },
    "punk": {
        "description": "Musical and cultural product of Punk Rock known for its simplistic, brash playstyle and anti-establishment themes.",
        "images": ["punk1.jpeg", "punk2.jpeg", "punk3.jpeg"],
        "subgenres": ["punk-rock", "emo", "goth", "grunge", "hardcore"]
    },
    "reggae": {
        "description": "Umbrella for related forms of Jamaican Music which have grown beyond their regional roots to become global phenomena.",
        "images": ["reggae1.jpeg", "reggae2.jpeg", "reggae3.jpeg"],
        "subgenres": ["reggaeton", "dancehall", "dub", "ska"]
    },
    "rock": {
        "description": "Typically uses a verse-chorus structure with a backbeat rhythm and the electric guitar at the forefront; generally heavier and/or faster than its predecessors.",
        "images": ["rock1.jpeg", "rock2.jpeg", "rock3.jpeg"],
        "subgenres": ["alt-rock", "alternative", "hard-rock", "punk-rock", "psych-rock", "rock-n-roll", "rockabilly", "garage", "grunge", "indie", "j-rock"]
    },
    "soul": {
        "description": "Soul music combines elements of rhythm and blues, gospel, and jazz, characterized by its emotive vocals, deep grooves, and a focus on personal and heartfelt lyrics.",
        "images": ["soul1.jpeg", "soul2.jpeg", "soul3.jpeg"],
        "subgenres": ["afrobeat", "trip-hop"]
    },
    "techno": {
        "description": "Techno is an electronic music genre known for its repetitive beats, synthetic sounds, and futuristic rhythms, designed to create an immersive and danceable experience.",
        "images": ["techno1.jpeg", "techno2.jpeg", "techno3.jpeg"],
        "subgenres": ["detroit-techno", "minimal-techno"]
    },
    "world-music": {
        "description": "World music encompasses diverse musical styles from around the globe, blending traditional and contemporary elements to highlight cultural diversity and global influences.",
        "images": ["world-music1.jpeg", "world-music2.jpeg", "world-music3.jpeg"],
        "subgenres": ["new-age"]
    }
}

all_genres = spotify_auth.get_available_genre_seeds(auth_header)

#BUILDING GENRES FIRST PAGE

@app.route('/genres')
def show_genres():
    return render_template('genres.html', genres=genres)

#BUILDING GENRES SECOND PAGES

@app.route('/genre/<genre_name>')
def show_genre(genre_name):
    if genre_name in all_genres:
        tracks = spotify_auth.get_recommendations_by_genre(auth_header, genre_name)
        albums = spotify_auth.get_album_from_tracks(tracks, auth_header)
        playlists = spotify_auth.search_playlists_by_genre(auth_header, genre_name)
        sorted_playlists = spotify_auth.get_sorted_playlists(playlists)

        return render_template('genre.html', genre_name=genre_name, albums=albums, playlists=sorted_playlists)
    else:
        return "Genre not found", 404

@app.route('/album/<album_id>')
def album_details(album_id):
    album = spotify_auth.get_album_details(album_id, auth_header)
    reviews = spotify_auth.get_reviews(album_id)
    return render_template('album.html', album=album, reviews=reviews)

@app.route('/artist/<artist_id>')
def show_artist(artist_id):
    artist_details = spotify_auth.get_artist_details(artist_id, auth_header)
    artist_name = artist_details.get('name')
    artist_genres = artist_details.get('genres')
    artist_image = artist_details.get('images')[0]['url'] if artist_details.get('images') else None
    
    # Spotify non fornisce direttamente data di nascita e data di morte, quindi queste informazioni potrebbero dover essere ricercate separatamente
    #usando api di wikipedia
    bio = spotify_auth.get_artist_bio(artist_name)
    dates = spotify_auth.get_artist_birth_and_death_dates(artist_name)
    birth_date = {dates['birth_date']}
    death_date = {dates['death_date']}

    # Ottieni tutti gli album, EP, singoli, ecc. dell'artista
    artist_albums = spotify_auth.get_artist_albums(artist_id, auth_header)
    
    return render_template('artist.html', 
                           artist_name=artist_name,
                           artist_genres=artist_genres,
                           artist_image=artist_image,
                           birth_date=birth_date,
                           death_date=death_date,
                           bio=bio,
                           artist_albums=artist_albums)

@app.route('/playlist/<playlist_id>')
def playlist_details(playlist_id):
    playlist = spotify_auth.get_playlist_details(playlist_id, auth_header)
    return render_template('playlist.html', playlist=playlist)

# FUNZIONE PER INSERIRE O AGGIORNARE VALUTAZIONE ALBUM

@app.route('/rate_album', methods=['POST'])
def rate_album():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'User not logged in'}), 401

    user_id = session['user_id']
    data = request.get_json()

    album_id = data.get('album_id')
    rating = data.get('rating')

    if not album_id or rating is None:
        return jsonify({'success': False, 'message': 'Missing album_id or rating'}), 400

    try:
        rating = int(rating)
    except ValueError:
        return jsonify({'success': False, 'message': 'Invalid rating value'}), 400

    try:
        conn = spotify_auth.get_db_connection()
        conn.execute('INSERT OR REPLACE INTO album_ratings (user_id, album_id, rating) VALUES (?, ?, ?)', (user_id, album_id, rating))
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'Rating submitted successfully!'}), 200
    except Exception as e:
        return jsonify({'success': False, 'message': f'An error occurred: {str(e)}'}), 500
    

@app.route('/review_album', methods=['POST'])
def review_album():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'User not logged in'}), 401

    user_id = session['user_id']
    data = request.get_json()

    album_id = data.get('album_id')
    review_title = data.get('review_title')
    review_text = data.get('review_text')

    if not review_text:
        return jsonify({'success': False, 'message': 'Review text is required'}), 400

    try:
        print(f'user_id: {user_id}, review_title: {review_title}, review_text: {review_text}')
        
        # Stampa di debug per verificare i valori e i loro tipi
        print(f'DEBUG: Values to insert - user_id: {user_id} ({type(user_id)}), review_title: {review_title} ({type(review_title)}), review_text: {review_text} ({type(review_text)})')

        # Esecuzione della query con il database
        conn = spotify_auth.get_db_connection()
        conn.execute('INSERT INTO album_reviews (user_id, album_id, review_title, review_text) VALUES (?, ?, ?, ?)',
                     (user_id, album_id, review_title, review_text))
        conn.commit()
        conn.close()

        return jsonify({'success': True}), 200
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/c_favs')
def show_c_favs():
    sort_by = request.args.get('sort_by', 'rating')
    conn = spotify_auth.get_db_connection()

    if sort_by == 'popularity':
        album_info = conn.execute("""
            SELECT
                ar.album_id,
                COUNT(ar.rating) AS vote_count,
                AVG(ar.rating) AS avg_rating
            FROM album_ratings ar
            GROUP BY ar.album_id
            ORDER BY vote_count DESC
        """).fetchall()
    else:  # Ordina per rating medio
        album_info = conn.execute("""
            SELECT
                ar.album_id,
                COUNT(ar.rating) AS vote_count,
                AVG(ar.rating) AS avg_rating
            FROM album_ratings ar
            GROUP BY ar.album_id
            ORDER BY avg_rating DESC
        """).fetchall()
    conn.close()
    
    album_details = []
    for album in album_info:
        album_info = spotify_auth.get_album_details(album['album_id'], auth_header)
        avg_rating = spotify_auth.get_average_rating(album['album_id'])
        album_details.append({
            'album_id': album['album_id'],
            'artist_id': album_info['artist_id'],
            'album_cover': album_info['cover_image'],
            'album_name': album_info['album_name'],
            'artist_name': album_info['artist_name'],
            'album_genres': album_info['genres'],
            
            'average_rating': avg_rating,
            'vote_count': album['vote_count']
        })

    return render_template("c_favs.html", album_details=album_details, sort_by=sort_by)

def spotify_request(endpoint, params=None):
    response = requests.get(endpoint, headers=auth_header, params=params)
    response.raise_for_status()  # Alza un'eccezione per errori HTTP
    return response.json()

@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('query', '').lower()
    category = request.args.get('category', '')

    results = []

    # Se la categoria è vuota, cerca in tutte le categorie
    if not category:
        # Cerca per album
        endpoint = 'https://api.spotify.com/v1/search'

        params = {'q': query, 'type': 'album'}
        albums = spotify_request(endpoint, params=params).get('albums', {}).get('items', [])
        results.extend([{
            'name': item['name'],
            'type': 'album',
            'cover_image': item['images'][0]['url'] if item['images'] else '',
            'id': item['id'],
            'artist_name': item['artists'][0]['name'] if item['artists'] else '',
            'artist_id': item['artists'][0]['id'] if item['artists'] else '',
            'release_date': item.get('release_date', '')  # Usa .get() per evitare errori se la chiave non esiste
        } for item in albums])

        # Cerca per artista
        params = {'q': query, 'type': 'artist'}
        artists = spotify_request(endpoint, params=params).get('artists', {}).get('items', [])
        results.extend([{
            'name': item['name'],
            'type': 'artist',
            'artist_image': item['images'][0]['url'] if item['images'] else '',
            'id': item['id'],
            'genres': item.get('genres', [])
        } for item in artists])

        # Cerca per traccia
        params = {'q': query, 'type': 'track'}
        tracks = spotify_request(endpoint, params=params).get('tracks', {}).get('items', [])
        results.extend([{
            'name': item['name'],
            'type': 'track',
            'album_image': item['album']['images'][0]['url'] if item['album'].get('images') else '',
            'album_name': item['album']['name'],
            'album_id': item['album']['id'],
            'artist_name': item['artists'][0]['name'] if item['artists'] else '',
            'artist_id': item['artists'][0]['id'] if item['artists'] else '',
            'duration': spotify_auth.format_duration(item['duration_ms'])
        } for item in tracks])
    else:
        # Cerca in base alla categoria specificata
        endpoint = 'https://api.spotify.com/v1/search'
        params = {'q': query, 'type': category}
        response = spotify_request(endpoint, params=params)
        
        items = []

        if category == 'album':
            items = response.get('albums', {}).get('items', [])
            results = [{
                'name': item['name'],
                'type': 'album',
                'cover_image': item['images'][0]['url'] if item.get('images') else 'default_cover_image_url',
                'id': item['id'],
                'artist_name': item['artists'][0]['name'] if item.get('artists') else 'Unknown Artist',
                'artist_id': item['artists'][0]['id'] if item.get('artists') else 'Unknown ID',
                'release_date': item.get('release_date', 'Unknown Date')
            } for item in items]
        elif category == 'artist':
            items = response.get('artists', {}).get('items', [])
            results.extend([{
                'name': item['name'],
                'type': 'artist',
                'artist_image': item['images'][0]['url'] if item['images'] else '',
                'id': item['id'],
                'genres': item.get('genres', [])
            } for item in items])
        elif category == 'track':
            items = response.get('tracks', {}).get('items', [])
            results.extend([{
                'name': item['name'],
                'type': 'track',
                'album_image': item['album']['images'][0]['url'] if item['album'].get('images') else '',
                'album_name': item['album']['name'],
                'album_id': item['album']['id'],
                'artist_name': item['artists'][0]['name'] if item['artists'] else '',
                'artist_id': item['artists'][0]['id'] if item['artists'] else '',
                'duration': spotify_auth.format_duration(item['duration_ms'])
            } for item in items])

    return render_template('search.html', results=results, category=category)
"""
if __name__ == '__main__':
    app.run(debug=True)
"""

