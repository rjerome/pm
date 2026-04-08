# Backend Scope

This directory contains the FastAPI backend for the Project Management MVP.

## Current State

- `app/main.py` contains the FastAPI app, auth endpoints, board routes, AI routes, and static frontend serving
- `app/config.py` holds shared backend constants and default paths
- `app/ai.py` contains the OpenRouter connectivity client, structured AI request building, and response parsing
- `app/dependencies.py` resolves auth and persistence dependencies
- `app/board_seed.py` owns the backend seed board data
- `app/models.py` defines request and response models for auth and board APIs
- `app/storage.py` owns the normalized SQLite schema, seeding, board assembly, focused mutations, and transactional AI operation application
- `tests/test_main.py` covers auth, placeholder fallback, database initialization, focused board mutations, AI connectivity, structured AI parsing, and AI-driven persistence safety
- The backend now proves the API path, auth path, persistence path, frontend hosting path, OpenRouter connectivity, and structured AI board updates

## Responsibility

- Own the API for login, board loading, board saving, and AI chat
- Own SQLite persistence
- Own OpenRouter integration, including the temporary part 8 connectivity route and the part 9 structured AI endpoint
- Serve the built frontend in the integrated Docker setup

## Working Guidance

- Keep the backend simple and boring
- Prefer a small application structure over early abstraction
- Persist the board in normalized SQLite tables, while assembling the current frontend board shape in backend code as needed
- Add tests as backend features are introduced
- The current auth model is intentionally lightweight: a hardcoded credential check and a frontend-managed bearer token
- Expand this file as modules and responsibilities become more concrete
