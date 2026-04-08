# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A full-stack Project Management MVP with a Kanban board and AI chat sidebar. The frontend (Next.js) is served as static files by the FastAPI backend in production (Docker). During development, both servers can run independently.

- App runs at `http://127.0.0.1:8000` (Docker/integrated) or `http://127.0.0.1:3000` (frontend dev)
- Auth: hardcoded credentials (`user` / `password`), bearer token `pm-mvp-user-token`
- AI model: `openai/gpt-oss-120b` via OpenRouter (`OPENROUTER_API_KEY` in root `.env`)
- Database: SQLite at `data/pm.sqlite3` (auto-created)

## Commands

### Running the App

```bash
./scripts/start-mac.sh      # macOS
./scripts/start-linux.sh    # Linux
./scripts/start-windows.ps1 # Windows PowerShell
```

### Backend

```bash
cd backend
uv sync                     # install dependencies
uv run pytest               # run all tests
uv run pytest tests/test_main.py::test_name  # run a single test
```

### Frontend

```bash
cd frontend
npm run dev                 # dev server on port 3000
npm run build               # production static export
npm run lint                # ESLint
npm run test:unit           # Vitest unit/component tests
npm run test:e2e            # Playwright e2e tests (requires dev server)
npm run test:all            # all tests
```

## Architecture

```
backend/app/
  main.py          # FastAPI app, all routes, static file serving
  config.py        # constants, OpenRouter config, API key loading
  models.py        # Pydantic request/response models
  dependencies.py  # auth + DB dependency injection
  storage.py       # SQLite BoardStore: schema, CRUD, AI operation application
  ai.py            # OpenRouterClient, structured AI request/response
  board_seed.py    # seed board data

frontend/src/
  app/             # Next.js App Router (layout.tsx, page.tsx)
  components/      # KanbanBoard, KanbanColumn, KanbanCard, AIChatSidebar, NewCardForm, HomeScreen
  lib/
    kanban.ts      # board data model, card movement helpers
    boardApi.ts    # all API calls: auth, board, AI chat
```

**Data flow:** `boardApi.ts` → FastAPI routes → `storage.py` (SQLite) / `ai.py` (OpenRouter)

**AI chat:** The sidebar sends messages to `/api/ai/chat`. The backend builds a structured JSON schema prompt and returns a reply plus focused board operations (create/edit/move/delete cards, rename columns). Operations are applied atomically in `storage.py`.

**Frontend state:** After any manual or AI-driven update, the frontend re-fetches the full board snapshot from the backend as the source of truth.

**Docker build:** Multi-stage — Node.js 22 compiles the frontend to static files, then Python 3.12 (`uv`) serves everything via FastAPI on port 8000.

## Color Scheme

- Accent Yellow: `#ecad0a`
- Blue Primary: `#209dd7`
- Purple Secondary: `#753991` (submit buttons, important actions)
- Dark Navy: `#032147` (main headings)
- Gray Text: `#888888`

## Coding Standards

- Keep it simple — no over-engineering, no unnecessary abstractions, no extra features
- No emojis, ever
- When hitting issues: identify root cause with evidence before fixing — do not guess
- Use latest idiomatic approaches for the stack
- `docs/PLAN.md` is the source of truth for implementation order and success criteria
