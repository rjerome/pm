# Database Design

## Goal

Keep persistence clean, queryable, and safe for partial updates while still staying simple enough for the MVP.

The current decision is:
- use SQLite
- create the database automatically if it does not exist
- persist boards in normalized relational tables
- make individual cards and columns easy to query
- support partial updates without replacing the whole board on every change
- keep authentication separate from database-backed credential storage for now

## Why This Structure

The persistence layer should be optimized for the operations we know we need:
- list a board with its columns and cards
- query an individual card
- rename a single column
- create, edit, move, or delete one card
- later let the AI perform focused mutations instead of broad board rewrites

This normalized structure is a good fit because it keeps:
- card-level queries straightforward
- partial updates small and targeted
- ordering logic explicit
- concurrent edits easier to reason about
- future AI-driven mutations aligned with real backend operations

## Proposed SQLite Schema

Use four tables:
- `users`
- `boards`
- `columns`
- `cards`

This keeps the model normalized without adding unnecessary indirection.

### `users`

Purpose:
- represent users in the database
- support future multi-user behavior even though MVP auth is still hardcoded

Schema:

```sql
CREATE TABLE IF NOT EXISTS users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT NOT NULL UNIQUE,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

Notes:
- `username` is the stable lookup key for the MVP
- no password column is needed yet because credentials remain hardcoded in backend logic

### `boards`

Purpose:
- represent the single board owned by a user
- provide a stable row for metadata and board-level versioning

Schema:

```sql
CREATE TABLE IF NOT EXISTS boards (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL UNIQUE,
  name TEXT NOT NULL DEFAULT 'Kanban Board',
  version INTEGER NOT NULL DEFAULT 1,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
```

Notes:
- `user_id` is unique because the MVP allows one board per user
- `version` supports optimistic concurrency at the board level when useful

### `columns`

Purpose:
- store the board columns as first-class rows
- allow renaming without losing the fixed-column identity

Schema:

```sql
CREATE TABLE IF NOT EXISTS columns (
  id TEXT PRIMARY KEY,
  board_id INTEGER NOT NULL,
  slot_key TEXT NOT NULL,
  title TEXT NOT NULL,
  position INTEGER NOT NULL,
  version INTEGER NOT NULL DEFAULT 1,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (board_id) REFERENCES boards(id) ON DELETE CASCADE,
  UNIQUE (board_id, slot_key),
  UNIQUE (board_id, position)
);
```

Notes:
- `id` can stay aligned with the current frontend IDs such as `col-backlog`
- `slot_key` preserves the fixed-column identity independently from the display title
- `title` is user-editable
- `position` preserves board column order
- `version` supports optimistic locking for column rename operations

Recommended slot keys:
- `backlog`
- `discovery`
- `progress`
- `review`
- `done`

### `cards`

Purpose:
- store cards as first-class rows
- allow targeted queries and partial updates

Schema:

```sql
CREATE TABLE IF NOT EXISTS cards (
  id TEXT PRIMARY KEY,
  board_id INTEGER NOT NULL,
  column_id TEXT NOT NULL,
  title TEXT NOT NULL,
  details TEXT NOT NULL,
  sort_order REAL NOT NULL,
  version INTEGER NOT NULL DEFAULT 1,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (board_id) REFERENCES boards(id) ON DELETE CASCADE,
  FOREIGN KEY (column_id) REFERENCES columns(id) ON DELETE CASCADE
);
```

Recommended indexes:

```sql
CREATE INDEX IF NOT EXISTS idx_cards_board_id ON cards(board_id);
CREATE INDEX IF NOT EXISTS idx_cards_column_sort ON cards(column_id, sort_order);
CREATE INDEX IF NOT EXISTS idx_cards_board_updated ON cards(board_id, updated_at);
```

Notes:
- `id` can stay aligned with the current frontend IDs such as `card-1`
- `column_id` makes filtering cards by column straightforward
- `sort_order` preserves card ordering inside a column
- `version` supports optimistic locking for card updates

## Ordering Strategy

Use a sparse numeric `sort_order` for cards.

Recommended convention:
- seed cards with gaps such as `1000`, `2000`, `3000`
- when moving a card between two neighbors, choose a midpoint value
- when moving to the top or bottom, choose a value before or after the nearest neighbor
- if a column becomes too dense over time, rebalance that column in one transaction

Why this is a good MVP fit:
- moving one card usually updates one row instead of renumbering many rows
- partial updates stay small
- concurrent changes to different cards conflict less often
- querying remains simple with `ORDER BY sort_order`

Column order can remain a simple integer `position` because columns are fixed and rarely reordered.

## Concurrency Model

Use optimistic concurrency with row versions.

Recommended rules:
- `boards.version` increments on board-wide changes when needed
- `columns.version` increments on column rename operations
- `cards.version` increments on card create, edit, move, or delete operations affecting that row
- mutation requests should carry the expected `version` for the row being changed once the API supports that

Behavior:
- if the stored version differs from the expected version, reject the mutation with a conflict response
- for multi-row changes such as moving a card between columns, wrap the operation in a transaction

This keeps partial updates elegant without introducing locking complexity too early.

## Data Lifecycle

### Startup / First Database Access

The backend should:
- resolve the configured database path
- create the parent directory if needed
- open the SQLite database, which creates the file automatically if missing
- run idempotent schema creation statements

### Default User

For the MVP, the backend login already accepts:
- username: `user`
- password: `password`

Persistence should use the same username.

Expected behavior:
- if `user` does not exist in `users`, create it
- if that user has no board, create the board and seed its columns and cards

### Default Board Seeding

The seed board should match the current demo board structure from the frontend.

Recommended approach:
- copy the current demo seed into backend-owned seed data during Part 6
- insert one `boards` row
- insert the five fixed `columns` rows
- insert the initial `cards` rows with `column_id` and `sort_order`
- do not read seed data from frontend files at runtime

Reason:
- the backend should own persistence rules
- seeding must remain explicit and testable

## File Location

Use one explicit environment variable:
- `PM_DB_PATH`

Recommended defaults:
- local non-Docker development: `/Users/richardjerome/projects/pm/data/pm.sqlite3`
- Docker container: `/app/data/pm.sqlite3`

Behavior:
- if `PM_DB_PATH` is set, use it
- otherwise use a sane app-relative default

Implementation preference for the MVP:
- create a `data/` directory under the app root
- keep the SQLite file there
- later, mount that location in Docker if persistence across container recreation is required

## Read Model

The frontend can still consume the current board-shaped object, but the backend should assemble it from normalized rows.

Recommended read flow:
- fetch the board row for the user
- fetch columns ordered by `position`
- fetch cards ordered by `column_id, sort_order`
- assemble the current frontend shape in backend code

That means we keep the current frontend contract easy while using better persistence underneath.

## Write Model

The backend should favor focused mutations over broad snapshot rewrites.

Recommended operations for Part 6 and Part 7:
- `get_or_create_user(username)`
- `get_or_seed_board(username)`
- `rename_column(column_id, title, expected_version)`
- `create_card(column_id, title, details, after_card_id | before_card_id | at_end)`
- `update_card(card_id, title, details, expected_version)`
- `move_card(card_id, target_column_id, before_card_id | after_card_id, expected_version)`
- `delete_card(card_id, expected_version)`

Each mutation should:
- run in a transaction
- update only the rows it needs
- update `updated_at`
- increment row versions where appropriate

## Validation Strategy

Validation should happen in application code, not through complex SQL-only rules.

That means:
- validate API payloads in FastAPI
- validate titles, details, IDs, and mutation intent before writing
- ensure referenced board, column, and card rows exist
- reject stale versions cleanly once optimistic concurrency is active

## Why This Design Fits The MVP

It stays reasonably small while solving the right problems:
- easy card querying
- targeted writes
- cleaner future AI actions
- better support for partial concurrent updates
- no need to rewrite the current frontend board shape immediately

It is normalized enough to support clean querying and partial updates, while still staying simple enough for SQLite and a local MVP.

## Expected Tests For Implementation

These tests should be added when Part 6 introduces the persistence layer:
- database file is created automatically if missing
- schema creation is idempotent
- missing user is created automatically on first board access
- missing board, columns, and cards are seeded automatically for a valid user
- board reads assemble the expected frontend shape from normalized rows
- querying an individual card by ID works directly
- column rename updates only the target column row
- card move updates the expected row fields and ordering
- stale versions are rejected when optimistic concurrency is enforced
- saved data persists across app restart

## Approval Point

This document proposes the persistence model to implement next.

If approved, Part 6 should build exactly this:
- `users`, `boards`, `columns`, and `cards` tables
- normalized card and column storage
- `sort_order`-based card ordering
- optimistic concurrency via row versions
- backend-assembled board snapshots for the current frontend
- configurable SQLite path via `PM_DB_PATH`
