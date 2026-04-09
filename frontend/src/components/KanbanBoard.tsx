"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import {
  DndContext,
  DragOverlay,
  PointerSensor,
  useSensor,
  useSensors,
  closestCorners,
  pointerWithin,
  type CollisionDetection,
  type DragCancelEvent,
  type DragEndEvent,
  type DragOverEvent,
  type DragStartEvent,
} from "@dnd-kit/core";

import { AIChatSidebar } from "@/components/AIChatSidebar";
import { KanbanColumn } from "@/components/KanbanColumn";
import { KanbanCardPreview } from "@/components/KanbanCardPreview";
import {
  getPersistedMoveInstruction,
  moveBoardPreview,
  type BoardData,
} from "@/lib/kanban";
import {
  createCard,
  deleteCard,
  fetchBoard,
  moveCard,
  renameColumn,
  updateCard,
} from "@/lib/boardApi";

type KanbanBoardProps = {
  token: string;
  onLogout?: () => void;
};

export const KanbanBoard = ({ token, onLogout }: KanbanBoardProps) => {
  const [board, setBoard] = useState<BoardData | null>(null);
  const [activeCardId, setActiveCardId] = useState<string | null>(null);
  const [dragSnapshot, setDragSnapshot] = useState<BoardData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState("");

  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: { distance: 6 },
    })
  );

  // pointerWithin detects drops on empty columns; closestCorners handles sorting within columns.
  const collisionDetection = useCallback<CollisionDetection>((args) => {
    const pointerCollisions = pointerWithin(args);
    if (pointerCollisions.length > 0) {
      return pointerCollisions;
    }
    return closestCorners(args);
  }, []);

  const cardsById = useMemo(() => board?.cards ?? {}, [board]);

  useEffect(() => {
    const loadBoard = async () => {
      setIsLoading(true);
      setErrorMessage("");

      try {
        const nextBoard = await fetchBoard(token);
        setBoard(nextBoard);
      } catch (error) {
        const message =
          error instanceof Error ? error.message : "Unable to load your board.";
        if (message === "Unauthorized") {
          onLogout?.();
          return;
        }
        setErrorMessage(message);
      } finally {
        setIsLoading(false);
      }
    };

    void loadBoard();
  }, [onLogout, token]);

  const runBoardMutation = async (
    action: () => Promise<BoardData>,
    rollbackBoard?: BoardData | null
  ): Promise<boolean> => {
    try {
      const nextBoard = await action();
      setBoard(nextBoard);
      setErrorMessage("");
      return true;
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "Unable to update your board.";
      if (message === "Unauthorized") {
        onLogout?.();
        return false;
      }
      if (rollbackBoard) {
        setBoard(rollbackBoard);
      }
      setErrorMessage(message);
      return false;
    }
  };

  const handleDragStart = (event: DragStartEvent) => {
    if (board) {
      setDragSnapshot(board);
    }
    setActiveCardId(event.active.id as string);
  };

  const handleDragOver = (event: DragOverEvent) => {
    const { active, over } = event;

    if (!over) {
      return;
    }

    setBoard((currentBoard) => {
      if (!currentBoard) {
        return currentBoard;
      }

      return moveBoardPreview(
        currentBoard,
        active.id as string,
        over.id as string
      );
    });
  };

  const handleDragCancel = (_event: DragCancelEvent) => {
    if (dragSnapshot) {
      setBoard(dragSnapshot);
    }
    setActiveCardId(null);
    setDragSnapshot(null);
  };

  const handleDragEnd = async (event: DragEndEvent) => {
    const { active, over } = event;
    setActiveCardId(null);

    if (!board) {
      setDragSnapshot(null);
      return;
    }

    if (!over) {
      if (dragSnapshot) {
        setBoard(dragSnapshot);
      }
      setDragSnapshot(null);
      return;
    }

    const rollbackBoard = dragSnapshot ?? board;
    const activeCard = rollbackBoard.cards[active.id as string];
    const finalPlacement = getPersistedMoveInstruction(
      rollbackBoard.columns,
      board.columns,
      active.id as string
    );

    if (!activeCard || !finalPlacement) {
      if (!activeCard && dragSnapshot) {
        setBoard(dragSnapshot);
      }
      setDragSnapshot(null);
      return;
    }

    await runBoardMutation(
      () =>
        moveCard(token, activeCard.id, {
          targetColumnId: finalPlacement.targetColumnId,
          version: activeCard.version,
          beforeCardId: finalPlacement.beforeCardId,
          afterCardId: finalPlacement.afterCardId,
        }),
      rollbackBoard
    );
    setDragSnapshot(null);
  };

  const handleRenameColumn = async (columnId: string, title: string) => {
    if (!board) {
      return false;
    }

    const column = board.columns.find((item) => item.id === columnId);
    if (!column) {
      return false;
    }

    const nextTitle = title.trim();
    if (!nextTitle || nextTitle === column.title) {
      return true;
    }

    return runBoardMutation(() =>
      renameColumn(token, columnId, nextTitle, column.version)
    );
  };

  const handleAddCard = async (columnId: string, title: string, details: string) => {
    return runBoardMutation(() =>
      createCard(token, {
        columnId,
        title,
        details,
      })
    );
  };

  const handleUpdateCard = async (
    cardId: string,
    title: string,
    details: string
  ) => {
    if (!board) {
      return false;
    }

    const card = board.cards[cardId];
    if (!card) {
      return false;
    }

    return runBoardMutation(() =>
      updateCard(token, cardId, {
        title,
        details,
        version: card.version,
      })
    );
  };

  const handleDeleteCard = async (_columnId: string, cardId: string) => {
    if (!board) {
      return false;
    }

    const card = board.cards[cardId];
    if (!card) {
      return false;
    }

    return runBoardMutation(() => deleteCard(token, card));
  };

  const handleAIBoardUpdate = (nextBoard: BoardData) => {
    setBoard(nextBoard);
    setActiveCardId(null);
    setDragSnapshot(null);
    setErrorMessage("");
  };

  const activeCard = activeCardId ? cardsById[activeCardId] : null;

  if (isLoading || !board) {
    return (
      <div className="flex min-h-screen items-center justify-center px-6">
        <div className="rounded-[28px] border border-[var(--stroke)] bg-white/85 px-8 py-6 text-center shadow-[var(--shadow)]">
          <p className="text-xs font-semibold uppercase tracking-[0.3em] text-[var(--gray-text)]">
            Board Sync
          </p>
          <p className="mt-3 text-sm text-[var(--navy-dark)]">
            Loading your persisted Kanban board.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="relative overflow-hidden">
      <div className="pointer-events-none absolute left-0 top-0 h-[420px] w-[420px] -translate-x-1/3 -translate-y-1/3 rounded-full bg-[radial-gradient(circle,_rgba(32,157,215,0.25)_0%,_rgba(32,157,215,0.05)_55%,_transparent_70%)]" />
      <div className="pointer-events-none absolute bottom-0 right-0 h-[520px] w-[520px] translate-x-1/4 translate-y-1/4 rounded-full bg-[radial-gradient(circle,_rgba(117,57,145,0.18)_0%,_rgba(117,57,145,0.05)_55%,_transparent_75%)]" />

      <main className="relative mx-auto flex min-h-screen max-w-[1500px] flex-col gap-10 px-6 pb-16 pt-12">
        <header className="flex flex-col gap-6 rounded-[32px] border border-[var(--stroke)] bg-white/80 p-8 shadow-[var(--shadow)] backdrop-blur">
          <div className="flex flex-wrap items-start justify-between gap-6">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.35em] text-[var(--gray-text)]">
                Single Board Kanban
              </p>
              <h1 className="mt-3 font-display text-4xl font-semibold text-[var(--navy-dark)]">
                Kanban Studio
              </h1>
              <p className="mt-3 max-w-xl text-sm leading-6 text-[var(--gray-text)]">
                Keep momentum visible. Rename columns, drag cards between stages,
                and capture quick notes without getting buried in settings.
              </p>
            </div>
            <div className="rounded-2xl border border-[var(--stroke)] bg-[var(--surface)] px-5 py-4">
              <p className="text-xs font-semibold uppercase tracking-[0.25em] text-[var(--gray-text)]">
                Focus
              </p>
              <p className="mt-2 text-lg font-semibold text-[var(--primary-blue)]">
                One board. Five columns. Zero clutter.
              </p>
              {onLogout ? (
                <button
                  type="button"
                  onClick={onLogout}
                  className="mt-4 rounded-full border border-[var(--stroke)] px-4 py-2 text-xs font-semibold uppercase tracking-[0.18em] text-[var(--navy-dark)] transition hover:border-[var(--primary-blue)] hover:text-[var(--primary-blue)]"
                >
                  Log out
                </button>
              ) : null}
            </div>
          </div>
          <div className="flex flex-wrap items-center gap-4">
            {board.columns.map((column) => (
              <div
                key={column.id}
                className="flex items-center gap-2 rounded-full border border-[var(--stroke)] px-4 py-2 text-xs font-semibold uppercase tracking-[0.2em] text-[var(--navy-dark)]"
              >
                <span className="h-2 w-2 rounded-full bg-[var(--accent-yellow)]" />
                {column.title}
              </div>
            ))}
          </div>
          {errorMessage ? (
            <p
              role="alert"
              className="rounded-2xl border border-[rgba(117,57,145,0.16)] bg-[rgba(117,57,145,0.08)] px-4 py-3 text-sm text-[var(--secondary-purple)]"
            >
              {errorMessage}
            </p>
          ) : null}
        </header>

        <section className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_360px]">
          <DndContext
            sensors={sensors}
            collisionDetection={collisionDetection}
            onDragStart={handleDragStart}
            onDragOver={handleDragOver}
            onDragCancel={handleDragCancel}
            onDragEnd={handleDragEnd}
          >
            <section className="grid gap-6 lg:grid-cols-5">
              {board.columns.map((column) => (
                <KanbanColumn
                  key={column.id}
                  column={column}
                  cards={column.cardIds.map((cardId) => board.cards[cardId]).filter(Boolean)}
                  onRename={handleRenameColumn}
                  onAddCard={handleAddCard}
                  onDeleteCard={handleDeleteCard}
                  onUpdateCard={handleUpdateCard}
                />
              ))}
            </section>
            <DragOverlay>
              {activeCard ? (
                <div className="w-[260px]">
                  <KanbanCardPreview card={activeCard} />
                </div>
              ) : null}
            </DragOverlay>
          </DndContext>

          <AIChatSidebar
            token={token}
            board={board}
            onBoardUpdate={handleAIBoardUpdate}
            onUnauthorized={onLogout}
          />
        </section>
      </main>
    </div>
  );
};
