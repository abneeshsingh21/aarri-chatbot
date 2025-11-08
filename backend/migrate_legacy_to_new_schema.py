# backend/migrate_legacy_to_new_schema.py
import sqlite3
import os
from datetime import datetime

DB = os.path.join(os.path.dirname(__file__), "aarii_chatlogs.db")

if not os.path.exists(DB):
    print("DB not found at:", DB)
    raise SystemExit(1)

conn = sqlite3.connect(DB)
cur = conn.cursor()

# detect columns in existing chat_logs table
cur.execute("PRAGMA table_info(chat_logs);")
rows = cur.fetchall()
cols = [r[1] for r in rows]
print("Existing columns:", cols)

# If already up-to-date (contains 'role' and 'content'), exit
if "role" in cols and "content" in cols:
    print("Database schema already contains 'role' and 'content' -- nothing to do.")
    conn.close()
    raise SystemExit(0)

# Create new table chat_logs_new with the desired schema
print("Creating chat_logs_new with desired schema...")
cur.execute("""
CREATE TABLE IF NOT EXISTS chat_logs_new (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT,
    role TEXT,
    content TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);
""")
conn.commit()

# CASE A: legacy layout where messages are split into user_message and bot_response in same row
if "user_message" in cols and "bot_response" in cols:
    print("Detected legacy columns 'user_message' and 'bot_response' — performing split-copy.")
    # fetch all legacy rows (keep ordering by rowid if no timestamp)
    cur.execute("SELECT id, session_id, user_message, bot_response FROM chat_logs ORDER BY id ASC;")
    legacy = cur.fetchall()
    inserted = 0
    for r in legacy:
        legacy_id, session_id, user_msg, bot_resp = r[0], r[1], r[2], r[3]
        # Insert user message row (if not empty)
        if user_msg is not None and str(user_msg).strip() != "":
            cur.execute(
                "INSERT INTO chat_logs_new (session_id, role, content, timestamp) VALUES (?, ?, ?, ?)",
                (session_id, "user", user_msg, datetime.utcnow().isoformat())
            )
            inserted += 1
        # Insert assistant reply row (if not empty)
        if bot_resp is not None and str(bot_resp).strip() != "":
            cur.execute(
                "INSERT INTO chat_logs_new (session_id, role, content, timestamp) VALUES (?, ?, ?, ?)",
                (session_id, "assistant", bot_resp, datetime.utcnow().isoformat())
            )
            inserted += 1
    conn.commit()
    print(f"Inserted {inserted} rows into chat_logs_new from legacy rows.")

# CASE B: if there is a single 'content' column but missing 'role'
elif "content" in cols and "role" not in cols:
    print("Detected 'content' without 'role'. Copying content into new table with default role='user'.")
    cur.execute("SELECT id, session_id, content FROM chat_logs ORDER BY id ASC;")
    legacy = cur.fetchall()
    inserted = 0
    for r in legacy:
        _, session_id, content = r
        cur.execute(
            "INSERT INTO chat_logs_new (session_id, role, content, timestamp) VALUES (?, ?, ?, ?)",
            (session_id, "user", content, datetime.utcnow().isoformat())
        )
        inserted += 1
    conn.commit()
    print(f"Inserted {inserted} rows into chat_logs_new from existing 'content' rows.")

# CASE C: unknown schema -- fallback: try to copy any text-like column into content
else:
    print("Unknown chat_logs schema. Attempting to find a text column to copy into new table.")
    text_col = None
    for candidate in ["message", "text", "body", "msg"]:
        if candidate in cols:
            text_col = candidate
            break
    if text_col is None:
        # fallback: try the third column (if exists)
        if len(cols) >= 3:
            text_col = cols[2]
    if text_col is None:
        print("Could not find a text-like column to migrate. Aborting.")
        conn.close()
        raise SystemExit(2)
    print(f"Using column '{text_col}' as content source.")
    cur.execute(f"SELECT id, session_id, {text_col} FROM chat_logs ORDER BY id ASC;")
    legacy = cur.fetchall()
    for r in legacy:
        _, session_id, content = r
        cur.execute(
            "INSERT INTO chat_logs_new (session_id, role, content, timestamp) VALUES (?, ?, ?, ?)",
            (session_id, "user", content or "", datetime.utcnow().isoformat())
        )
    conn.commit()
    print(f"Copied {len(legacy)} rows into chat_logs_new using column '{text_col}'.")

# Finalize: backup old table name and replace
print("Finalizing migration: renaming tables.")
try:
    # rename old table as backup name
    cur.execute("ALTER TABLE chat_logs RENAME TO chat_logs_old;")
    conn.commit()
    # rename new -> chat_logs
    cur.execute("ALTER TABLE chat_logs_new RENAME TO chat_logs;")
    conn.commit()
    print("Migration completed. Old table renamed to 'chat_logs_old'. New table is 'chat_logs'.")
except Exception as e:
    print("Failed to finalize renaming:", e)
    print("You still have 'chat_logs_new' table. Please inspect DB manually.")
    conn.close()
    raise

conn.close()
print("Done.")
