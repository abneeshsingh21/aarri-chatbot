Deployment guide — Frontend + Backend
===================================

This repository now includes CI workflows to make deployment straightforward.

What I added
- `.github/workflows/frontend-gh-pages.yml` — builds the React app in `frontend/` and deploys the static build to GitHub Pages when you push to the `deploy-fix-clean` branch.
- `.github/workflows/backend-ghcr.yml` — builds a Docker image from `backend/Dockerfile` and pushes it to GitHub Container Registry (GHCR) when you push to the `deploy-fix-clean` branch.

Goal
----
Create one public frontend URL (GitHub Pages) and provide a deployable backend Docker image that you can attach to a hosting service (Render, Railway, Fly, etc.).

Steps I recommend to get a single live site (frontend + backend):

1) Frontend (automatic)
   - After this branch (`deploy-fix-clean`) is pushed, the frontend workflow will build and publish it to GitHub Pages.
   - The Pages URL will be one of:
     - `https://<your-github-username>.github.io/<repo-name>/`
     - (or a custom domain if configured)

2) Backend (requires creating a service)
   - Use the Docker image I pushed to GHCR: `ghcr.io/<your-username>/aarri-chatbot-backend:latest`.
   - Create a service on Render / Railway / Fly / DigitalOcean App Platform and point it at that image (or connect Render directly to this repo and use the `backend/Dockerfile`).

   Minimal Render steps (recommended, GUI):
   - Create a new Web Service on Render.
   - Choose "Deploy from GitHub" and connect to this repo, branch `deploy-fix-clean`.
   - Set the build command to use the `backend/Dockerfile` or provide the Dockerfile path.
   - Add environment variables required by the backend (example):
     - `DATABASE_URL` (e.g. `sqlite` or a hosted Postgres)
     - `GROQ_API_KEY` (your model API key)
     - `FLASK_DEBUG=false`
   - Deploy.

3) Make frontend talk to backend
   - After the backend deploys you'll get a public URL, e.g. `https://aarii-backend.onrender.com`.
   - Update frontend to call that API (set `REACT_APP_API_BASE` in `frontend/.env` or configure the frontend to use a runtime env). Then re-deploy the frontend (the GitHub Pages workflow runs on every push to the branch).

Notes & next steps I can do for you
- I can add a GitHub Action to automatically call the Render API to trigger a deployment when the backend image changes — but that requires a `RENDER_API_KEY` secret in your repo (you'd need to create it in Render and then add it to GitHub secrets).
- I can also set up a one-click Render manifest file if you want to create the Render service from the repo.

If you'd like I can now:
- A) Add the optional Render deploy workflow (requires you to add `RENDER_API_KEY` and `RENDER_SERVICE_ID` secrets), or
- B) Proceed to configure automatic deployment for a different host (Railway/Fly) — tell me which provider you prefer.

Which would you like next? (A or B) — or tell me the provider you prefer and I'll prepare the necessary CI and instructions.

Render secret setup (exact steps)
--------------------------------

1. Create a Render API key
   - Log into Render (https://dashboard.render.com).
   - Click your avatar (top-right) -> "Account Settings" -> "API Keys" -> "Generate API Key".
   - Copy the generated key.

2. Get your Service ID
   - In Render, go to the Service you created for the backend.
   - The Service ID can be found in the URL (it appears after `/services/`) or under the service's "Settings" page.
   - Copy this ID.

3. Add GitHub repository secrets
   - Go to your GitHub repository -> Settings -> Secrets and variables -> Actions -> New repository secret.
   - Add two secrets with the exact names used by the workflow:
     - `RENDER_API_KEY` — paste the API key value
     - `RENDER_SERVICE_ID` — paste the Service ID

After adding these secrets, the workflow `.github/workflows/render-deploy.yml` will be able to trigger Render deploys automatically when the backend image is updated.

Frontend runtime config
-----------------------
If your frontend needs to call the backend, add a runtime variable to the frontend build or set `REACT_APP_API_BASE` in `frontend/.env` before building. Example:

```
REACT_APP_API_BASE=https://<your-backend-domain>
```

Then push to `deploy-fix-clean` to re-run the frontend build and publish the updated site.
