# 🚀 Aarii — Complete Deployment Guide

## Overview
This guide walks you through deploying both the frontend and backend of Aarii in under 10 minutes, resulting in a single public chatbot URL.

**Final Result**: A public React app (GitHub Pages) + a live backend API (Render) = **one chatbot link you can share**.

---

## Architecture

```
Frontend (GitHub Pages)  → API calls → Backend (Render)
     ↓                                      ↓
   React App                         Flask API + SQLite/PostgreSQL
  (Static Site)                      (AI Engine + Memory)
```

---

## Part 1: Frontend deployment (automated via GitHub Actions)

### What happens automatically
- When you push to the `deploy-fix-clean` branch, GitHub Actions:
  1. Builds the React app from `frontend/` (using `npm run build`)
  2. Publishes the static build to GitHub Pages

### Your Frontend URL will be
```
https://<your-github-username>.github.io/aarri-chatbot/
```

### Enable GitHub Pages (one-time setup)
1. Go to your GitHub repository → Settings → Pages
2. Under "Source", select: **Deploy from a branch**
3. Choose branch: **deploy-fix-clean**
4. Folder: **/ (root)**
5. Click Save

GitHub Actions will automatically build and publish the frontend.

---

## Part 2: Backend deployment (Render)

### Step 1: Sign up for Render
- Go to https://render.com (free tier available)
- Sign up with GitHub (recommended)

### Step 2: Create a new Web Service
1. In Render, click "New +" → **Web Service**
2. **Connect your GitHub repository** (`aarri-chatbot`)
3. Choose branch: **deploy-fix-clean**
4. **Runtime**: Python 3
5. **Build command**: `pip install -r backend/requirements.txt`
6. **Start command**: 
   ```
   cd backend && gunicorn -w 2 -b 0.0.0.0:$PORT app:app
   ```

### Step 3: Set environment variables in Render
Click "Environment" and add these variables:

| Key | Value | Notes |
|-----|-------|-------|
| `GROQ_API_KEY` | (your API key) | **Required** — get from Groq API |
| `GROQ_MODEL` | `llama-3.1-8b-instant` | LLM model name |
| `GROQ_BASE_URL` | `https://api.groq.com/openai/v1` | Groq API endpoint |
| `DATABASE_URL` | `sqlite:///./aarii_chatlogs.db` | SQLite (free), or add Postgres |
| `FLASK_DEBUG` | `false` | Production mode |
| `AARII_SYSTEM_PROMPT` | `You are Aarii, a helpful AI assistant.` | Default system message |
| `AARII_TEMP` | `0.2` | Temperature (0.0-1.0) |
| `AARII_MAX_TOKENS` | `512` | Max response length |
| `EMBED_MODEL` | `all-MiniLM-L6-v2` | Embedding model for memory |
| `FRONTEND_URL` | `https://abneeshsingh21.github.io/aarri-chatbot` | Update with your GitHub Pages URL |

### Step 4: Deploy
- Click **Create Web Service**
- Render will build and deploy your backend
- You'll get a public URL like: `https://aarii-backend.onrender.com`

---

## Part 3: Connect frontend ↔ backend

### Update frontend to call the live backend

1. In your repo, edit `frontend/.env`:
   ```
   REACT_APP_AARII_API_BASE=https://aarii-backend.onrender.com
   ```

2. Commit and push to `deploy-fix-clean`:
   ```bash
   git add frontend/.env
   git commit -m "chore: update frontend API base to live backend"
   git push origin deploy-fix-clean
   ```

3. GitHub Actions will re-build and publish the updated frontend (wait ~2-3 minutes)

### Update backend to allow frontend domain

The backend already allows GitHub Pages origins via CORS. If you use a custom domain, update `backend/app.py` line with `FRONTEND_URL` environment variable.

---

## Part 4: Get your single public link

Once both are deployed, your public chatbot link is:

```
https://<your-github-username>.github.io/aarri-chatbot/
```

This frontend will call your backend API at:
```
https://aarii-backend.onrender.com
```

---

## Testing the integration

1. **Visit** your frontend URL (from Part 1)
2. **Type a message** and click "Send"
3. **Verify**: You should see the AI respond (if `GROQ_API_KEY` is set)

If you see an error like "⚠️ Aarii is not configured", check:
- [ ] `GROQ_API_KEY` is set in Render environment
- [ ] Backend API is running (check Render logs)
- [ ] Frontend `.env` has the correct `REACT_APP_AARII_API_BASE` URL

---

## Advanced: Set up automatic backend redeployment

If you want the backend to redeploy automatically when you push code, you can set up GitHub Actions secrets in your repo and use the `render-deploy.yml` workflow:

1. Get your Render API key:
   - Render dashboard → Account → API Keys → Create API Key

2. Get your backend service ID:
   - Your service URL: `https://aarii-backend-<randomid>.onrender.com`
   - The ID is the part after `services/` in Render dashboard URL

3. Add GitHub repo secrets:
   - Go to GitHub repo → Settings → Secrets and variables → Actions
   - Add:
     - `RENDER_API_KEY` = (your Render API key)
     - `RENDER_SERVICE_ID` = (your service ID)

4. Push code to `deploy-fix-clean`
   - The workflow `.github/workflows/render-deploy.yml` will trigger and redeploy

---

## Features you can now use

✅ **Multi-mode conversation** — switch conversation styles (Teacher, Creative, Technical, Friendly)  
✅ **Sentiment analysis** — responses include sentiment metrics  
✅ **Smart memory** — contextual retrieval of past messages  
✅ **Voice input/output** — dictate messages and hear AI responses (browser dependent)  
✅ **Export chat** — download conversation as JSON  
✅ **Rate limiting** — API protected against abuse  
✅ **Production ready** — CORS headers, error handling, logging

---

## Troubleshooting

### Frontend not building?
- Check GitHub Actions tab in your repo → frontend workflow logs
- Common issue: missing `frontend/package.json` or Node version mismatch

### Backend not responding?
- Check Render service logs (Render dashboard → your service → Logs)
- Verify `GROQ_API_KEY` is set (should not show "(no reply from model)" or config error)
- Ensure backend is not in "Suspended" state (Render suspends free tier after 15 min of inactivity)

### CORS errors?
- Check that your frontend URL is included in `backend/app.py` CORS origins
- Or set `FRONTEND_URL` environment variable in Render

### Database errors?
- Default SQLite works locally; for production consider adding a Postgres database on Render (free tier available)
- If using SQLite in production, note data will be lost on Render redeploy (use Postgres for persistence)

---

## Summary of all links & commands

| Item | Link/Command |
|------|---------|
| GitHub repo | https://github.com/abneeshsingh21/aarri-chatbot |
| Repo branch | `deploy-fix-clean` |
| **Frontend URL** | `https://<your-username>.github.io/aarri-chatbot/` |
| **Backend URL** | `https://aarii-backend.onrender.com` |
| GitHub Actions | Repo → Actions tab |
| Render dashboard | https://dashboard.render.com |

---

## Next steps

1. ✅ Ensure `deploy-fix-clean` branch is pushed to GitHub
2. ✅ Enable GitHub Pages (Settings → Pages)
3. ✅ Create Render service (using repo or `render.yaml` manifest)
4. ✅ Set `GROQ_API_KEY` in Render environment
5. ✅ Update `frontend/.env` with your backend Render URL
6. ✅ Push the updated frontend to GitHub
7. ✅ Wait for GitHub Actions to build and publish
8. ✅ Visit your public frontend link and test the chatbot

---

**🎉 You're done! You now have a live AI chatbot accessible from anywhere.**

For questions or issues, check the logs in GitHub Actions (frontend) and Render (backend).
