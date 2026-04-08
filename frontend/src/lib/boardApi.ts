import type { BoardData, Card } from "@/lib/kanban";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "";
const AI_CHAT_TIMEOUT_MS = 45_000;

const createAuthHeaders = (token: string, includeJson = false) => ({
  Authorization: `Bearer ${token}`,
  ...(includeJson ? { "Content-Type": "application/json" } : {}),
});

const getErrorMessage = async (response: Response) => {
  try {
    const payload = (await response.json()) as { detail?: string };
    return payload.detail ?? "Request failed";
  } catch {
    return "Request failed";
  }
};

const readBoardResponse = async (response: Response): Promise<BoardData> => {
  if (!response.ok) {
    throw new Error(await getErrorMessage(response));
  }

  const payload = (await response.json()) as { board: BoardData };
  return payload.board;
};

export type AIChatHistoryMessage = {
  role: "user" | "assistant";
  content: string;
};

export type AIChatOperation =
  | {
      type: "rename_column";
      columnId: string;
      title: string;
    }
  | {
      type: "create_card";
      columnId: string;
      title: string;
      details: string;
      beforeCardId?: string | null;
      afterCardId?: string | null;
    }
  | {
      type: "update_card";
      cardId: string;
      title: string;
      details: string;
    }
  | {
      type: "move_card";
      cardId: string;
      targetColumnId: string;
      beforeCardId?: string | null;
      afterCardId?: string | null;
    }
  | {
      type: "delete_card";
      cardId: string;
    };

export type AIChatResult = {
  model: string;
  reply: string;
  operations: AIChatOperation[];
  boardUpdated: boolean;
  board: BoardData;
};

export const fetchBoard = async (token: string): Promise<BoardData> => {
  const response = await fetch(`${API_BASE_URL}/api/board`, {
    headers: createAuthHeaders(token),
  });

  return readBoardResponse(response);
};

export const renameColumn = async (
  token: string,
  columnId: string,
  title: string,
  version: number
): Promise<BoardData> => {
  const response = await fetch(`${API_BASE_URL}/api/columns/${columnId}`, {
    method: "PATCH",
    headers: createAuthHeaders(token, true),
    body: JSON.stringify({ title, version }),
  });

  return readBoardResponse(response);
};

export const createCard = async (
  token: string,
  input: {
    columnId: string;
    title: string;
    details: string;
    beforeCardId?: string;
    afterCardId?: string;
  }
): Promise<BoardData> => {
  const response = await fetch(`${API_BASE_URL}/api/cards`, {
    method: "POST",
    headers: createAuthHeaders(token, true),
    body: JSON.stringify(input),
  });

  return readBoardResponse(response);
};

export const updateCard = async (
  token: string,
  cardId: string,
  input: {
    title: string;
    details: string;
    version: number;
  }
): Promise<BoardData> => {
  const response = await fetch(`${API_BASE_URL}/api/cards/${cardId}`, {
    method: "PATCH",
    headers: createAuthHeaders(token, true),
    body: JSON.stringify(input),
  });

  return readBoardResponse(response);
};

export const moveCard = async (
  token: string,
  cardId: string,
  input: {
    targetColumnId: string;
    version: number;
    beforeCardId?: string;
    afterCardId?: string;
  }
): Promise<BoardData> => {
  const response = await fetch(`${API_BASE_URL}/api/cards/${cardId}/move`, {
    method: "POST",
    headers: createAuthHeaders(token, true),
    body: JSON.stringify(input),
  });

  return readBoardResponse(response);
};

export const deleteCard = async (
  token: string,
  card: Pick<Card, "id" | "version">
): Promise<BoardData> => {
  const response = await fetch(
    `${API_BASE_URL}/api/cards/${card.id}?version=${card.version}`,
    {
      method: "DELETE",
      headers: createAuthHeaders(token),
    }
  );

  return readBoardResponse(response);
};

export const sendAIChatMessage = async (
  token: string,
  input: {
    message: string;
    history: AIChatHistoryMessage[];
  }
): Promise<AIChatResult> => {
  const controller = new AbortController();
  const timeoutId = window.setTimeout(() => {
    controller.abort();
  }, AI_CHAT_TIMEOUT_MS);

  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}/api/ai/chat`, {
      method: "POST",
      headers: createAuthHeaders(token, true),
      body: JSON.stringify(input),
      signal: controller.signal,
    });
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError") {
      throw new Error("The AI assistant took too long to respond. Please try again.");
    }
    throw error;
  } finally {
    window.clearTimeout(timeoutId);
  }

  if (!response.ok) {
    throw new Error(await getErrorMessage(response));
  }

  return (await response.json()) as AIChatResult;
};
