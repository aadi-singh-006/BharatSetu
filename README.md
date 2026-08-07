# BharatSetu AI

BharatSetu AI is a hackathon prototype with a React + Vite frontend and a FastAPI backend. The repository intentionally has no authentication, database, Firebase, or WhatsApp integration.

## Project Structure

```text
BharatSetu-AI/
├── frontend/              # React, Vite, Tailwind CSS
│   ├── src/
│   ├── .env.example
│   ├── package.json
│   └── ...
├── backend/               # FastAPI, Python
│   ├── app/
│   ├── .env.example
│   └── requirements.txt
└── README.md
```

## Prerequisites

- Node.js 18+
- Python 3.10+

## Run the Frontend

```bash
cd frontend
cp .env.example .env
npm install
npm run dev
```

The Vite development server runs at `http://localhost:5173`.

## Run the Backend

In a second terminal:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate       # macOS/Linux
# .venv\Scripts\activate      # Windows
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

The API runs at `http://localhost:8000`. Visit `http://localhost:8000/docs` for the automatically generated API docs, or `http://localhost:8000/health` for a health check.

Before starting the backend, set `GEMINI_API_KEY` in `backend/.env`. The API uses `gemini-2.5-flash` by default.

### API Endpoints

- `GET /` - API information
- `GET /health` - Health check
- `POST /chat` - Search the local service knowledge base first, then use Gemini when no entry matches

## Environment Variables

Frontend variables must use the `VITE_` prefix. See [frontend/.env.example](frontend/.env.example) and [backend/.env.example](backend/.env.example). Keep the Gemini API key in `backend/.env`; never expose it through a frontend variable or commit it to source control.

## Available Scripts

From `frontend/`:

```bash
npm run dev      # Start Vite in development mode
npm run build    # Create a production build
npm run preview  # Preview the production build locally
```
