# Frontend Scope

This directory contains the current frontend-only MVP for the project management app.

## Current State

- Framework: Next.js App Router
- Language: TypeScript
- Styling: Tailwind CSS v4 plus CSS variables in `src/app/globals.css`
- Drag and drop: `@dnd-kit/core` and `@dnd-kit/sortable`
- Tests: Vitest for unit and component tests, Playwright for end-to-end tests
- Current behavior is API-backed and persistent through the FastAPI backend
- Production builds are exported as static files so FastAPI can serve them in the integrated app

## Entry Points

- `src/app/layout.tsx` sets fonts, metadata, and global styles
- `src/app/page.tsx` renders the main `KanbanBoard`
- `src/components/KanbanBoard.tsx` owns the main board state and drag-and-drop flow
- `src/components/AIChatSidebar.tsx` owns the sidebar chat UI and AI interaction flow
- `src/lib/kanban.ts` contains the board data model, demo seed data, and card movement helpers
- `src/lib/boardApi.ts` owns login, board, and AI chat API calls

## Current Features

- Renders a single-board Kanban UI with five columns
- Allows inline renaming of fixed columns
- Allows adding cards within a column
- Allows deleting cards
- Allows dragging cards within and across columns
- Allows chatting with the AI in a sidebar and applying AI-driven board updates
- Shows a polished visual design that already follows the project color palette

## Important Constraints

- Authentication is a lightweight client-managed token flow backed by `/api/auth/login` and `/api/auth/me`
- The sidebar depends on backend AI responses shaped as a reply plus focused board operations
- The frontend should treat backend board snapshots as the source of truth after both manual and AI-driven updates

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

- Refine the AI chat experience if future product requirements expand beyond the MVP
