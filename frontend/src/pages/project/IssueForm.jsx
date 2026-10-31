import { useState } from "react";
import { Alert, Button, Form, Modal } from "react-bootstrap";
import { api, errorMessage, fieldErrors } from "../../api/client";

export const PRIORITIES = ["low", "medium", "high", "urgent"];
export const parseLabels = (s) => s.split(",").map((x) => x.trim()).filter(Boolean).slice(0, 10);

export default function IssueForm({ show, onHide, base, members, statuses, onCreated }) {
  const [form, setForm] = useState({ title: "", description: "", priority: "medium", assignee: "", status: "", labels: "" });
  const [errors, setErrors] = useState({});
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }));

  const submit = async (e) => {
    e.preventDefault();
    setBusy(true);
    setError("");
    setErrors({});
    const body = { title: form.title.trim(), description: form.description, priority: form.priority, labels: parseLabels(form.labels) };
    if (form.assignee) body.assignee = Number(form.assignee);
    if (form.status) body.status = form.status;
    try {
      const res = await api.post(`${base}/issues/`, body);
      setForm({ title: "", description: "", priority: "medium", assignee: "", status: "", labels: "" });
      onCreated(res.data);
    } catch (err) {
      setErrors(fieldErrors(err));
      setError(errorMessage(err));
    } finally {
      setBusy(false);
    }
  };

  return (
    <Modal show={show} onHide={onHide} centered>
      <Form onSubmit={submit}>
        <Modal.Header closeButton><Modal.Title as="h2" className="h5">New issue</Modal.Title></Modal.Header>
        <Modal.Body>
          {error && <Alert variant="danger" role="alert">{error}</Alert>}
          <Form.Group className="mb-3" controlId="i-title">
            <Form.Label>Title</Form.Label>
            <Form.Control required maxLength={200} value={form.title} onChange={set("title")} isInvalid={Boolean(errors.title)} />
            <Form.Control.Feedback type="invalid">{errors.title}</Form.Control.Feedback>
          </Form.Group>
          <Form.Group className="mb-3" controlId="i-desc">
            <Form.Label>Description</Form.Label>
            <Form.Control as="textarea" rows={3} value={form.description} onChange={set("description")} />
          </Form.Group>
          <div className="row">
            <Form.Group className="col-6 mb-3" controlId="i-priority">
              <Form.Label>Priority</Form.Label>
              <Form.Select value={form.priority} onChange={set("priority")}>
                {PRIORITIES.map((p) => <option key={p}>{p}</option>)}
              </Form.Select>
            </Form.Group>
            <Form.Group className="col-6 mb-3" controlId="i-status">
              <Form.Label>Status</Form.Label>
              <Form.Select value={form.status} onChange={set("status")}>
                <option value="">Default</option>
                {statuses.map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}
              </Form.Select>
            </Form.Group>
          </div>
          <Form.Group className="mb-3" controlId="i-assignee">
            <Form.Label>Assignee</Form.Label>
            <Form.Select value={form.assignee} onChange={set("assignee")} isInvalid={Boolean(errors.assignee)}>
              <option value="">Unassigned</option>
              {members.map((m) => <option key={m.user_id} value={m.user_id}>{m.email}</option>)}
            </Form.Select>
            <Form.Control.Feedback type="invalid">{errors.assignee}</Form.Control.Feedback>
          </Form.Group>
          <Form.Group controlId="i-labels">
            <Form.Label>Labels</Form.Label>
            <Form.Control value={form.labels} onChange={set("labels")} placeholder="bug, ui (comma separated)" />
          </Form.Group>
        </Modal.Body>
        <Modal.Footer>
          <Button variant="outline-secondary" onClick={onHide}>Cancel</Button>
          <Button type="submit" disabled={busy || !form.title.trim()}>{busy ? "Creating…" : "Create issue"}</Button>
        </Modal.Footer>
      </Form>
    </Modal>
  );
}
