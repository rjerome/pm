# The Project Management MVP web app

## Business Requirements

This project is building a Project Management App. Key features:
- A user can sign in
- When signed in, the user sees a Kanban board representing their project
- The Kanban board has fixed columns that can be renamed
- The cards on the Kanban board can be moved with drag and drop, and edited
- There is an AI chat feature in a sidebar; the AI is able to create / edit / move one or more cards

## Limitations

- For the MVP, there will only be a user sign in (hardcoded to `user` and `password`) but the database will support multiple users in future.
- For the MVP, there will only be 1 Kanban board per signed in user.
- For the MVP, this will run locally in Docker.

## Technical Decisions

- Next.js frontend in `frontend/`
- Python FastAPI backend in `backend/`
- FastAPI serves the built frontend at `/` in the integrated Docker setup
- During local development, separate frontend and backend dev servers are acceptable if that keeps the workflow simpler and more robust
- Everything is packaged into a Docker container
- Use `uv` as the package manager for Python in the Docker container
- Use OpenRouter for the AI calls. `OPENROUTER_API_KEY` is in `.env` in the project root
- Use `openai/gpt-oss-120b` as the model
- Use SQLite locally, creating the database automatically if it does not exist
- Persist the entire board as one JSON document per user
- Start and stop server scripts for Mac, Windows, and Linux in `scripts/`

## MVP Clarifications

- Authentication is intentionally lightweight for the MVP: the backend verifies the hardcoded credentials, and the frontend manages logged-in state without introducing cookie or session infrastructure
- The AI is allowed to create, edit, move, and delete cards
- The AI is also allowed to rename columns
- The app should be tested both outside Docker during development and inside Docker as part of integrated verification

## Starting Point

A working MVP of the frontend has been built and is already in frontend. This is not yet designed for the Docker setup. It's a pure frontend-only demo.

## Color Scheme

- Accent Yellow: `#ecad0a` - accent lines, highlights
- Blue Primary: `#209dd7` - links, key sections
- Purple Secondary: `#753991` - submit buttons, important actions
- Dark Navy: `#032147` - main headings
- Gray Text: `#888888` - supporting text, labels

## Coding standards

1. Use latest versions of libraries and idiomatic approaches as of today
2. Keep it simple - NEVER over-engineer, ALWAYS simplify, NO unnecessary defensive programming. No extra features - focus on simplicity.
3. Be concise. Keep README minimal. IMPORTANT: no emojis ever
4. When hitting issues, always identify root cause before trying a fix. Do not guess. Prove with evidence, then fix the root cause.

## Execution Notes

- `docs/PLAN.md` is the source of truth for execution order, checkpoints, tests, and success criteria
- Update scoped `AGENTS.md` files inside subdirectories when their responsibilities become concrete
- Treat the existing frontend as a real starting point: preserve useful code and tests rather than rebuilding it without evidence

## Working documentation

All documents for planning and executing this project will be in the docs/ directory.
Please review the docs/PLAN.md document before proceeding.
