from flask import Flask, request, jsonify
from vosk import Model, KaldiRecognizer
import wave
import json

app = Flask(__name__)
model = Model("model")  # Path to your Vosk model

@app.route('/transcribe', methods=['POST'])
def transcribe():
    if 'audio' not in request.files:
        return jsonify({"error": "No audio file provided"}), 400
    audio_file = request.files['audio']
    wf = wave.open(audio_file, "rb")
    if wf.getnchannels() != 1 or wf.getsampwidth() != 2 or wf.getframerate() not in [8000, 16000, 32000, 44100]:
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
    return jsonify({"transcription": transcription})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
