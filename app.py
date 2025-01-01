from flask import Flask, request, jsonify
from vosk import Model, KaldiRecognizer
import yt_dlp
import wave
import json
import os
import requests
import zipfile

app = Flask(__name__)

def download_model():
    """Download and extract the Vosk model if not already available."""
    model_path = "model"
    if not os.path.exists(model_path):
        print("Downloading Vosk model...")
        url = "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip"  # Update to your desired model
        response = requests.get(url, stream=True)
        with open("model.zip", "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        with zipfile.ZipFile("model.zip", "r") as zip_ref:
            zip_ref.extractall(".")
        os.rename("vosk-model-small-en-us-0.15", model_path)  # Rename extracted folder to 'model'
        os.remove("model.zip")
        print("Model downloaded and extracted.")

# Download the model if necessary
download_model()

# Load the Vosk model
model = Model("model")  # Path to your Vosk model

def download_audio(youtube_url, output_file="audio.mp3"):
    """Download audio from a YouTube video using yt-dlp."""
    cookies_path = '/etc/secrets/cookies.txt'

    if not os.path.exists(cookies_path):
        raise FileNotFoundError(f"Cookies file not found at {cookies_path}")
    print(f"Using cookies file at: {cookies_path}")

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': output_file,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'cookiefile': '/etc/secrets/cookies.txt',
        'quiet': False,  # Set to False for verbose logging
    }

    try:
        print(f"Downloading audio from: {youtube_url}")
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([youtube_url])
        print(f"Audio downloaded successfully to: {output_file}")
    except Exception as e:
        print(f"Error downloading audio: {e}")
        raise RuntimeError(f"Error downloading audio: {e}")

    return output_file

@app.route('/transcribe', methods=['POST'])
def transcribe():
    data = request.json
    youtube_url = data.get('youtube_url')
    if not youtube_url:
        return jsonify({"error": "youtube_url is required"}), 400

    try:
        # Step 1: Download audio from YouTube
        print(f"Downloading audio from: {youtube_url}")
        audio_file = download_audio(youtube_url)

        # Step 2: Convert MP3 to WAV (if needed)
        wav_file = "audio.wav"
        os.system(f"ffmpeg -i {audio_file} -ar 16000 -ac 1 -c:a pcm_s16le {wav_file}")
        os.remove(audio_file)  # Clean up the MP3 file

        # Step 3: Transcribe audio using Vosk
        wf = wave.open(wav_file, "rb")
        if wf.getnchannels() != 1 or wf.getsampwidth() != 2 or wf.getframerate() != 16000:
            return jsonify({"error": "Unsupported audio format"}), 400

        rec = KaldiRecognizer(model, wf.getframerate())
        result = []
        while True:
            data = wf.readframes(4000)
            if len(data) == 0:
                break
            if rec.AcceptWaveform(data):
                result.append(json.loads(rec.Result()))
        result.append(json.loads(rec.FinalResult()))
        transcription = " ".join([res['text'] for res in result])

        os.remove(wav_file)  # Clean up the WAV file
        return jsonify({"transcription": transcription})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
