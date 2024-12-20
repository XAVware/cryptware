
from flask import Flask, jsonify, render_template, request, send_file
from dexscraper import fetch_new, fetch_pairs
import mysql.connector
import time
import atexit
from apscheduler.schedulers.background import BackgroundScheduler
from twitter import *
from youtube import yt_search, download_video
import K

app = Flask(__name__)

DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': K.MYSQL_KEY, 
    'database': 'cryptware'
}

def get_db_connection():
    return mysql.connector.connect(**DB_CONFIG)

def store_new(data):
    conn = get_db_connection()
    new_entries = []
    cursor = conn.cursor()

    for token in data:
        url = token.get('url', '')
        chain_id = token.get('chainId', '')
        token_address = token.get('tokenAddress', '')
        icon = token.get('icon', '')
        header = token.get('header', '')
        description = token.get('description', '')

        if not token_address or not chain_id:
            print(f"Skipping token due to missing critical fields: {token}")
            continue

        try:
            cursor.execute('''
                INSERT INTO TOKENS (url, chain_id, token_address, icon, header, description)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE 
                    url=VALUES(url),
                    chain_id=VALUES(chain_id),
                    icon=VALUES(icon),
                    header=VALUES(header),
                    description=VALUES(description)
            ''', (url, chain_id, token_address, icon, header, description))

            if cursor.rowcount > 0:
                new_entries.append(token_address)
                token_id = cursor.lastrowid

                links = token.get('links', [])
                for link in links:
                    link_type = link.get('type', '')
                    label = link.get('label', '')
                    link_url = link.get('url', '')

                    cursor.execute('''
                        INSERT INTO TOKEN_LINKS (token_id, type, label, url)
                        VALUES (%s, %s, %s, %s)
                    ''', (token_id, link_type, label, link_url))

        except Exception as e:
            print(f"Error inserting token {token_address}: {e}")

    conn.commit()
    cursor.close()
    conn.close()
    return new_entries

def get_saved_tokens():
    """Retrieve all saved tokens and aggregate their links into a readable JSON format."""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM TOKENS t GROUP BY t.id ORDER BY t.id DESC")
    tokens = cursor.fetchall()
    cursor.close()
    conn.close()
    return tokens

### PAIRS
def save_token_details(table_name, address, name, symbol):
    """Save base or quote token details into BASE_TOKENS or QUOTE_TOKENS."""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(f'SELECT id FROM {table_name} WHERE address = %s', (address,))
        token = cursor.fetchone()

        if not token:
            cursor.execute(f'INSERT INTO {table_name} (address, name, symbol) VALUES (%s, %s, %s)', (address, name, symbol))
            conn.commit()
            return cursor.lastrowid
        else:
            return token[0]
        
    except Exception as e:
        print(f"Error saving token details ({table_name}): {e}")

    finally:
        cursor.close()
        conn.close()


def save_nonexisting_pairs_to_db(token_id, pairs):
    conn = get_db_connection()
    cursor = conn.cursor()

    for pair in pairs:
        chain_id = pair.get('chainId')
        dex_id = pair.get('dexId')
        pair_address = pair.get('pairAddress')
        price_native = pair.get('priceNative', None)
        price_usd = pair.get('priceUsd', None)
        liquidity_usd = pair.get('liquidity', {}).get('usd', 0)
        liquidity_base = pair.get('liquidity', {}).get('base', 0)
        liquidity_quote = pair.get('liquidity', {}).get('quote', 0)
        fdv = pair.get('fdv', 0)
        market_cap = pair.get('marketCap', 0)
        url = pair.get('url', '')

        cursor.execute('''
            SELECT id FROM TOKEN_PAIRS
            WHERE token_id = %s AND pair_address = %s
        ''', (token_id, pair_address))
        existing_pair = cursor.fetchone()

        if existing_pair:
            pair_id = existing_pair[0]
        else:
            cursor.execute('''
                INSERT INTO TOKEN_PAIRS (
                    token_id, chain_id, dex_id, pair_address, price_native, price_usd,
                    liquidity_usd, liquidity_base, liquidity_quote, fdv, market_cap, url
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ''', (
                token_id, chain_id, dex_id, pair_address, price_native, price_usd,
                liquidity_usd, liquidity_base, liquidity_quote, fdv, market_cap, url
            ))
            pair_id = cursor.lastrowid

        websites = pair.get('info', {}).get('websites', [])
        for website in websites:
            cursor.execute('''
                INSERT INTO PAIR_WEBSITES (pair_id, url)
                VALUES (%s, %s)
            ''', (pair_id, website.get('url', '')))

        socials = pair.get('info', {}).get('socials', [])
        for social in socials:
            cursor.execute('''
                INSERT INTO PAIR_SOCIALS (pair_id, platform, handle)
                VALUES (%s, %s, %s)
            ''', (pair_id, social.get('platform', ''), social.get('handle', '')))

    conn.commit()
    cursor.close()
    conn.close()

def update_all_token_pairs():
    raw_data = fetch_new()
    new_tokens = store_new(raw_data)

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute('SELECT * FROM TOKENS')
    tokens = cursor.fetchall()

    for token in tokens:
        token_id = token['id']
        token_address = token['token_address']

        pairs = fetch_pairs(token_address)
        if pairs:
            save_nonexisting_pairs_to_db(token_id, pairs)
            print(f"Token {token_address[:2]}..{token_address[:6]}")
            for pair in pairs:
                pa = pair.get("pairAddress", "")
                print(f">> {pa}")
                # print(f">> {pair.get("pairAddress", "")[:2]}..{pair.get("pairAddress", "")[:6]}")
            
        else:
            print(f"No pairs found for token {token_address}.")

    cursor.close()
    conn.close()

def refresh():
    update_all_token_pairs()

sched = BackgroundScheduler(daemon=True)
sched.add_job(refresh,'interval',minutes=5)
sched.start()

### View Routes ###
# Home
@app.route('/')
def home():
    tokens = get_saved_tokens()
    # update_all_token_pairs()
    return render_template('index.html', tokens=tokens)


@app.route('/twitter')
def twitter_page():
    return render_template('twitter.html')

@app.route('/twitter/process/<tweet_id>')
def twitter_process(tweet_id):
    try:
        comments = get_tweet_comments(tweet_id)
        df = process_comments_with_mentions(comments)
        if not df.empty:
            reorder_and_save_with_summary(df, tweet_id)
            return jsonify({"message": "Data processed successfully.", "data": df.to_dict(orient="records")})
        else:
            return jsonify({"message": "No comments found for the provided Tweet ID."}), 404
    except Exception as e:
        return jsonify({"message": str(e)}), 500

@app.route('/twitter/download/<tweet_id>')
def twitter_download(tweet_id):
    try:
        file_path = f"{tweet_id}.xlsx"
        return send_file(file_path, as_attachment=True)
    except Exception as e:
        return jsonify({"message": str(e)}), 500


@app.route('/youtube')
def youtube_page():
    return render_template('youtube.html')

@app.route('/youtube/search')
def youtube_search():
    query = request.args.get('query', '')
    if not query:
        return jsonify({"error": "Search query is required"}), 400

    try:
        params = {
            'part': 'snippet',
            'q': query,
            'type': 'video',
            'key': K.YT_KEY
        }
        response = requests.get('https://www.googleapis.com/youtube/v3/search', params=params)

        if response.status_code == 200:
            return jsonify(response.json())
        else:
            return jsonify({"error": response.text}), response.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/youtube/download/<video_id>')
def youtube_download(video_id):
    try:
        video_url = f"https://www.youtube.com/watch?v={video_id}"
        filepath = download_video(video_url)
        if filepath:
            return jsonify({"filepath": filepath})
        else:
            return jsonify({"error": "Failed to download video"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

### App ###
if __name__ == '__main__':
    app.run(port=5000)
