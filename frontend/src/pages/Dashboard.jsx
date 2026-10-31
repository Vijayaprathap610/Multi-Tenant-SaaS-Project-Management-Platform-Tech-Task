import { useState } from "react";
import { Alert, Badge, Button, Card, Form, Modal } from "react-bootstrap";
import { Link } from "react-router";
import { api, errorMessage, fieldErrors } from "../api/client";
import { EmptyState, ErrorAlert, Loading } from "../components/common";
import { MANAGE, useWorkspace } from "../context/WorkspaceContext";
import useFetch from "../hooks/useFetch";

function NewProject({ show, onHide, onCreated }) {
  const { base } = useWorkspace();
  const [form, setForm] = useState({ name: "", key: "", description: "" });
  const [errors, setErrors] = useState({});
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    setBusy(true);
    setError("");
    setErrors({});
    try {
      const res = await api.post(`${base}/projects/`, { ...form, key: form.key.toUpperCase() });
      setForm({ name: "", key: "", description: "" });
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
        <Modal.Header closeButton><Modal.Title as="h2" className="h5">New project</Modal.Title></Modal.Header>
        <Modal.Body>
          {error && <Alert variant="danger" role="alert">{error}</Alert>}
          <Form.Group className="mb-3" controlId="p-name">
            <Form.Label>Name</Form.Label>
            <Form.Control required maxLength={120} value={form.name} isInvalid={Boolean(errors.name)}
              onChange={(e) => setForm({ ...form, name: e.target.value })} />
          </Form.Group>
          <Form.Group className="mb-3" controlId="p-key">
            <Form.Label>Key</Form.Label>
            <Form.Control required maxLength={10} placeholder="e.g. WEB" value={form.key} isInvalid={Boolean(errors.key)}
              onChange={(e) => setForm({ ...form, key: e.target.value.toUpperCase() })} />
            <Form.Control.Feedback type="invalid">{errors.key}</Form.Control.Feedback>
            <Form.Text>2–10 capital letters or digits. Used in issue keys like WEB-1. Cannot be changed later.</Form.Text>
          </Form.Group>
          <Form.Group controlId="p-desc">
            <Form.Label>Description</Form.Label>
            <Form.Control as="textarea" rows={3} value={form.description}
              onChange={(e) => setForm({ ...form, description: e.target.value })} />
          </Form.Group>
        </Modal.Body>
        <Modal.Footer>
          <Button variant="outline-secondary" onClick={onHide}>Cancel</Button>
          <Button type="submit" disabled={busy}>{busy ? "Creating…" : "Create project"}</Button>
        </Modal.Footer>
      </Form>
    </Modal>
  );
}

export default function Dashboard() {
  const { base, can, workspace } = useWorkspace();
  const [q, setQ] = useState("");
  const { data, loading, error, reload } = useFetch(`${base}/projects/`, { page_size: 100, q: q || undefined }, [base]);
  const [show, setShow] = useState(false);

  return (
    <>
      <div className="d-flex flex-wrap justify-content-between align-items-center gap-2 mb-3">
        <h1 className="h4 mb-0">Projects in {workspace.workspace_name}</h1>
        <div className="d-flex gap-2">
          <Form.Control aria-label="Search projects" placeholder="Search projects" value={q} onChange={(e) => setQ(e.target.value)} />
          {can(MANAGE) && <Button onClick={() => setShow(true)}>New project</Button>}
        </div>
      </div>
      <ErrorAlert error={error} onRetry={reload} />
      {loading && <Loading />}
      {data && data.results.length === 0 && (
        <EmptyState title="No projects yet">
          {can(MANAGE) ? "Create your first project to start planning." : "You have not been added to any project yet. Ask a workspace admin."}
        </EmptyState>
      )}
      <div className="row g-3">
        {data?.results.map((p) => (
          <div className="col-md-6 col-xl-4" key={p.id}>
            <Card className="h-100"><Card.Body>
              <div className="d-flex justify-content-between">
                <Card.Title as="h2" className="h6"><Link to={`/app/projects/${p.id}`}>{p.name}</Link></Card.Title>
                <Badge bg={p.status === "active" ? "success" : "secondary"}>{p.status}</Badge>
              </div>
              <div className="text-muted small mb-2">{p.key}</div>
              <Card.Text>{p.description || "No description."}</Card.Text>
            </Card.Body></Card>
          </div>
        ))}
      </div>
      <NewProject show={show} onHide={() => setShow(false)} onCreated={() => { setShow(false); reload(); }} />
    </>
  );
}
