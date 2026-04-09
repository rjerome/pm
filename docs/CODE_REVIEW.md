# Code Review

Reviewed against commit `09ecb90` (Step 10 Complete). All 10 implementation phases are complete. This is a single-user MVP running locally in Docker.

Intentional MVP simplifications (hardcoded credentials, single user, SQLite, no HTTPS) are not flagged unless they introduce a real risk even at MVP scope.

---

## High

### 1. Auth header comparison rejects valid Bearer tokens

**File:** `backend/app/dependencies.py:29-30`

```python
expected_value = f"Bearer {AUTH_TOKEN}"
if authorization != expected_value:
```

The comparison is case-sensitive on the scheme prefix. RFC 6750 requires clients to send `Bearer` (capitalised), which all real clients do, but any client or test that sends `bearer` or `BEARER` is silently rejected with a 401 that is hard to diagnose. The fix is a two-part split:

```python
parts = (authorization or "").split(None, 1)
if len(parts) != 2 or parts[0].lower() != "bearer" or parts[1] != AUTH_TOKEN:
    raise HTTPException(status_code=401, detail="Unauthorized")
```

---

### 2. `sort_order` floating-point convergence is unbounded

**File:** `backend/app/storage.py` — `_resolve_sort_order`

Cards moved between neighbours use the midpoint `(a + b) / 2`. After enough moves between the same two cards, the gap shrinks below IEEE 754 double precision (~2⁻⁵²) and the two values become indistinguishable, making further ordering impossible. The current seed gap of `1000` units gives roughly 50 bisections before values are within 0.001 of each other — reachable in a busy board.

Add a minimum-gap check and rebalance the column when triggered:

```python
MIN_GAP = 1.0
if abs(after_order - before_order) < MIN_GAP:
    self._rebalance_column(connection, board_id, target_column_id)
    # retry sort_order resolution after rebalance
```

A `_rebalance_column` helper that reassigns evenly-spaced integers (1000, 2000, …) to all cards in the column inside the same transaction is sufficient.

---

### 3. Delete button has no in-flight guard

**File:** `frontend/src/components/KanbanCard.tsx:167`

```typescript
void onDelete(card.id);
```

The save button (`isSaving` state) is protected against double-submit, but the delete button has no equivalent guard. A double-click or slow network can send two DELETE requests for the same card. The second will 404 silently, but it creates noise and could interfere with concurrent AI operations on the same card.

Add a local `isDeleting` state mirroring the existing `isSaving` pattern and `disabled={isDeleting}` on the button.

---

## Medium

### 4. `apply_ai_operations` does not validate all operations before executing any

**File:** `backend/app/storage.py:236-348`

The method iterates over operations and executes them one at a time, committing at the end. The SQLite context manager (`with self.connect()`) does roll back automatically on an uncaught exception, so partial persistence is not currently possible. However, a validation failure (e.g. unknown `operation_type` on the last item) raises an `HTTPException` that propagates out of the `with` block and triggers rollback — silently discarding work done by the earlier operations in the batch.

This is correct behaviour, but it means the AI can craft a batch where 4 of 5 operations are valid and the whole batch is rejected. Pre-validate all operations before executing any:

```python
# Pass 1: validate
for operation in operations:
    if operation["type"] not in SUPPORTED_OPERATION_TYPES:
        raise HTTPException(400, f"Unsupported operation: {operation['type']}")
    # ... existence checks ...

# Pass 2: execute
for operation in operations:
    ...
```

---

### 5. Seed data is duplicated between frontend and backend

**Files:** `backend/app/board_seed.py` and `frontend/src/lib/kanban.ts` (`initialData`)

The same five columns and initial cards are defined independently in both places. The frontend `initialData` is used only as a fallback if the board API fails to load — but if the backend seed changes (e.g. column IDs or card content), the frontend fallback diverges silently. Currently `initialData` in `kanban.ts` also appears in Vitest component tests as the assumed starting state.

At minimum, add a comment in `kanban.ts` making the dependency explicit. A cleaner fix is for the frontend to have no fallback board state and instead show an error on load failure, making `initialData` and its duplication unnecessary.

---

### 6. `withRequestTimeout` leaves dangling promises on timeout

**File:** `frontend/src/components/AIChatSidebar.tsx:37-53`

When the 45-second timeout fires, the original `sendAIChatMessage` promise keeps running in the background. The `activeRequestIdRef` guard correctly prevents the stale response from updating UI state, but the fetch is never aborted — it holds an open HTTP connection and will eventually call the backend's `/api/ai/chat` endpoint to completion, consuming OpenRouter credits and backend resources.

`boardApi.ts` already uses `AbortController` in other call sites. Pass a signal through `sendAIChatMessage` and abort it when the timeout fires:

```typescript
const controller = new AbortController();
const timeoutId = window.setTimeout(() => controller.abort(), UI_TIMEOUT_MS);
sendAIChatMessage(token, board, messages, { signal: controller.signal })
  .finally(() => window.clearTimeout(timeoutId));
```

---

### 7. Unused `username` parameter uses `del` rather than conventional underscore

**File:** `backend/app/main.py:163-166`

```python
def run_ai_connectivity_check(
    username: str = Depends(require_username),
) -> AIConnectivityCheckResponse:
    del username
```

`del username` works but is non-idiomatic Python. FastAPI and type checkers accept `_: str = Depends(...)` for dependency-injection-only parameters:

```python
def run_ai_connectivity_check(
    _: str = Depends(require_username),
) -> AIConnectivityCheckResponse:
```

---

## Low

### 8. Split `typing` import in `models.py`

**File:** `backend/app/models.py:1-2`

```python
from typing import Annotated, Dict, List, Optional, Union
from typing import Literal
```

`Literal` belongs on the first line.

---

### 9. Magic numbers in `config.py` lack rationale

**File:** `backend/app/config.py`

`OPENROUTER_TIMEOUT_SECONDS = 30` and `OPENROUTER_MAX_RETRIES = 2` are unexplained. If AI latency increases or retries cause issues, future developers have no basis for adjusting these. Add a one-line comment per constant explaining the trade-off.

---

### 10. `filter(Boolean)` silently drops missing cards

**File:** `frontend/src/components/KanbanBoard.tsx`

```typescript
cards={column.cardIds.map((cardId) => board.cards[cardId]).filter(Boolean)}
```

A card ID in `cardIds` with no matching entry in `board.cards` is silently dropped. This would hide a backend desync bug entirely. A `console.warn` on the missing case would surface the problem during development without changing production behaviour.

---

### 11. Keyboard shortcuts in column title editing are undiscoverable

**File:** `frontend/src/components/KanbanColumn.tsx`

`Enter` commits a column rename; `Escape` reverts it. Neither is documented in the UI. Users who rename a column by clicking will not know Escape exists. Adding `title="Press Enter to save, Escape to cancel"` on the input is a one-line fix.

---

### 12. Token stored in localStorage without expiry comment

**File:** `frontend/src/components/HomeScreen.tsx`

The bearer token has no expiry and is stored in localStorage. This is acceptable for the MVP (single hardcoded user, local deployment), but the code has no comment marking it as intentional and temporary. Add a comment so future contributors don't assume the pattern is production-ready.

---

## Positive observations

- **Transaction safety:** `BoardStore.connect()` as a context manager uses SQLite's built-in rollback-on-exception, so all mutations are atomically safe even in `apply_ai_operations`.
- **Test breadth:** 22 backend tests, 18 frontend unit/component tests, and 8 e2e Playwright tests cover all core paths including auth, persistence, AI parsing, and board mutation.
- **Version-based optimistic locking:** Implemented consistently on cards and columns, preventing silent concurrent overwrites.
- **AI operation atomicity:** All AI-driven board operations commit in a single SQLite transaction with automatic rollback on any failure.
- **Type safety:** Full TypeScript strict mode on frontend; Pydantic with `model_validator` on backend. Input validation is thorough.
- **Drag-and-drop rollback:** Frontend correctly reverts to pre-drag state on a failed save, keeping UI and backend in sync.

---

## Action summary

| # | Severity | File | Action |
|---|----------|------|--------|
| 1 | High | `dependencies.py` | Case-insensitive Bearer token parsing |
| 2 | High | `storage.py` | Add `_rebalance_column` triggered by min-gap check |
| 3 | High | `KanbanCard.tsx` | Add `isDeleting` guard on delete button |
| 4 | Medium | `storage.py` | Validate all AI operations before executing any |
| 5 | Medium | `board_seed.py` / `kanban.ts` | Remove frontend `initialData` fallback or add explicit cross-reference comment |
| 6 | Medium | `AIChatSidebar.tsx` | Use `AbortController` to cancel in-flight fetch on timeout |
| 7 | Medium | `main.py` | Replace `del username` with `_: str = Depends(...)` |
| 8 | Low | `models.py` | Merge split `typing` imports |
| 9 | Low | `config.py` | Add rationale comments on timeout and retry constants |
| 10 | Low | `KanbanBoard.tsx` | `console.warn` on missing card ID instead of silent drop |
| 11 | Low | `KanbanColumn.tsx` | Add `title` tooltip on rename input for keyboard shortcuts |
| 12 | Low | `HomeScreen.tsx` | Add comment marking localStorage token as intentional MVP shortcut |
