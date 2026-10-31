import { useState } from "react";
import { Alert, Badge, Button, Card, Form, Modal, Nav, Tab } from "react-bootstrap";
import { Link } from "react-router";
import { api, errorMessage, fieldErrors } from "../api/client";
import { EmptyState, ErrorAlert, Loading, fmtDate, fmtDateTime } from "../components/common";
import { useAuth } from "../context/AuthContext";
import { MANAGE, useWorkspace } from "../context/WorkspaceContext";
import useFetch from "../hooks/useFetch";

function NewProjectModal({ show, onHide, onCreated }) {
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
        <Modal.Header closeButton><Modal.Title as="h2" className="h5">Create new project</Modal.Title></Modal.Header>
        <Modal.Body>
          {error && <Alert variant="danger" role="alert">{error}</Alert>}
          <Form.Group className="mb-3" controlId="p-name">
            <Form.Label>Project name</Form.Label>
            <Form.Control required maxLength={120} placeholder="e.g. Core Platform" value={form.name} isInvalid={Boolean(errors.name)}
              onChange={(e) => setForm({ ...form, name: e.target.value })} />
            <Form.Control.Feedback type="invalid">{errors.name}</Form.Control.Feedback>
          </Form.Group>
          <Form.Group className="mb-3" controlId="p-key">
            <Form.Label>Project key</Form.Label>
            <Form.Control required maxLength={10} placeholder="e.g. PLAT" value={form.key} isInvalid={Boolean(errors.key)}
              onChange={(e) => setForm({ ...form, key: e.target.value.toUpperCase() })} />
            <Form.Control.Feedback type="invalid">{errors.key}</Form.Control.Feedback>
            <Form.Text>2–10 uppercase letters or digits. Used in issue keys like PLAT-1.</Form.Text>
          </Form.Group>
          <Form.Group controlId="p-desc">
            <Form.Label>Description (optional)</Form.Label>
            <Form.Control as="textarea" rows={3} placeholder="Brief summary of the project goals…" value={form.description}
              onChange={(e) => setForm({ ...form, description: e.target.value })} />
          </Form.Group>
        </Modal.Body>
        <Modal.Footer>
          <Button variant="outline-secondary" onClick={onHide}>Cancel</Button>
          <Button type="submit" disabled={busy || !form.name.trim() || !form.key.trim()}>{busy ? "Creating…" : "Create project"}</Button>
        </Modal.Footer>
      </Form>
    </Modal>
  );
}

export default function Dashboard() {
  const { user } = useAuth();
  const { base, can, workspace } = useWorkspace();
  const [q, setQ] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [showNewProject, setShowNewProject] = useState(false);

  const projectsFetch = useFetch(`${base}/projects/`, { page_size: 100, q: q || undefined }, [base, q]);
  const membersFetch = useFetch(`${base}/members/`, { page_size: 100 }, [base]);
  const notifsFetch = useFetch(`${base}/notifications/`, { page_size: 5 }, [base]);

  const projects = projectsFetch.data?.results || [];
  const members = membersFetch.data?.results || [];
  const notifications = notifsFetch.data?.results || [];

  const filteredProjects = projects.filter((p) => {
    if (statusFilter === "active") return p.status === "active";
    if (statusFilter === "archived") return p.status === "archived";
    return true;
  });

  const activeCount = projects.filter((p) => p.status === "active").length;
  const displayName = user.first_name || user.email.split("@")[0];
  const roleName = workspace.role ? workspace.role.replace("_", " ") : "member";

  return (
    <>
      {/* Welcome Banner */}
      <div className="bg-white p-4 rounded border mb-4 shadow-sm">
        <div className="d-flex flex-wrap justify-content-between align-items-center gap-3">
          <div>
            <h1 className="h4 mb-1">Welcome, {displayName}</h1>
            <p className="text-muted mb-0 small">
              Workspace: <strong>{workspace.workspace_name}</strong> · Role: <Badge bg="secondary" className="text-capitalize">{roleName}</Badge>
            </p>
          </div>
          <div className="d-flex gap-2">
            {can(MANAGE) && (
              <Button variant="primary" onClick={() => setShowNewProject(true)}>
                + New project
              </Button>
            )}
            {can(MANAGE) && (
              <Link to="/app/settings" className="btn btn-outline-primary">
                Workspace settings
              </Link>
            )}
          </div>
        </div>
      </div>

      {/* KPI Summary Metrics */}
      <div className="row g-3 mb-4">
        <div className="col-sm-6 col-lg-3">
          <Card className="border shadow-sm h-100">
            <Card.Body>
              <div className="text-muted small text-uppercase fw-semibold">Total Projects</div>
              <div className="h3 mb-0 mt-1">{projectsFetch.loading ? "…" : projects.length}</div>
              <small className="text-muted">{activeCount} active</small>
            </Card.Body>
          </Card>
        </div>
        <div className="col-sm-6 col-lg-3">
          <Card className="border shadow-sm h-100">
            <Card.Body>
              <div className="text-muted small text-uppercase fw-semibold">Team Members</div>
              <div className="h3 mb-0 mt-1">{membersFetch.loading ? "…" : members.length}</div>
              <small className="text-muted">In this workspace</small>
            </Card.Body>
          </Card>
        </div>
        <div className="col-sm-6 col-lg-3">
          <Card className="border shadow-sm h-100">
            <Card.Body>
              <div className="text-muted small text-uppercase fw-semibold">Active Sprints</div>
              <div className="h3 mb-0 mt-1">{activeCount > 0 ? "Tracking" : "None"}</div>
              <small className="text-muted">Across projects</small>
            </Card.Body>
          </Card>
        </div>
        <div className="col-sm-6 col-lg-3">
          <Card className="border shadow-sm h-100">
            <Card.Body>
              <div className="text-muted small text-uppercase fw-semibold">Recent Alerts</div>
              <div className="h3 mb-0 mt-1">{notifsFetch.loading ? "…" : notifications.length}</div>
              <small className="text-muted"><Link to="/app/notifications">View all</Link></small>
            </Card.Body>
          </Card>
        </div>
      </div>

      <div className="row g-4">
        {/* Main Projects Section */}
        <div className="col-lg-8">
          <div className="d-flex flex-wrap justify-content-between align-items-center gap-2 mb-3">
            <h2 className="h5 mb-0">Projects</h2>
            <div className="d-flex gap-2">
              <Form.Select size="sm" style={{ width: "auto" }} value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)} aria-label="Filter status">
                <option value="all">All statuses</option>
                <option value="active">Active</option>
                <option value="archived">Archived</option>
              </Form.Select>
              <Form.Control size="sm" style={{ maxWidth: 200 }} placeholder="Filter by name…" value={q} onChange={(e) => setQ(e.target.value)} aria-label="Search projects" />
            </div>
          </div>

          <ErrorAlert error={projectsFetch.error} onRetry={projectsFetch.reload} />
          {projectsFetch.loading && <Loading label="Loading projects…" />}

          {!projectsFetch.loading && filteredProjects.length === 0 && (
            <EmptyState title="No projects found">
              {can(MANAGE) ? "Create your first project to begin organizing work." : "No projects assigned to you yet. Ask a project manager."}
            </EmptyState>
          )}

          <div className="row g-3">
            {filteredProjects.map((p) => (
              <div className="col-12" key={p.id}>
                <Card className="border shadow-sm">
                  <Card.Body>
                    <div className="d-flex justify-content-between align-items-start mb-2">
                      <div>
                        <Badge bg="light" text="dark" className="border me-2 font-monospace">{p.key}</Badge>
                        <Link to={`/app/projects/${p.id}/board`} className="h6 text-decoration-none fw-bold text-dark">
                          {p.name}
                        </Link>
                      </div>
                      <Badge bg={p.status === "active" ? "success" : "secondary"}>
                        {p.status}
                      </Badge>
                    </div>
                    <Card.Text className="text-muted small mb-3">
                      {p.description || "No description provided."}
                    </Card.Text>
                    <div className="d-flex flex-wrap gap-2 pt-2 border-top">
                      <Link to={`/app/projects/${p.id}/board`} className="btn btn-sm btn-outline-primary">
                        📋 Board
                      </Link>
                      <Link to={`/app/projects/${p.id}/issues`} className="btn btn-sm btn-outline-secondary">
                        📝 Issues
                      </Link>
                      <Link to={`/app/projects/${p.id}/sprints`} className="btn btn-sm btn-outline-secondary">
                        🏃 Sprints
                      </Link>
                      <Link to={`/app/projects/${p.id}/reports`} className="btn btn-sm btn-outline-secondary">
                        📊 Reports
                      </Link>
                      <Link to={`/app/projects/${p.id}/members`} className="btn btn-sm btn-outline-secondary ms-auto">
                        👥 Team
                      </Link>
                    </div>
                  </Card.Body>
                </Card>
              </div>
            ))}
          </div>
        </div>

        {/* Sidebar: Activity Stream & Team */}
        <div className="col-lg-4">
          {/* Recent Activity */}
          <Card className="border shadow-sm mb-4">
            <Card.Header className="bg-white py-3 border-bottom d-flex justify-content-between align-items-center">
              <span className="fw-semibold">Recent Notifications</span>
              <Link to="/app/notifications" className="small">All</Link>
            </Card.Header>
            <Card.Body className="p-0">
              {notifsFetch.loading ? (
                <div className="p-3"><Loading /></div>
              ) : notifications.length === 0 ? (
                <p className="text-muted small p-3 mb-0">No notifications yet.</p>
              ) : (
                <div className="list-group list-group-flush">
                  {notifications.map((n) => (
                    <div key={n.id} className="list-group-item p-3">
                      <div className="small mb-1">{n.message}</div>
                      <small className="text-muted">{fmtDateTime(n.created_at)}</small>
                    </div>
                  ))}
                </div>
              )}
            </Card.Body>
          </Card>

          {/* Workspace Team */}
          <Card className="border shadow-sm">
            <Card.Header className="bg-white py-3 border-bottom d-flex justify-content-between align-items-center">
              <span className="fw-semibold">Workspace Members</span>
              {can(MANAGE) && <Link to="/app/settings" className="small">Manage</Link>}
            </Card.Header>
            <Card.Body className="p-0">
              {membersFetch.loading ? (
                <div className="p-3"><Loading /></div>
              ) : members.length === 0 ? (
                <p className="text-muted small p-3 mb-0">No members found.</p>
              ) : (
                <div className="list-group list-group-flush">
                  {members.slice(0, 5).map((m) => (
                    <div key={m.id} className="list-group-item p-3 d-flex justify-content-between align-items-center">
                      <span className="small text-truncate" style={{ maxWidth: 180 }}>{m.email}</span>
                      <Badge bg="light" text="dark" className="border text-capitalize">{m.role.replace("_", " ")}</Badge>
                    </div>
                  ))}
                  {members.length > 5 && (
                    <div className="p-2 text-center border-top">
                      <small className="text-muted">+{members.length - 5} more members</small>
                    </div>
                  )}
                </div>
              )}
            </Card.Body>
          </Card>
        </div>
      </div>

      <NewProjectModal show={showNewProject} onHide={() => setShowNewProject(false)} onCreated={() => { setShowNewProject(false); projectsFetch.reload(); }} />
    </>
  );
}
