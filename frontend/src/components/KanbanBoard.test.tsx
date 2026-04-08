import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { KanbanBoard } from "@/components/KanbanBoard";
import { initialData, type BoardData } from "@/lib/kanban";

const createBoardState = (): BoardData => JSON.parse(JSON.stringify(initialData));

const createResponse = (data: unknown, status = 200) => ({
  ok: status >= 200 && status < 300,
  status,
  json: async () => data,
});

describe("KanbanBoard", () => {
  beforeEach(() => {
    let board = createBoardState();
    let chatRequestCount = 0;

    vi.stubGlobal(
      "fetch",
      vi.fn(async (input: string | URL | Request, init?: RequestInit) => {
        const url = input.toString();
        const method = init?.method ?? "GET";

        if (url.endsWith("/api/board") && method === "GET") {
          return createResponse({ board });
        }

        if (url.endsWith("/api/columns/col-backlog") && method === "PATCH") {
          const payload = JSON.parse(init?.body as string) as {
            title: string;
            version: number;
          };
          board = {
            ...board,
            version: board.version + 1,
            columns: board.columns.map((column) =>
              column.id === "col-backlog"
                ? { ...column, title: payload.title, version: payload.version + 1 }
                : column
            ),
          };
          return createResponse({ board });
        }

        if (url.endsWith("/api/cards") && method === "POST") {
          const payload = JSON.parse(init?.body as string) as {
            columnId: string;
            title: string;
            details: string;
          };
          const id = "card-created";
          board = {
            ...board,
            version: board.version + 1,
            cards: {
              ...board.cards,
              [id]: {
                id,
                columnId: payload.columnId,
                title: payload.title,
                details: payload.details,
                sortOrder: 3000,
                version: 1,
              },
            },
            columns: board.columns.map((column) =>
              column.id === payload.columnId
                ? { ...column, cardIds: [...column.cardIds, id] }
                : column
            ),
          };
          return createResponse({ board }, 201);
        }

        if (url.endsWith("/api/cards/card-created") && method === "PATCH") {
          const payload = JSON.parse(init?.body as string) as {
            title: string;
            details: string;
          };
          const existingCard = board.cards["card-created"];
          board = {
            ...board,
            version: board.version + 1,
            cards: {
              ...board.cards,
              "card-created": {
                ...existingCard,
                title: payload.title,
                details: payload.details,
                version: existingCard.version + 1,
              },
            },
          };
          return createResponse({ board });
        }

        if (
          url.includes("/api/cards/card-created?version=") &&
          method === "DELETE"
        ) {
          const { ["card-created"]: _removed, ...restCards } = board.cards;
          board = {
            ...board,
            version: board.version + 1,
            cards: restCards,
            columns: board.columns.map((column) =>
              column.id === "col-backlog"
                ? {
                    ...column,
                    cardIds: column.cardIds.filter((cardId) => cardId !== "card-created"),
                  }
                : column
            ),
          };
          return createResponse({ board });
        }

        if (url.endsWith("/api/ai/chat") && method === "POST") {
          const payload = JSON.parse(init?.body as string) as {
            message: string;
            history: Array<{ role: "user" | "assistant"; content: string }>;
          };

          if (payload.message.includes("fail")) {
            return createResponse(
              { detail: "AI returned invalid board operations: Column not found" },
              502
            );
          }

          if (chatRequestCount === 1) {
            expect(payload.history).toEqual([
              { role: "user", content: "Rename backlog to Ideas and add a review card." },
              {
                role: "assistant",
                content: "I renamed the column and added the review card.",
              },
            ]);
          }

          chatRequestCount += 1;

          board = {
            ...board,
            version: board.version + 2,
            cards: {
              ...board.cards,
              "card-ai": {
                id: "card-ai",
                columnId: "col-review",
                title: "Review launch checklist",
                details: "AI-created follow-up.",
                sortOrder: 1500,
                version: 1,
              },
            },
            columns: board.columns.map((column) =>
              column.id === "col-review"
                ? { ...column, cardIds: ["card-6", "card-ai"] }
                : column.id === "col-backlog"
                  ? { ...column, title: "Ideas", version: column.version + 1 }
                  : column
            ),
          };

          return createResponse({
            model: "openai/gpt-oss-120b",
            reply: "I renamed the column and added the review card.",
            operations: [
              {
                type: "rename_column",
                columnId: "col-backlog",
                title: "Ideas",
              },
              {
                type: "create_card",
                columnId: "col-review",
                title: "Review launch checklist",
                details: "AI-created follow-up.",
                beforeCardId: null,
                afterCardId: "card-6",
              },
            ],
            boardUpdated: true,
            board,
          });
        }

        throw new Error(`Unhandled fetch call: ${method} ${url}`);
      })
    );
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("loads the board from the backend", async () => {
    render(<KanbanBoard token="pm-mvp-user-token" />);

    expect(await screen.findByRole("heading", { name: "Kanban Studio" })).toBeInTheDocument();
    expect(screen.getAllByTestId(/column-/i)).toHaveLength(5);
  });

  it("renames a column through the backend", async () => {
    render(<KanbanBoard token="pm-mvp-user-token" />);

    const column = await screen.findByTestId("column-col-backlog");
    const input = within(column).getByLabelText("Column title");
    await userEvent.clear(input);
    await userEvent.type(input, "Ideas");
    input.blur();

    expect(await within(column).findByDisplayValue("Ideas")).toBeInTheDocument();
  });

  it("adds, edits, and removes a card through the backend", async () => {
    render(<KanbanBoard token="pm-mvp-user-token" />);

    const column = await screen.findByTestId("column-col-backlog");
    await userEvent.click(within(column).getByRole("button", { name: /add a card/i }));
    await userEvent.type(within(column).getByPlaceholderText(/card title/i), "New card");
    await userEvent.type(within(column).getByPlaceholderText(/details/i), "Notes");
    await userEvent.click(within(column).getByRole("button", { name: /add card/i }));

    expect(await within(column).findByText("New card")).toBeInTheDocument();

    const card = within(column).getByTestId("card-card-created");
    await userEvent.click(within(card).getByLabelText(/edit new card/i));
    await userEvent.clear(within(card).getByLabelText(/edit new card title/i));
    await userEvent.type(within(card).getByLabelText(/edit new card title/i), "Updated card");
    await userEvent.clear(within(card).getByLabelText(/edit new card details/i));
    await userEvent.type(
      within(card).getByLabelText(/edit new card details/i),
      "Updated notes"
    );
    await userEvent.click(within(card).getByRole("button", { name: /save/i }));

    expect(await within(column).findByText("Updated card")).toBeInTheDocument();

    await userEvent.click(
      within(column).getByRole("button", { name: /delete updated card/i })
    );

    expect(within(column).queryByText("Updated card")).not.toBeInTheDocument();
  });

  it("applies AI-driven board updates from the sidebar", async () => {
    render(<KanbanBoard token="pm-mvp-user-token" />);

    expect(await screen.findByRole("heading", { name: "Kanban Studio" })).toBeInTheDocument();

    await userEvent.type(
      screen.getByLabelText(/ask the ai assistant/i),
      "Rename backlog to Ideas and add a review card."
    );
    await userEvent.click(screen.getByRole("button", { name: /^send$/i }));

    expect(await screen.findByText("I renamed the column and added the review card.")).toBeInTheDocument();
    expect(await screen.findByDisplayValue("Ideas")).toBeInTheDocument();

    const reviewColumn = screen.getByTestId("column-col-review");
    expect(await within(reviewColumn).findByText("Review launch checklist")).toBeInTheDocument();
    expect(await screen.findByText(/board updated/i)).toBeInTheDocument();

    await userEvent.type(screen.getByLabelText(/ask the ai assistant/i), "Do that again");
    await userEvent.click(screen.getByRole("button", { name: /^send$/i }));

    expect(await screen.findAllByText("I renamed the column and added the review card.")).toHaveLength(2);
  });

  it("shows an AI error without changing the board", async () => {
    render(<KanbanBoard token="pm-mvp-user-token" />);

    expect(await screen.findByRole("heading", { name: "Kanban Studio" })).toBeInTheDocument();

    await userEvent.type(screen.getByLabelText(/ask the ai assistant/i), "fail this request");
    await userEvent.click(screen.getByRole("button", { name: /^send$/i }));

    expect(
      await screen.findByText("AI returned invalid board operations: Column not found")
    ).toBeInTheDocument();
    expect(screen.getByDisplayValue("Backlog")).toBeInTheDocument();
    expect(screen.queryByText("Review launch checklist")).not.toBeInTheDocument();
  });
});
