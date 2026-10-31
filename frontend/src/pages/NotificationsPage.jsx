import { useState } from "react";
import { Button, ListGroup } from "react-bootstrap";
import { Link } from "react-router";
import { api, errorMessage } from "../api/client";
import { EmptyState, ErrorAlert, Loading, fmtDateTime } from "../components/common";
import { useWorkspace } from "../context/WorkspaceContext";
import useFetch from "../hooks/useFetch";

export default function NotificationsPage() {
  const { base } = useWorkspace();
  const { data, loading, error, reload } = useFetch(`${base}/notifications/`, { page_size: 50 }, [base]);
  const [err, setErr] = useState("");
  const run = async (fn) => { setErr(""); try { await fn(); reload(); } catch (e) { setErr(errorMessage(e)); } };

  return (
    <>
      <div className="d-flex justify-content-between align-items-center mb-3">
        <h1 className="h4 mb-0">Notifications</h1>
        <Button size="sm" variant="outline-primary" onClick={() => run(() => api.post(`${base}/notifications/read-all/`))}>Mark all read</Button>
      </div>
      <ErrorAlert error={error || err} onRetry={reload} />
      {loading && <Loading />}
      {data?.results.length === 0 && <EmptyState title="You're all caught up">New assignments, status changes and comments appear here.</EmptyState>}
      <ListGroup>
        {data?.results.map((n) => (
          <ListGroup.Item key={n.id} className="d-flex justify-content-between align-items-center" variant={n.read_at ? undefined : "light"}>
            <div>
              <div className={n.read_at ? "" : "fw-semibold"}>
                {n.project_id && n.issue_id ? <Link to={`/app/projects/${n.project_id}/issues/${n.issue_id}`}>{n.message}</Link> : n.message}
              </div>
              <small className="text-muted">{fmtDateTime(n.created_at)}</small>
            </div>
            {!n.read_at && <Button size="sm" variant="link" onClick={() => run(() => api.post(`${base}/notifications/${n.id}/read/`))}>Mark read</Button>}
          </ListGroup.Item>
        ))}
      </ListGroup>
    </>
  );
}
