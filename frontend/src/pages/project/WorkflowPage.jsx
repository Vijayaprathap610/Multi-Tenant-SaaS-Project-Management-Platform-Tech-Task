import { useState } from "react";
import { Alert, Badge, Button, Card, Form, Table } from "react-bootstrap";
import { useOutletContext } from "react-router";
import { api, errorMessage } from "../../api/client";
import { statusVariant } from "../../components/common";

export default function WorkflowPage() {
  const { base, statuses, transitions, canManage, reloadRef } = useOutletContext();
  const [form, setForm] = useState({ name: "", category: "todo" });
  const [error, setError] = useState("");
  const tmap = new Map(transitions.map((t) => [`${t.from_status}>${t.to_status}`, t.id]));

  const run = async (fn) => {
    setError("");
    try { await fn(); await reloadRef(); } catch (e) { setError(errorMessage(e)); }
  };
  const toggle = (from, to) => run(async () => {
    const id = tmap.get(`${from}>${to}`);
    if (id) await api.delete(`${base}/transitions/${id}/`);
    else await api.post(`${base}/transitions/`, { from_status: from, to_status: to });
  });
  const addStatus = (e) => {
    e.preventDefault();
    run(async () => { await api.post(`${base}/statuses/`, { ...form, position: statuses.length }); setForm({ name: "", category: "todo" }); });
  };

  return (
    <>
      {error && <Alert variant="danger" dismissible onClose={() => setError("")} role="alert">{error}</Alert>}
      <Card className="mb-3"><Card.Body>
        <h2 className="h6">Statuses</h2>
        <div className="d-flex flex-wrap gap-2 mb-3">
          {statuses.map((s) => (
            <Badge key={s.id} bg={statusVariant[s.category]} text={s.category === "in_progress" ? "dark" : undefined} className="p-2">
              {s.name}
              {canManage && <button type="button" className="btn btn-sm btn-link p-0 ms-2 text-reset" aria-label={`Delete status ${s.name}`}
                onClick={() => run(() => api.delete(`${base}/statuses/${s.id}/`))}>×</button>}
            </Badge>
          ))}
        </div>
        {canManage && (
          <Form onSubmit={addStatus} className="row g-2">
            <Form.Group className="col-md-5" controlId="st-name"><Form.Label className="visually-hidden">Status name</Form.Label>
              <Form.Control required placeholder="New status name" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} /></Form.Group>
            <Form.Group className="col-md-4" controlId="st-cat"><Form.Label className="visually-hidden">Category</Form.Label>
              <Form.Select value={form.category} onChange={(e) => setForm({ ...form, category: e.target.value })}>
                <option value="todo">To do</option><option value="in_progress">In progress</option><option value="done">Done</option>
              </Form.Select></Form.Group>
            <div className="col-md-3"><Button type="submit" className="w-100">Add status</Button></div>
          </Form>
        )}
      </Card.Body></Card>
      <Card><Card.Body>
        <h2 className="h6">Allowed transitions</h2>
        <p className="small text-muted">Rows are the current status, columns the status an issue may move to. The backend rejects every other move, including direct API calls.</p>
        <div className="table-responsive">
          <Table bordered size="sm" className="bg-white text-center align-middle">
            <thead><tr><th scope="col">From ↓ / To →</th>{statuses.map((s) => <th scope="col" key={s.id}>{s.name}</th>)}</tr></thead>
            <tbody>
              {statuses.map((from) => (
                <tr key={from.id}>
                  <th scope="row">{from.name}</th>
                  {statuses.map((to) => (
                    <td key={to.id}>
                      {from.id === to.id ? "—" : (
                        <Form.Check type="checkbox" id={`t-${from.id}-${to.id}`} aria-label={`${from.name} to ${to.name}`}
                          checked={tmap.has(`${from.id}>${to.id}`)} disabled={!canManage} onChange={() => toggle(from.id, to.id)} />
                      )}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </Table>
        </div>
      </Card.Body></Card>
    </>
  );
}
