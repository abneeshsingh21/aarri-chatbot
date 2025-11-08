# backend/routes/export_routes.py
from flask import Blueprint, request, send_file, jsonify
import io, json
try:
    from database.models import SessionLocal, ChatLog
    DB_AVAILABLE = True
except Exception:
    DB_AVAILABLE = False

export_bp = Blueprint("export_bp", __name__)

@export_bp.route("/export", methods=["GET"])
def export_chat():
    session_id = request.args.get("session_id", "default")
    if not DB_AVAILABLE:
        return jsonify({"error":"db not available"}), 500
    db = SessionLocal()
    rows = db.query(ChatLog).filter(ChatLog.session_id==session_id).order_by(ChatLog.timestamp.asc()).all()
    db.close()
    out = [{"role": r.role, "text": r.content, "ts": r.timestamp.isoformat()} for r in rows]
    buf = io.BytesIO()
    buf.write(json.dumps(out, indent=2).encode("utf-8"))
    buf.seek(0)
    return send_file(buf, mimetype="application/json", as_attachment=True, download_name=f"aarii_{session_id}.json")
