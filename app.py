from flask import Flask, request, jsonify
import yt_dlp
import os

app = Flask(__name__)

@app.route('/transcribe', methods=['POST'])
def transcribe_video():
    youtube_url = request.json.get('youtube_url')
    cookies_file = request.files.get('cookies')  # Get the uploaded cookies.txt file

    if not youtube_url or not cookies_file:
        return jsonify({'error': 'Missing YouTube URL or cookies file'}), 400

    # Save the cookies file to a writable path
    cookies_path = '/tmp/cookies.txt'
    cookies_file.save(cookies_path)

    # yt-dlp options
    options = {
        'format': 'bestaudio/best',
        'outtmpl': '/tmp/%(title)s.%(ext)s',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'cookiefile': cookies_path,
    }

    try:
        with yt_dlp.YoutubeDL(options) as ydl:
            info_dict = ydl.extract_info(youtube_url, download=True)
            return jsonify({'title': info_dict.get('title', 'Unknown Title')})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        # Clean up cookies file
        if os.path.exists(cookies_path):
            os.remove(cookies_path)

if __name__ == '__main__':
    app.run()
