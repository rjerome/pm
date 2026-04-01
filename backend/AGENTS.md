# Backend Scope

This directory contains the FastAPI backend for the Project Management MVP.

## Current State

- `app/main.py` contains the FastAPI app, `/api/health`, and the logic that serves the built frontend export when present
- `app/main.py` also contains the MVP auth endpoints for login and token verification
- `tests/test_main.py` covers the health route, auth endpoints, placeholder fallback, and static frontend serving behavior
- The current backend is intentionally small and proves the API path, auth path, and frontend hosting path work

## Responsibility

- Own the API for login, board loading, board saving, and AI chat
- Own SQLite persistence
- Own OpenRouter integration
- Serve the built frontend in the integrated Docker setup

## Working Guidance

- Keep the backend simple and boring
- Prefer a small application structure over early abstraction
- Persist one full board JSON document per user
- Add tests as backend features are introduced
- The current auth model is intentionally lightweight: a hardcoded credential check and a frontend-managed bearer token
- Expand this file as modules and responsibilities become more concrete
