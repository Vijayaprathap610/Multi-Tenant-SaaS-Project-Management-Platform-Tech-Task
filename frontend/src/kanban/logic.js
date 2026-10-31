/**
 * Pure drag-and-drop logic (unit-tested). `columns` is the Kanban payload:
 * [{ id, status_id, issues: [{ id, status_id, ... }] }].
 *
 * computeMoveToIndex(columns, issueId, toColumnId, toIndex): `toIndex` is the issue's FINAL index in the
 * destination column (what @hello-pangea/dnd reports as destination.index).
 * Returns null when nothing would change, otherwise what is needed to persist the move:
 *   { statusId, beforeIssueId, newColumns }
 * `beforeIssueId` matches the API: place the issue before that issue in the target column, or at the end if null.
 */
export function findIssue(columns, issueId) {
  for (const col of columns) {
    const index = col.issues.findIndex((i) => i.id === issueId);
    if (index >= 0) return { col, index };
  }
  return null;
}

export function computeMoveToIndex(columns, issueId, toColumnId, toIndex) {
  const from = findIssue(columns, issueId);
  const toCol = columns.find((c) => c.id === toColumnId);
  if (!from || !toCol) return null;
  const card = from.col.issues[from.index];

  const without = toCol.issues.filter((i) => i.id !== issueId);
  const insertAt = Math.max(0, Math.min(toIndex, without.length));
  if (toCol.id === from.col.id && insertAt === from.index) return null; // same place

  const moved = { ...card, status_id: toCol.status_id };
  const newColumns = columns.map((col) => {
    if (col.id === from.col.id && col.id !== toCol.id) return { ...col, issues: col.issues.filter((i) => i.id !== issueId) };
    if (col.id === toCol.id) {
      const list = [...without];
      list.splice(insertAt, 0, moved);
      return { ...col, issues: list };
    }
    return col;
  });

  return { statusId: toCol.status_id, beforeIssueId: without[insertAt]?.id ?? null, newColumns };
}
