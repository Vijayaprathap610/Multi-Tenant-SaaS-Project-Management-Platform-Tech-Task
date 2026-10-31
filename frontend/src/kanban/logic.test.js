import { describe, expect, it } from "vitest";
import { computeMoveToIndex } from "./logic";

const issue = (id, status_id) => ({ id, key: id.toUpperCase(), status_id });
const board = () => [
  { id: "c1", status_id: "s1", issues: [issue("a", "s1"), issue("b", "s1"), issue("c", "s1")] },
  { id: "c2", status_id: "s2", issues: [issue("d", "s2")] },
  { id: "c3", status_id: "s3", issues: [] },
];
const ids = (cols, id) => cols.find((c) => c.id === id).issues.map((i) => i.id);

describe("computeMoveToIndex", () => {
  it("moves into an empty column and updates the card's status", () => {
    const m = computeMoveToIndex(board(), "a", "c3", 0);
    expect(m.statusId).toBe("s3");
    expect(m.beforeIssueId).toBeNull();
    expect(ids(m.newColumns, "c3")).toEqual(["a"]);
    expect(ids(m.newColumns, "c1")).toEqual(["b", "c"]);
    expect(m.newColumns.find((c) => c.id === "c3").issues[0].status_id).toBe("s3");
  });

  it("inserts before an existing card in another column", () => {
    const m = computeMoveToIndex(board(), "a", "c2", 0);
    expect(ids(m.newColumns, "c2")).toEqual(["a", "d"]);
    expect(m.beforeIssueId).toBe("d");
    expect(m.statusId).toBe("s2");
  });

  it("appends to the end of another column", () => {
    const m = computeMoveToIndex(board(), "a", "c2", 1);
    expect(ids(m.newColumns, "c2")).toEqual(["d", "a"]);
    expect(m.beforeIssueId).toBeNull();
  });

  it("reorders upwards inside a column", () => {
    const m = computeMoveToIndex(board(), "c", "c1", 0);
    expect(ids(m.newColumns, "c1")).toEqual(["c", "a", "b"]);
    expect(m.beforeIssueId).toBe("a");
  });

  it("reorders downwards inside a column", () => {
    const m = computeMoveToIndex(board(), "a", "c1", 1);
    expect(ids(m.newColumns, "c1")).toEqual(["b", "a", "c"]);
    expect(m.beforeIssueId).toBe("c");
  });

  it("moving a card to the end of its own column sends no 'before' id", () => {
    const m = computeMoveToIndex(board(), "a", "c1", 2);
    expect(ids(m.newColumns, "c1")).toEqual(["b", "c", "a"]);
    expect(m.beforeIssueId).toBeNull();
  });

  it("dropping a card back where it was is a no-op", () => {
    expect(computeMoveToIndex(board(), "b", "c1", 1)).toBeNull();
  });

  it("clamps an out-of-range index to the end", () => {
    const m = computeMoveToIndex(board(), "a", "c2", 99);
    expect(ids(m.newColumns, "c2")).toEqual(["d", "a"]);
  });

  it("returns null for unknown ids", () => {
    expect(computeMoveToIndex(board(), "zzz", "c1", 0)).toBeNull();
    expect(computeMoveToIndex(board(), "a", "zzz", 0)).toBeNull();
  });

  it("does not mutate the input", () => {
    const before = JSON.stringify(board());
    const input = board();
    computeMoveToIndex(input, "a", "c3", 0);
    expect(JSON.stringify(input)).toBe(before);
  });
});
