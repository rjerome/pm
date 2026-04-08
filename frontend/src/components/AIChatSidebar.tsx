"use client";

import { FormEvent, useEffect, useMemo, useRef, useState } from "react";
import type { BoardData } from "@/lib/kanban";
import {
  sendAIChatMessage,
  type AIChatHistoryMessage,
  type AIChatOperation,
} from "@/lib/boardApi";

type ChatMessage = {
  id: string;
  role: "user" | "assistant";
  content: string;
  boardUpdated?: boolean;
  operations?: AIChatOperation[];
};

type AIChatSidebarProps = {
  token: string;
  board: BoardData;
  onBoardUpdate: (nextBoard: BoardData) => void;
  onUnauthorized?: () => void;
};

const SUGGESTED_PROMPTS = [
  "Rename Backlog to Ideas.",
  "Add a review card for launch prep after QA micro-interactions.",
  "Move the analytics prototype card into In Progress.",
];

const createMessageId = () =>
  `msg-${Math.random().toString(16).slice(2)}${Date.now().toString(16)}`;
const UI_TIMEOUT_MESSAGE = "The AI assistant took too long to respond. Please try again.";
const UI_TIMEOUT_MS = 45_000;

const withRequestTimeout = <T,>(task: Promise<T>): Promise<T> =>
  new Promise<T>((resolve, reject) => {
    const timeoutId = window.setTimeout(() => {
      reject(new Error(UI_TIMEOUT_MESSAGE));
    }, UI_TIMEOUT_MS);

    task.then(
      (value) => {
        window.clearTimeout(timeoutId);
        resolve(value);
      },
      (error) => {
        window.clearTimeout(timeoutId);
        reject(error);
      }
    );
  });

export const AIChatSidebar = ({
  token,
  board,
  onBoardUpdate,
  onUnauthorized,
}: AIChatSidebarProps) => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [draftMessage, setDraftMessage] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");
  const messageViewportRef = useRef<HTMLDivElement | null>(null);
  const activeRequestIdRef = useRef(0);

  useEffect(() => {
    const viewport = messageViewportRef.current;
    if (!viewport) {
      return;
    }

    if (typeof viewport.scrollTo === "function") {
      viewport.scrollTo({
        top: viewport.scrollHeight,
        behavior: "smooth",
      });
    } else {
      viewport.scrollTop = viewport.scrollHeight;
    }
  }, [messages, isSending]);

  const boardSummary = useMemo(() => {
    const cardCount = Object.keys(board.cards).length;
    return `${board.columns.length} columns · ${cardCount} cards`;
  }, [board]);

  const conversationHistory = useMemo<AIChatHistoryMessage[]>(
    () =>
      messages.map((message) => ({
        role: message.role,
        content: message.content,
      })),
    [messages]
  );

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    const nextMessage = draftMessage.trim();
    if (!nextMessage || isSending) {
      return;
    }

    const userMessage: ChatMessage = {
      id: createMessageId(),
      role: "user",
      content: nextMessage,
    };

    setMessages((currentMessages) => [...currentMessages, userMessage]);
    setDraftMessage("");
    setErrorMessage("");
    setIsSending(true);
    activeRequestIdRef.current += 1;
    const requestId = activeRequestIdRef.current;

    try {
      const response = await withRequestTimeout(
        sendAIChatMessage(token, {
          message: nextMessage,
          history: conversationHistory,
        })
      );

      if (activeRequestIdRef.current !== requestId) {
        return;
      }

      setMessages((currentMessages) => [
        ...currentMessages,
        {
          id: createMessageId(),
          role: "assistant",
          content: response.reply,
          boardUpdated: response.boardUpdated,
          operations: response.operations,
        },
      ]);

      if (response.boardUpdated) {
        onBoardUpdate(response.board);
      }
    } catch (error) {
      if (activeRequestIdRef.current !== requestId) {
        return;
      }

      const message =
        error instanceof Error ? error.message : "Unable to reach the AI assistant.";

      if (message === "Unauthorized") {
        onUnauthorized?.();
        return;
      }

      setErrorMessage(message);
    } finally {
      if (activeRequestIdRef.current === requestId) {
        setIsSending(false);
      }
    }
  };

  return (
    <aside className="self-start rounded-[30px] border border-[var(--stroke)] bg-[rgba(255,255,255,0.84)] p-5 shadow-[var(--shadow)] backdrop-blur xl:sticky xl:top-8 xl:max-h-[calc(100vh-5rem)] xl:overflow-hidden">
      <div className="flex flex-col">
        <div className="rounded-[24px] border border-[rgba(32,157,215,0.12)] bg-[linear-gradient(135deg,rgba(32,157,215,0.12),rgba(236,173,10,0.14)_55%,rgba(117,57,145,0.1))] p-5">
          <p className="text-xs font-semibold uppercase tracking-[0.28em] text-[var(--gray-text)]">
            AI Copilot
          </p>
          <h2 className="mt-3 font-display text-2xl font-semibold text-[var(--navy-dark)]">
            Ask for board updates in plain language.
          </h2>
          <p className="mt-3 text-sm leading-6 text-[rgba(3,33,71,0.72)]">
            The assistant can rename columns and create, edit, move, or delete cards,
            then sync the board immediately.
          </p>
          <div className="mt-4 flex flex-wrap gap-2">
            <span className="rounded-full border border-[rgba(3,33,71,0.08)] bg-white/80 px-3 py-2 text-[11px] font-semibold uppercase tracking-[0.18em] text-[var(--primary-blue)]">
              {boardSummary}
            </span>
            <span className="rounded-full border border-[rgba(3,33,71,0.08)] bg-white/80 px-3 py-2 text-[11px] font-semibold uppercase tracking-[0.18em] text-[var(--secondary-purple)]">
              Board v{board.version}
            </span>
          </div>
        </div>

        <form className="mt-4 flex flex-col gap-3" onSubmit={handleSubmit}>
          <label className="block">
            <span className="sr-only">Ask the AI assistant</span>
            <textarea
              value={draftMessage}
              onChange={(event) => setDraftMessage(event.target.value)}
              rows={4}
              placeholder="Ask the AI to update your board..."
              className="w-full resize-none rounded-[24px] border border-[var(--stroke)] bg-white px-4 py-3 text-sm leading-6 text-[var(--navy-dark)] outline-none transition focus:border-[var(--primary-blue)]"
              aria-label="Ask the AI assistant"
            />
          </label>
          <div className="flex items-center justify-between gap-3">
            <p className="text-xs leading-5 text-[var(--gray-text)]">
              Changes are validated before they touch the saved board.
            </p>
            <button
              type="submit"
              disabled={isSending || !draftMessage.trim()}
              className="rounded-full bg-[var(--secondary-purple)] px-5 py-3 text-xs font-semibold uppercase tracking-[0.18em] text-white transition hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {isSending ? "Sending..." : "Send"}
            </button>
          </div>
        </form>

        <div className="mt-5 rounded-[24px] border border-[var(--stroke)] bg-[var(--surface)] p-4">
          <p className="text-xs font-semibold uppercase tracking-[0.22em] text-[var(--gray-text)]">
            Try asking
          </p>
          <div className="mt-3 flex flex-wrap gap-2">
            {SUGGESTED_PROMPTS.map((prompt) => (
              <button
                key={prompt}
                type="button"
                onClick={() => setDraftMessage(prompt)}
                className="rounded-full border border-[rgba(3,33,71,0.08)] bg-white px-3 py-2 text-left text-xs font-medium text-[var(--navy-dark)] transition hover:border-[var(--primary-blue)] hover:text-[var(--primary-blue)]"
              >
                {prompt}
              </button>
            ))}
          </div>
        </div>

        {errorMessage ? (
          <p
            role="alert"
            className="mt-4 rounded-2xl border border-[rgba(117,57,145,0.16)] bg-[rgba(117,57,145,0.08)] px-4 py-3 text-sm text-[var(--secondary-purple)]"
          >
            {errorMessage}
          </p>
        ) : null}

        <div
          ref={messageViewportRef}
          className="mt-5 flex max-h-[260px] min-h-[180px] flex-col gap-3 overflow-y-auto pr-1 xl:max-h-[calc(100vh-36rem)]"
          aria-label="AI conversation"
        >
          {messages.length === 0 ? (
            <div className="rounded-[24px] border border-dashed border-[var(--stroke)] bg-white/70 px-4 py-6 text-sm leading-6 text-[var(--gray-text)]">
              Start with a natural request like “move the analytics prototype into
              In Progress” or “rename Backlog to Ideas and add a review card.”
            </div>
          ) : null}

          {messages.map((message) => (
            <div
              key={message.id}
              className={
                message.role === "user"
                  ? "ml-8 rounded-[24px_24px_8px_24px] bg-[var(--navy-dark)] px-4 py-3 text-sm leading-6 text-white"
                  : "mr-8 rounded-[24px_24px_24px_8px] border border-[var(--stroke)] bg-white px-4 py-3 text-sm leading-6 text-[var(--navy-dark)]"
              }
              data-testid={`chat-message-${message.role}`}
            >
              <p className="text-[10px] font-semibold uppercase tracking-[0.24em] opacity-70">
                {message.role === "user" ? "You" : "AI"}
              </p>
              <p className="mt-2 whitespace-pre-wrap">{message.content}</p>
              {message.role === "assistant" && message.boardUpdated ? (
                <div className="mt-3 flex flex-wrap gap-2">
                  <span className="rounded-full bg-[rgba(236,173,10,0.16)] px-3 py-1 text-[10px] font-semibold uppercase tracking-[0.18em] text-[var(--navy-dark)]">
                    Board updated
                  </span>
                  {message.operations?.length ? (
                    <span className="rounded-full bg-[rgba(32,157,215,0.1)] px-3 py-1 text-[10px] font-semibold uppercase tracking-[0.18em] text-[var(--primary-blue)]">
                      {message.operations.length} operation
                      {message.operations.length === 1 ? "" : "s"}
                    </span>
                  ) : null}
                </div>
              ) : null}
            </div>
          ))}

          {isSending ? (
            <div className="mr-8 rounded-[24px_24px_24px_8px] border border-[var(--stroke)] bg-white px-4 py-3 text-sm text-[var(--gray-text)]">
              Thinking through the board update...
            </div>
          ) : null}
        </div>
      </div>
    </aside>
  );
};
