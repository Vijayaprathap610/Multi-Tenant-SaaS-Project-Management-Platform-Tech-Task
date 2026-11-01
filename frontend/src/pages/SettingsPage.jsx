import { useState } from "react";
import { Alert, Badge, Button, Card, Form, ListGroup, Modal, Table, Tab, Tabs } from "react-bootstrap";
import { Link } from "react-router";
import { api, errorMessage } from "../api/client";
import { ConfirmModal, EmptyState, ErrorAlert, Loading, fmtDateTime } from "../components/common";
import { useAuth } from "../context/AuthContext";
import { MANAGE, useWorkspace } from "../context/WorkspaceContext";
import useFetch from "../hooks/useFetch";

const ROLES = ["owner", "admin", "project_manager", "member"];
const INVITE_ROLES = ["admin", "project_manager", "member"];
const EVENTS = ["issue.created", "issue.assigned", "issue.status_changed", "issue.deleted", "comment.created",
  "attachment.uploaded", "sprint.started", "sprint.completed", "ping"];
const label = (r) => r.replace("_", " ");

function General() {
  const { base, workspace, workspaceId } = useWorkspace();
  const { refresh } = useAuth();
  const [name, setName] = useState(workspace.workspace_name);
  const [msg, setMsg] = useState({});
  const save = async (e) => {
    e.preventDefault();
    try { await api.patch(`${base}/`, { name }); await refresh(); setMsg({ ok: "Saved." }); }
    catch (err) { setMsg({ err: errorMessage(err) }); }
  };
  return (
    <Card><Card.Body>
      {msg.ok && <Alert variant="success">{msg.ok}</Alert>}
      {msg.err && <Alert variant="danger" role="alert">{msg.err}</Alert>}
      <Form onSubmit={save}>
        <Form.Group className="mb-3" controlId="ws-name"><Form.Label>Workspace name</Form.Label>
          <Form.Control required value={name} onChange={(e) => setName(e.target.value)} /></Form.Group>
        <Button type="submit">Save</Button>
      </Form>
      <p className="small text-muted mt-3 mb-0">Your role: {label(workspace.role)} · id {workspaceId}</p>
    </Card.Body></Card>
  );
}

function Members() {
  const { base, role } = useWorkspace();
  const { user } = useAuth();
  const { data, loading, error, reload } = useFetch(`${base}/members/`, { page_size: 200 }, [base]);
  const [err, setErr] = useState("");
  const [remove, setRemove] = useState(null);
  const change = async (id, newRole) => {
    setErr("");
    try { await api.patch(`${base}/members/${id}/`, { role: newRole }); } catch (e) { setErr(errorMessage(e)); }
    reload();
  };
  const doRemove = async () => {
    try { await api.delete(`${base}/members/${remove.id}/`); } catch (e) { setErr(errorMessage(e)); }
    setRemove(null); reload();
  };
  return (
    <>
      <div className="d-flex justify-content-between align-items-center mb-3">
        <p className="small text-muted mb-0">Manage roles and project assignments for workspace users.</p>
        <Link to="/app?tab=team" className="btn btn-sm btn-primary">
          ➕ Create / Manage Team
        </Link>
      </div>
      <ErrorAlert error={error || err} />
      {loading && <Loading />}
      <div className="table-responsive"><Table className="bg-white align-middle">
        <thead><tr><th>Member</th><th>Role</th><th /></tr></thead>
        <tbody>
          {data?.results.map((m) => {
            const protectedRow = role === "admin" && ["owner", "admin"].includes(m.role);
            return (
              <tr key={m.id}>
                <td>{m.email}{m.email === user.email && " (you)"}</td>
                <td>
                  <Form.Select size="sm" aria-label={`Role for ${m.email}`} value={m.role} disabled={protectedRow}
                    onChange={(e) => change(m.id, e.target.value)}>
                    {ROLES.filter((r) => role === "owner" || !["owner", "admin"].includes(r) || r === m.role).map((r) => <option key={r} value={r}>{label(r)}</option>)}
                  </Form.Select>
                </td>
                <td><Button size="sm" variant="outline-danger" disabled={protectedRow} onClick={() => setRemove(m)}>Remove</Button></td>
              </tr>
            );
          })}
        </tbody>
      </Table></div>
      <ConfirmModal show={Boolean(remove)} title="Remove member?" confirmLabel="Remove"
        body={`${remove?.email} will lose access to this workspace.`} onConfirm={doRemove} onCancel={() => setRemove(null)} />
    </>
  );
}

function Invitations() {
  const { base } = useWorkspace();
  const { data, loading, error, reload } = useFetch(`${base}/invitations/`, { page_size: 100 }, [base]);
  const [form, setForm] = useState({ email: "", role: "member" });
  const [err, setErr] = useState("");
  const [ok, setOk] = useState("");
  const invite = async (e) => {
    e.preventDefault();
    setErr(""); setOk("");
    try { await api.post(`${base}/invitations/`, form); setOk(`Invitation sent to ${form.email}.`); setForm({ email: "", role: "member" }); reload(); }
    catch (x) { setErr(errorMessage(x)); }
  };
  const revoke = async (id) => { try { await api.delete(`${base}/invitations/${id}/`); } catch (x) { setErr(errorMessage(x)); } reload(); };
  return (
    <>
      <Card className="mb-3"><Card.Body>
        {ok && <Alert variant="success">{ok}</Alert>}
        {err && <Alert variant="danger" role="alert">{err}</Alert>}
        <Form onSubmit={invite} className="row g-2">
          <Form.Group className="col-md-6" controlId="inv-email"><Form.Label className="visually-hidden">Email</Form.Label>
            <Form.Control type="email" required placeholder="colleague@company.com" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} /></Form.Group>
          <Form.Group className="col-md-3" controlId="inv-role"><Form.Label className="visually-hidden">Role</Form.Label>
            <Form.Select value={form.role} onChange={(e) => setForm({ ...form, role: e.target.value })}>{INVITE_ROLES.map((r) => <option key={r} value={r}>{label(r)}</option>)}</Form.Select></Form.Group>
          <div className="col-md-3"><Button type="submit" className="w-100">Send invitation</Button></div>
        </Form>
      </Card.Body></Card>
      <ErrorAlert error={error} />
      {loading && <Loading />}
      {data?.results.length === 0 && <EmptyState title="No pending invitations" />}
      <ListGroup>
        {data?.results.map((i) => (
          <ListGroup.Item key={i.id} className="d-flex justify-content-between align-items-center">
            <span>{i.email} <Badge bg="secondary">{label(i.role)}</Badge> <small className="text-muted">expires {fmtDateTime(i.expires_at)}</small></span>
            <Button size="sm" variant="outline-danger" onClick={() => revoke(i.id)}>Revoke</Button>
          </ListGroup.Item>
        ))}
      </ListGroup>
    </>
  );
}

function Webhooks() {
  const { base } = useWorkspace();
  const { data, loading, error, reload } = useFetch(`${base}/webhooks/`, { page_size: 100 }, [base]);
  const [show, setShow] = useState(false);
  const [form, setForm] = useState({ url: "", description: "", events: ["issue.created"] });
  const [secret, setSecret] = useState(null);
  const [err, setErr] = useState("");
  const [deliveries, setDeliveries] = useState(null);

  const create = async (e) => {
    e.preventDefault();
    setErr("");
    try { const r = await api.post(`${base}/webhooks/`, form); setSecret(r.data.secret); setShow(false); reload(); }
    catch (x) { setErr(errorMessage(x)); }
  };
  const act = async (fn) => { setErr(""); try { await fn(); } catch (x) { setErr(errorMessage(x)); } reload(); };
  const toggleEvent = (ev) => setForm((f) => ({ ...f, events: f.events.includes(ev) ? f.events.filter((x) => x !== ev) : [...f.events, ev] }));
  const showDeliveries = async (id) => {
    try { setDeliveries({ id, rows: (await api.get(`${base}/webhooks/${id}/deliveries/`, { params: { page_size: 20 } })).data.results }); }
    catch (x) { setErr(errorMessage(x)); }
  };

  return (
    <>
      <div className="d-flex justify-content-between mb-3"><h2 className="h6">Webhook endpoints</h2><Button onClick={() => setShow(true)}>Add endpoint</Button></div>
      {secret && (
        <Alert variant="warning" dismissible onClose={() => setSecret(null)}>
          Copy this signing secret now. It will not be shown again:<br /><code data-testid="webhook-secret">{secret}</code>
        </Alert>
      )}
      <ErrorAlert error={error || err} />
      {loading && <Loading />}
      {data?.results.length === 0 && <EmptyState title="No webhooks">Endpoints must use https and a public address.</EmptyState>}
      <ListGroup className="mb-3">
        {data?.results.map((w) => (
          <ListGroup.Item key={w.id}>
            <div className="d-flex justify-content-between flex-wrap gap-2">
              <div><div className="fw-semibold">{w.url}</div><small className="text-muted">{w.events.join(", ")}</small></div>
              <div className="d-flex gap-1 align-items-start">
                <Button size="sm" variant="outline-primary" onClick={() => act(() => api.post(`${base}/webhooks/${w.id}/test/`))}>Send test</Button>
                <Button size="sm" variant="outline-primary" onClick={() => showDeliveries(w.id)}>Deliveries</Button>
                <Button size="sm" variant="outline-primary" onClick={() => act(async () => setSecret((await api.post(`${base}/webhooks/${w.id}/rotate-secret/`)).data.secret))}>Rotate secret</Button>
                <Button size="sm" variant="outline-danger" onClick={() => act(() => api.delete(`${base}/webhooks/${w.id}/`))}>Delete</Button>
              </div>
            </div>
            {deliveries?.id === w.id && (
              <Table size="sm" className="mt-2 mb-0"><thead><tr><th>Event</th><th>Status</th><th>Attempts</th><th>Result</th></tr></thead>
                <tbody>{deliveries.rows.map((d) => <tr key={d.id}><td>{d.event_type}</td><td>{d.status}</td><td>{d.attempts}</td><td>{d.response_status || d.error || "—"}</td></tr>)}</tbody></Table>
            )}
          </ListGroup.Item>
        ))}
      </ListGroup>
      <Modal show={show} onHide={() => setShow(false)} centered>
        <Form onSubmit={create}>
          <Modal.Header closeButton><Modal.Title as="h2" className="h5">New webhook endpoint</Modal.Title></Modal.Header>
          <Modal.Body>
            {err && <Alert variant="danger" role="alert">{err}</Alert>}
            <Form.Group className="mb-3" controlId="wh-url"><Form.Label>URL (https)</Form.Label>
              <Form.Control type="url" required value={form.url} onChange={(e) => setForm({ ...form, url: e.target.value })} /></Form.Group>
            <Form.Group className="mb-3" controlId="wh-desc"><Form.Label>Description</Form.Label>
              <Form.Control value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} /></Form.Group>
            <fieldset><legend className="h6">Events</legend>
              {EVENTS.map((ev) => <Form.Check key={ev} id={`ev-${ev}`} label={ev} checked={form.events.includes(ev)} onChange={() => toggleEvent(ev)} />)}
            </fieldset>
          </Modal.Body>
          <Modal.Footer><Button type="submit" disabled={!form.events.length}>Create endpoint</Button></Modal.Footer>
        </Form>
      </Modal>
    </>
  );
}

function Audit() {
  const { base } = useWorkspace();
  const [page, setPage] = useState(1);
  const { data, loading, error, reload } = useFetch(`${base}/audit/`, { page, page_size: 25 }, [base]);
  return (
    <>
      <ErrorAlert error={error} onRetry={reload} />
      {loading && <Loading />}
      {data && (
        <>
          <div className="table-responsive"><Table size="sm" className="bg-white">
            <thead><tr><th>When</th><th>Event</th><th>Actor</th><th>Details</th></tr></thead>
            <tbody>{data.results.map((e) => (
              <tr key={e.id}><td>{fmtDateTime(e.created_at)}</td><td>{e.event_type}</td><td>{e.actor_email || "—"}</td>
                <td className="small">{Object.entries(e.metadata || {}).map(([k, v]) => `${k}: ${v}`).join(", ")}</td></tr>
            ))}</tbody>
          </Table></div>
          <div className="d-flex gap-2">
            <Button size="sm" variant="outline-secondary" disabled={!data.previous} onClick={() => setPage(page - 1)}>Previous</Button>
            <Button size="sm" variant="outline-secondary" disabled={!data.next} onClick={() => setPage(page + 1)}>Next</Button>
          </div>
        </>
      )}
    </>
  );
}

export default function SettingsPage() {
  const { can } = useWorkspace();
  if (!can(MANAGE)) return <Alert variant="warning">Only workspace owners and admins can open settings.</Alert>;
  return (
    <>
      <h1 className="h4 mb-3">Workspace settings</h1>
      <Tabs defaultActiveKey="general" className="mb-3" mountOnEnter unmountOnExit>
        <Tab eventKey="general" title="General"><General /></Tab>
        <Tab eventKey="members" title="Members and roles"><Members /></Tab>
        <Tab eventKey="invitations" title="Invitations"><Invitations /></Tab>
        <Tab eventKey="webhooks" title="Webhooks"><Webhooks /></Tab>
        <Tab eventKey="audit" title="Audit log"><Audit /></Tab>
      </Tabs>
    </>
  );
}
