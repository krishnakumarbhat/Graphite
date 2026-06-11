# Graphite

![Python](https://img.shields.io/badge/python-3.10-blue)
![Flask](https://img.shields.io/badge/backend-Flask-000)
![React](https://img.shields.io/badge/frontend-React-61dafb)
![Expo](https://img.shields.io/badge/mobile-Expo-000)
![Gemini](https://img.shields.io/badge/AI-Gemini-4285F4)
![License](https://img.shields.io/badge/license-MIT-green)

**Local-first, AI-powered second brain** — a notes + workflows application with semantic search, agentic research, and an LLM-optimized data pipeline. Built as a mobile-first Expo app with a Flask backend.

---

## ✨ Features

- **Semantic search** — Gemini embeddings (768-dim) + cosine similarity over 500+ notes
- **ReAct agents** — Finance, career, VC, and scraper agents reason over your notes
- **Deep research** — Chunk → embed → retrieve → LLM-synthesized reports with citations
- **Voice notes** — Local STT (Whisper Tiny) + TTS (Kitten) support
- **Mobile-first** — React Native / Expo with web preview
- **Local + cloud** — SQLite (dev) / Supabase pgvector (prod)

---

## 📊 Pipeline Reports

| Report | Description |
|--------|-------------|
| [**Pipeline Report**](note.html) | Before/after metrics on embedding pipeline, search relevance (Precision@5: 0.71), retrieval latency, vector DB benchmarks, and architecture diagrams |
| [**Demo Presentation**](presentation.html) | Interactive demo deck with baseline vs optimized comparison, clickable architecture, Altimate optimization tools, and live demo script |

---

## 🧱 Stack

| Layer | Technology |
|-------|-----------|
| Mobile + Web preview | React Native + Expo |
| Local DB | expo-sqlite |
| Cloud DB | Supabase (PostgreSQL + pgvector) |
| Auth | Supabase Auth (email/password) |
| Backend API | Flask |
| AI engine | Gemini 2.0 Flash (fallback: 3.1 Flash) |
| Embeddings | Gemini text-embedding-004 (768-dim) |
| Local STT | Whisper Tiny |
| Local TTS | Kitten TTS Nano |

---

## 📁 Monorepo Layout

```
├── backend/          — Flask API, Gemini workflows, static serving
│   └── src/          — agents, pipelines, routes, STT/TTS engines
├── frontend/         — legacy React web package (built SPA)
├── mobile/           — primary React Native / Expo client
├── docs/             — architecture, HLD diagrams, contribution docs
├── tests/            — backend tests, eval datasets
├── note.html         — LLM pipeline improvement report
├── presentation.html — interactive demo presentation
└── .env.example      — canonical config template
```

---

## 🚀 Quick Start

### 1) Backend (localhost:8001)

```bash
cp .env.example .env

cd backend
pip3 install --user -r requirements.txt
python3 server.py
```

**Required** in root `.env`:
- `SUPABASE_URL` + `SUPABASE_PUBLIC_KEY`
- `GEMINI_API_KEY`

**Optional** (backend writes to Supabase):
- `SUPABASE_SECRET_KEY`

### 2) Mobile app + web preview (localhost:8081)

Set env vars in your shell:

```bash
export EXPO_PUBLIC_SUPABASE_URL="https://your-project.supabase.co"
export EXPO_PUBLIC_SUPABASE_ANON_KEY="your_anon_key"
export EXPO_PUBLIC_API_URL="http://127.0.0.1:8001"
```

Run:

```bash
cd mobile
npm install
npm run web
```

### 3) Open pipeline reports

```bash
# Open in browser:
open note.html
open presentation.html
```

---

## 🔌 USB Android Localhost Access

```bash
adb devices
adb reverse tcp:8081 tcp:8081
adb reverse tcp:8001 tcp:8001
```

- Expo web preview: `http://127.0.0.1:8081`
- Backend health: `http://127.0.0.1:8001/api/health`

---

## 🧪 Testing

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/python -m pytest tests/
```

---

## 🐳 Docker

```bash
docker build -t graphite .
docker run --rm -p 8001:8001 --env-file backend/.env graphite
```

---

## 📱 APK Build (EAS)

```bash
cd mobile
npm install -g eas-cli
eas login
eas build:configure
eas build -p android --profile preview
```

Download APK from the EAS build URL after completion.

---

## 📄 Open-Source Docs

- [Contributing](CONTRIBUTING.md)
- [Code of Conduct](CODE_OF_CONDUCT.md)
- [Security](SECURITY.md)
- [Rules](RULES.md)
- [Architecture](docs/ARCHITECTURE.md)
- [UI Parity](docs/UI_PARITY.md)
- [Edge Model Matrix](docs/EDGE_MODEL_MATRIX.md)
- [Notebook LLM Guide](docs/NOTEBOOK_LLM_GUIDE.md)
- [Profiling](docs/PROFILING.md)

---

## 🔧 Local Model Setup

```bash
# Store models under:
mobile/models/tts
mobile/models/stt
mobile/models/vision

# Bootstrap edge-model workspace:
.venv/bin/python scripts/generate_edge_model_assets.py
```

---

## 🧠 Pipeline Architecture

```
User Note → Chunker (1400c/180 overlap) → Gemini Embedding (768d)
  → SQLite / pgvector (cosine sim) → ReAct Agent (Gemini Flash)
  → Synthesized Answer with Citations
```

See [**note.html**](note.html) for the full before/after analysis and [**presentation.html**](presentation.html) for the interactive architecture walkthrough.
