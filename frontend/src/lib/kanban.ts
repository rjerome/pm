export type Card = {
  id: string;
  columnId: string;
  title: string;
  details: string;
  sortOrder: number;
  version: number;
};

export type Column = {
  id: string;
  slotKey: string;
  title: string;
  position: number;
  version: number;
  cardIds: string[];
};

export type BoardData = {
  version: number;
  columns: Column[];
  cards: Record<string, Card>;
};

export const initialData: BoardData = {
  version: 1,
  columns: [
    {
      id: "col-backlog",
      slotKey: "backlog",
      title: "Backlog",
      position: 0,
      version: 1,
      cardIds: ["card-1", "card-2"],
    },
    {
      id: "col-discovery",
      slotKey: "discovery",
      title: "Discovery",
      position: 1,
      version: 1,
      cardIds: ["card-3"],
    },
    {
      id: "col-progress",
      slotKey: "progress",
      title: "In Progress",
      position: 2,
      version: 1,
      cardIds: ["card-4", "card-5"],
    },
    {
      id: "col-review",
      slotKey: "review",
      title: "Review",
      position: 3,
      version: 1,
      cardIds: ["card-6"],
    },
    {
      id: "col-done",
      slotKey: "done",
      title: "Done",
      position: 4,
      version: 1,
      cardIds: ["card-7", "card-8"],
    },
  ],
  cards: {
    "card-1": {
      id: "card-1",
      columnId: "col-backlog",
      title: "Align roadmap themes",
      details: "Draft quarterly themes with impact statements and metrics.",
      sortOrder: 1000,
      version: 1,
    },
    "card-2": {
      id: "card-2",
      columnId: "col-backlog",
      title: "Gather customer signals",
      details: "Review support tags, sales notes, and churn feedback.",
      sortOrder: 2000,
      version: 1,
    },
    "card-3": {
      id: "card-3",
      columnId: "col-discovery",
      title: "Prototype analytics view",
      details: "Sketch initial dashboard layout and key drill-downs.",
      sortOrder: 1000,
      version: 1,
    },
    "card-4": {
      id: "card-4",
      columnId: "col-progress",
      title: "Refine status language",
      details: "Standardize column labels and tone across the board.",
      sortOrder: 1000,
      version: 1,
    },
    "card-5": {
      id: "card-5",
      columnId: "col-progress",
      title: "Design card layout",
      details: "Add hierarchy and spacing for scanning dense lists.",
      sortOrder: 2000,
      version: 1,
    },
    "card-6": {
      id: "card-6",
      columnId: "col-review",
      title: "QA micro-interactions",
      details: "Verify hover, focus, and loading states.",
      sortOrder: 1000,
      version: 1,
    },
    "card-7": {
      id: "card-7",
      columnId: "col-done",
      title: "Ship marketing page",
      details: "Final copy approved and asset pack delivered.",
      sortOrder: 1000,
      version: 1,
    },
    "card-8": {
      id: "card-8",
      columnId: "col-done",
      title: "Close onboarding sprint",
      details: "Document release notes and share internally.",
      sortOrder: 2000,
      version: 1,
    },
  },
};

const isColumnId = (columns: Column[], id: string) =>
  columns.some((column) => column.id === id);

const findColumnId = (columns: Column[], id: string) => {
  if (isColumnId(columns, id)) {
    return id;
  }
  return columns.find((column) => column.cardIds.includes(id))?.id;
};

export type MoveInstruction = {
  targetColumnId: string;
  beforeCardId?: string;
  afterCardId?: string;
};

export const getCardPlacement = (
  columns: Column[],
  cardId: string
): MoveInstruction | null => {
  const targetColumn = columns.find((column) => column.cardIds.includes(cardId));
  if (!targetColumn) {
    return null;
  }

  const cardIndex = targetColumn.cardIds.indexOf(cardId);
  if (cardIndex === -1) {
    return null;
  }

  if (cardIndex === 0) {
    const nextCardId = targetColumn.cardIds[1];
    return nextCardId
      ? {
          targetColumnId: targetColumn.id,
          beforeCardId: nextCardId,
        }
      : {
          targetColumnId: targetColumn.id,
        };
  }

  return {
    targetColumnId: targetColumn.id,
    afterCardId: targetColumn.cardIds[cardIndex - 1],
  };
};

export const isSamePlacement = (
  left: MoveInstruction | null,
  right: MoveInstruction | null
) =>
  left?.targetColumnId === right?.targetColumnId &&
  left?.beforeCardId === right?.beforeCardId &&
  left?.afterCardId === right?.afterCardId;

export const getPersistedMoveInstruction = (
  previousColumns: Column[],
  nextColumns: Column[],
  cardId: string
): MoveInstruction | null => {
  const previousPlacement = getCardPlacement(previousColumns, cardId);
  const nextPlacement = getCardPlacement(nextColumns, cardId);

  if (!nextPlacement || isSamePlacement(previousPlacement, nextPlacement)) {
    return null;
  }

  return nextPlacement;
};

export const getMoveInstruction = (
  columns: Column[],
  activeId: string,
  overId: string
): MoveInstruction | null => {
  const targetColumnId = findColumnId(columns, overId);

  if (!targetColumnId) {
    return null;
  }

  const targetColumn = columns.find((column) => column.id === targetColumnId);
  if (!targetColumn) {
    return null;
  }

  if (isColumnId(columns, overId)) {
    const otherCardIds = targetColumn.cardIds.filter((cardId) => cardId !== activeId);
    const afterCardId = otherCardIds[otherCardIds.length - 1];
    return {
      targetColumnId,
      afterCardId,
    };
  }

  if (activeId === overId) {
    return null;
  }

  return {
    targetColumnId,
    beforeCardId: overId,
  };
};

export const moveCard = (
  columns: Column[],
  activeId: string,
  overId: string
): Column[] => {
  const activeColumnId = findColumnId(columns, activeId);
  const overColumnId = findColumnId(columns, overId);

  if (!activeColumnId || !overColumnId) {
    return columns;
  }

  const activeColumn = columns.find((column) => column.id === activeColumnId);
  const overColumn = columns.find((column) => column.id === overColumnId);

  if (!activeColumn || !overColumn) {
    return columns;
  }

  const isOverColumn = isColumnId(columns, overId);

  if (activeColumnId === overColumnId) {
    if (isOverColumn) {
      const nextCardIds = activeColumn.cardIds.filter(
        (cardId) => cardId !== activeId
      );
      nextCardIds.push(activeId);
      return columns.map((column) =>
        column.id === activeColumnId
          ? { ...column, cardIds: nextCardIds }
          : column
      );
    }

    const oldIndex = activeColumn.cardIds.indexOf(activeId);
    const newIndex = activeColumn.cardIds.indexOf(overId);

    if (oldIndex === -1 || newIndex === -1 || oldIndex === newIndex) {
      return columns;
    }

    const nextCardIds = [...activeColumn.cardIds];
    nextCardIds.splice(oldIndex, 1);
    nextCardIds.splice(newIndex, 0, activeId);

    return columns.map((column) =>
      column.id === activeColumnId
        ? { ...column, cardIds: nextCardIds }
        : column
    );
  }

  const activeIndex = activeColumn.cardIds.indexOf(activeId);
  if (activeIndex === -1) {
    return columns;
  }

  const nextActiveCardIds = [...activeColumn.cardIds];
  nextActiveCardIds.splice(activeIndex, 1);

  const nextOverCardIds = [...overColumn.cardIds];
  if (isOverColumn) {
    nextOverCardIds.push(activeId);
  } else {
    const overIndex = overColumn.cardIds.indexOf(overId);
    const insertIndex = overIndex === -1 ? nextOverCardIds.length : overIndex;
    nextOverCardIds.splice(insertIndex, 0, activeId);
  }

  return columns.map((column) => {
    if (column.id === activeColumnId) {
      return { ...column, cardIds: nextActiveCardIds };
    }
    if (column.id === overColumnId) {
      return { ...column, cardIds: nextOverCardIds };
    }
    return column;
  });
};

export const moveBoardPreview = (
  board: BoardData,
  activeId: string,
  overId: string
): BoardData => {
  const activeCard = board.cards[activeId];
  if (!activeCard) {
    return board;
  }

  const nextColumns = moveCard(board.columns, activeId, overId);
  if (nextColumns === board.columns) {
    return board;
  }

  const nextColumnId = findColumnId(nextColumns, activeId) ?? activeCard.columnId;
  if (nextColumnId === activeCard.columnId) {
    return {
      ...board,
      columns: nextColumns,
    };
  }

  return {
    ...board,
    columns: nextColumns,
    cards: {
      ...board.cards,
      [activeId]: {
        ...activeCard,
        columnId: nextColumnId,
      },
    },
  };
};

export const createId = (prefix: string) => {
  const randomPart = Math.random().toString(36).slice(2, 8);
  const timePart = Date.now().toString(36);
  return `${prefix}-${randomPart}${timePart}`;
};
