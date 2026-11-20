from flask import Flask, request, Response
import subprocess
import tempfile
import os

app = Flask(__name__)

# ESP32'nin 8kHz 8-bit unsigned mono WAV/PCM formatına uygun temel TTS sunucusu
# Not: Metni sese çevirmek için sistemde kurulu TTS (örneğin edge-tts veya gTTS) + ffmpeg kullanır.
@app.route("/tts", methods=["GET", "POST"])
def tts():
    data = request.get_json(silent=True) or {}
    text = (
        request.args.get("text")
        or data.get("text")
        or request.form.get("text")
        or request.data.decode("utf-8", errors="ignore").strip()
    )
    print("Gelen metin:", text)

    if not text:
        return Response(b"", status=400)

    try:
        from gtts import gTTS
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as mp3_f:
            mp3_path = mp3_f.name
        wav_path = mp3_path.replace(".mp3", ".wav")

        tts_obj = gTTS(text=text, lang="tr")
        tts_obj.save(mp3_path)

        # 8000 Hz, mono, 8-bit unsigned WAV dönüşümü (ESP32 DAC için)
        subprocess.run(
            ["ffmpeg", "-y", "-i", mp3_path, "-ar", "8000", "-ac", "1", "-acodec", "pcm_u8", wav_path],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True,
        )

        with open(wav_path, "rb") as f:
            audio_bytes = f.read()

        os.remove(mp3_path)
        os.remove(wav_path)

        return Response(audio_bytes, status=200, mimetype="audio/wav")
    except Exception as e:
        print("TTS Hatasi:", e)
        return Response(str(e), status=500)

if __name__ == "__main__":
    print("AK-BOT TTS Sunucusu baslatildi: http://0.0.0.0:5000/tts")
    app.run(host="0.0.0.0", port=5000)
