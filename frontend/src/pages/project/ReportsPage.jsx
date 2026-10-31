import { useEffect, useState } from "react";
import { Alert, Badge, Button, Card, ListGroup, Table } from "react-bootstrap";
import { useOutletContext } from "react-router";
import { api, errorMessage } from "../../api/client";
import { EmptyState, ErrorAlert, Loading, fmtDateTime } from "../../components/common";
import useFetch from "../../hooks/useFetch";

function ReportView({ data }) {
  return (
    <>
      <p className="mb-2">
        <strong>{data.total_issues}</strong> issues · <strong>{data.done_issues}</strong> done ({Math.round(data.completion_rate * 100)}%) ·
        <strong> {data.overdue_issues}</strong> overdue
      </p>
      <div className="row">
        <div className="col-md-4"><h3 className="h6">By status</h3>
          <Table size="sm"><tbody>{data.by_status.map((s) => <tr key={s.status}><td>{s.status}</td><td>{s.count}</td></tr>)}</tbody></Table></div>
        <div className="col-md-4"><h3 className="h6">By priority</h3>
          <Table size="sm"><tbody>{Object.entries(data.by_priority).map(([k, v]) => <tr key={k}><td>{k}</td><td>{v}</td></tr>)}</tbody></Table></div>
        <div className="col-md-4"><h3 className="h6">By assignee</h3>
          <Table size="sm"><tbody>{Object.entries(data.by_assignee).map(([k, v]) => <tr key={k}><td>{k}</td><td>{v}</td></tr>)}</tbody></Table></div>
      </div>
      {data.sprints.length > 0 && <><h3 className="h6">Sprints</h3>
        <Table size="sm"><thead><tr><th>Name</th><th>Status</th><th>Done / total</th></tr></thead>
          <tbody>{data.sprints.map((s) => <tr key={s.name}><td>{s.name}</td><td>{s.status}</td><td>{s.done} / {s.total}</td></tr>)}</tbody></Table></>}
    </>
  );
}

export default function ReportsPage() {
  const { base, canManage } = useOutletContext();
  const { data, loading, error, reload } = useFetch(`${base}/reports/`, { page_size: 20 }, [base]);
  const [err, setErr] = useState("");
  const [open, setOpen] = useState(null);
  const pending = data?.results.some((r) => r.status === "pending");

  // Reports are built by a background job; poll while one is pending.
  useEffect(() => {
    if (!pending) return undefined;
    const t = setInterval(reload, 2000);
    return () => clearInterval(t);
  }, [pending, reload]);

  if (!canManage) return <Alert variant="info">Reports are available to project managers and admins.</Alert>;
  const request = async () => { setErr(""); try { await api.post(`${base}/reports/`, {}); reload(); } catch (e) { setErr(errorMessage(e)); } };

  return (
    <>
      <div className="d-flex gap-2 mb-3">
        <Button onClick={request}>Generate report</Button>
        <a className="btn btn-outline-primary" href={`/api${base}/reports/export/issues/`}>Export issues (CSV)</a>
      </div>
      <ErrorAlert error={error || err} onRetry={reload} />
      {loading && !data && <Loading />}
      {data?.results.length === 0 && <EmptyState title="No reports yet">Generate one to see a summary of this project.</EmptyState>}
      <ListGroup>
        {data?.results.map((r) => (
          <ListGroup.Item key={r.id}>
            <div className="d-flex justify-content-between">
              <span>{fmtDateTime(r.created_at)} <Badge bg={r.status === "ready" ? "success" : r.status === "failed" ? "danger" : "secondary"}>{r.status}</Badge></span>
              {r.status === "ready" && <Button size="sm" variant="link" onClick={() => setOpen(open === r.id ? null : r.id)}>{open === r.id ? "Hide" : "View"}</Button>}
            </div>
            {r.status === "failed" && <small className="text-danger">{r.error}</small>}
            {open === r.id && <div className="mt-2"><ReportView data={r.data} /></div>}
          </ListGroup.Item>
        ))}
      </ListGroup>
    </>
  );
}
