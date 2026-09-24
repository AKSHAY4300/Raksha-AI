# RoadVision AI - 1-Click Vercel & Supabase Cloud Deployment Guide

Yes! You can deploy **RoadVision AI (Traffic Police & PWD)** on **Vercel** with **Supabase Free Cloud Database** completely free.

---

## 🏗️ Architecture on Vercel

- **Hosting Platform:** **Vercel** (Serverless Python runtime via `@vercel/python` + Edge Static CDN).
- **Cloud Database:** **Supabase** (Free Tier PostgreSQL + PostGIS + REST API).
- **Security:** AES-256-GCM authenticated payload encryption.
- **Cost:** **$0.00 / month (100% Free)**.

---

## 📁 Pre-Configured Vercel Files in this Codebase

Your project is already pre-configured for Vercel with:
1. [`vercel.json`](file:///d:/Projects/VisionAI/vercel.json): Configures `@vercel/python` for [`api/index.py`](file:///d:/Projects/VisionAI/api/index.py) and edge caching for static assets.
2. [`api/index.py`](file:///d:/Projects/VisionAI/api/index.py): Serverless ASGI bridge that exports the FastAPI `app`.
3. [`app/database.py`](file:///d:/Projects/VisionAI/app/database.py): Auto-detects Vercel serverless environment and uses `/tmp/` storage when running in read-only lambdas, with direct sync to Supabase.
4. [`requirements.txt`](file:///d:/Projects/VisionAI/requirements.txt): Optimized dependencies for Python 3.11.

---

## 🚀 Step-by-Step Deployment Instructions

### Step 1: Set Up Free Cloud Database on Supabase

1. Go to **[supabase.com](https://supabase.com)** and sign in with GitHub.
2. Click **New Project** ➔ Name: `roadvision-ai` ➔ Create.
3. In Supabase Dashboard ➔ Navigate to **Project Settings ➔ API**.
4. Copy your two credentials:
   - **Project URL:** `https://your-project-id.supabase.co`
   - **API Key (anon / public):** `eyJhbGciOi...`

*(Optional)* Run this in the Supabase SQL Editor:
```sql
CREATE TABLE IF NOT EXISTS incidents (
    id TEXT PRIMARY KEY,
    category TEXT NOT NULL,
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

### Step 2: Push Your Codebase to GitHub

In your project terminal, run:
```bash
git init
git add .
git commit -m "RoadVision AI: Police HQ, PWD Admin, MADT Cockpit, Vercel & Supabase Ready"
git remote add origin https://github.com/YOUR_GITHUB_USERNAME/roadvision-ai.git
git branch -M main
git push -u origin main
```

---

### Step 3: Deploy to Vercel (1-Click)

1. Go to **[vercel.com](https://vercel.com)** and sign in with GitHub.
2. Click **Add New... ➔ Project**.
3. Select your `roadvision-ai` repository and click **Import**.
4. Configure Project Settings:
   - **Framework Preset:** `Other`
   - **Root Directory:** `./`
5. Expand **Environment Variables** and add:

| Key | Value |
|---|---|
| `VISION_AI_AES_KEY` | `e4d9b2a7f8301c65b9d318e24f0c9a5b7134d6e802f1a5c39b7d8e204a1f6c8b` |
| `SUPABASE_URL` | `https://your-project-id.supabase.co` |
| `SUPABASE_KEY` | `your-supabase-anon-key` |
| `VERCEL` | `1` |

6. Click **Deploy**.
7. Vercel will build the serverless functions and deploy your web app to a production URL:
   `https://roadvision-ai.vercel.app`

---

## 🧪 Testing Your Live Vercel Deployment

Once deployed on Vercel:
1. Open `https://your-app.vercel.app/`
2. **Police HQ Tab:** Inspect live collision geofences, click **"Dispatch Patrol"** or **"Mark Cleared"** to remove geofence circles.
3. **PWD Admin Tab:** Inspect road potholes, faded zebra crossings, and test **"Mark as Repaired"**.
4. **Driver MADT Tab:** Click **"Start Simulated Bus Route"** to watch the in-cabin HUD dynamically announce audio/voice collision warnings.
5. **Edge AI Tab:** Test live AES-256 encrypted payload packet transmission.
