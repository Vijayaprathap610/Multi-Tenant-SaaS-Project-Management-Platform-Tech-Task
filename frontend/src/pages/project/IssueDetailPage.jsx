import { useEffect, useRef, useState } from "react";
import { Alert, Badge, Button, Card, Form, ListGroup } from "react-bootstrap";
import { Link, useNavigate, useOutletContext, useParams } from "react-router";
import { all, api, errorMessage, fieldErrors } from "../../api/client";
import { ConfirmModal, ErrorAlert, Loading, fmtDateTime } from "../../components/common";
import { useAuth } from "../../context/AuthContext";
import { useWorkspace } from "../../context/WorkspaceContext";
import useFetch from "../../hooks/useFetch";
import { PRIORITIES, parseLabels } from "./IssueForm";

function Comments({ base, issueId }) {
  const { user } = useAuth();
  const { can } = useWorkspace();
  const url = `${base}/issues/${issueId}/comments/`;
  const { data, loading, error, reload } = useFetch(url, { page_size: 100 }, [url]);
  const [body, setBody] = useState("");
  const [err, setErr] = useState("");
  const [editing, setEditing] = useState(null);

  const add = async (e) => {
    e.preventDefault();
    setErr("");
    try { await api.post(url, { body }); setBody(""); reload(); } catch (x) { setErr(errorMessage(x)); }
  };
  const save = async () => {
    try { await api.patch(`${url}${editing.id}/`, { body: editing.body }); setEditing(null); reload(); } catch (x) { setErr(errorMessage(x)); }
  };
  const remove = async (id) => {
    try { await api.delete(`${url}${id}/`); reload(); } catch (x) { setErr(errorMessage(x)); }
  };

  return (
    <Card className="mb-3"><Card.Body>
      <h2 className="h6">Comments</h2>
      <ErrorAlert error={error || err} />
      {loading && <Loading />}
      <ListGroup variant="flush" className="mb-3">
        {data?.results.map((c) => (
          <ListGroup.Item key={c.id}>
            <div className="small text-muted">{c.author_email} · {fmtDateTime(c.created_at)}{c.edited_at && " · edited"}</div>
            {editing?.id === c.id ? (
              <>
                <Form.Control as="textarea" rows={2} aria-label="Edit comment" value={editing.body}
                  onChange={(e) => setEditing({ ...editing, body: e.target.value })} />
                <Button size="sm" className="mt-1 me-1" onClick={save}>Save</Button>
                <Button size="sm" variant="outline-secondary" className="mt-1" onClick={() => setEditing(null)}>Cancel</Button>
              </>
            ) : (
              <>
                <div style={{ whiteSpace: "pre-wrap" }}>{c.body}</div>
                <div className="mt-1">
                  {c.author_email === user.email && <Button size="sm" variant="link" onClick={() => setEditing({ id: c.id, body: c.body })}>Edit</Button>}
                  {(c.author_email === user.email || can(["owner", "admin", "project_manager"])) &&
                    <Button size="sm" variant="link" className="text-danger" onClick={() => remove(c.id)}>Delete</Button>}
                </div>
              </>
            )}
          </ListGroup.Item>
        ))}
        {data && data.results.length === 0 && <ListGroup.Item className="text-muted">No comments yet.</ListGroup.Item>}
      </ListGroup>
      <Form onSubmit={add}>
        <Form.Group controlId="new-comment">
          <Form.Label className="visually-hidden">Add a comment</Form.Label>
          <Form.Control as="textarea" rows={2} placeholder="Add a comment" value={body} onChange={(e) => setBody(e.target.value)} />
        </Form.Group>
        <Button type="submit" size="sm" className="mt-2" disabled={!body.trim()}>Comment</Button>
      </Form>
    </Card.Body></Card>
  );
}

function Attachments({ base, issueId }) {
  const url = `${base}/issues/${issueId}/attachments/`;
  const { data, loading, error, reload } = useFetch(url, { page_size: 100 }, [url]);
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);
  const input = useRef();

  const upload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    setBusy(true);
    setErr("");
    const fd = new FormData();
    fd.append("file", file);
    try { await api.post(url, fd); reload(); } catch (x) { setErr(errorMessage(x)); }
    finally { setBusy(false); if (input.current) input.current.value = ""; }
  };
  const remove = async (id) => {
    try { await api.delete(`${url}${id}/`); reload(); } catch (x) { setErr(errorMessage(x)); }
  };

  return (
    <Card className="mb-3"><Card.Body>
      <h2 className="h6">Attachments</h2>
      <ErrorAlert error={error || err} />
      {loading && <Loading />}
      <ListGroup variant="flush" className="mb-2">
        {data?.results.map((a) => (
          <ListGroup.Item key={a.id} className="d-flex justify-content-between align-items-center">
            <span>
              <a href={`/api${url}${a.id}/download/`}>{a.original_name}</a>{" "}
              <small className="text-muted">{(a.size / 1024).toFixed(1)} KB · {a.uploaded_by_email}</small>
            </span>
            <Button size="sm" variant="link" className="text-danger" onClick={() => remove(a.id)}>Delete</Button>
          </ListGroup.Item>
        ))}
        {data && data.results.length === 0 && <ListGroup.Item className="text-muted">No attachments.</ListGroup.Item>}
      </ListGroup>
      <Form.Group controlId="upload">
        <Form.Label className="visually-hidden">Upload a file</Form.Label>
        <Form.Control type="file" ref={input} onChange={upload} disabled={busy} />
        <Form.Text>Images, PDF, text, Office files or zip up to 10 MB.</Form.Text>
      </Form.Group>
    </Card.Body></Card>
  );
}

export default function IssueDetailPage() {
  const { issueId } = useParams();
  const { base, members, statuses, transitions, project } = useOutletContext();
  const { user } = useAuth();
  const { role } = useWorkspace();
  const navigate = useNavigate();
  const sprints = useFetch(`${base}/sprints/`, { page_size: 100 }, [base]);
  const issue = useFetch(`${base}/issues/${issueId}/`, null, [base, issueId]);
  const [form, setForm] = useState(null);
  const [errors, setErrors] = useState({});
  const [error, setError] = useState("");
  const [saved, setSaved] = useState(false);
  const [confirm, setConfirm] = useState(false);

  useEffect(() => {
    const d = issue.data;
    if (d) setForm({ title: d.title, description: d.description, priority: d.priority, status: d.status,
      assignee: d.assignee ?? "", sprint: d.sprint ?? "", due_date: d.due_date ?? "", labels: (d.labels || []).join(", ") });
  }, [issue.data]);

  if (issue.loading || !form) return issue.error ? <ErrorAlert error="Issue not found." /> : <Loading />;
  const d = issue.data;
  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });
  const allowed = new Set([d.status, ...transitions.filter((t) => t.from_status === d.status).map((t) => t.to_status)]);
  const canDelete = role !== "member" || d.reporter_email === user.email;

  const save = async (e) => {
    e.preventDefault();
    setError(""); setErrors({}); setSaved(false);
    try {
      await api.patch(`${base}/issues/${issueId}/`, {
        title: form.title, description: form.description, priority: form.priority, status: form.status,
        assignee: form.assignee === "" ? null : Number(form.assignee), sprint: form.sprint || null,
        due_date: form.due_date || null, labels: parseLabels(form.labels),
      });
      setSaved(true);
      issue.reload();
    } catch (err) {
      setErrors(fieldErrors(err));
      setError(errorMessage(err));
    }
  };
  const remove = async () => {
    try { await api.delete(`${base}/issues/${issueId}/`); navigate(`/app/projects/${project.id}/issues`); }
    catch (err) { setError(errorMessage(err)); setConfirm(false); }
  };

  return (
    <>
      <Link to={`/app/projects/${project.id}/board`} className="small">← Back to board</Link>
      <h2 className="h5 mt-2">{d.key} <Badge bg="secondary">{statuses.find((s) => s.id === d.status)?.name}</Badge></h2>
      <p className="text-muted small">Reported by {d.reporter_email || "unknown"} · created {fmtDateTime(d.created_at)}</p>
      <Card className="mb-3"><Card.Body>
        {error && <Alert variant="danger" role="alert">{error}</Alert>}
        {saved && <Alert variant="success" onClose={() => setSaved(false)} dismissible>Saved.</Alert>}
        <Form onSubmit={save}>
          <Form.Group className="mb-3" controlId="d-title">
            <Form.Label>Title</Form.Label>
            <Form.Control required value={form.title} onChange={set("title")} isInvalid={Boolean(errors.title)} />
          </Form.Group>
          <Form.Group className="mb-3" controlId="d-desc">
            <Form.Label>Description</Form.Label>
            <Form.Control as="textarea" rows={4} value={form.description} onChange={set("description")} />
          </Form.Group>
          <div className="row">
            <Form.Group className="col-md-3 mb-3" controlId="d-status">
              <Form.Label>Status</Form.Label>
              <Form.Select value={form.status} onChange={set("status")} isInvalid={Boolean(errors.status)}>
                {statuses.map((s) => <option key={s.id} value={s.id} disabled={!allowed.has(s.id)}>{s.name}{!allowed.has(s.id) ? " (not allowed)" : ""}</option>)}
              </Form.Select>
              <Form.Control.Feedback type="invalid">{errors.status}</Form.Control.Feedback>
            </Form.Group>
            <Form.Group className="col-md-3 mb-3" controlId="d-priority">
              <Form.Label>Priority</Form.Label>
              <Form.Select value={form.priority} onChange={set("priority")}>{PRIORITIES.map((p) => <option key={p}>{p}</option>)}</Form.Select>
            </Form.Group>
            <Form.Group className="col-md-3 mb-3" controlId="d-assignee">
              <Form.Label>Assignee</Form.Label>
              <Form.Select value={form.assignee} onChange={set("assignee")} isInvalid={Boolean(errors.assignee)}>
                <option value="">Unassigned</option>
                {members.map((m) => <option key={m.user_id} value={m.user_id}>{m.email}</option>)}
              </Form.Select>
            </Form.Group>
            <Form.Group className="col-md-3 mb-3" controlId="d-sprint">
              <Form.Label>Sprint</Form.Label>
              <Form.Select value={form.sprint} onChange={set("sprint")} isInvalid={Boolean(errors.sprint)}>
                <option value="">Backlog</option>
                {sprints.data?.results.filter((s) => s.status !== "completed" || s.id === d.sprint).map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}
              </Form.Select>
              <Form.Control.Feedback type="invalid">{errors.sprint}</Form.Control.Feedback>
            </Form.Group>
          </div>
          <div className="row">
            <Form.Group className="col-md-4 mb-3" controlId="d-due">
              <Form.Label>Due date</Form.Label>
              <Form.Control type="date" value={form.due_date} onChange={set("due_date")} />
            </Form.Group>
            <Form.Group className="col-md-8 mb-3" controlId="d-labels">
              <Form.Label>Labels</Form.Label>
              <Form.Control value={form.labels} onChange={set("labels")} placeholder="comma separated" />
            </Form.Group>
          </div>
          <Button type="submit">Save changes</Button>{" "}
          {canDelete && <Button variant="outline-danger" onClick={() => setConfirm(true)}>Delete</Button>}
        </Form>
      </Card.Body></Card>
      <Comments base={base} issueId={issueId} />
      <Attachments base={base} issueId={issueId} />
      <ConfirmModal show={confirm} title="Delete issue?" body={`${d.key} and its comments and attachments will be permanently deleted.`}
        onConfirm={remove} onCancel={() => setConfirm(false)} />
    </>
  );
}
