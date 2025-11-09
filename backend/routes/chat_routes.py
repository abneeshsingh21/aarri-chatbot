# backend/routes/chat_routes.py
from flask import Blueprint, request, jsonify
import logging
from typing import List, Dict, Any

# Package-qualified imports so running as "python -m backend.app" works
try:
    from backend.core.ai_engine import AariiEngine
    CORE_AVAILABLE = True
except Exception as e:
    CORE_AVAILABLE = False
    _core_import_error = e

try:
    from backend.database.models import SessionLocal, ChatLog
    DB_AVAILABLE = True
except Exception:
    DB_AVAILABLE = False

try:
    from backend.memory.store import query_memory, add_memory
    MEMORY_AVAILABLE = True
except Exception:
    MEMORY_AVAILABLE = False

chat_bp = Blueprint("chat_bp", __name__)
logger = logging.getLogger("aarii.chat_routes")

# Initialize engine safely (may be heavy)
engine = None
if CORE_AVAILABLE:
    try:
        engine = AariiEngine()
        logger.info("AariiEngine initialized")
    except Exception as e:
        engine = None
        logger.exception("Failed to initialize AariiEngine: %s", e)
else:
    logger.warning("Core not available: %s", globals().get("_core_import_error", "unknown"))

def get_history_from_db(session_id: str, limit: int = 20) -> List[Dict[str, str]]:
    if not DB_AVAILABLE:
        return []
    try:
        db = SessionLocal()
        rows = db.query(ChatLog).filter(ChatLog.session_id == session_id).order_by(ChatLog.timestamp.asc()).all()
        db.close()
        # take last `limit` messages
        messages = [{"role": r.role, "content": r.content} for r in rows]
        return messages[-limit:]
    except Exception as e:
        logger.exception("history fetch failed: %s", e)
        return []

def _safe_save_db(session_id: str, role: str, content: str) -> None:
    if not DB_AVAILABLE:
        return
    try:
        db = SessionLocal()
        row = ChatLog(session_id=session_id, role=role, content=content)
        db.add(row)
        db.commit()
        db.close()
    except Exception:
        logger.exception("failed to save chat log")

def _safe_add_memory(session_id: str, text: str, meta: Dict[str, Any] = None) -> None:
    if not MEMORY_AVAILABLE:
        return
    try:
        add_memory(session_id, text, meta or {})
    except Exception:
        logger.exception("failed to add memory")

def get_memory_system_msgs(session_id: str, user_message: str, top_k: int = 3) -> List[Dict[str, str]]:
    if not MEMORY_AVAILABLE:
        return []
    try:
        mems = query_memory(user_message, top_k=top_k)
        # Expect mems as iterable of (_id, score, text, meta) or (score, text)
        msgs = []
        for item in mems:
            try:
                # try common unpacking patterns
                if len(item) >= 3:
                    _id, score, text = item[0], item[1], item[2]
                else:
                    # fallback: assume (score, text)
                    score, text = item[0], item[1]
                msgs.append({"role": "system", "content": f"Memory (score={float(score):.3f}): {text}"})
            except Exception:
                # On unexpected shape, stringify item
                msgs.append({"role": "system", "content": f"Memory: {str(item)}"})
        return msgs
    except Exception:
        logger.exception("memory query failed")
        return []

@chat_bp.route("/", methods=["POST"])
def chat():
    if engine is None:
        # Engine not available — return an informative error
        logger.error("Chat request received but engine is not available")
        return jsonify({"error": "engine_unavailable", "message": "NLP engine not initialized"}), 500

    data = request.get_json(force=True) or {}
    # accept both "message" and "prompt" keys for compatibility
    message = (data.get("message") or data.get("prompt") or "").strip()
    session_id = data.get("session_id", "default")
    if not isinstance(session_id, str) or not session_id.strip():
        session_id = "default"

    if not message:
        return jsonify({"reply": "Please send a non-empty message."}), 400

    # Build history + memory system messages
    history = get_history_from_db(session_id, limit=20)
    mem_systems = get_memory_system_msgs(session_id, message, top_k=3)
    combined_history = mem_systems + history

    # persist user message
    try:
        _safe_save_db(session_id, "user", message)
        _safe_add_memory(session_id, message, {"source": "user"})
    except Exception:
        logger.exception("error while saving user message")

    # get reply from engine
    try:
        # engine.get_response expected to return (reply, meta)
        reply, meta = engine.get_response(message, session_id=session_id, history=combined_history, max_history_messages=12)
    except Exception as e:
        logger.exception("Engine get_response failed: %s", e)
        return jsonify({"error": "engine_error", "message": str(e)}), 500

    # persist assistant reply
    try:
        _safe_save_db(session_id, "assistant", reply)
        _safe_add_memory(session_id, reply, {"source": "assistant"})
    except Exception:
        logger.exception("error while saving assistant reply")

    status = 200
    if isinstance(meta, dict) and meta.get("error"):
        status = 500

    return jsonify({"reply": reply, "meta": meta}), status
