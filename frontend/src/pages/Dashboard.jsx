import { useEffect, useState } from "react";
import { Alert, Badge, Button, Card, Form, Modal, Tab, Table, Tabs } from "react-bootstrap";
import { Link, useNavigate, useSearchParams } from "react-router";
import { api, errorMessage, fieldErrors } from "../api/client";
import { ConfirmModal, EmptyState, ErrorAlert, Loading, fmtDate, fmtDateTime } from "../components/common";
import { useAuth } from "../context/AuthContext";
import { MANAGE, PM_UP, useWorkspace } from "../context/WorkspaceContext";
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

// 1. Create Project Manager Modal (Company Owner)
function CreatePMModal({ show, onHide, onCreated }) {
  const { base } = useWorkspace();
  const [form, setForm] = useState({
    full_name: "",
    email: "",
    password: "",
    confirm_password: "",
    designation: "Project Manager",
    contact_number: "",
  });
  const [errors, setErrors] = useState({});
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }));

  const submit = async (e) => {
    e.preventDefault();
    setError("");
    setErrors({});
    if (form.password && form.password !== form.confirm_password) {
      setErrors({ confirm_password: "Passwords do not match." });
      return;
    }
    setBusy(true);
    try {
      const payload = {
        email: form.email.trim(),
        full_name: form.full_name.trim(),
        password: form.password,
        role: "project_manager",
        designation: form.designation.trim(),
        contact_number: form.contact_number.trim(),
      };
      const res = await api.post(`${base}/members/`, payload);
      setForm({
        full_name: "",
        email: "",
        password: "",
        confirm_password: "",
        designation: "Project Manager",
        contact_number: "",
      });
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
        <Modal.Header closeButton>
          <Modal.Title as="h2" className="h5">Create Project Manager Account</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          {error && <Alert variant="danger" role="alert">{error}</Alert>}
          <Form.Group className="mb-3" controlId="pm-name">
            <Form.Label>Full name</Form.Label>
            <Form.Control required placeholder="e.g. Sarah Connor" value={form.full_name} isInvalid={Boolean(errors.full_name)} onChange={set("full_name")} />
            <Form.Control.Feedback type="invalid">{errors.full_name}</Form.Control.Feedback>
          </Form.Group>
          <Form.Group className="mb-3" controlId="pm-email">
            <Form.Label>Email address</Form.Label>
            <Form.Control type="email" required placeholder="pm@company.com" value={form.email} isInvalid={Boolean(errors.email)} onChange={set("email")} />
            <Form.Control.Feedback type="invalid">{errors.email}</Form.Control.Feedback>
            <Form.Text>An invitation email with activation & login details will be sent.</Form.Text>
          </Form.Group>
          <div className="row g-2 mb-3">
            <Form.Group className="col-md-6" controlId="pm-password">
              <Form.Label>Password</Form.Label>
              <Form.Control type="password" required placeholder="Account password" value={form.password} isInvalid={Boolean(errors.password)} onChange={set("password")} />
              <Form.Control.Feedback type="invalid">{errors.password}</Form.Control.Feedback>
            </Form.Group>
            <Form.Group className="col-md-6" controlId="pm-confirm">
              <Form.Label>Confirm password</Form.Label>
              <Form.Control type="password" required placeholder="Confirm password" value={form.confirm_password} isInvalid={Boolean(errors.confirm_password)} onChange={set("confirm_password")} />
              <Form.Control.Feedback type="invalid">{errors.confirm_password}</Form.Control.Feedback>
            </Form.Group>
          </div>
          <div className="row g-2 mb-3">
            <Form.Group className="col-md-6" controlId="pm-desig">
              <Form.Label>Designation</Form.Label>
              <Form.Control placeholder="e.g. Senior Project Lead" value={form.designation} onChange={set("designation")} />
            </Form.Group>
            <Form.Group className="col-md-6" controlId="pm-contact">
              <Form.Label>Contact number (optional)</Form.Label>
              <Form.Control placeholder="+1-555-0123" value={form.contact_number} onChange={set("contact_number")} />
            </Form.Group>
          </div>
        </Modal.Body>
        <Modal.Footer>
          <Button variant="outline-secondary" onClick={onHide}>Cancel</Button>
          <Button type="submit" disabled={busy || !form.email.trim() || !form.full_name.trim() || !form.password}>
            {busy ? "Creating Account…" : "Create Project Manager"}
          </Button>
        </Modal.Footer>
      </Form>
    </Modal>
  );
}

// 2. Create Team Member Modal (Project Manager or Owner)
function CreateTeamMemberModal({ show, onHide, projects, onCreated }) {
  const { base } = useWorkspace();
  const [form, setForm] = useState({
    full_name: "",
    email: "",
    auth_mode: "password", // 'password' or 'invite'
    password: "",
    confirm_password: "",
    designation: "Developer",
    project_id: "",
    contact_number: "",
  });
  const [errors, setErrors] = useState({});
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (projects.length > 0 && !form.project_id) {
      setForm((f) => ({ ...f, project_id: projects[0].id }));
    }
  }, [projects, form.project_id]);

  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }));

  const submit = async (e) => {
    e.preventDefault();
    setError("");
    setErrors({});
    if (form.auth_mode === "password" && form.password !== form.confirm_password) {
      setErrors({ confirm_password: "Passwords do not match." });
      return;
    }
    setBusy(true);
    try {
      const payload = {
        email: form.email.trim(),
        full_name: form.full_name.trim(),
        role: "member",
        designation: form.designation.trim(),
        contact_number: form.contact_number.trim(),
        project_id: form.project_id || undefined,
      };
      if (form.auth_mode === "password" && form.password) {
        payload.password = form.password;
      }
      const res = await api.post(`${base}/members/`, payload);
      setForm({
        full_name: "",
        email: "",
        auth_mode: "password",
        password: "",
        confirm_password: "",
        designation: "Developer",
        project_id: projects[0]?.id || "",
        contact_number: "",
      });
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
        <Modal.Header closeButton>
          <Modal.Title as="h2" className="h5">Create Team Member Account</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          {error && <Alert variant="danger" role="alert">{error}</Alert>}
          <Form.Group className="mb-3" controlId="tm-name">
            <Form.Label>Full name</Form.Label>
            <Form.Control required placeholder="e.g. Alex Murphy" value={form.full_name} isInvalid={Boolean(errors.full_name)} onChange={set("full_name")} />
            <Form.Control.Feedback type="invalid">{errors.full_name}</Form.Control.Feedback>
          </Form.Group>
          <Form.Group className="mb-3" controlId="tm-email">
            <Form.Label>Email address</Form.Label>
            <Form.Control type="email" required placeholder="alex@company.com" value={form.email} isInvalid={Boolean(errors.email)} onChange={set("email")} />
            <Form.Control.Feedback type="invalid">{errors.email}</Form.Control.Feedback>
          </Form.Group>

          <Form.Group className="mb-3">
            <Form.Label>Account setup option</Form.Label>
            <div>
              <Form.Check inline type="radio" id="mode-pw" name="auth_mode" label="Set initial password" checked={form.auth_mode === "password"} onChange={() => setForm({ ...form, auth_mode: "password" })} />
              <Form.Check inline type="radio" id="mode-inv" name="auth_mode" label="Send invitation email with activation link" checked={form.auth_mode === "invite"} onChange={() => setForm({ ...form, auth_mode: "invite" })} />
            </div>
          </Form.Group>

          {form.auth_mode === "password" && (
            <div className="row g-2 mb-3">
              <Form.Group className="col-md-6" controlId="tm-password">
                <Form.Label>Password</Form.Label>
                <Form.Control type="password" required placeholder="Set password" value={form.password} isInvalid={Boolean(errors.password)} onChange={set("password")} />
                <Form.Control.Feedback type="invalid">{errors.password}</Form.Control.Feedback>
              </Form.Group>
              <Form.Group className="col-md-6" controlId="tm-confirm">
                <Form.Label>Confirm password</Form.Label>
                <Form.Control type="password" required placeholder="Confirm password" value={form.confirm_password} isInvalid={Boolean(errors.confirm_password)} onChange={set("confirm_password")} />
                <Form.Control.Feedback type="invalid">{errors.confirm_password}</Form.Control.Feedback>
              </Form.Group>
            </div>
          )}

          <div className="row g-2 mb-3">
            <Form.Group className="col-md-6" controlId="tm-proj">
              <Form.Label>Assign to project</Form.Label>
              <Form.Select required value={form.project_id} onChange={set("project_id")}>
                <option value="">Select project…</option>
                {projects.map((p) => (
                  <option key={p.id} value={p.id}>{p.name} ({p.key})</option>
                ))}
              </Form.Select>
            </Form.Group>
            <Form.Group className="col-md-6" controlId="tm-desig">
              <Form.Label>Designation</Form.Label>
              <Form.Control placeholder="e.g. Frontend Engineer" value={form.designation} onChange={set("designation")} />
            </Form.Group>
          </div>

          <Form.Group className="mb-3" controlId="tm-contact">
            <Form.Label>Contact number (optional)</Form.Label>
            <Form.Control placeholder="+1-555-0144" value={form.contact_number} onChange={set("contact_number")} />
          </Form.Group>
        </Modal.Body>
        <Modal.Footer>
          <Button variant="outline-secondary" onClick={onHide}>Cancel</Button>
          <Button type="submit" disabled={busy || !form.email.trim() || !form.full_name.trim() || (form.auth_mode === "password" && !form.password)}>
            {busy ? "Creating Account…" : "Create Team Member"}
          </Button>
        </Modal.Footer>
      </Form>
    </Modal>
  );
}

// 3. Edit Member Details Modal
function EditMemberModal({ show, onHide, member, onUpdated }) {
  const { base } = useWorkspace();
  const [form, setForm] = useState({
    first_name: "",
    last_name: "",
    designation: "",
    contact_number: "",
  });
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (member) {
      setForm({
        first_name: member.first_name || "",
        last_name: member.last_name || "",
        designation: member.designation || "",
        contact_number: member.contact_number || "",
      });
    }
  }, [member]);

  const submit = async (e) => {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      const res = await api.patch(`${base}/members/${member.id}/`, form);
      onUpdated(res.data);
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setBusy(false);
    }
  };

  if (!member) return null;

  return (
    <Modal show={show} onHide={onHide} centered>
      <Form onSubmit={submit}>
        <Modal.Header closeButton>
          <Modal.Title as="h2" className="h5">Edit Details: {member.email}</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          {error && <Alert variant="danger" role="alert">{error}</Alert>}
          <div className="row g-2 mb-3">
            <Form.Group className="col-6" controlId="em-fn">
              <Form.Label>First name</Form.Label>
              <Form.Control value={form.first_name} onChange={(e) => setForm({ ...form, first_name: e.target.value })} />
            </Form.Group>
            <Form.Group className="col-6" controlId="em-ln">
              <Form.Label>Last name</Form.Label>
              <Form.Control value={form.last_name} onChange={(e) => setForm({ ...form, last_name: e.target.value })} />
            </Form.Group>
          </div>
          <Form.Group className="mb-3" controlId="em-desig">
            <Form.Label>Designation</Form.Label>
            <Form.Control value={form.designation} onChange={(e) => setForm({ ...form, designation: e.target.value })} />
          </Form.Group>
          <Form.Group className="mb-3" controlId="em-contact">
            <Form.Label>Contact number</Form.Label>
            <Form.Control value={form.contact_number} onChange={(e) => setForm({ ...form, contact_number: e.target.value })} />
          </Form.Group>
        </Modal.Body>
        <Modal.Footer>
          <Button variant="outline-secondary" onClick={onHide}>Cancel</Button>
          <Button type="submit" disabled={busy}>{busy ? "Saving…" : "Save changes"}</Button>
        </Modal.Footer>
      </Form>
    </Modal>
  );
}

// 4. Assign / Manage Projects Modal
function AssignProjectsModal({ show, onHide, member, projects, onUpdated }) {
  const { base } = useWorkspace();
  const [selectedIds, setSelectedIds] = useState([]);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (member?.assigned_projects) {
      setSelectedIds(member.assigned_projects.map((p) => p.id));
    }
  }, [member]);

  const toggle = (id) => {
    setSelectedIds((prev) => (prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]));
  };

  const submit = async (e) => {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      const res = await api.patch(`${base}/members/${member.id}/`, { project_ids: selectedIds });
      onUpdated(res.data);
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setBusy(false);
    }
  };

  if (!member) return null;

  return (
    <Modal show={show} onHide={onHide} centered>
      <Form onSubmit={submit}>
        <Modal.Header closeButton>
          <Modal.Title as="h2" className="h5">Assigned Projects: {member.full_name || member.email}</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          {error && <Alert variant="danger" role="alert">{error}</Alert>}
          <p className="small text-muted mb-3">
            Select the projects that <strong>{member.full_name || member.email}</strong> is assigned to work on:
          </p>
          {projects.length === 0 ? (
            <p className="text-muted small">No projects created in this workspace yet.</p>
          ) : (
            <div className="list-group">
              {projects.map((p) => {
                const checked = selectedIds.includes(p.id);
                return (
                  <label key={p.id} className="list-group-item d-flex align-items-center gap-2 cursor-pointer">
                    <Form.Check
                      type="checkbox"
                      id={`proj-${p.id}`}
                      checked={checked}
                      onChange={() => toggle(p.id)}
                    />
                    <div>
                      <span className="fw-semibold font-monospace me-2">[{p.key}]</span>
                      <span>{p.name}</span>
                    </div>
                  </label>
                );
              })}
            </div>
          )}
        </Modal.Body>
        <Modal.Footer>
          <Button variant="outline-secondary" onClick={onHide}>Cancel</Button>
          <Button type="submit" disabled={busy}>{busy ? "Updating…" : "Update project assignments"}</Button>
        </Modal.Footer>
      </Form>
    </Modal>
  );
}

// 5. Team Management View (Company Owner & Project Manager)
function TeamManagementView({ members, projects, role, reloadMembers }) {
  const { base } = useWorkspace();
  const isOwnerOrAdmin = role === "owner" || role === "admin";
  const isPM = role === "project_manager";

  const [showCreatePM, setShowCreatePM] = useState(false);
  const [showCreateTM, setShowCreateTM] = useState(false);
  const [editingMember, setEditingMember] = useState(null);
  const [managingProjects, setManagingProjects] = useState(null);
  const [toggleActiveTarget, setToggleActiveTarget] = useState(null);

  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [notice, setNotice] = useState("");
  const [error, setError] = useState("");

  // Filter list based on role viewpoint
  const displayMembers = members.filter((m) => {
    // Search
    if (search) {
      const s = search.toLowerCase();
      const match =
        m.email?.toLowerCase().includes(s) ||
        m.full_name?.toLowerCase().includes(s) ||
        m.designation?.toLowerCase().includes(s);
      if (!match) return false;
    }
    // Status
    if (statusFilter === "active" && !m.is_active) return false;
    if (statusFilter === "inactive" && m.is_active) return false;

    // Viewpoint scoping
    if (isPM) {
      // PMs manage team members
      return m.role === "member";
    }
    return true; // Owner/Admin sees everyone
  });

  const doToggleActive = async () => {
    if (!toggleActiveTarget) return;
    setError("");
    try {
      await api.patch(`${base}/members/${toggleActiveTarget.id}/`, {
        is_active: !toggleActiveTarget.is_active,
      });
      setNotice(`Member status updated for ${toggleActiveTarget.email}.`);
      setToggleActiveTarget(null);
      reloadMembers();
    } catch (err) {
      setError(errorMessage(err));
    }
  };

  return (
    <div>
      {notice && <Alert variant="success" dismissible onClose={() => setNotice("")}>{notice}</Alert>}
      {error && <Alert variant="danger" dismissible onClose={() => setError("")}>{error}</Alert>}

      <div className="d-flex flex-wrap justify-content-between align-items-center gap-2 mb-3">
        <div>
          <h2 className="h5 mb-1">{isPM ? "Project Team Management" : "Company Team & Role Management"}</h2>
          <p className="text-muted small mb-0">
            {isPM
              ? "Create, view, and assign Team Members to your managed projects."
              : "Create Project Managers, oversee assignments, and maintain active status."}
          </p>
        </div>
        <div className="d-flex gap-2">
          {isOwnerOrAdmin && (
            <Button variant="primary" onClick={() => setShowCreatePM(true)}>
              ➕ Create Project Manager
            </Button>
          )}
          {(isOwnerOrAdmin || isPM) && (
            <Button variant={isPM ? "primary" : "outline-primary"} onClick={() => setShowCreateTM(true)}>
              👥 Create Team Member
            </Button>
          )}
        </div>
      </div>

      <div className="d-flex flex-wrap gap-2 mb-3 bg-white p-3 border rounded shadow-sm">
        <Form.Control
          size="sm"
          style={{ maxWidth: 260 }}
          placeholder="Search by name, email, designation…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          aria-label="Search members"
        />
        <Form.Select
          size="sm"
          style={{ width: "auto" }}
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          aria-label="Filter status"
        >
          <option value="all">All statuses</option>
          <option value="active">Active only</option>
          <option value="inactive">Inactive only</option>
        </Form.Select>
        <span className="ms-auto small text-muted align-self-center">
          Showing {displayMembers.length} of {members.length} member(s)
        </span>
      </div>

      {displayMembers.length === 0 ? (
        <EmptyState title="No members found">
          {isOwnerOrAdmin
            ? "Create your first Project Manager or team member using the button above."
            : "No team members created yet. Use 'Create Team Member' to add collaborators."}
        </EmptyState>
      ) : (
        <div className="table-responsive bg-white rounded border shadow-sm">
          <Table hover className="align-middle mb-0">
            <thead className="table-light">
              <tr>
                <th>Member / Name</th>
                <th>Role</th>
                <th>Designation</th>
                <th>Contact</th>
                <th>Status</th>
                <th>Assigned Projects</th>
                <th className="text-end">Actions</th>
              </tr>
            </thead>
            <tbody>
              {displayMembers.map((m) => (
                <tr key={m.id} className={!m.is_active ? "table-secondary text-muted" : undefined}>
                  <td>
                    <div className="fw-semibold text-dark">{m.full_name || "—"}</div>
                    <small className="text-muted">{m.email}</small>
                  </td>
                  <td>
                    <Badge
                      bg={
                        m.role === "owner"
                          ? "dark"
                          : m.role === "project_manager"
                          ? "primary"
                          : m.role === "admin"
                          ? "warning"
                          : "info"
                      }
                      className="text-capitalize"
                    >
                      {m.role?.replace("_", " ")}
                    </Badge>
                  </td>
                  <td>
                    <span className="small">{m.designation || <span className="text-muted">—</span>}</span>
                  </td>
                  <td>
                    <span className="small font-monospace">{m.contact_number || <span className="text-muted">—</span>}</span>
                  </td>
                  <td>
                    <Badge bg={m.is_active ? "success" : "secondary"}>
                      {m.is_active ? "Active" : "Deactivated"}
                    </Badge>
                  </td>
                  <td>
                    {m.assigned_projects?.length > 0 ? (
                      <div className="d-flex flex-wrap gap-1">
                        {m.assigned_projects.map((p) => (
                          <Link key={p.id} to={`/app/projects/${p.id}/board`} className="badge bg-light text-dark border text-decoration-none">
                            {p.key}
                          </Link>
                        ))}
                      </div>
                    ) : (
                      <span className="small text-muted">None</span>
                    )}
                  </td>
                  <td className="text-end">
                    <div className="btn-group btn-group-sm">
                      <Button variant="outline-secondary" title="Edit member details" onClick={() => setEditingMember(m)}>
                        ✏️ Edit
                      </Button>
                      <Button variant="outline-secondary" title="View/Assign projects" onClick={() => setManagingProjects(m)}>
                        📁 Projects
                      </Button>
                      {m.role !== "owner" && (
                        <Button
                          variant={m.is_active ? "outline-warning" : "outline-success"}
                          onClick={() => setToggleActiveTarget(m)}
                        >
                          {m.is_active ? "Deactivate" : "Activate"}
                        </Button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </Table>
        </div>
      )}

      {/* Modals */}
      <CreatePMModal
        show={showCreatePM}
        onHide={() => setShowCreatePM(false)}
        onCreated={() => {
          setShowCreatePM(false);
          setNotice("Project Manager account created successfully! Notification email sent.");
          reloadMembers();
        }}
      />

      <CreateTeamMemberModal
        show={showCreateTM}
        projects={projects}
        onHide={() => setShowCreateTM(false)}
        onCreated={() => {
          setShowCreateTM(false);
          setNotice("Team Member account created and assigned to project! Notification email sent.");
          reloadMembers();
        }}
      />

      <EditMemberModal
        show={Boolean(editingMember)}
        member={editingMember}
        onHide={() => setEditingMember(null)}
        onUpdated={() => {
          setEditingMember(null);
          setNotice("Member details updated successfully.");
          reloadMembers();
        }}
      />

      <AssignProjectsModal
        show={Boolean(managingProjects)}
        member={managingProjects}
        projects={projects}
        onHide={() => setManagingProjects(null)}
        onUpdated={() => {
          setManagingProjects(null);
          setNotice("Project assignments updated.");
          reloadMembers();
        }}
      />

      <ConfirmModal
        show={Boolean(toggleActiveTarget)}
        title={toggleActiveTarget?.is_active ? "Deactivate Account?" : "Activate Account?"}
        confirmLabel={toggleActiveTarget?.is_active ? "Deactivate" : "Activate"}
        confirmVariant={toggleActiveTarget?.is_active ? "warning" : "success"}
        body={`Are you sure you want to ${
          toggleActiveTarget?.is_active ? "deactivate" : "activate"
        } account for ${toggleActiveTarget?.email}?`}
        onConfirm={doToggleActive}
        onCancel={() => setToggleActiveTarget(null)}
      />
    </div>
  );
}

// Main Responsive Unified Dashboard with Role Adaptation
export default function Dashboard() {
  const { user } = useAuth();
  const { base, can, workspace } = useWorkspace();
  const navigate = useNavigate();

  const role = workspace?.role || "member";
  const isOwnerOrAdmin = role === "owner" || role === "admin";
  const isPM = role === "project_manager";
  const isMember = role === "member";

  const [searchParams, setSearchParams] = useSearchParams();
  const tabFromUrl = searchParams.get("tab");
  const defaultTab = isMember ? "tasks" : "projects";

  const [q, setQ] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [showNewProject, setShowNewProject] = useState(false);
  const [activeTab, setActiveTab] = useState(tabFromUrl || defaultTab);
  const [taskFilter, setTaskFilter] = useState("");

  useEffect(() => {
    if (tabFromUrl && ["projects", "team", "tasks", "activity"].includes(tabFromUrl)) {
      setActiveTab(tabFromUrl);
    }
  }, [tabFromUrl]);

  const handleSelectTab = (k) => {
    setActiveTab(k);
    if (k && k !== defaultTab) {
      setSearchParams({ tab: k });
    } else {
      setSearchParams({});
    }
  };

  const projectsFetch = useFetch(`${base}/projects/`, { page_size: 100, q: q || undefined }, [base, q]);
  const membersFetch = useFetch(`${base}/members/`, { page_size: 100 }, [base]);
  const notifsFetch = useFetch(`${base}/notifications/`, { page_size: 10 }, [base]);

  const projects = projectsFetch.data?.results || [];
  const members = membersFetch.data?.results || [];
  const notifications = notifsFetch.data?.results || [];

  // Cross-project assigned tasks
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
  const roleTitle =
    role === "owner"
      ? "Company Owner"
      : role === "admin"
      ? "Company Administrator"
      : role === "project_manager"
      ? "Project Manager"
      : "Team Member";

  const pmCount = members.filter((m) => m.role === "project_manager").length;
  const tmCount = members.filter((m) => m.role === "member").length;

  return (
    <>
      {/* Role-Specific Corporate Header Banner */}
      <div className="bg-white p-4 rounded border mb-4 shadow-sm">
        <div className="d-flex flex-wrap justify-content-between align-items-center gap-3">
          <div>
            <div className="d-flex align-items-center gap-2 mb-1">
              <h1 className="h4 mb-0">Welcome, {displayName}</h1>
              <Badge bg={isOwnerOrAdmin ? "dark" : isPM ? "primary" : "info"}>{roleTitle}</Badge>
            </div>
            <p className="text-muted mb-0 small">
              Company Workspace: <strong>{workspace.workspace_name}</strong>
              {user.designation && <span> · Designation: <span className="text-dark fw-semibold">{user.designation}</span></span>}
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
                Settings
              </Link>
            )}
          </div>
        </div>
      </div>

      {/* Role-Adapted KPI Summary Metrics */}
      <div className="row g-3 mb-4">
        <div className="col-sm-6 col-lg-3">
          <Card className="border shadow-sm h-100">
            <Card.Body>
              <div className="text-muted small text-uppercase fw-semibold">{isMember ? "My Projects" : "Total Projects"}</div>
              <div className="h3 mb-0 mt-1">{projectsFetch.loading ? "…" : projects.length}</div>
              <small className="text-muted">{activeCount} active</small>
            </Card.Body>
          </Card>
        </div>
        <div className="col-sm-6 col-lg-3">
          <Card className="border shadow-sm h-100">
            <Card.Body>
              <div className="text-muted small text-uppercase fw-semibold">
                {isOwnerOrAdmin ? "Project Managers" : "My Assigned Tasks"}
              </div>
              <div className="h3 mb-0 mt-1">
                {isOwnerOrAdmin ? pmCount : loadingTasks ? "…" : assignedIssues.length}
              </div>
              <small className="text-muted">
                {isOwnerOrAdmin ? "Leading project delivery" : "Active tasks across projects"}
              </small>
            </Card.Body>
          </Card>
        </div>
        <div className="col-sm-6 col-lg-3">
          <Card className="border shadow-sm h-100">
            <Card.Body>
              <div className="text-muted small text-uppercase fw-semibold">
                {isPM ? "Team Members" : "Total Team"}
              </div>
              <div className="h3 mb-0 mt-1">
                {isPM ? tmCount : membersFetch.loading ? "…" : members.length}
              </div>
              <small className="text-muted">In this company</small>
            </Card.Body>
          </Card>
        </div>
        <div className="col-sm-6 col-lg-3">
          <Card className="border shadow-sm h-100">
            <Card.Body>
              <div className="text-muted small text-uppercase fw-semibold">Alerts & Updates</div>
              <div className="h3 mb-0 mt-1">{notifsFetch.loading ? "…" : notifications.length}</div>
              <small className="text-muted"><Link to="/app/notifications">View all</Link></small>
            </Card.Body>
          </Card>
        </div>
      </div>

      {/* Main Tabs Area */}
      <div className="row g-4">
        <div className="col-lg-8">
          <Tabs activeKey={activeTab} onSelect={handleSelectTab} className="mb-3">
            {/* Projects Tab */}
            <Tab eventKey="projects" title={isPM ? `My Projects (${projects.length})` : `Projects (${projects.length})`}>
              <div className="d-flex flex-wrap justify-content-between align-items-center gap-2 mb-3">
                <h2 className="h6 mb-0">{isPM ? "Projects Under Management" : "All Company Projects"}</h2>
                <div className="d-flex gap-2">
                  <Form.Select size="sm" style={{ width: "auto" }} value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)} aria-label="Filter status">
                    <option value="all">All statuses</option>
                    <option value="active">Active</option>
                    <option value="archived">Archived</option>
                  </Form.Select>
                  <Form.Control size="sm" style={{ maxWidth: 200 }} placeholder="Filter projects…" value={q} onChange={(e) => setQ(e.target.value)} aria-label="Search projects" />
                </div>
              </div>

              <ErrorAlert error={projectsFetch.error} onRetry={projectsFetch.reload} />
              {projectsFetch.loading && <Loading label="Loading projects…" />}

              {!projectsFetch.loading && filteredProjects.length === 0 && (
                <EmptyState title="No projects found">
                  {can(MANAGE) ? "Create your first project to begin organizing work." : "No projects assigned to you yet. Contact your Project Manager."}
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
                            👥 Project Team
                          </Link>
                        </div>
                      </Card.Body>
                    </Card>
                  </div>
                ))}
              </div>
            </Tab>

            {/* Dedicated Team Management Tab for Owner and Project Manager */}
            {(isOwnerOrAdmin || isPM) && (
              <Tab
                eventKey="team"
                title={
                  isOwnerOrAdmin
                    ? `Team Management (${pmCount} PMs)`
                    : `Team Management (${tmCount} Members)`
                }
              >
                <TeamManagementView
                  members={members}
                  projects={projects}
                  role={role}
                  reloadMembers={membersFetch.reload}
                />
              </Tab>
            )}

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
              <h2 className="h6 mb-3">Recent Company Activity</h2>
              {notifsFetch.loading ? (
                <Loading label="Loading activity feed…" />
              ) : notifications.length === 0 ? (
                <EmptyState title="No recent activity">
                  No notifications recorded recently in this workspace.
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
              {isOwnerOrAdmin && (
                <Button variant="outline-primary" size="sm" className="text-start" onClick={() => setActiveTab("team")}>
                  👔 Manage Project Managers
                </Button>
              )}
              {isPM && (
                <Button variant="outline-primary" size="sm" className="text-start" onClick={() => setActiveTab("team")}>
                  👥 Manage Team Members
                </Button>
              )}
              <Link to="/app/notifications" className="btn btn-sm btn-outline-secondary text-start">
                🔔 View Notifications ({notifications.length})
              </Link>
              {can(MANAGE) && (
                <Link to="/app/settings" className="btn btn-sm btn-outline-secondary text-start">
                  ⚙️ Company Settings & Members
                </Link>
              )}
              {can(MANAGE) && (
                <Link to="/app/billing" className="btn btn-sm btn-outline-secondary text-start">
                  💳 Subscription Plan
                </Link>
              )}
              <Link to="/app/profile" className="btn btn-sm btn-outline-secondary text-start">
                👤 My Profile Settings
              </Link>
            </Card.Body>
          </Card>

          {/* Company Members Snapshot */}
          <Card className="border shadow-sm">
            <Card.Header className="bg-white py-3 border-bottom d-flex justify-content-between align-items-center">
              <span className="fw-semibold">Team Members Snapshot</span>
              {(isOwnerOrAdmin || isPM) && (
                <Button variant="link" size="sm" className="p-0 text-decoration-none" onClick={() => setActiveTab("team")}>
                  Manage
                </Button>
              )}
            </Card.Header>
            <Card.Body className="p-0">
              {membersFetch.loading ? (
                <div className="p-3"><Loading /></div>
              ) : members.length === 0 ? (
                <p className="text-muted small p-3 mb-0">No members found.</p>
              ) : (
                <div className="list-group list-group-flush">
                  {members.slice(0, 6).map((m) => (
                    <div key={m.id} className="list-group-item p-3 d-flex justify-content-between align-items-center">
                      <div>
                        <div className="small fw-semibold text-truncate" style={{ maxWidth: 170 }}>
                          {m.full_name || m.email}
                        </div>
                        {m.designation && <div className="text-muted" style={{ fontSize: "0.75rem" }}>{m.designation}</div>}
                      </div>
                      <div className="d-flex flex-column align-items-end gap-1">
                        <Badge bg="light" text="dark" className="border text-capitalize">
                          {m.role?.replace("_", " ")}
                        </Badge>
                        {!m.is_active && <Badge bg="danger" style={{ fontSize: "0.65rem" }}>Inactive</Badge>}
                      </div>
                    </div>
                  ))}
                  {members.length > 6 && (
                    <div className="p-2 text-center border-top">
                      <small className="text-muted">+{members.length - 6} more members</small>
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
