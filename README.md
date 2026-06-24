# 📖 YourDiary — AI-Powered Personal Diary

> A modern full-stack journaling app with a personal LSTM neural network that learns your unique writing style.

[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688?style=flat&logo=fastapi)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/Frontend-React-61DAFB?style=flat&logo=react)](https://react.dev)
[![Vite](https://img.shields.io/badge/Bundler-Vite-646CFF?style=flat&logo=vite)](https://vitejs.dev)
[![PostgreSQL](https://img.shields.io/badge/Database-PostgreSQL-4169E1?style=flat&logo=postgresql)](https://postgresql.org)
[![SQLite](https://img.shields.io/badge/Dev%20DB-SQLite-003B57?style=flat&logo=sqlite)](https://sqlite.org)

---

## ✨ Features

| Feature | Description |
|---|---|
| 🧠 **Personal AI** | Per-user LSTM neural network learns your writing style |
| ✍️ **Smart Suggestions** | Real-time AI completions — short, medium, full sentence, or custom length |
| 📔 **Diary Timeline** | Chronological view of all your entries with search |
| ✅ **Task Management** | Convert diary thoughts into tasks with priorities and due dates |
| 📊 **Stats Dashboard** | Track total, pending, completed, and overdue tasks at a glance |
| 🔒 **JWT Auth** | Secure signup/login with hashed passwords and token-based sessions |
| 🗄️ **Flexible Database** | SQLite for local dev, PostgreSQL (Supabase/Neon/Railway) for production |
| 🚀 **Deployable** | FastAPI on Render + React on Vercel — fully decoupled |

---

## 🏗️ Architecture

```
┌─────────────────────────┐        ┌──────────────────────────┐
│   React Frontend (Vite) │  HTTP  │   FastAPI Backend         │
│   Vercel                │◄──────►│   Render                  │
│                         │  JWT   │                           │
│  /            Home      │        │  /api/auth/signup         │
│  /diary       Timeline  │        │  /api/auth/login          │
│  /tasks       Tasks     │        │  /api/diary/entry         │
│  /entries     List      │        │  /api/diary/entries       │
│  /login       Auth      │        │  /api/diary/suggestions   │
│  /signup      Auth      │        │  /api/tasks  (CRUD)       │
└─────────────────────────┘        └──────────┬───────────────┘
                                              │ DATABASE_URL set?
                                   ┌──────────▼───────────────┐
                                   │  PostgreSQL (production)  │
                                   │  Supabase / Neon /        │
                                   │  Railway                  │
                                   └──────────────────────────┘
                                              │ No DATABASE_URL?
                                   ┌──────────▼───────────────┐
                                   │  SQLite  (local dev)      │
                                   │  yourdiary.db             │
                                   └──────────────────────────┘
```

---

## 📁 Project Structure

```
Your_diary/
├── app.py                   # FastAPI application — all routes & JWT auth
├── requirements.txt         # Python dependencies
├── render.yaml              # Render deployment config
├── procfile                 # Start command
├── .env.example             # Backend env variable template ← copy to .env
├── base_model.npz           # Pre-trained LSTM weights (Sherlock Holmes corpus)
├── yourdiary.db             # SQLite DB — auto-created when no DATABASE_URL set
│
├── models/
│   ├── database.py          # DB layer: auto-detects SQLite or PostgreSQL
│   └── lstm_model.py        # Custom LSTM neural network (pure NumPy)
│
└── frontend/
    ├── index.html
    ├── vercel.json          # Vercel SPA routing config
    ├── vite.config.js       # Dev proxy → localhost:8000
    ├── .env.example         # Frontend env variable template ← copy to .env.local
    └── src/
        ├── main.jsx
        ├── App.jsx          # Routes (React Router)
        ├── api.js           # Axios + JWT interceptor
        ├── index.css        # Global dark design system
        ├── context/
        │   └── AuthContext.jsx
        ├── components/
        │   ├── Navbar.jsx
        │   └── ProtectedRoute.jsx
        └── pages/
            ├── Login.jsx
            ├── Signup.jsx
            ├── Home.jsx     # Smart writing + AI suggestions
            ├── Diary.jsx    # Entry timeline
            ├── Tasks.jsx    # Task dashboard
            └── Entries.jsx  # All entries list
```

---

## 🚀 Local Setup

### Prerequisites
- Python 3.9+
- Node.js 18+

### 1. Clone & Configure Backend

```bash
git clone https://github.com/your-username/Your_diary.git
cd Your_diary

# Create your local env file
cp .env.example .env
# Edit .env — at minimum set SECRET_KEY (leave DATABASE_URL blank for SQLite)

# Install Python dependencies
pip install -r requirements.txt

# Start FastAPI
uvicorn app:app --reload --port 8000
```

| URL | Description |
|---|---|
| `http://localhost:8000` | API base |
| `http://localhost:8000/docs` | Swagger UI (auto-generated!) |
| `http://localhost:8000/redoc` | ReDoc API reference |

### 2. Configure & Start Frontend

```bash
cd frontend

# Create local env file
cp .env.example .env.local
# .env.local already points to localhost:8000 — no changes needed for local dev

# Install Node dependencies
npm install

# Start dev server
npm run dev
# → http://localhost:5173
```

> **Note:** Vite proxies all `/api` calls to `localhost:8000` in dev mode — no CORS configuration needed locally.

---

## 🔑 Environment Variables

### Backend — `.env` (copy from `.env.example`)

| Variable | Required | Default | Description |
|---|---|---|---|
| `SECRET_KEY` | ✅ **Yes** | `yourdiary-secret...` | JWT signing secret. **Must be changed in production.** Generate with: `openssl rand -hex 32` |
| `ALLOWED_ORIGINS` | ✅ **Yes** | `http://localhost:5173` | Comma-separated CORS origins. Set to your Vercel URL in production. |
| `DATABASE_URL` | ⬜ Optional | *(empty)* | PostgreSQL connection string. If empty, SQLite is used automatically. |

**Example `.env`:**
```env
SECRET_KEY=a3f8c2e1d4b7a9f0e3c6b5d8a1f4e7c0b3d6a9f2e5c8b1d4a7f0e3c6b9d2a5
ALLOWED_ORIGINS=https://yourdiary.vercel.app
DATABASE_URL=postgresql://postgres.xxxx:mypass@aws-0-us-east-1.pooler.supabase.com:6543/postgres
```

---

### Frontend — `frontend/.env.local` (copy from `frontend/.env.example`)

| Variable | Required | Description |
|---|---|---|
| `VITE_API_URL` | ✅ **Yes** | Base URL of the FastAPI backend. `http://localhost:8000` locally, your Render URL in production. |

**Example `frontend/.env.local`:**
```env
# Local development
VITE_API_URL=http://localhost:8000

# Production (use Render URL)
# VITE_API_URL=https://yourdiary-api.onrender.com
```

---

## 🗄️ Database Setup

### Option A — SQLite (Local Dev, Zero Config)

Don't set `DATABASE_URL` in your `.env`. The app automatically creates and uses `yourdiary.db` in the project root. No installation or account needed.

```env
DATABASE_URL=   # leave blank
```

### Option B — PostgreSQL (Production, Persistent)

SQLite on Render's free tier is **ephemeral** — the file is wiped on every redeploy. Use a hosted PostgreSQL database for persistent production data.

#### 🟦 Supabase (Recommended — Free 500 MB)

1. Go to [supabase.com](https://supabase.com) → **New Project**
2. Choose a region and set a strong database password
3. Go to **Project Settings → Database → Connection String → URI**
4. Copy the **Session pooler** string (port `5432`)
5. Replace `[YOUR-PASSWORD]` with your actual password
6. Set it as `DATABASE_URL` on Render

```env
DATABASE_URL=postgresql://postgres.abcdef:yourpassword@aws-0-us-east-1.pooler.supabase.com:5432/postgres
```

#### 🟢 Neon (Free 0.5 GB, Serverless)

1. Go to [neon.tech](https://neon.tech) → **New Project**
2. Copy the connection string from **Dashboard → Connection Details**
3. Make sure it includes `?sslmode=require`

```env
DATABASE_URL=postgresql://user:password@ep-cool-darkness-123456.us-east-2.aws.neon.tech/neondb?sslmode=require
```

#### 🟣 Railway (PostgreSQL addon)

1. Go to [railway.app](https://railway.app) → **New Project → Add PostgreSQL**
2. Click the PostgreSQL service → **Variables** → copy `DATABASE_URL`

```env
DATABASE_URL=postgresql://postgres:password@containers-us-west-1.railway.app:5432/railway
```

> **How it works:** The database layer auto-detects the environment. If `DATABASE_URL` is set, it uses `psycopg2` to connect to PostgreSQL. If not, it uses the built-in `sqlite3` with a local file. No code changes needed between environments.

---

## 🌐 API Reference

All protected routes require:
```
Authorization: Bearer <token>
```

### Auth

| Method | Endpoint | Auth | Body | Description |
|---|---|---|---|---|
| `POST` | `/api/auth/signup` | — | `{username, password}` | Register new user |
| `POST` | `/api/auth/login` | — | `{username, password}` | Login → JWT token |

**Login response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "username": "john"
}
```

### Diary

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `POST` | `/api/diary/entry` | ✅ | Save a diary entry |
| `GET` | `/api/diary/entries` | ✅ | Get all entries (newest first) |
| `POST` | `/api/diary/suggestions` | ✅ | Get AI writing completions |

**Suggestion request:**
```json
{
  "text": "Today I felt",
  "max_length": 20,
  "num_suggestions": 3
}
```
> Set `"max_length": "sentence"` to generate text until the next period.

### Tasks

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `GET` | `/api/tasks` | ✅ | Get all tasks + stats |
| `POST` | `/api/tasks` | ✅ | Create a task |
| `PATCH` | `/api/tasks/{id}/status` | ✅ | Update status |
| `DELETE` | `/api/tasks/{id}` | ✅ | Delete task |

---

## 🧠 How the AI Works

### Training & Personalization Pipeline

```
User writes entry
      │
      ▼
Save entry to DB  ──────────────────────────────────────────────────────►  Diary entries table
      │
      ▼
  entry_count % 3 == 0?
      │  YES
      ▼
Spawn daemon thread (non-blocking)
      │
      ▼
LSTM incremental training
  - Join recent 10 entries into training text
  - Run backprop on up to 10 sequences (seq_length=25)
  - Gradient clipping applied
      │
      ▼
Serialize weights → bytes (npz format, ~990 KB)
      │
      ├──► Save to DB  (user_models table — BLOB/BYTEA)  ← survives redeploys ✅
      │
      └──► Save to filesystem (yourdiary_users/user_X.npz) ← local dev fallback
```

### On Next Request (Weight Loading Priority)
```
1. Database BLOB  ─ exists? → load  (production, always up to date)
2. Filesystem .npz ─ exists? → load  (local dev, or DB unavailable)
3. Base model copy  ─ fallback for brand-new users
```

### Technical Details

| Property | Value |
|---|---|
| Architecture | Single-layer LSTM, character-level |
| Hidden size | 128 units |
| Vocabulary | 89 characters (letters, punctuation, symbols) |
| Base training | Sherlock Holmes corpus (`base_model.npz`) |
| Per-user training | Incremental, every 3 diary entries |
| Weight storage | `user_models` DB table (`BLOB`/`BYTEA`, ~990 KB per user) |
| Training thread | Daemon thread — never blocks API responses |
| Learning rate | 0.005 |
| Gradient clipping | ±5 |

### Why DB Storage Matters

On **Render free tier**, the filesystem is **ephemeral** — all files in `yourdiary_users/` are wiped on every redeploy. Without DB storage, every user's personalization would be lost on each deployment.

By serializing the LSTM weight matrices (`W_i`, `W_f`, `W_c`, `W_o`, `W_hy` and biases) to an npz blob and storing it in the database, personalization **persists permanently** regardless of server restarts or redeploys.


---

## 🚢 Deployment

### Step 1 — Set Up PostgreSQL

Pick a free provider (Supabase recommended) and get your `DATABASE_URL`. See [Database Setup](#️-database-setup) above.

### Step 2 — Deploy Backend to Render

1. Push repo to GitHub
2. [render.com](https://render.com) → **New Web Service** → connect your repo
3. Render reads `render.yaml` automatically, or set manually:
   - **Build**: `pip install -r requirements.txt`
   - **Start**: `uvicorn app:app --host 0.0.0.0 --port $PORT`
4. Set **Environment Variables** on Render dashboard:

| Variable | Value |
|---|---|
| `SECRET_KEY` | `openssl rand -hex 32` output |
| `ALLOWED_ORIGINS` | Your Vercel URL (set after Step 3) |
| `DATABASE_URL` | Your PostgreSQL connection string |

5. Click **Deploy** — note your Render URL (e.g. `https://yourdiary-api.onrender.com`)

### Step 3 — Deploy Frontend to Vercel

1. [vercel.com](https://vercel.com) → **New Project** → import your repo
2. Set **Root Directory** to `frontend`
3. Add environment variable:

| Variable | Value |
|---|---|
| `VITE_API_URL` | Your Render URL from Step 2 |

4. Click **Deploy** — note your Vercel URL

### Step 4 — Connect Both

- Copy your **Vercel URL** → go back to Render → update `ALLOWED_ORIGINS` → redeploy
- Done ✅

---

## 🛠️ Tech Stack

### Backend
| Library | Purpose |
|---|---|
| [FastAPI](https://fastapi.tiangolo.com) | Web framework with auto Swagger docs |
| [Uvicorn](https://www.uvicorn.org) | ASGI server |
| [python-jose](https://github.com/mpdavis/python-jose) | JWT signing & verification |
| [passlib + bcrypt](https://passlib.readthedocs.io) | Password hashing |
| [psycopg2-binary](https://www.psycopg.org) | PostgreSQL adapter |
| [NumPy](https://numpy.org) | LSTM neural network (no TensorFlow needed) |
| SQLite / PostgreSQL | Database (auto-detected from environment) |

### Frontend
| Library | Purpose |
|---|---|
| [React 19](https://react.dev) | UI library |
| [Vite](https://vitejs.dev) | Build tool with HMR |
| [React Router v7](https://reactrouter.com) | Client-side routing |
| [Axios](https://axios-http.com) | HTTP client with JWT interceptor |
| Vanilla CSS | Custom dark design system |

---

## 📜 License

MIT — feel free to use, modify, and distribute.

---

*YourDiary — Where Technology Meets Thoughtfulness 💭✨*
