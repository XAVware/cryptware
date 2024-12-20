
import os
import requests
import subprocess
import json
import assemblyai as aai
import pprint
import K # Make sure you add your keys to a K.py file.

DOWNLOADS_FOLDER = "./downloads"

def yt_search(search_query):
    params = {
        'part': 'snippet',
        'q': search_query,
        'type': 'video',
        'key': K.YT_KEY,
        'maxResults': 5,
        'videoDuration': 'medium'
    }

    response = requests.get('https://www.googleapis.com/youtube/v3/search', params=params)

    if response.status_code == 200:
        results = []
        data = response.json()
        pprint.pprint(data)
        for item in data['items']:
            video_id = item['id']['videoId']
            results.append(f"https://www.youtube.com/watch?v={video_id}")
            title = item['snippet']['title']
            print(f"Transcribing video '{title}' from https://www.youtube.com/watch?v={video_id}...")
        return results
    else:
        print(f"Error: {response.status_code}, {response.text}")

def download_video(url):
    try:
        result = subprocess.run(
            [
                "yt-dlp",
                "-P", DOWNLOADS_FOLDER,
                "-o", "%(uploader)s/%(title)s.%(ext)s",
                "--print", "after_move:filepath",
                url
            ],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print("Error occurred while downloading video:")
        print(e.stderr)
        return None
    



def get_parsed_file_path(file_path):
    print("original path: " + file_path)
    s = DOWNLOADS_FOLDER.replace(".", "cryptware")
    return file_path.split(s)[1]



def transcribe_file(path):
    aai.settings.api_key = K.ASSEMBLYAI_KEY
    transcriber = aai.Transcriber()
    path_to_transcribe = DOWNLOADS_FOLDER + path
    transcript = transcriber.transcribe(path_to_transcribe)
    text = transcript.text

    with open(path_to_transcribe + ".txt", "w+") as f:
        f.write(text)

    return transcript


results = yt_search("Day trading")

for r in results:
    file_path = download_video(r)
    internal_path = get_parsed_file_path(file_path)
    transcript = transcribe_file(internal_path)

    