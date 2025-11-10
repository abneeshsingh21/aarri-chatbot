# backend/Dockerfile
FROM python:3.11-slim

# system deps for many python packages (add more if your packages need them)
RUN apt-get update && apt-get install -y build-essential gcc git && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# copy only what's needed first for better caching
COPY backend/requirements.txt backend/requirements-dev.txt /app/
RUN python -m pip install --upgrade pip setuptools wheel
RUN python -m pip install -r requirements.txt
# Optional dev requirements:
# RUN python -m pip install -r requirements-dev.txt

# copy app code
COPY backend/ /app/

# If your Flask app entry is app.py and app variable is `app`
ENV PORT=8080
CMD ["gunicorn", "-b", "0.0.0.0:8080", "app:app", "--workers", "2", "--timeout", "120"]
