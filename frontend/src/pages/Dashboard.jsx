import { useEffect, useState } from "react";
import { Alert, Badge, Button, Card, Form, Modal, Tab, Table, Tabs } from "react-bootstrap";
import { Link, useNavigate } from "react-router";
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
  const navigate = useNavigate();
  const [q, setQ] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [showNewProject, setShowNewProject] = useState(false);
  const [activeTab, setActiveTab] = useState("projects");
  const [taskFilter, setTaskFilter] = useState("");

  const projectsFetch = useFetch(`${base}/projects/`, { page_size: 100, q: q || undefined }, [base, q]);
  const membersFetch = useFetch(`${base}/members/`, { page_size: 100 }, [base]);
  const notifsFetch = useFetch(`${base}/notifications/`, { page_size: 10 }, [base]);

  const projects = projectsFetch.data?.results || [];
  const members = membersFetch.data?.results || [];
  const notifications = notifsFetch.data?.results || [];

  // Load user's assigned issues across accessible projects
  const [assignedIssues, setAssignedIssues] = useState([]);
  const [loadingTasks, setLoadingTasks] = useState(false);

  useEffect(() => {
    if (!projects.length || !user?.id) {
      setAssignedIssues([]);
      return;
    }
    let alive = true;
    setLoadingTasks(true);

    Promise.all(
      projects.slice(0, 15).map((p) =>
        api
          .get(`${base}/projects/${p.id}/issues/`, { params: { assignee: user.id } })
          .then((res) => (res.data?.results || []).map((iss) => ({ ...iss, project_id: p.id, project_name: p.name, project_key: p.key })))
          .catch(() => [])
      )
    ).then((results) => {
      if (alive) {
        setAssignedIssues(results.flat());
        setLoadingTasks(false);
      }
    });

    return () => {
      alive = false;
    };
  }, [base, projects, user?.id]);

  const filteredProjects = projects.filter((p) => {
    if (statusFilter === "active") return p.status === "active";
    if (statusFilter === "archived") return p.status === "archived";
    return true;
  });

  const filteredTasks = assignedIssues.filter((t) => {
    if (!taskFilter) return true;
    const term = taskFilter.toLowerCase();
    return (
      t.title?.toLowerCase().includes(term) ||
      t.key?.toLowerCase().includes(term) ||
      t.priority?.toLowerCase().includes(term)
    );
  });

  const activeCount = projects.filter((p) => p.status === "active").length;
  const displayName = [user.first_name, user.last_name].filter(Boolean).join(" ") || user.email.split("@")[0];
  const roleName = workspace.role ? workspace.role.replace("_", " ") : "member";

  return (
    <>
      {/* Welcome Banner with Project Quick Switcher */}
      <div className="bg-white p-4 rounded border mb-4 shadow-sm">
        <div className="d-flex flex-wrap justify-content-between align-items-center gap-3">
          <div>
            <h1 className="h4 mb-1">Welcome, {displayName}</h1>
            <p className="text-muted mb-0 small">
              Workspace: <strong>{workspace.workspace_name}</strong> · Role: <Badge bg="secondary" className="text-capitalize">{roleName}</Badge>
            </p>
          </div>
          <div className="d-flex flex-wrap align-items-center gap-2">
            {projects.length > 0 && (
              <Form.Select
                size="sm"
                style={{ width: "auto", minWidth: 180 }}
                aria-label="Quick jump to project"
                defaultValue=""
                onChange={(e) => {
                  if (e.target.value) navigate(`/app/projects/${e.target.value}/board`);
                }}
              >
                <option value="" disabled>Jump to project board…</option>
                {projects.map((p) => (
                  <option key={p.id} value={p.id}>{p.name} ({p.key})</option>
                ))}
              </Form.Select>
            )}
            {can(MANAGE) && (
              <Button variant="primary" size="sm" onClick={() => setShowNewProject(true)}>
                + New project
              </Button>
            )}
            {can(MANAGE) && (
              <Link to="/app/settings" className="btn btn-sm btn-outline-primary">
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
              <div className="text-muted small text-uppercase fw-semibold">Assigned To Me</div>
              <div className="h3 mb-0 mt-1">{loadingTasks ? "…" : assignedIssues.length}</div>
              <small className="text-muted">Tasks across projects</small>
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
              <div className="text-muted small text-uppercase fw-semibold">Recent Alerts</div>
              <div className="h3 mb-0 mt-1">{notifsFetch.loading ? "…" : notifications.length}</div>
              <small className="text-muted"><Link to="/app/notifications">View notifications</Link></small>
            </Card.Body>
          </Card>
        </div>
      </div>

      <div className="row g-4">
        {/* Main Content Area: Tabs */}
        <div className="col-lg-8">
          <Tabs activeKey={activeTab} onSelect={(k) => setActiveTab(k)} className="mb-3">
            {/* Projects Tab */}
            <Tab eventKey="projects" title={`Projects (${projects.length})`}>
              <div className="d-flex flex-wrap justify-content-between align-items-center gap-2 mb-3">
                <h2 className="h6 mb-0">All Workspace Projects</h2>
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
            </Tab>

            {/* My Tasks Tab */}
            <Tab eventKey="tasks" title={`My Tasks (${assignedIssues.length})`}>
              <div className="d-flex flex-wrap justify-content-between align-items-center gap-2 mb-3">
                <h2 className="h6 mb-0">Tasks Assigned to You</h2>
                <Form.Control
                  size="sm"
                  style={{ maxWidth: 220 }}
                  placeholder="Filter tasks…"
                  value={taskFilter}
                  onChange={(e) => setTaskFilter(e.target.value)}
                  aria-label="Filter my tasks"
                />
              </div>

              {loadingTasks && <Loading label="Loading your assigned tasks…" />}

              {!loadingTasks && filteredTasks.length === 0 && (
                <EmptyState title="No tasks assigned">
                  You currently have no open tasks assigned to you.
                </EmptyState>
              )}

              {!loadingTasks && filteredTasks.length > 0 && (
                <div className="table-responsive">
                  <Table hover className="bg-white align-middle shadow-sm border">
                    <thead className="table-light">
                      <tr>
                        <th>Key</th>
                        <th>Project</th>
                        <th>Title</th>
                        <th>Priority</th>
                        <th>Due Date</th>
                      </tr>
                    </thead>
                    <tbody>
                      {filteredTasks.map((t) => (
                        <tr key={t.id}>
                          <td>
                            <Link to={`/app/projects/${t.project_id}/issues/${t.id}`} className="font-monospace fw-semibold">
                              {t.key}
                            </Link>
                          </td>
                          <td>
                            <Badge bg="light" text="dark" className="border">
                              {t.project_name || t.project_key}
                            </Badge>
                          </td>
                          <td>
                            <Link to={`/app/projects/${t.project_id}/issues/${t.id}`} className="text-decoration-none text-dark">
                              {t.title}
                            </Link>
                          </td>
                          <td>
                            <Badge bg={t.priority === "urgent" ? "danger" : t.priority === "high" ? "warning" : "secondary"}>
                              {t.priority}
                            </Badge>
                          </td>
                          <td>{t.due_date ? fmtDate(t.due_date) : <span className="text-muted">—</span>}</td>
                        </tr>
                      ))}
                    </tbody>
                  </Table>
                </div>
              )}
            </Tab>

            {/* Activity Stream Tab */}
            <Tab eventKey="activity" title="Activity Feed">
              <h2 className="h6 mb-3">Recent Workspace Activity</h2>
              {notifsFetch.loading ? (
                <Loading label="Loading activity feed…" />
              ) : notifications.length === 0 ? (
                <EmptyState title="No recent activity">
                  No notifications or events recorded in this workspace recently.
                </EmptyState>
              ) : (
                <div className="list-group shadow-sm">
                  {notifications.map((n) => (
                    <div key={n.id} className="list-group-item p-3">
                      <div className="d-flex justify-content-between align-items-start">
                        <div>
                          <div className="mb-1">
                            {n.project_id && n.issue_id ? (
                              <Link to={`/app/projects/${n.project_id}/issues/${n.issue_id}`}>
                                {n.message}
                              </Link>
                            ) : (
                              n.message
                            )}
                          </div>
                          <small className="text-muted">{fmtDateTime(n.created_at)}</small>
                        </div>
                        <Badge bg="light" text="dark" className="border">{n.event_type || "alert"}</Badge>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </Tab>
          </Tabs>
        </div>

        {/* Sidebar */}
        <div className="col-lg-4">
          {/* Quick Actions Card */}
          <Card className="border shadow-sm mb-4">
            <Card.Header className="bg-white py-3 border-bottom">
              <span className="fw-semibold">Quick Actions</span>
            </Card.Header>
            <Card.Body className="d-flex flex-column gap-2">
              {can(MANAGE) && (
                <Button variant="outline-primary" size="sm" className="text-start" onClick={() => setShowNewProject(true)}>
                  ➕ Create New Project
                </Button>
              )}
              <Link to="/app/notifications" className="btn btn-sm btn-outline-secondary text-start">
                🔔 View Notifications ({notifications.length})
              </Link>
              {can(MANAGE) && (
                <Link to="/app/settings" className="btn btn-sm btn-outline-secondary text-start">
                  ⚙️ Workspace Settings & Team
                </Link>
              )}
              <Link to="/app/billing" className="btn btn-sm btn-outline-secondary text-start">
                💳 Subscription & Plan
              </Link>
              <Link to="/app/profile" className="btn btn-sm btn-outline-secondary text-start">
                👤 My Profile Settings
              </Link>
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
