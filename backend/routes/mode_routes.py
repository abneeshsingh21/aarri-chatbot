# backend/routes/mode_routes.py
from flask import Blueprint, request, jsonify
try:
    from database.models import SessionLocal, ChatLog
    DB_AVAILABLE = True
except Exception:
    DB_AVAILABLE = False

mode_bp = Blueprint("mode_bp", __name__)

@mode_bp.route("/mode", methods=["POST"])
def set_mode():
    data = request.get_json(force=True) or {}
    session_id = data.get("session_id", "default")
    prompt = data.get("prompt", "")
    if not DB_AVAILABLE:
        return jsonify({"error":"db missing"}), 500
    db = SessionLocal()
    row = ChatLog(session_id=session_id, role="system", content=prompt)
    db.add(row)
    db.commit()
    db.close()
    return jsonify({"ok": True})
