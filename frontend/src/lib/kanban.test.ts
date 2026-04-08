import {
  getCardPlacement,
  getPersistedMoveInstruction,
  isSamePlacement,
  moveCard,
  type Column,
} from "@/lib/kanban";

describe("moveCard", () => {
  const baseColumns: Column[] = [
    {
      id: "col-a",
      slotKey: "a",
      title: "A",
      position: 0,
      version: 1,
      cardIds: ["card-1", "card-2"],
    },
    {
      id: "col-b",
      slotKey: "b",
      title: "B",
      position: 1,
      version: 1,
      cardIds: ["card-3"],
    },
  ];

  it("reorders cards in the same column", () => {
    const result = moveCard(baseColumns, "card-2", "card-1");
    expect(result[0].cardIds).toEqual(["card-2", "card-1"]);
  });

  it("moves cards to another column", () => {
    const result = moveCard(baseColumns, "card-2", "card-3");
    expect(result[0].cardIds).toEqual(["card-1"]);
    expect(result[1].cardIds).toEqual(["card-2", "card-3"]);
  });

  it("drops cards to the end of a column", () => {
    const result = moveCard(baseColumns, "card-1", "col-b");
    expect(result[0].cardIds).toEqual(["card-2"]);
    expect(result[1].cardIds).toEqual(["card-3", "card-1"]);
  });

  it("describes the final persisted placement for a moved card", () => {
    const movedColumns = moveCard(baseColumns, "card-2", "card-3");
    expect(getCardPlacement(movedColumns, "card-2")).toEqual({
      targetColumnId: "col-b",
      beforeCardId: "card-3",
    });
  });

  it("can compare placements for no-op drops", () => {
    const placement = getCardPlacement(baseColumns, "card-1");
    expect(isSamePlacement(placement, placement)).toBe(true);
  });

  it("returns the persisted instruction for a reordered preview state", () => {
    const movedToColumnB = moveCard(baseColumns, "card-2", "card-3");
    const reorderedWithinColumnB = moveCard(movedToColumnB, "card-2", "col-b");

    expect(
      getPersistedMoveInstruction(movedToColumnB, reorderedWithinColumnB, "card-2")
    ).toEqual({
      targetColumnId: "col-b",
      afterCardId: "card-3",
    });
  });

  it("returns null when the preview placement did not change", () => {
    expect(getPersistedMoveInstruction(baseColumns, baseColumns, "card-1")).toBeNull();
  });
});
