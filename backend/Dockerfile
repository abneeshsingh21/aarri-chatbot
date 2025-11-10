# backend/Dockerfile - ensures /app/backend exists so backend.app can be imported
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=8080

ARG APP_USER=aarii
ARG APP_GROUP=aarii
WORKDIR /app

# system deps
RUN apt-get update \
  && apt-get install -y --no-install-recommends \
     build-essential gcc git curl ca-certificates \
  && rm -rf /var/lib/apt/lists/*

# create non-root user
RUN groupadd -r ${APP_GROUP} && useradd -r -g ${APP_GROUP} ${APP_USER}

# --- Copy only dependency files first (cache benefit) ---
# If your requirements files are under backend/, copy them explicitly
COPY backend/requirements.txt /app/backend/requirements.txt
# optional dev reqs (won't fail build if not present in build context)
COPY backend/requirements-dev.txt /app/backend/requirements-dev.txt

# Install Python deps (prefer backend/requirements.txt)
RUN python -m pip install --upgrade pip setuptools wheel \
 && if [ -f /app/backend/requirements.txt ]; then \
      python -m pip install --no-cache-dir -r /app/backend/requirements.txt; \
    elif [ -f /app/requirements.txt ]; then \
      python -m pip install --no-cache-dir -r /app/requirements.txt; \
    else \
      echo "Warning: No requirements.txt found at /app/backend or /app"; \
    fi \
 && python -m pip install --no-cache-dir gunicorn

# --- Now copy the backend directory into /app/backend so Python can import backend.* ---
# This preserves the backend package at /app/backend
COPY backend/ /app/backend/

# Add an entrypoint script that chooses module automatically (but we prefer backend.app)
RUN mkdir -p /app/scripts \
 && cat > /app/scripts/entrypoint.sh <<'EOF' \
#!/usr/bin/env bash
set -euo pipefail
PORT="${PORT:-8080}"
# Prefer backend.app if present
if [ -f "/app/backend/app.py" ]; then
  MODULE="backend.app:app"
  echo "Entrypoint: using module backend.app:app"
elif [ -f "/app/app.py" ]; then
  MODULE="app:app"
  echo "Entrypoint: using module app:app"
else
  echo "ERROR: Could not find /app/backend/app.py or /app/app.py"
  ls -la /app
  exit 1
fi
exec gunicorn -b "0.0.0.0:${PORT}" "${MODULE}" --workers 2 --timeout 120 --access-logfile - --error-logfile -
EOF

RUN chmod +x /app/scripts/entrypoint.sh

# set ownership & switch to non-root
RUN chown -R ${APP_USER}:${APP_GROUP} /app
USER ${APP_USER}

EXPOSE 8080

CMD ["/app/scripts/entrypoint.sh"]
