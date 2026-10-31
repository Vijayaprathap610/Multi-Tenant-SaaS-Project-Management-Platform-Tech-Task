import { useEffect, useState } from "react";
import { Alert, Button, Form } from "react-bootstrap";
import { useOutletContext } from "react-router";
import { api, errorMessage } from "../../api/client";
import { EmptyState, ErrorAlert, Loading } from "../../components/common";
import useFetch from "../../hooks/useFetch";
import KanbanBoard from "../../kanban/KanbanBoard";
import IssueForm from "./IssueForm";

export default function BoardPage() {
  const { base, members, statuses } = useOutletContext();
  const linkBase = base.replace(/^\/workspaces\/[^/]+/, "/app");
  const boards = useFetch(`${base}/boards/`, null, [base]);
  const boardId = boards.data?.results?.[0]?.id;
  const [filters, setFilters] = useState({ q: "", assignee: "", priority: "" });
  const params = Object.fromEntries(Object.entries(filters).filter(([, v]) => v));
  const kanban = useFetch(boardId ? `${base}/boards/${boardId}/kanban/` : null, params, [boardId]);
  const [columns, setColumns] = useState([]);
  const [moveError, setMoveError] = useState("");
  const [show, setShow] = useState(false);

  useEffect(() => { if (kanban.data) setColumns(kanban.data.columns); }, [kanban.data]);

  // Persist through the API; on rejection restore the previous state and tell the user why.
  const onMove = async ({ issueId, statusId, beforeIssueId }, previous) => {
    setMoveError("");
    try {
      await api.post(`${base}/issues/${issueId}/move/`, { status: statusId, before_issue_id: beforeIssueId });
      kanban.reload();
    } catch (err) {
      setColumns(previous);
      setMoveError(`Move rejected: ${errorMessage(err)}`);
    }
  };

  if (boards.loading || (boardId && kanban.loading && !columns.length)) return <Loading />;
  return (
    <>
      <div className="d-flex flex-wrap gap-2 mb-3">
        <Form.Control style={{ maxWidth: 220 }} aria-label="Search issues" placeholder="Search issues" value={filters.q}
          onChange={(e) => setFilters({ ...filters, q: e.target.value })} />
        <Form.Select style={{ maxWidth: 200 }} aria-label="Filter by assignee" value={filters.assignee}
          onChange={(e) => setFilters({ ...filters, assignee: e.target.value })}>
          <option value="">All assignees</option>
          {members.map((m) => <option key={m.user_id} value={m.user_id}>{m.email}</option>)}
        </Form.Select>
        <Form.Select style={{ maxWidth: 160 }} aria-label="Filter by priority" value={filters.priority}
          onChange={(e) => setFilters({ ...filters, priority: e.target.value })}>
          <option value="">All priorities</option>
          {["low", "medium", "high", "urgent"].map((p) => <option key={p}>{p}</option>)}
        </Form.Select>
        <Button className="ms-auto" onClick={() => setShow(true)}>New issue</Button>
      </div>
      <ErrorAlert error={boards.error || kanban.error} onRetry={kanban.reload} />
      {moveError && <Alert variant="warning" dismissible onClose={() => setMoveError("")} role="alert">{moveError}</Alert>}
      {kanban.data?.truncated && <Alert variant="info">Showing the first 500 issues. Use filters to narrow the board.</Alert>}
      {!boardId && !boards.loading && <EmptyState title="No board">This project has no board yet.</EmptyState>}
      {boardId && (
        <KanbanBoard columns={columns} setColumns={setColumns} onMove={onMove} linkBase={linkBase} />
      )}
      <IssueForm show={show} onHide={() => setShow(false)} base={base} members={members} statuses={statuses}
        onCreated={() => { setShow(false); kanban.reload(); }} />
    </>
  );
}
