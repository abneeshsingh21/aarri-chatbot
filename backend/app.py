# backend/app.py
from flask import Flask, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv
import os
import logging

# Load environment variables from .env (do NOT commit .env to git)
load_dotenv()

# Optional: initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("aarii.backend")

# Create Flask app
app = Flask(__name__)

# Enable CORS for React frontend (restrict before production)
# For local dev this allows all origins under /api/*; change before production.
CORS(app, resources={r"/api/*": {"origins": "*"}})

# -------------------------
# Import and register route blueprints (package-qualified)
# -------------------------
# Using package-qualified imports ensures modules are found when running as package 'backend'
try:
    from backend.routes.chat_routes import chat_bp
    app.register_blueprint(chat_bp, url_prefix="/api/chat")
    logger.info("Registered chat routes")
except Exception as e:
    logger.warning("Chat routes NOT registered: %s", e)

try:
    from backend.routes.voice_routes import voice_bp
    app.register_blueprint(voice_bp, url_prefix="/api/voice")
    logger.info("Registered voice routes")
except Exception as e:
    logger.warning("Voice routes NOT registered: %s", e)

try:
    from backend.routes.export_routes import export_bp
    app.register_blueprint(export_bp, url_prefix="/api")
    logger.info("Registered export routes")
except Exception as e:
    logger.warning("Export routes NOT registered: %s", e)

try:
    from backend.routes.mode_routes import mode_bp
    app.register_blueprint(mode_bp, url_prefix="/api")
    logger.info("Registered mode routes")
except Exception as e:
    logger.warning("Mode routes NOT registered: %s", e)

# -------------------------
# Optional: initialize DBs / memory indices if modules exist (package paths)
# -------------------------
try:
    # Ensure SQLAlchemy models and DB created
    from backend.database.models import init_db as _init_db
    _init_db()
    logger.info("Database initialized")
except Exception as e:
    logger.info("Database init skipped or failed: %s", e)

try:
    # Ensure FAISS + memory DB created
    from backend.memory.store import init_db as _init_mem_db
    _init_mem_db()
    logger.info("Memory store initialized")
except Exception as e:
    logger.info("Memory store init skipped or failed: %s", e)

# -------------------------
# Basic health endpoint (root)
# -------------------------
@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "message": "🚀 Aarii AI Backend is running successfully!",
        "status": "ok",
        "provider": os.getenv("GROQ_PROVIDER", "Groq API"),
        "model": os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
    })

# Optional dedicated health endpoint (useful for monitoring)
@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "message": "Aarii backend running"})

# JSON error handler for uncaught exceptions (useful during dev)
@app.errorhandler(Exception)
def handle_exception(e):
    # log the exception server-side
    logger.exception("Unhandled exception: %s", e)
    # return JSON response
    return jsonify({
        "error": "internal_server_error",
        "message": str(e)
    }), 500

# Only run the dev server when executed directly
if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    debug_mode = os.getenv("FLASK_DEBUG", "True").lower() in ("1", "true", "yes")
    # Use host 0.0.0.0 to be reachable from other devices on LAN if needed
    app.run(host="0.0.0.0", port=port, debug=debug_mode)
