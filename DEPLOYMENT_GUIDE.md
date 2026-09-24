# RoadVision AI - Cloud Hosting & Supabase Deployment Guide

This guide details how to deploy the **RoadVision AI (Traffic Police & PWD)** web application online **100% free** using **Render.com** (Free Web Compute) and **Supabase** (Free PostgreSQL Cloud Database).

---

## 🏗️ Architecture Stack

- **Frontend & Admin Dashboards:** HTML5, CSS3, Vanilla JS, Leaflet.js (Traffic Police Command, PWD Civil Road Admin, Bus Driver MADT In-Cabin HUD).
- **Backend API:** FastAPI (Python 3.11), Uvicorn.
- **Security:** AES-256-GCM End-to-End Encryption with 256-bit keys and 96-bit dynamic IVs.
- **Cloud Database (Free Tier):** Supabase (PostgreSQL with PostGIS) + Embedded SQLite fallback.
- **Free Web Hosting:** Render.com (Free Tier Web Service) or Hugging Face Spaces.

---

## 🚀 Step 1: Set Up Free Cloud Database on Supabase

1. Visit **[supabase.com](https://supabase.com)** and sign in with GitHub or email (100% free tier).
2. Click **New Project** and name it `roadvision-ai`. Choose a region close to you (e.g. `ap-south-1` Mumbai or `us-east-1`).
3. Once the database is provisioned, navigate to **Project Settings ➔ API**.
4. Copy the following two credentials:
   - **Project URL:** `https://your-project-id.supabase.co`
   - **Project API Key (anon / service_role):** `eyJhbGciOi...`
5. *(Optional SQL Setup)* In Supabase SQL Editor, run:
```sql
CREATE TABLE IF NOT EXISTS incidents (
    id TEXT PRIMARY KEY,
    category TEXT NOT NULL,         -- 'POLICE' or 'PWD'
    hazard_type TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    severity TEXT NOT NULL,
    lat REAL NOT NULL,
    lng REAL NOT NULL,
    address TEXT,
    geofence_radius REAL DEFAULT 160.0,
    status TEXT NOT NULL DEFAULT 'ACTIVE',
    bus_id TEXT DEFAULT 'BUS-104',
    speed_kmh REAL DEFAULT 42.0,
    confidence REAL DEFAULT 0.92,
    image_url TEXT,
    created_at TEXT NOT NULL
);
```

---

## 🌐 Step 2: Deploy to Render.com (100% Free Web Hosting)

1. Push your project codebase to a GitHub repository:
```bash
git init
git add .
git commit -m "RoadVision AI: Police HQ, PWD, Driver MADT, Geofencing, AES-256"
git remote add origin https://github.com/YOUR_USERNAME/roadvision-ai.git
git branch -M main
git push -u origin main
```

2. Sign in to **[render.com](https://render.com)**.
3. Click **New ➔ Web Service** and select your GitHub repository (`roadvision-ai`).
4. Configure the Web Service settings:
   - **Name:** `roadvision-ai-hub`
   - **Region:** Any region (e.g., Singapore, Frankfurt, Oregon)
   - **Branch:** `main`
   - **Runtime:** `Python 3`
   - **Build Command:**
     ```bash
     pip install -r requirements.txt && python app/generate_assets.py
     ```
   - **Start Command:**
     ```bash
     uvicorn app.server:app --host 0.0.0.0 --port $PORT
     ```
   - **Instance Type:** `Free`

5. Under **Environment Variables**, add:
   | Key | Value |
   |---|---|
   | `PYTHON_VERSION` | `3.11.0` |
   | `VISION_AI_AES_KEY` | `e4d9b2a7f8301c65b9d318e24f0c9a5b7134d6e802f1a5c39b7d8e204a1f6c8b` |
   | `SUPABASE_URL` | `https://your-project-id.supabase.co` |
   | `SUPABASE_KEY` | `your-supabase-api-key` |

6. Click **Create Web Service**. Render will build and deploy your live URL:
   `https://roadvision-ai-hub.onrender.com`

---

## ⚡ Alternative Free Hosting: Hugging Face Spaces

1. Create a free account at **[huggingface.co](https://huggingface.co)**.
2. Click **New Space ➔ Space SDK: Docker**.
3. Push your repository to the Hugging Face Space git remote.
4. Hugging Face will automatically build the included [`Dockerfile`](file:///d:/Projects/VisionAI/Dockerfile) and host your dashboard on port 7860.

---

## 🧪 Testing Your Live Web App

Once deployed online:
1. Open your live URL in any desktop or mobile browser.
2. Open **Police HQ**: Inspect geofenced vehicle collisions, dispatch traffic patrol, and test **"Mark as Cleared (Reopen Road)"** to remove the geofence.
3. Open **PWD Admin**: Inspect asphalt potholes and test **"Mark as Repaired"**.
4. Open **Driver MADT**: Start the simulated bus route to hear live synthesized audio/voice warnings and watch the speedometer and distance countdown.
5. Open **Edge AI & AES**: Inspect the live AES-256 encrypted telemetry packet transmission.
