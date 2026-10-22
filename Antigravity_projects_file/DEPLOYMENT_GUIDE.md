# MediSafe AI — Complete Deployment Guide (எளிய வரிசைமுறை கையேடு)

This guide provides instructions to run and deploy **MediSafe AI** locally or to free cloud hosting platforms.

---

## 1. Quick Local Deployment (Windows)

To start the app on your current machine:

### Option A: Double-Click Launcher
Double click the newly created [`run_local.bat`](file:///c:/Users/Jeeva/OneDrive/Documents/Antigravity_projects_file/run_local.bat) in the project root folder.

### Option B: Terminal Command
Run in PowerShell:
```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```
Then open your browser at:
👉 **`http://localhost:8000`**

---

## 2. Free Cloud Deployment on Render.com (பரிந்துரைக்கப்படும் கிளவுட் தளம்)

[Render.com](https://render.com) offers free hosting for web services with automated GitHub deployment.

### Steps:
1. **Push your code to GitHub:**
   - Create a new GitHub repository (e.g. `medisafe-ai`).
   - Push this project folder to your repository.
2. **Connect to Render:**
   - Go to [dashboard.render.com](https://dashboard.render.com/) and Sign Up / Log In.
   - Click **New +** > **Web Service**.
   - Connect your GitHub repository.
3. **Configure the Service:**
   - **Name:** `medisafe-ai`
   - **Language:** `Python 3`
   - **Branch:** `main` (or `master`)
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
   - **Plan:** Free
4. **Environment Variables (Optional):**
   - Under *Environment Variables*, add:
     - `GOOGLE_API_KEY`: *(Optional) Your Gemini API key*
     - `FDA_API_KEY`: *(Optional) Your OpenFDA API key*
5. **Click "Deploy Web Service":**
   - Render will build your application and provide a free live HTTPS URL (e.g., `https://medisafe-ai.onrender.com`).

*(Note: The project already contains [`render.yaml`](file:///c:/Users/Jeeva/OneDrive/Documents/Antigravity_projects_file/render.yaml) and [`Procfile`](file:///c:/Users/Jeeva/OneDrive/Documents/Antigravity_projects_file/Procfile) for automatic setup.)*

---

## 3. Instant Public URL / Mobile Demo (Tunneling via localtunnel)

If you need a public URL immediately to demonstrate the app on mobile devices or share with colleagues without setting up cloud servers:

1. Start the local server:
   ```powershell
   .\.venv\Scripts\python.exe -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
   ```
2. In another terminal, run:
   ```powershell
   npx localtunnel --port 8000
   ```
3. Open the generated HTTPS URL on any device.

---

## 4. Docker Deployment (Local or Cloud Containers)

A production-ready [`Dockerfile`](file:///c:/Users/Jeeva/OneDrive/Documents/Antigravity_projects_file/Dockerfile) and [`docker-compose.yml`](file:///c:/Users/Jeeva/OneDrive/Documents/Antigravity_projects_file/docker-compose.yml) have been created.

### Build and Run:
```bash
docker compose up -d --build
```
The application will be live at `http://localhost:8000`.

---

## 5. Free Deployment on Railway.app

1. Log into [Railway.app](https://railway.app/).
2. Click **New Project** > **Deploy from GitHub repo**.
3. Railway automatically detects the [`Procfile`](file:///c:/Users/Jeeva/OneDrive/Documents/Antigravity_projects_file/Procfile) or [`Dockerfile`](file:///c:/Users/Jeeva/OneDrive/Documents/Antigravity_projects_file/Dockerfile) and deploys it.
4. Under project settings, click **Generate Domain** to get a public HTTPS link.
