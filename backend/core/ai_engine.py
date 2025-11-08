# backend/core/ai_engine.py
import os
from dotenv import load_dotenv
from openai import OpenAI
from typing import List, Dict, Tuple, Optional

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_BASE = os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY not set in .env")

client = OpenAI(api_key=GROQ_API_KEY, base_url=GROQ_BASE, timeout=60)

# DB logging (best-effort)
try:
    from database.models import SessionLocal, ChatLog
    DB_AVAILABLE = True
except Exception:
    DB_AVAILABLE = False

class AariiEngine:
    def __init__(self):
        self.model = GROQ_MODEL
        self.system_prompt = os.getenv("AARII_SYSTEM_PROMPT", "You are Aarii, a helpful, concise AI assistant.")

    def _log(self, session_id: str, role: str, content: str):
        if not DB_AVAILABLE:
            return
        try:
            db = SessionLocal()
            r = ChatLog(session_id=session_id, role=role, content=content)
            db.add(r)
            db.commit()
            db.close()
        except Exception:
            pass

    def get_response(self, user_message: str, session_id: str = "default", history: Optional[List[Dict[str, str]]] = None, max_history_messages: int = 12) -> Tuple[str, dict]:
        """
        history: list of {role: 'user'|'assistant'|'system', content: '...'}, in chronological order oldest->newest.
        """
        if history is None:
            history = []

        # Limit history
        history = history[-max_history_messages:]

        messages = [{"role": "system", "content": self.system_prompt}]
        # add history (already may include memory system messages)
        for item in history:
            role = item.get("role", "user")
            content = item.get("content", "")
            if role in ("system", "user", "assistant"):
                messages.append({"role": role, "content": content})
        # finally append current user message
        messages.append({"role": "user", "content": user_message})

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": float(os.getenv("AARII_TEMP", "0.2")),
            "max_tokens": int(os.getenv("AARII_MAX_TOKENS", "512")),
            "n": 1,
        }

        try:
            resp = client.chat.completions.create(**payload)
            # Extract reply safely
            reply = "(no reply)"
            try:
                choices = getattr(resp, "choices", None)
                if choices and len(choices) > 0:
                    first = choices[0]
                    msg = getattr(first, "message", None)
                    if msg and getattr(msg, "content", None):
                        reply = msg.content
                    else:
                        reply = getattr(first, "text", None) or str(first)
            except Exception:
                reply = str(resp)

            if reply is None:
                reply = "(no reply from model)"

            # Meta: try to produce JSON-serializable meta
            meta = {}
            try:
                if hasattr(resp, "to_dict"):
                    meta = {"raw": resp.to_dict()}
                else:
                    meta = {
                        "model": getattr(resp, "model", None),
                        "choices_count": len(getattr(resp, "choices", []) or []),
                        "raw_str": str(resp),
                    }
            except Exception:
                meta = {"raw_str": str(resp)}

            # log
            try:
                self._log(session_id, "user", user_message)
                self._log(session_id, "assistant", reply)
            except Exception:
                pass

            return reply, meta

        except Exception as e:
            return f"⚠️ Aarii error contacting Groq: {e}", {"error": str(e)}
