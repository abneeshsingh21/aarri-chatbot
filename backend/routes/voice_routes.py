# backend/routes/voice_routes.py
from flask import Blueprint, request, send_file
from gtts import gTTS
import io

voice_bp = Blueprint("voice_bp", __name__)

@voice_bp.route("/tts", methods=["POST"])
def tts():
    data = request.get_json(force=True) or {}
    text = data.get("text", "")
    lang = data.get("lang", "en")
    if not text:
        return {"error":"empty text"}, 400
    try:
        tts = gTTS(text, lang=lang)
        buf = io.BytesIO()
        tts.write_to_fp(buf)
        buf.seek(0)
        return send_file(buf, mimetype="audio/mpeg", as_attachment=False, download_name="aarii.mp3")
    except Exception as e:
        return {"error": str(e)}, 500
