# ⚡ QuickShare

> Temporarily share text or files between devices using a 6-digit code. Auto-expires in 10 minutes.

**Live Demo:** [quickshare frontend URL]  
**API:** [quickshare backend URL]

---

## Architecture

```
User (Browser)
    │
    ▼
Vercel (React Frontend)
    │  /api/share/text
    │  /api/share/file
    │  /api/receive/{code}
    ▼
Render.com (FastAPI Backend)
    │
    ├── Redis (Upstash) ──► TTL auto-expiry (600s)
    │
    └── /tmp/quickshare/ ──► File storage (deleted with Redis TTL)
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 19, Vite, plain CSS |
| Backend | Python, FastAPI 0.99, Uvicorn |
| Storage | Redis (Upstash) with 600s TTL |
| Rate limiting | SlowAPI |
| Deployment | Vercel (frontend) + Render (backend) |

---

## Features

- 📝 Share text (up to 100KB)
- 📁 Share files (PDF, DOCX, PNG, JPG, APK, ZIP, and more — up to 50MB)
- 🔢 6-digit secure random access code
- ⏱ Auto-expires in exactly 10 minutes
- 📱 Mobile-friendly responsive UI
- 🌑 Dark theme

---

## Security

- Cryptographically secure codes (`secrets.randbelow`)
- Rate limiting on all endpoints (SlowAPI)
- File type allowlist (no exe/sh/php/js/html/py)
- UUID-based filenames (original name never used for storage)
- Filename sanitization (path traversal prevention)
- Redis key injection prevention
- File path traversal check on download
- Max file size enforced in streaming chunks
- CORS restricted to frontend origin
- `.env` never committed

---

## Local Development

### Prerequisites
- Python 3.10+
- Node.js 18+
- Redis (local or Upstash)

### Backend

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your Redis URL
redis-server &          # start local Redis
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
cp .env.example .env
# Edit .env: VITE_API_URL=http://localhost:8000
npm run dev
```

Open http://localhost:5173

### Run Tests

```bash
cd backend
pytest tests/ -v --cov=app --cov-report=term-missing
```

---

## Environment Variables

### Backend `.env`

```env
REDIS_URL=redis://localhost:6379
MAX_FILE_SIZE_MB=50
CODE_TTL_SECONDS=600
CORS_ORIGINS=["http://localhost:5173"]
FRONTEND_URL=http://localhost:5173
UPLOAD_DIR=/tmp/quickshare
```

### Frontend `.env`

```env
VITE_API_URL=http://localhost:8000
```

---

## Deployment

### 1. Redis — Upstash (free)

1. Go to https://upstash.com → sign up with GitHub
2. Create a Redis database (region: closest to your backend)
3. Copy the `REDIS_URL` (starts with `rediss://`)

### 2. Backend — Render (free)

1. Go to https://render.com → New → Web Service
2. Connect your GitHub repo
3. Set root directory: `backend`
4. Build command: `pip install -r requirements.txt`
5. Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
6. Add env vars: `REDIS_URL`, `FRONTEND_URL` (your Vercel URL)

### 3. Frontend — Vercel (free)

```bash
cd frontend
npx vercel deploy --prod
# Set env var: VITE_API_URL = your Render backend URL
```

Or connect GitHub repo in Vercel dashboard.

---

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check |
| `POST` | `/api/share/text` | Share text, returns code |
| `POST` | `/api/share/file` | Upload file, returns code |
| `GET` | `/api/receive/{code}` | Get share metadata |
| `GET` | `/api/receive/{code}/download` | Download file |

### POST /api/share/text

```json
{ "text": "hello world", "type": "text" }
```

Response:
```json
{ "code": "382910", "expires_in": 600, "type": "text" }
```

### GET /api/receive/{code}

Response (text):
```json
{ "type": "text", "content": "hello world", "expires_in": 543 }
```

Response (file):
```json
{ "type": "file", "filename": "document.pdf", "download_url": "/api/receive/382910/download", "expires_in": 543 }
```
