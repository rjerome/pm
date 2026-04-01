from typing import Dict, List


SEED_COLUMNS: List[dict] = [
    {
        "id": "col-backlog",
        "slot_key": "backlog",
        "title": "Backlog",
        "position": 0,
    },
    {
        "id": "col-discovery",
        "slot_key": "discovery",
        "title": "Discovery",
        "position": 1,
    },
    {
        "id": "col-progress",
        "slot_key": "progress",
        "title": "In Progress",
        "position": 2,
    },
    {
        "id": "col-review",
        "slot_key": "review",
        "title": "Review",
        "position": 3,
    },
    {
        "id": "col-done",
        "slot_key": "done",
        "title": "Done",
        "position": 4,
    },
]

SEED_CARDS: List[dict] = [
    {
        "id": "card-1",
        "column_id": "col-backlog",
        "title": "Align roadmap themes",
        "details": "Draft quarterly themes with impact statements and metrics.",
        "sort_order": 1000.0,
    },
    {
        "id": "card-2",
        "column_id": "col-backlog",
        "title": "Gather customer signals",
        "details": "Review support tags, sales notes, and churn feedback.",
        "sort_order": 2000.0,
    },
    {
        "id": "card-3",
        "column_id": "col-discovery",
        "title": "Prototype analytics view",
        "details": "Sketch initial dashboard layout and key drill-downs.",
        "sort_order": 1000.0,
    },
    {
        "id": "card-4",
        "column_id": "col-progress",
        "title": "Refine status language",
        "details": "Standardize column labels and tone across the board.",
        "sort_order": 1000.0,
    },
    {
        "id": "card-5",
        "column_id": "col-progress",
        "title": "Design card layout",
        "details": "Add hierarchy and spacing for scanning dense lists.",
        "sort_order": 2000.0,
    },
    {
        "id": "card-6",
        "column_id": "col-review",
        "title": "QA micro-interactions",
        "details": "Verify hover, focus, and loading states.",
        "sort_order": 1000.0,
    },
    {
        "id": "card-7",
        "column_id": "col-done",
        "title": "Ship marketing page",
        "details": "Final copy approved and asset pack delivered.",
        "sort_order": 1000.0,
    },
    {
        "id": "card-8",
        "column_id": "col-done",
        "title": "Close onboarding sprint",
        "details": "Document release notes and share internally.",
        "sort_order": 2000.0,
    },
]


def seed_board_snapshot() -> Dict[str, object]:
    columns = []
    cards_by_id = {}

    for column in SEED_COLUMNS:
        card_ids = [card["id"] for card in SEED_CARDS if card["column_id"] == column["id"]]
        columns.append(
            {
                "id": column["id"],
                "slotKey": column["slot_key"],
                "title": column["title"],
                "position": column["position"],
                "version": 1,
                "cardIds": card_ids,
            }
        )

    for card in SEED_CARDS:
        cards_by_id[card["id"]] = {
            "id": card["id"],
            "columnId": card["column_id"],
            "title": card["title"],
            "details": card["details"],
            "sortOrder": card["sort_order"],
            "version": 1,
        }

    return {
        "version": 1,
        "columns": columns,
        "cards": cards_by_id,
    }
