# Project Plan

## Working Assumptions

- Keep the architecture simple: Next.js remains the frontend app, FastAPI owns the backend API, and FastAPI serves the built frontend in the integrated Docker setup
- During development, separate frontend and backend dev servers are acceptable if they improve iteration speed and reduce coupling
- Authentication is a lightweight MVP flow: backend credential verification plus frontend-managed auth state, with no cookie or session system
- SQLite stores the board in normalized relational tables for boards, columns, and cards
- The AI may create, edit, move, and delete cards, and may rename columns
- Testing is required both in normal local development and in Docker-based integrated verification

## Part 1: Planning And Documentation

Goal: turn the repo instructions into an implementation-ready plan without changing product code.

Checklist
- [x] Revise the root `AGENTS.md` with the clarified MVP decisions
- [x] Expand this plan into concrete implementation phases, tests, and success criteria
- [x] Add `frontend/AGENTS.md` describing the existing frontend structure, current capabilities, and current test setup
- [x] Update placeholder `backend/AGENTS.md` and `scripts/AGENTS.md` once those areas have enough structure to document
- [x] Get explicit user approval on the revised plan before starting implementation work

Tests
- [x] No code changes required in this phase
- [x] Verify documentation is internally consistent and reflects the agreed decisions

Success Criteria
- [x] A future implementation pass can proceed phase by phase without major ambiguity
- [x] The user has approved the execution order and scope

## Part 2: Scaffolding

Goal: establish the backend, container, and script foundations before integrating the real frontend.

Checklist
- [x] Create the FastAPI application skeleton in `backend/`
- [x] Add Python dependency management using `uv`
- [x] Create a minimal Docker build that can run the backend locally
- [x] Create start and stop scripts for macOS, Windows, and Linux in `scripts/`
- [x] Serve a simple placeholder HTML page from FastAPI at `/`
- [x] Add at least one simple API route, such as a health or hello endpoint
- [x] Document how to start the app locally and in Docker with minimal README changes

Tests
- [x] Add backend tests for the health or hello route
- [x] Verify the backend starts locally outside Docker
- [x] Verify the container starts and serves both the placeholder page and API route

Success Criteria
- [x] A developer can start the app locally with the scripts
- [x] Visiting `/` returns backend-served HTML
- [x] Visiting the API test route returns a successful JSON response
- [x] The same basic flow works inside Docker

## Part 3: Serve The Existing Frontend

Goal: replace the placeholder page with the current Kanban frontend, still without persistence.

Checklist
- [x] Decide the simplest reliable build path for the current frontend so FastAPI can serve it in the integrated setup
- [x] Update frontend build configuration only as needed to support backend hosting
- [x] Wire the Docker image so the built frontend assets are served by FastAPI at `/`
- [x] Keep the existing Kanban demo behavior working
- [x] Document the frontend serving approach in the relevant `AGENTS.md` files if needed

Tests
- [x] Run the existing frontend unit tests and fix only real integration breakage
- [x] Run the existing Playwright tests against the appropriate local setup
- [x] Add or adjust an integration check proving FastAPI serves the built frontend
- [x] Verify the integrated flow in Docker

Success Criteria
- [x] The Kanban board loads from `/` through FastAPI
- [x] Existing demo interactions still work
- [x] Local and Docker verification both pass

## Part 4: MVP Login Experience

Goal: gate the board behind a simple login flow using the hardcoded credentials.

Checklist
- [x] Add a backend login endpoint that validates `user` / `password`
- [x] Decide and document the frontend auth-state storage approach
- [x] Show a login screen at `/` when the user is not authenticated
- [x] On successful login, show the Kanban board
- [x] Add a logout action that returns the app to the login state
- [x] Prevent protected backend routes from being used without the lightweight auth mechanism chosen for the MVP

Tests
- [x] Add backend tests for successful and failed login attempts
- [x] Add frontend tests for login form validation and logout
- [x] Add end-to-end coverage for failed login, successful login, refresh behavior, and logout
- [x] Verify the auth flow in Docker

Success Criteria
- [x] The board is not accessible from the normal UI until login succeeds
- [x] Only the hardcoded credentials are accepted
- [x] Logout reliably clears access and returns the user to the login screen

## Part 5: Database Modeling

Goal: define and document the simplest durable persistence model before wiring full CRUD.

Checklist
- [x] Design the SQLite schema for users, boards, columns, and cards
- [x] Normalize persistence so cards and columns can be queried and updated individually
- [x] Define how the database file location is configured for local and Docker use
- [x] Decide how the initial board is seeded for a user with no saved board
- [x] Document the schema and persistence rules in `docs/`
- [x] Get user sign-off on the database approach before building the full persistence layer

Tests
- [x] Add backend tests for database initialization
- [x] Add backend tests for creating a missing database automatically
- [x] Add backend tests for seeding or retrieving a default board for a new user

Success Criteria
- [x] The persistence design is documented and approved
- [x] The database can be created from scratch without manual setup
- [x] A new user path yields a valid seeded board state assembled from normalized rows

## Part 6: Backend Board API

Goal: provide the backend endpoints needed to load and save a user board.

Checklist
- [x] Implement database access for reading a board by user from normalized tables
- [x] Implement database access for focused column and card mutations
- [x] Add API routes for loading the current board snapshot and applying supported mutations
- [x] Validate mutation payloads before writing
- [x] Return useful error responses for invalid credentials, invalid board references, and stale versions
- [x] Keep writes transaction-based and row-focused instead of replacing the whole board

Tests
- [x] Add backend unit tests for read and write operations
- [x] Add backend API tests for valid and invalid board payloads
- [x] Add backend tests for persistence across app restarts where practical
- [x] Verify database creation and board persistence in Docker

Success Criteria
- [x] The backend can load a board snapshot and apply supported card and column mutations for the signed-in user
- [x] Invalid mutation payloads are rejected clearly
- [x] Persisted changes survive app restart

## Part 7: Frontend And Backend Integration

Goal: make the board persistent by having the frontend use the backend API instead of in-memory state only.

Checklist
- [ ] Add frontend API client helpers for login and board operations
- [ ] Load the board from the backend after login
- [ ] Save board changes through focused backend mutations for column renames, card edits, card moves, card creation, and card deletion
- [ ] Handle loading, saving, and error states without overcomplicating the UI
- [ ] Make sure the initial in-memory demo state is only used as a seed reference, not as the source of truth

Tests
- [ ] Update frontend unit tests where behavior changes from local-only to API-backed
- [ ] Add integration tests around fetching and saving board state
- [ ] Add end-to-end coverage proving persisted changes survive page reloads
- [ ] Verify the full flow in Docker

Success Criteria
- [ ] User changes persist after reload
- [ ] All core board actions remain functional
- [ ] The integrated app works both locally and in Docker

## Part 8: AI Connectivity

Goal: prove the backend can call OpenRouter successfully before introducing board mutation logic.

Checklist
- [ ] Add backend configuration for `OPENROUTER_API_KEY`
- [ ] Implement a minimal OpenRouter client using `openai/gpt-oss-120b`
- [ ] Add a simple internal or test route that performs a connectivity check
- [ ] Confirm the backend handles missing or invalid API keys clearly
- [ ] Keep the first AI verification narrow, such as a simple `2+2` prompt

Tests
- [ ] Add backend tests that mock the OpenRouter client
- [ ] Run a real connectivity check when credentials are available
- [ ] Verify the container can access the required environment configuration

Success Criteria
- [ ] The backend can successfully complete a real AI request
- [ ] Failure paths for missing configuration are understandable
- [ ] AI connectivity is proven before chat features depend on it

## Part 9: Structured AI Board Updates

Goal: let the backend send board context and conversation history to the AI and receive a structured reply plus an optional board update.

Checklist
- [ ] Define a structured output schema for AI responses
- [ ] Include the current board snapshot, the user message, and conversation history in the AI request
- [ ] Decide the simplest update contract for the MVP
- [ ] Prefer a structured list of board operations aligned to backend mutations over full-board replacement
- [ ] Validate any AI-returned board operations before saving them
- [ ] Apply and persist the returned board operations only when they are valid
- [ ] Return both the assistant reply and any board update metadata to the frontend

Tests
- [ ] Add backend tests for parsing valid structured outputs
- [ ] Add backend tests for invalid or partial AI responses
- [ ] Add backend tests proving valid AI board updates are persisted
- [ ] Add backend tests proving invalid AI board updates are rejected safely

Success Criteria
- [ ] The backend can turn a user message plus board context into a structured AI response
- [ ] Optional board operations are validated and persisted correctly
- [ ] Invalid AI output does not corrupt saved data

## Part 10: AI Sidebar UI

Goal: expose the AI workflow in the frontend and keep the board in sync with AI-driven changes.

Checklist
- [ ] Design and build a sidebar chat UI that fits the existing visual direction
- [ ] Add message history rendering and a composer
- [ ] Send user messages to the backend AI endpoint
- [ ] Show loading and error states clearly
- [ ] Apply AI-returned board updates to the UI automatically
- [ ] Refresh or reconcile frontend board state after AI mutations so the board and chat stay consistent
- [ ] Allow AI-driven card creation, editing, moving, deletion, and column renaming through the shared board update flow

Tests
- [ ] Add frontend component tests for the chat sidebar states
- [ ] Add integration tests for successful and failed AI interactions
- [ ] Add end-to-end coverage for AI-driven board changes appearing in the UI
- [ ] Verify the AI sidebar flow in Docker

Success Criteria
- [ ] The user can chat with the AI from the sidebar
- [ ] AI responses appear in the UI with usable feedback during loading and failure
- [ ] AI board changes are reflected on the board automatically

## Definition Of Done

- [ ] The app runs locally through the provided scripts
- [ ] The app runs in Docker
- [ ] Login works with the MVP credentials
- [ ] The board is persistent per user through SQLite
- [ ] The AI sidebar can respond and update the board
- [ ] Local and Docker verification steps are documented and pass
