import { useState } from "react";
import { Badge, Button, Form, Pagination, Table } from "react-bootstrap";
import { Link, useOutletContext } from "react-router";
import { EmptyState, ErrorAlert, Loading, fmtDate } from "../../components/common";
import useFetch from "../../hooks/useFetch";
import IssueForm, { PRIORITIES } from "./IssueForm";

const PAGE = 15;

export default function IssuesPage() {
  const { base, members, statuses } = useOutletContext();
  const [f, setF] = useState({ q: "", status: "", priority: "", assignee: "", ordering: "-created_at", page: 1 });
  const [show, setShow] = useState(false);
  const params = Object.fromEntries(Object.entries({ ...f, page_size: PAGE }).filter(([, v]) => v !== ""));
  const { data, loading, error, reload } = useFetch(`${base}/issues/`, params, [base]);
  const set = (k) => (e) => setF({ ...f, [k]: e.target.value, page: 1 });
  const statusName = Object.fromEntries(statuses.map((s) => [s.id, s.name]));
  const pages = data ? Math.ceil(data.count / PAGE) : 0;

  return (
    <>
      <div className="d-flex flex-wrap gap-2 mb-3">
        <Form.Control style={{ maxWidth: 220 }} aria-label="Search issues" placeholder="Search title" value={f.q} onChange={set("q")} />
        <Form.Select style={{ maxWidth: 170 }} aria-label="Filter by status" value={f.status} onChange={set("status")}>
          <option value="">All statuses</option>{statuses.map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}
        </Form.Select>
        <Form.Select style={{ maxWidth: 150 }} aria-label="Filter by priority" value={f.priority} onChange={set("priority")}>
          <option value="">All priorities</option>{PRIORITIES.map((p) => <option key={p}>{p}</option>)}
        </Form.Select>
        <Form.Select style={{ maxWidth: 200 }} aria-label="Filter by assignee" value={f.assignee} onChange={set("assignee")}>
          <option value="">All assignees</option>{members.map((m) => <option key={m.user_id} value={m.user_id}>{m.email}</option>)}
        </Form.Select>
        <Form.Select style={{ maxWidth: 170 }} aria-label="Sort by" value={f.ordering} onChange={set("ordering")}>
          <option value="-created_at">Newest</option><option value="created_at">Oldest</option>
          <option value="-updated_at">Recently updated</option><option value="due_date">Due date</option><option value="title">Title</option>
        </Form.Select>
        <Button className="ms-auto" onClick={() => setShow(true)}>New issue</Button>
      </div>
      <ErrorAlert error={error} onRetry={reload} />
      {loading && <Loading />}
      {data && data.results.length === 0 && <EmptyState title="No issues match">Adjust the filters or create an issue.</EmptyState>}
      {data && data.results.length > 0 && (
        <div className="table-responsive">
          <Table hover className="bg-white align-middle">
            <thead><tr><th>Key</th><th>Title</th><th>Status</th><th>Priority</th><th>Assignee</th><th>Due</th></tr></thead>
            <tbody>
              {data.results.map((i) => (
                <tr key={i.id}>
                  <td><Link to={i.id}>{i.key}</Link></td><td>{i.title}</td>
                  <td><Badge bg="secondary">{statusName[i.status] || "—"}</Badge></td>
                  <td>{i.priority}</td><td>{i.assignee_email || "—"}</td><td>{fmtDate(i.due_date)}</td>
                </tr>
              ))}
            </tbody>
          </Table>
        </div>
      )}
      {pages > 1 && (
        <Pagination>
          <Pagination.Prev disabled={f.page <= 1} onClick={() => setF({ ...f, page: f.page - 1 })} />
          <Pagination.Item active>{f.page} / {pages}</Pagination.Item>
          <Pagination.Next disabled={f.page >= pages} onClick={() => setF({ ...f, page: f.page + 1 })} />
        </Pagination>
      )}
      <IssueForm show={show} onHide={() => setShow(false)} base={base} members={members} statuses={statuses}
        onCreated={() => { setShow(false); reload(); }} />
    </>
  );
}
