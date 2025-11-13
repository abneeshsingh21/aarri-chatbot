# backend/app.py
from flask import Flask, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import os
import logging

# Load environment variables
load_dotenv()

# Optional: initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("aarii.backend")

# Create Flask app
app = Flask(__name__)

# Enable CORS for React frontend with multiple origins
cors_origins = [
    "http://localhost:3000",
    "http://localhost:5000",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5000",
    "https://*.github.io",
    "https://aarii-backend.onrender.com",
    os.getenv("FRONTEND_URL", "*"),
]

CORS(
    app,
    resources={r"/api/*": {"origins": cors_origins}},
    supports_credentials=True,
)


# Import and register route blueprints (best-effort)
try:
    from routes.chat_routes import chat_bp

    app.register_blueprint(chat_bp, url_prefix="/api/chat")
    logger.info("Registered chat routes")
except Exception as exc:  # pragma: no cover - optional module
    logger.warning("Chat routes NOT registered: %s", exc)


try:
    from routes.voice_routes import voice_bp

    app.register_blueprint(voice_bp, url_prefix="/api/voice")
    logger.info("Registered voice routes")
except Exception as exc:  # pragma: no cover - optional module
    logger.warning("Voice routes NOT registered: %s", exc)


try:
    from routes.export_routes import export_bp

    app.register_blueprint(export_bp, url_prefix="/api")
    logger.info("Registered export routes")
except Exception as exc:  # pragma: no cover - optional module
    logger.warning("Export routes NOT registered: %s", exc)


try:
    from routes.mode_routes import mode_bp

    app.register_blueprint(mode_bp, url_prefix="/api")
    logger.info("Registered mode routes")
except Exception as exc:  # pragma: no cover - optional module
    logger.warning("Mode routes NOT registered: %s", exc)


# Optional: initialize DB (database is lightweight)
try:
    # Ensure SQLAlchemy models and DB created
    from database.models import init_db as _init_db

    _init_db()
    logger.info("Database initialized")
except Exception as exc:  # pragma: no cover - optional module
    logger.info("Database init skipped or failed: %s", exc)


# Defer FAISS initialization to avoid worker timeout during startup
# It will be lazy-loaded on first request
_memory_store_initialized = False


def _ensure_memory_initialized():
    """Lazy-load memory store on first use."""
    global _memory_store_initialized
    if not _memory_store_initialized:
        try:
            from memory.store import init_db as _init_mem_db

            _init_mem_db()
            logger.info("Memory store initialized (lazy-loaded)")
            _memory_store_initialized = True
        except Exception as exc:  # pragma: no cover - optional module
            logger.info("Memory store init skipped or failed: %s", exc)
            _memory_store_initialized = True


# Basic health endpoint (no heavy initialization)
@app.route("/", methods=["GET"])
def home():
    return jsonify(
        {
            "message": "🚀 Aarii AI Backend is running successfully!",
            "status": "ok",
            "provider": os.getenv("GROQ_PROVIDER", "Groq API"),
            "model": os.getenv("GROQ_MODEL", "llama-3.1-8b-instant"),
        }
    )


# JSON error handler for uncaught exceptions (useful during dev)
@app.errorhandler(Exception)
def handle_exception(e):
    # log the exception server-side
    logger.exception("Unhandled exception: %s", e)
    # return JSON response
    return (
        jsonify({"error": "internal_server_error", "message": str(e)}),
        500,
    )


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    _debug_val = os.getenv("FLASK_DEBUG", "True").lower()
    debug_mode = _debug_val in ("1", "true", "yes")
    # Use host 0.0.0.0 to be reachable from other devices on LAN if needed
    app.run(host="0.0.0.0", port=port, debug=debug_mode)
