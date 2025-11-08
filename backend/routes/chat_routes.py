# backend/routes/chat_routes.py
from flask import Blueprint, request, jsonify
from core.ai_engine import AariiEngine
import logging

try:
    from database.models import SessionLocal, ChatLog
    DB_AVAILABLE = True
except Exception:
    DB_AVAILABLE = False

try:
    from memory.store import query_memory, add_memory
    MEMORY_AVAILABLE = True
except Exception:
    MEMORY_AVAILABLE = False

chat_bp = Blueprint("chat_bp", __name__)
engine = AariiEngine()
logger = logging.getLogger("chat_routes")

def get_history_from_db(session_id: str, limit: int = 20):
    if not DB_AVAILABLE:
        return []
    try:
        db = SessionLocal()
        rows = db.query(ChatLog).filter(ChatLog.session_id == session_id).order_by(ChatLog.timestamp.asc()).all()
        db.close()
        return [{"role": r.role, "content": r.content} for r in rows][-limit:]
    except Exception as e:
        logger.exception("history fetch failed: %s", e)
        return []

def _safe_save_db(session_id: str, role: str, content: str):
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

def _safe_add_memory(session_id: str, text: str, meta: dict = None):
    if not MEMORY_AVAILABLE:
        return
    try:
        add_memory(session_id, text, meta or {})
    except Exception:
        logger.exception("failed to add memory")

def get_memory_system_msgs(session_id: str, user_message: str, top_k: int = 3):
    if not MEMORY_AVAILABLE:
        return []
    try:
        mems = query_memory(user_message, top_k=top_k)
        msgs = [{"role":"system", "content": f"Memory (score={score:.3f}): {text}"} for (_id, score, text, meta) in mems]
        return msgs
    except Exception:
        logger.exception("memory query failed")
        return []

@chat_bp.route("/", methods=["POST"])
def chat():
    data = request.get_json(force=True) or {}
    message = data.get("message", "")
    session_id = data.get("session_id", "default")
    if not isinstance(session_id, str) or not session_id.strip():
        session_id = "default"

    if not message or not message.strip():
        return jsonify({"reply": "Please send a non-empty message."}), 400

    history = get_history_from_db(session_id, limit=20)
    mem_systems = get_memory_system_msgs(session_id, message, top_k=3)
    combined_history = mem_systems + history

    # persist user message
    _safe_save_db(session_id, "user", message)
    _safe_add_memory(session_id, message, {"source":"user"})

    # get reply
    reply, meta = engine.get_response(message, session_id=session_id, history=combined_history, max_history_messages=12)

    # persist assistant reply
    _safe_save_db(session_id, "assistant", reply)
    _safe_add_memory(session_id, reply, {"source":"assistant"})

    status = 200
    if isinstance(meta, dict) and meta.get("error"):
        status = 500

    return jsonify({"reply": reply, "meta": meta}), status
