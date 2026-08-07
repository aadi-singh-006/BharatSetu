# BharatSetu AI

> A hackathon prototype that makes Indian public services easier to understand through a simple, multilingual AI conversation.

BharatSetu AI combines a polished React interface with a small FastAPI service. It answers supported public-service questions from a local knowledge base and can use Gemini as a fallback for unmatched questions.

## Demo Highlights

- Guided questions for Aadhaar, passports, PM-KISAN, scholarships, health, and education
- Responsive conversational UI with markdown answers and official links
- English and Hindi interface modes
- Browser-based voice input and read-aloud responses
- Dark mode, loading skeletons, empty states, graceful errors, and a custom 404 view
- Local JSON knowledge base with Gemini fallback

## Tech Stack

| Layer | Technology |
| --- | --- |
| Frontend | React, Vite, Tailwind CSS, Lucide React |
| Backend | Python, FastAPI, Uvicorn |
| AI | Google Gemini API |
| Prototype data | Local JSON knowledge base |

## Architecture

```text
Browser (React + Tailwind)
        |
        | POST /chat
        v
FastAPI chat route
        |
        +-- Local public-service knowledge base
        |
        +-- Gemini fallback for unmatched questions
```

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

## Quick Start

### Prerequisites

- Node.js 18+
- Python 3.10+

### 1. Run the backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

Set `GEMINI_API_KEY` in `backend/.env` to enable fallback answers. Known knowledge-base questions continue to work without Gemini.

The API runs at `http://localhost:8000`. Interactive API documentation is available at `http://localhost:8000/docs`.

### 2. Run the frontend

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

Open `http://localhost:5173`.

## API Endpoints

- `GET /` - API information
- `GET /health` - Health check
- `POST /chat` - Search the local service knowledge base first, then use Gemini when no entry matches

## Environment

Frontend variables must use the `VITE_` prefix. See [frontend/.env.example](frontend/.env.example) and [backend/.env.example](backend/.env.example). Keep the Gemini API key in `backend/.env`; never expose it through a frontend variable or commit it to source control.

## Frontend Scripts

From `frontend/`:

```bash
npm run dev      # Start Vite in development mode
npm run build    # Create a production build
npm run preview  # Preview the production build locally
```

## Suggested Demo Flow

1. Open the landing page and select a public-service category.
2. Ask “What documents are needed for a passport?” to demonstrate a local knowledge-base answer.
3. Switch between English and Hindi interface modes.
4. Use the microphone button in a supported browser, then use read-aloud on the response.
5. Toggle dark mode and resize to a mobile viewport to demonstrate responsive behavior.

## Prototype Boundaries

This repository is intentionally scoped for a hackathon demonstration. It does **not** include authentication, user accounts, persistent chat history, databases, Firebase, WhatsApp, analytics, payments, admin tooling, or production deployment infrastructure. AI answers may be incomplete or outdated and should be verified against linked official sources.

## Future Scope

Potential next steps after validating the prototype:

- Expand coverage across central and state government services
- Add more Indian languages and higher-quality regional speech models
- Build a verified-source ingestion and freshness workflow
- Add accessibility testing with real users across devices and network conditions
- Introduce user consent, privacy controls, observability, and security review before any production pilot
- Partner with public-service experts to evaluate answer quality and usefulness

These items are roadmap ideas only and are not implemented in this hackathon build.
