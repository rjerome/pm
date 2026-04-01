# Frontend Scope

This directory contains the current frontend-only MVP for the project management app.

## Current State

- Framework: Next.js App Router
- Language: TypeScript
- Styling: Tailwind CSS v4 plus CSS variables in `src/app/globals.css`
- Drag and drop: `@dnd-kit/core` and `@dnd-kit/sortable`
- Tests: Vitest for unit and component tests, Playwright for end-to-end tests
- Current behavior is entirely client-side and in-memory
- Production builds are exported as static files so FastAPI can serve them in the integrated app

## Entry Points

- `src/app/layout.tsx` sets fonts, metadata, and global styles
- `src/app/page.tsx` renders the main `KanbanBoard`
- `src/components/KanbanBoard.tsx` owns the main board state and drag-and-drop flow
- `src/lib/kanban.ts` contains the board data model, demo seed data, and card movement helpers

## Current Features

- Renders a single-board Kanban UI with five columns
- Allows inline renaming of fixed columns
- Allows adding cards within a column
- Allows deleting cards
- Allows dragging cards within and across columns
- Shows a polished visual design that already follows the project color palette

## Important Constraints

- There is no backend integration yet
- Authentication is a lightweight client-managed token flow backed by `/api/auth/login` and `/api/auth/me`
- There is no persistence yet
- There is no AI sidebar yet
- The frontend currently assumes it owns all board state locally

## Test Setup

- `npm run test:unit` runs Vitest against `src/**/*.{test,spec}.{ts,tsx}`
- `npm run test:e2e` runs Playwright against a Next dev server on `127.0.0.1:3000`
- Existing coverage includes:
  - board utility tests in `src/lib/kanban.test.ts`
  - component behavior tests in `src/components/KanbanBoard.test.tsx`
  - browser-flow tests in `tests/kanban.spec.ts`

## Working Guidance

- Preserve the existing UI quality and current interaction patterns unless requirements force a change
- Treat `src/lib/kanban.ts` as the current frontend domain model until a shared backend contract replaces or refines it
- When integrating the backend, prefer adapting the existing board and tests instead of rewriting the frontend from scratch
- Keep the frontend simple: no extra state layers or abstractions without clear need
- Avoid build-time dependencies on external font downloads or other fragile network fetches

## Expected Future Work In This Directory

- Add login UI
- Replace in-memory board loading and saving with backend API calls
- Add AI chat sidebar UI
- Adjust build output as needed so FastAPI can serve the integrated frontend
