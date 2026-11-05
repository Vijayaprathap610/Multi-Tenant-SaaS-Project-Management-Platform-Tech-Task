import { useEffect, useState } from "react";
import { Alert, Badge, Button, Card, Col, Form, InputGroup, Modal, Nav, Row, Table } from "react-bootstrap";
import { Link, Navigate, useNavigate } from "react-router";
import { api, ensureCsrf, errorMessage } from "../api/client";
import { EmptyState, Loading, PasswordInput, fmtDate, fmtDateTime } from "../components/common";
import Logo from "../components/Logo";
import { AuthLayout } from "../components/layouts";

export function PlatformAdminLogin() {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      await ensureCsrf();
      await api.post("/platform-admin/login/", { email: email.trim(), password });
      navigate("/platform-admin", { replace: true });
    } catch (err) {
      setError(errorMessage(err));
      setBusy(false);
    }
  };

  return (
    <AuthLayout>
      <Card>
        <Card.Body className="p-4">
          <div className="d-flex align-items-center justify-content-between mb-3">
            <h1 className="h4 mb-0">Platform Admin</h1>
            <Badge bg="dark">Root Control</Badge>
          </div>
          <p className="text-muted small mb-4">
            Sign in with platform administrator credentials to manage companies, subscriptions, and platform settings.
          </p>
          {error && <Alert variant="danger" role="alert">{error}</Alert>}
          <Form onSubmit={submit}>
            <Form.Group className="mb-3" controlId="email">
              <Form.Label>Email</Form.Label>
              <Form.Control
                type="email"
                required
                autoComplete="username"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
            </Form.Group>
            <PasswordInput
              id="password"
              label="Password"
              value={password}
              autoComplete="current-password"
              onChange={(e) => setPassword(e.target.value)}
            />
            <Button type="submit" className="w-100 mt-2" disabled={busy}>
              {busy ? "Authenticating…" : "Sign in as Platform Admin"}
            </Button>
          </Form>
          <div className="text-center mt-3 pt-2 border-top">
            <Link to="/login" className="btn btn-outline-primary btn-sm w-100">
              &larr; Go to General Login (Company & Staff)
            </Link>
          </div>
        </Card.Body>
      </Card>
    </AuthLayout>
  );
}

// Company Details Modal
function CompanyDetailModal({ companyId, show, onHide, onUpdated }) {
  const [loading, setLoading] = useState(true);
  const [company, setCompany] = useState(null);
  const [error, setError] = useState("");
  const [selectedPlan, setSelectedPlan] = useState("");
  const [savingPlan, setSavingPlan] = useState(false);

  useEffect(() => {
    if (!companyId || !show) return;
    setLoading(true);
    setError("");
    api.get(`/platform-admin/companies/${companyId}/`)
      .then((r) => {
        setCompany(r.data);
        setSelectedPlan(r.data.subscription?.plan || "free");
        setLoading(false);
      })
      .catch((err) => {
        setError(errorMessage(err));
        setLoading(false);
      });
  }, [companyId, show]);

  const savePlan = async () => {
    setSavingPlan(true);
    try {
      await api.patch(`/platform-admin/companies/${companyId}/`, { plan: selectedPlan });
      if (onUpdated) onUpdated();
      setCompany((prev) => ({
        ...prev,
        subscription: { ...prev.subscription, plan: selectedPlan, status: "active" },
      }));
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setSavingPlan(false);
    }
  };

  return (
    <Modal show={show} onHide={onHide} size="lg" centered>
      <Modal.Header closeButton>
        <Modal.Title className="h5">
          🏢 Company Details {company && `– ${company.workspace.name}`}
        </Modal.Title>
      </Modal.Header>
      <Modal.Body>
        {loading ? (
          <Loading label="Loading company details…" />
        ) : error ? (
          <Alert variant="danger">{error}</Alert>
        ) : company ? (
          <div>
            <div className="row g-3 mb-4">
              <div className="col-md-6">
                <Card className="h-100 border">
                  <Card.Body>
                    <h6 className="text-muted small text-uppercase mb-2">Company Information</h6>
                    <div className="mb-1"><strong>Name:</strong> {company.workspace.name}</div>
                    <div className="mb-1"><strong>Slug:</strong> <code>{company.workspace.slug}</code></div>
                    <div className="mb-1"><strong>Registered:</strong> {fmtDateTime(company.workspace.created_at)}</div>
                    <div>
                      <strong>Owner:</strong> {company.owner ? `${company.owner.name} (${company.owner.email})` : "None"}
                    </div>
                  </Card.Body>
                </Card>
              </div>
              <div className="col-md-6">
                <Card className="h-100 border">
                  <Card.Body>
                    <h6 className="text-muted small text-uppercase mb-2">Subscription & Plan Control</h6>
                    <div className="d-flex align-items-center gap-2 mb-2">
                      <span className="text-muted">Current:</span>
                      <Badge bg={company.subscription?.plan === "business" ? "dark" : company.subscription?.plan === "pro" ? "primary" : "secondary"} className="text-uppercase">
                        {company.subscription?.plan || "free"}
                      </Badge>
                      <Badge bg={company.subscription?.status === "active" ? "success" : "warning"}>
                        {company.subscription?.status || "inactive"}
                      </Badge>
                    </div>
                    <div className="d-flex gap-2 align-items-center mt-3">
                      <Form.Select
                        size="sm"
                        value={selectedPlan}
                        onChange={(e) => setSelectedPlan(e.target.value)}
                        style={{ maxWidth: "160px" }}
                      >
                        <option value="free">Free Plan</option>
                        <option value="pro">Pro Plan</option>
                        <option value="business">Business Plan</option>
                      </Form.Select>
                      <Button
                        size="sm"
                        variant="primary"
                        onClick={savePlan}
                        disabled={savingPlan || selectedPlan === company.subscription?.plan}
                      >
                        {savingPlan ? "Saving…" : "Update Plan"}
                      </Button>
                    </div>
                  </Card.Body>
                </Card>
              </div>
            </div>

            <h6 className="mt-4 mb-2">👥 Company Members ({company.members?.length || 0})</h6>
            {company.members?.length > 0 ? (
              <Table size="sm" responsive className="table-bordered align-middle">
                <thead className="table-light">
                  <tr>
                    <th>Name</th>
                    <th>Email</th>
                    <th>Role</th>
                    <th>Designation</th>
                    <th>Status</th>
                    <th>Joined</th>
                  </tr>
                </thead>
                <tbody>
                  {company.members.map((m) => (
                    <tr key={m.id}>
                      <td>{m.name}</td>
                      <td><code>{m.email}</code></td>
                      <td>
                        <Badge bg={m.role === "owner" ? "danger" : m.role === "admin" ? "warning" : m.role === "project_manager" ? "info" : "secondary"}>
                          {m.role}
                        </Badge>
                      </td>
                      <td>{m.designation || "—"}</td>
                      <td>
                        <Badge bg={m.is_active ? "success" : "secondary"}>
                          {m.is_active ? "Active" : "Inactive"}
                        </Badge>
                      </td>
                      <td className="small text-muted">{fmtDate(m.created_at)}</td>
                    </tr>
                  ))}
                </tbody>
              </Table>
            ) : (
              <p className="text-muted small">No members found.</p>
            )}

            <h6 className="mt-4 mb-2">📁 Projects ({company.projects?.length || 0})</h6>
            {company.projects?.length > 0 ? (
              <Table size="sm" responsive className="table-bordered align-middle">
                <thead className="table-light">
                  <tr>
                    <th>Project Name</th>
                    <th>Key</th>
                    <th>Status</th>
                    <th>Issues Count</th>
                    <th>Created</th>
                  </tr>
                </thead>
                <tbody>
                  {company.projects.map((p) => (
                    <tr key={p.id}>
                      <td>{p.name}</td>
                      <td><code>{p.key}</code></td>
                      <td>
                        <Badge bg={p.status === "active" ? "success" : "secondary"}>
                          {p.status}
                        </Badge>
                      </td>
                      <td>{p.issues_count}</td>
                      <td className="small text-muted">{fmtDate(p.created_at)}</td>
                    </tr>
                  ))}
                </tbody>
              </Table>
            ) : (
              <p className="text-muted small">No projects created yet.</p>
            )}
          </div>
        ) : null}
      </Modal.Body>
      <Modal.Footer>
        <Button variant="secondary" onClick={onHide}>Close</Button>
      </Modal.Footer>
    </Modal>
  );
}

// Change Plan Modal
function ChangePlanModal({ show, onHide, workspace, onPlanUpdated }) {
  const [plan, setPlan] = useState("pro");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (workspace?.plan) setPlan(workspace.plan);
  }, [workspace]);

  const submit = async (e) => {
    e.preventDefault();
    if (!workspace) return;
    setBusy(true);
    setError("");
    try {
      await api.patch(`/platform-admin/subscriptions/${workspace.id}/`, { plan, status: "active" });
      onPlanUpdated();
      onHide();
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setBusy(false);
    }
  };

  return (
    <Modal show={show} onHide={onHide} centered>
      <Form onSubmit={submit}>
        <Modal.Header closeButton>
          <Modal.Title className="h5">Change Subscription Plan</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          {error && <Alert variant="danger">{error}</Alert>}
          <p>
            Adjust the active subscription tier for <strong>{workspace?.name}</strong>.
          </p>
          <Form.Group className="mb-3">
            <Form.Label>Select Tier</Form.Label>
            <Form.Select value={plan} onChange={(e) => setPlan(e.target.value)}>
              <option value="free">Free Plan (3 members, 2 projects)</option>
              <option value="pro">Pro Plan (15 members, 20 projects)</option>
              <option value="business">Business Plan (Unlimited members & projects)</option>
            </Form.Select>
          </Form.Group>
        </Modal.Body>
        <Modal.Footer>
          <Button variant="outline-secondary" onClick={onHide}>Cancel</Button>
          <Button type="submit" variant="primary" disabled={busy}>
            {busy ? "Updating…" : "Apply Subscription"}
          </Button>
        </Modal.Footer>
      </Form>
    </Modal>
  );
}

export function PlatformAdminDashboard() {
  const navigate = useNavigate();
  const [authStatus, setAuthStatus] = useState({ loading: true, denied: false });
  const [currentTab, setCurrentTab] = useState("overview");

  // Overview stats & metrics
  const [stats, setStats] = useState(null);
  const [analytics, setAnalytics] = useState(null);

  // Companies
  const [companies, setCompanies] = useState([]);
  const [companiesLoading, setCompaniesLoading] = useState(false);
  const [companySearch, setCompanySearch] = useState("");
  const [companyPlanFilter, setCompanyPlanFilter] = useState("");
  const [selectedCompanyId, setSelectedCompanyId] = useState(null);
  const [planModalWs, setPlanModalWs] = useState(null);

  // Subscriptions
  const [subscriptions, setSubscriptions] = useState([]);
  const [subsLoading, setSubsLoading] = useState(false);

  // Users
  const [users, setUsers] = useState([]);
  const [usersLoading, setUsersLoading] = useState(false);
  const [userSearch, setUserSearch] = useState("");
  const [userStatusFilter, setUserStatusFilter] = useState("");

  // Activity logs
  const [activityLogs, setActivityLogs] = useState([]);
  const [activityLoading, setActivityLoading] = useState(false);

  // Settings
  const [platformSettings, setPlatformSettings] = useState(null);
  const [settingsLoading, setSettingsLoading] = useState(false);
  const [settingsSaving, setSettingsSaving] = useState(false);
  const [settingsSaved, setSettingsSaved] = useState(false);
  const [settingsError, setSettingsError] = useState("");

  // Initial Auth Check
  useEffect(() => {
    api.get("/platform-admin/stats/")
      .then((r) => {
        setStats(r.data);
        setAuthStatus({ loading: false, denied: false });
      })
      .catch((err) => {
        if ([401, 403].includes(err.response?.status)) {
          setAuthStatus({ loading: false, denied: true });
        } else {
          setAuthStatus({ loading: false, denied: false });
        }
      });
  }, []);

  // Fetch tab data when tab changes
  useEffect(() => {
    if (authStatus.denied || authStatus.loading) return;

    if (currentTab === "overview") {
      api.get("/platform-admin/analytics/").then((r) => setAnalytics(r.data)).catch(() => {});
      api.get("/platform-admin/stats/").then((r) => setStats(r.data)).catch(() => {});
    } else if (currentTab === "companies") {
      loadCompanies();
    } else if (currentTab === "subscriptions") {
      loadSubscriptions();
    } else if (currentTab === "users") {
      loadUsers();
    } else if (currentTab === "activity") {
      loadActivity();
    } else if (currentTab === "settings") {
      loadSettings();
    }
  }, [currentTab, authStatus.loading, authStatus.denied]);

  const loadCompanies = () => {
    setCompaniesLoading(true);
    const params = {};
    if (companySearch) params.q = companySearch;
    if (companyPlanFilter) params.plan = companyPlanFilter;
    api.get("/platform-admin/companies/", { params })
      .then((r) => {
        setCompanies(r.data);
        setCompaniesLoading(false);
      })
      .catch(() => setCompaniesLoading(false));
  };

  const loadSubscriptions = () => {
    setSubsLoading(true);
    api.get("/platform-admin/subscriptions/")
      .then((r) => {
        setSubscriptions(r.data);
        setSubsLoading(false);
      })
      .catch(() => setSubsLoading(false));
  };

  const loadUsers = () => {
    setUsersLoading(true);
    const params = {};
    if (userSearch) params.q = userSearch;
    if (userStatusFilter) params.active = userStatusFilter;
    api.get("/platform-admin/users/", { params })
      .then((r) => {
        setUsers(r.data);
        setUsersLoading(false);
      })
      .catch(() => setUsersLoading(false));
  };

  const toggleUserActive = async (userId, currentActive) => {
    try {
      await api.patch(`/platform-admin/users/${userId}/`, { is_active: !currentActive });
      loadUsers();
    } catch (err) {
      alert("Failed to update user status: " + errorMessage(err));
    }
  };

  const loadActivity = () => {
    setActivityLoading(true);
    api.get("/platform-admin/activity/")
      .then((r) => {
        setActivityLogs(r.data);
        setActivityLoading(false);
      })
      .catch(() => setActivityLoading(false));
  };

  const loadSettings = () => {
    setSettingsLoading(true);
    api.get("/platform-admin/settings/")
      .then((r) => {
        setPlatformSettings(r.data);
        setSettingsLoading(false);
      })
      .catch(() => setSettingsLoading(false));
  };

  const saveSettings = async (e) => {
    e.preventDefault();
    setSettingsSaving(true);
    setSettingsSaved(false);
    setSettingsError("");
    try {
      const res = await api.post("/platform-admin/settings/", platformSettings);
      setPlatformSettings(res.data);
      setSettingsSaved(true);
      setTimeout(() => setSettingsSaved(false), 4000);
    } catch (err) {
      setSettingsError(errorMessage(err));
    } finally {
      setSettingsSaving(false);
    }
  };

  const logout = async () => {
    await api.post("/auth/logout/").catch(() => {});
    navigate("/platform-admin/login");
  };

  if (authStatus.loading) return <Loading label="Checking Platform Admin authorization…" />;
  if (authStatus.denied) return <Navigate to="/platform-admin/login" replace />;

  return (
    <div style={{ minHeight: "100vh", display: "flex", flexDirection: "column" }}>
      {/* Top Admin Navbar */}
      <header className="tt-navbar py-2 px-4 d-flex justify-content-between align-items-center">
        <div className="d-flex align-items-center gap-3">
          <Logo size={32} to="/platform-admin" />
          <Badge bg="dark" className="px-2 py-1 text-uppercase" style={{ letterSpacing: "0.05em" }}>
            Platform Super Admin
          </Badge>
        </div>
        <div className="d-flex align-items-center gap-3">
          <span className="small text-muted d-none d-md-inline">Signed in as <strong>Root Administrator</strong></span>
          <Link to="/" className="btn btn-outline-secondary btn-sm">Public Site</Link>
          <Button variant="outline-primary" size="sm" onClick={logout}>Log out</Button>
        </div>
      </header>

      {/* Main Container */}
      <div className="container-fluid flex-grow-1 py-4 px-md-4">
        <div className="row g-4">
          {/* Left Navigation Sidebar */}
          <div className="col-lg-2 col-md-3">
            <Card className="border shadow-sm">
              <Card.Body className="p-2">
                <Nav className="flex-column nav-pills gap-1">
                  <Nav.Link
                    active={currentTab === "overview"}
                    onClick={() => setCurrentTab("overview")}
                    className="tt-sidebar-link d-flex align-items-center gap-2"
                  >
                    <span>📊</span> <span>Platform Overview</span>
                  </Nav.Link>
                  <Nav.Link
                    active={currentTab === "companies"}
                    onClick={() => setCurrentTab("companies")}
                    className="tt-sidebar-link d-flex align-items-center gap-2"
                  >
                    <span>🏢</span> <span>Companies ({stats?.total_workspaces ?? "…"})</span>
                  </Nav.Link>
                  <Nav.Link
                    active={currentTab === "subscriptions"}
                    onClick={() => setCurrentTab("subscriptions")}
                    className="tt-sidebar-link d-flex align-items-center gap-2"
                  >
                    <span>💳</span> <span>Subscriptions</span>
                  </Nav.Link>
                  <Nav.Link
                    active={currentTab === "users"}
                    onClick={() => setCurrentTab("users")}
                    className="tt-sidebar-link d-flex align-items-center gap-2"
                  >
                    <span>👥</span> <span>Users ({stats?.total_users ?? "…"})</span>
                  </Nav.Link>
                  <Nav.Link
                    active={currentTab === "activity"}
                    onClick={() => setCurrentTab("activity")}
                    className="tt-sidebar-link d-flex align-items-center gap-2"
                  >
                    <span>📜</span> <span>Audit Trail</span>
                  </Nav.Link>
                  <Nav.Link
                    active={currentTab === "settings"}
                    onClick={() => setCurrentTab("settings")}
                    className="tt-sidebar-link d-flex align-items-center gap-2"
                  >
                    <span>⚙️</span> <span>Platform Settings</span>
                  </Nav.Link>
                </Nav>
              </Card.Body>
            </Card>

            {/* Platform Status Widget */}
            <Card className="border shadow-sm mt-3">
              <Card.Body className="p-3">
                <div className="small fw-bold text-uppercase text-muted mb-2">Platform Status</div>
                <div className="d-flex align-items-center gap-2 mb-1">
                  <span className="badge bg-success rounded-pill p-1">●</span>
                  <span className="small">System: Operational</span>
                </div>
                <div className="d-flex align-items-center gap-2 mb-1">
                  <span className="badge bg-success rounded-pill p-1">●</span>
                  <span className="small">Database: Connected</span>
                </div>
                <div className="d-flex align-items-center gap-2">
                  <span className="badge bg-primary rounded-pill p-1">●</span>
                  <span className="small">Multi-tenant: Enforced</span>
                </div>
              </Card.Body>
            </Card>
          </div>

          {/* Right Main Content Area */}
          <div className="col-lg-10 col-md-9">
            {/* OVERVIEW TAB */}
            {currentTab === "overview" && (
              <div>
                <div className="d-flex justify-content-between align-items-center mb-3">
                  <div>
                    <h1 className="h4 mb-1">Platform Overview & Metrics</h1>
                    <p className="text-muted small mb-0">High-level telemetry across all registered companies and users.</p>
                  </div>
                  <div className="d-flex gap-2">
                    <Button variant="outline-primary" size="sm" onClick={() => setCurrentTab("companies")}>
                      Manage Companies &rarr;
                    </Button>
                    <Button variant="primary" size="sm" onClick={() => setCurrentTab("subscriptions")}>
                      View Subscriptions &rarr;
                    </Button>
                  </div>
                </div>

                {/* KPI Metrics Row */}
                <div className="row g-3 mb-4">
                  <div className="col-sm-6 col-lg-3">
                    <Card className="h-100 border shadow-sm">
                      <Card.Body>
                        <div className="text-muted small text-uppercase">Registered Users</div>
                        <div className="display-6 fw-bold my-1">{stats?.total_users ?? "—"}</div>
                        <div className="small text-muted">
                          {analytics ? `${analytics.active_users} active accounts` : "Across all tenants"}
                        </div>
                      </Card.Body>
                    </Card>
                  </div>
                  <div className="col-sm-6 col-lg-3">
                    <Card className="h-100 border shadow-sm">
                      <Card.Body>
                        <div className="text-muted small text-uppercase">Registered Companies</div>
                        <div className="display-6 fw-bold my-1">{stats?.total_workspaces ?? "—"}</div>
                        <div className="small text-muted">
                          {analytics ? `+${analytics.recent_workspaces_30d} past 30 days` : "Active workspaces"}
                        </div>
                      </Card.Body>
                    </Card>
                  </div>
                  <div className="col-sm-6 col-lg-3">
                    <Card className="h-100 border shadow-sm">
                      <Card.Body>
                        <div className="text-muted small text-uppercase">Total Projects</div>
                        <div className="display-6 fw-bold my-1">{analytics?.total_projects ?? "—"}</div>
                        <div className="small text-muted">
                          {analytics ? `${analytics.active_projects} currently active` : "Tenant projects"}
                        </div>
                      </Card.Body>
                    </Card>
                  </div>
                  <div className="col-sm-6 col-lg-3">
                    <Card className="h-100 border shadow-sm">
                      <Card.Body>
                        <div className="text-muted small text-uppercase">Total Issues & Tasks</div>
                        <div className="display-6 fw-bold my-1">{analytics?.total_issues ?? "—"}</div>
                        <div className="small text-muted">{stats?.total_memberships ?? 0} total memberships</div>
                      </Card.Body>
                    </Card>
                  </div>
                </div>

                {/* Subscriptions & Distribution */}
                <div className="row g-3 mb-4">
                  <div className="col-md-7">
                    <Card className="border shadow-sm h-100">
                      <Card.Header className="bg-white py-3">
                        <div className="h6 mb-0">Subscription Tiers Breakdown</div>
                      </Card.Header>
                      <Card.Body>
                        {stats?.subscriptions?.length === 0 ? (
                          <p className="text-muted mb-0">No paid subscriptions yet. All companies currently on Free tier.</p>
                        ) : (
                          <Table size="sm" responsive className="align-middle mb-0">
                            <thead>
                              <tr>
                                <th>Plan Tier</th>
                                <th>Status</th>
                                <th>Active Workspaces</th>
                              </tr>
                            </thead>
                            <tbody>
                              {stats?.subscriptions?.map((s) => (
                                <tr key={`${s.plan}-${s.status}`}>
                                  <td>
                                    <Badge bg={s.plan === "business" ? "dark" : s.plan === "pro" ? "primary" : "secondary"} className="text-uppercase">
                                      {s.plan}
                                    </Badge>
                                  </td>
                                  <td>
                                    <Badge bg={s.status === "active" ? "success" : "warning"}>
                                      {s.status}
                                    </Badge>
                                  </td>
                                  <td><strong>{s.count}</strong></td>
                                </tr>
                              ))}
                            </tbody>
                          </Table>
                        )}
                      </Card.Body>
                    </Card>
                  </div>
                  <div className="col-md-5">
                    <Card className="border shadow-sm h-100">
                      <Card.Header className="bg-white py-3">
                        <div className="h6 mb-0">Platform Security & Isolation</div>
                      </Card.Header>
                      <Card.Body>
                        <ul className="list-unstyled mb-0 small">
                          <li className="mb-2">🔒 <strong>Tenant Isolation:</strong> Enforced at database and API layers with <code>TenantModel</code>.</li>
                          <li className="mb-2">🛡️ <strong>Authentication:</strong> Strict role separation between Platform Admin and Company Staff.</li>
                          <li className="mb-2">💳 <strong>Billing:</strong> Stripe integration + Demo Gateway support.</li>
                          <li>📜 <strong>Audit Trail:</strong> Append-only immutable log for all critical actions.</li>
                        </ul>
                      </Card.Body>
                    </Card>
                  </div>
                </div>
              </div>
            )}

            {/* COMPANIES TAB */}
            {currentTab === "companies" && (
              <div>
                <div className="d-flex justify-content-between align-items-center mb-3">
                  <div>
                    <h1 className="h4 mb-1">Company & Workspace Management</h1>
                    <p className="text-muted small mb-0">Inspect, monitor and manage all tenant workspaces registered on the platform.</p>
                  </div>
                  <Button variant="outline-primary" size="sm" onClick={loadCompanies}>
                    🔄 Refresh
                  </Button>
                </div>

                {/* Filter & Search Bar */}
                <Card className="border shadow-sm mb-3">
                  <Card.Body className="p-3">
                    <div className="row g-2">
                      <div className="col-md-7">
                        <InputGroup size="sm">
                          <Form.Control
                            placeholder="Search by company name, slug, or owner email…"
                            value={companySearch}
                            onChange={(e) => setCompanySearch(e.target.value)}
                            onKeyDown={(e) => e.key === "Enter" && loadCompanies()}
                          />
                          <Button variant="outline-secondary" onClick={loadCompanies}>Search</Button>
                        </InputGroup>
                      </div>
                      <div className="col-md-3">
                        <Form.Select
                          size="sm"
                          value={companyPlanFilter}
                          onChange={(e) => { setCompanyPlanFilter(e.target.value); setTimeout(loadCompanies, 50); }}
                        >
                          <option value="">All Subscription Plans</option>
                          <option value="free">Free Plan</option>
                          <option value="pro">Pro Plan</option>
                          <option value="business">Business Plan</option>
                        </Form.Select>
                      </div>
                      <div className="col-md-2 text-end">
                        <span className="small text-muted">{companies.length} companies</span>
                      </div>
                    </div>
                  </Card.Body>
                </Card>

                {/* Companies Table */}
                <Card className="border shadow-sm">
                  <Card.Body className="p-0">
                    {companiesLoading ? (
                      <Loading label="Loading companies…" />
                    ) : companies.length === 0 ? (
                      <EmptyState title="No companies found">
                        Try adjusting your search query or plan filter.
                      </EmptyState>
                    ) : (
                      <Table responsive hover className="align-middle mb-0">
                        <thead className="table-light">
                          <tr>
                            <th>Company Name</th>
                            <th>Slug</th>
                            <th>Company Owner</th>
                            <th>Members</th>
                            <th>Projects</th>
                            <th>Plan</th>
                            <th>Created</th>
                            <th className="text-end">Actions</th>
                          </tr>
                        </thead>
                        <tbody>
                          {companies.map((c) => (
                            <tr key={c.id}>
                              <td>
                                <strong>{c.name}</strong>
                              </td>
                              <td><code>{c.slug}</code></td>
                              <td>
                                {c.owner ? (
                                  <div>
                                    <div>{c.owner.name || "Owner"}</div>
                                    <div className="small text-muted">{c.owner.email}</div>
                                  </div>
                                ) : (
                                  <span className="text-muted">—</span>
                                )}
                              </td>
                              <td><Badge bg="light" text="dark" className="border">{c.members_count}</Badge></td>
                              <td><Badge bg="light" text="dark" className="border">{c.projects_count}</Badge></td>
                              <td>
                                <Badge bg={c.plan === "business" ? "dark" : c.plan === "pro" ? "primary" : "secondary"} className="text-uppercase">
                                  {c.plan}
                                </Badge>
                              </td>
                              <td className="small text-muted">{fmtDate(c.created_at)}</td>
                              <td className="text-end">
                                <div className="btn-group btn-group-sm">
                                  <Button variant="outline-primary" onClick={() => setSelectedCompanyId(c.id)}>
                                    Details
                                  </Button>
                                  <Button variant="outline-secondary" onClick={() => setPlanModalWs(c)}>
                                    Plan
                                  </Button>
                                </div>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </Table>
                    )}
                  </Card.Body>
                </Card>
              </div>
            )}

            {/* SUBSCRIPTIONS TAB */}
            {currentTab === "subscriptions" && (
              <div>
                <div className="d-flex justify-content-between align-items-center mb-3">
                  <div>
                    <h1 className="h4 mb-1">Company Subscriptions Monitoring</h1>
                    <p className="text-muted small mb-0">Review active subscription plans, payment status, and period renewals across all companies.</p>
                  </div>
                  <Button variant="outline-primary" size="sm" onClick={loadSubscriptions}>
                    🔄 Refresh
                  </Button>
                </div>

                <Card className="border shadow-sm">
                  <Card.Body className="p-0">
                    {subsLoading ? (
                      <Loading label="Loading subscriptions…" />
                    ) : subscriptions.length === 0 ? (
                      <EmptyState title="No subscriptions found" />
                    ) : (
                      <Table responsive hover className="align-middle mb-0">
                        <thead className="table-light">
                          <tr>
                            <th>Workspace / Company</th>
                            <th>Owner Contact</th>
                            <th>Active Plan</th>
                            <th>Status</th>
                            <th>Customer / Subscription ID</th>
                            <th>Period End</th>
                            <th className="text-end">Manage</th>
                          </tr>
                        </thead>
                        <tbody>
                          {subscriptions.map((s) => (
                            <tr key={s.workspace_id}>
                              <td>
                                <strong>{s.workspace_name}</strong>
                                <div className="small text-muted"><code>{s.workspace_slug}</code></div>
                              </td>
                              <td>{s.owner_email || "—"}</td>
                              <td>
                                <Badge bg={s.plan === "business" ? "dark" : s.plan === "pro" ? "primary" : "secondary"} className="text-uppercase">
                                  {s.plan}
                                </Badge>
                              </td>
                              <td>
                                <Badge bg={s.status === "active" ? "success" : "warning"}>
                                  {s.status}
                                </Badge>
                              </td>
                              <td className="small text-muted">
                                {s.stripe_customer_id ? <code>{s.stripe_customer_id}</code> : <span className="text-muted">Demo Gateway</span>}
                              </td>
                              <td className="small text-muted">
                                {s.current_period_end ? fmtDate(s.current_period_end) : "Lifetime / Ongoing"}
                              </td>
                              <td className="text-end">
                                <Button
                                  variant="outline-primary"
                                  size="sm"
                                  onClick={() => setPlanModalWs({ id: s.workspace_id, name: s.workspace_name, plan: s.plan })}
                                >
                                  Override Plan
                                </Button>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </Table>
                    )}
                  </Card.Body>
                </Card>
              </div>
            )}

            {/* USERS TAB */}
            {currentTab === "users" && (
              <div>
                <div className="d-flex justify-content-between align-items-center mb-3">
                  <div>
                    <h1 className="h4 mb-1">Platform-Wide User Directory</h1>
                    <p className="text-muted small mb-0">Monitor all registered accounts, workspace memberships, and account statuses.</p>
                  </div>
                  <Button variant="outline-primary" size="sm" onClick={loadUsers}>
                    🔄 Refresh
                  </Button>
                </div>

                {/* Filter & Search */}
                <Card className="border shadow-sm mb-3">
                  <Card.Body className="p-3">
                    <div className="row g-2">
                      <div className="col-md-7">
                        <InputGroup size="sm">
                          <Form.Control
                            placeholder="Search by user email or name…"
                            value={userSearch}
                            onChange={(e) => setUserSearch(e.target.value)}
                            onKeyDown={(e) => e.key === "Enter" && loadUsers()}
                          />
                          <Button variant="outline-secondary" onClick={loadUsers}>Search</Button>
                        </InputGroup>
                      </div>
                      <div className="col-md-3">
                        <Form.Select
                          size="sm"
                          value={userStatusFilter}
                          onChange={(e) => { setUserStatusFilter(e.target.value); setTimeout(loadUsers, 50); }}
                        >
                          <option value="">All Statuses</option>
                          <option value="true">Active Only</option>
                          <option value="false">Inactive / Suspended</option>
                        </Form.Select>
                      </div>
                      <div className="col-md-2 text-end">
                        <span className="small text-muted">{users.length} users</span>
                      </div>
                    </div>
                  </Card.Body>
                </Card>

                {/* Users Table */}
                <Card className="border shadow-sm">
                  <Card.Body className="p-0">
                    {usersLoading ? (
                      <Loading label="Loading users…" />
                    ) : users.length === 0 ? (
                      <EmptyState title="No users found" />
                    ) : (
                      <Table responsive hover className="align-middle mb-0">
                        <thead className="table-light">
                          <tr>
                            <th>User Name</th>
                            <th>Email</th>
                            <th>Designation</th>
                            <th>Associated Companies</th>
                            <th>Status</th>
                            <th>Registered</th>
                            <th className="text-end">Actions</th>
                          </tr>
                        </thead>
                        <tbody>
                          {users.map((u) => (
                            <tr key={u.id}>
                              <td><strong>{u.name}</strong></td>
                              <td><code>{u.email}</code></td>
                              <td>{u.designation || "—"}</td>
                              <td>
                                {u.workspaces?.length > 0 ? (
                                  <div className="d-flex flex-wrap gap-1">
                                    {u.workspaces.map((ws) => (
                                      <Badge key={ws.id} bg="light" text="dark" className="border">
                                        {ws.name} ({ws.role})
                                      </Badge>
                                    ))}
                                  </div>
                                ) : (
                                  <span className="text-muted small">No company assigned</span>
                                )}
                              </td>
                              <td>
                                <Badge bg={u.is_active ? "success" : "danger"}>
                                  {u.is_active ? "Active" : "Suspended"}
                                </Badge>
                              </td>
                              <td className="small text-muted">{fmtDate(u.date_joined)}</td>
                              <td className="text-end">
                                <Button
                                  variant={u.is_active ? "outline-danger" : "outline-success"}
                                  size="sm"
                                  onClick={() => toggleUserActive(u.id, u.is_active)}
                                >
                                  {u.is_active ? "Suspend" : "Activate"}
                                </Button>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </Table>
                    )}
                  </Card.Body>
                </Card>
              </div>
            )}

            {/* AUDIT LOGS TAB */}
            {currentTab === "activity" && (
              <div>
                <div className="d-flex justify-content-between align-items-center mb-3">
                  <div>
                    <h1 className="h4 mb-1">Platform Audit Trail & Security Events</h1>
                    <p className="text-muted small mb-0">Immutable, chronological record of authentication and administrative events.</p>
                  </div>
                  <Button variant="outline-primary" size="sm" onClick={loadActivity}>
                    🔄 Refresh
                  </Button>
                </div>

                <Card className="border shadow-sm">
                  <Card.Body className="p-0">
                    {activityLoading ? (
                      <Loading label="Loading audit events…" />
                    ) : activityLogs.length === 0 ? (
                      <EmptyState title="No audit events recorded yet" />
                    ) : (
                      <Table responsive hover className="align-middle mb-0 font-monospace" style={{ fontSize: "0.85rem" }}>
                        <thead className="table-light">
                          <tr>
                            <th>Timestamp</th>
                            <th>Event</th>
                            <th>Actor</th>
                            <th>Workspace</th>
                            <th>Details</th>
                          </tr>
                        </thead>
                        <tbody>
                          {activityLogs.map((log) => (
                            <tr key={log.id}>
                              <td className="text-nowrap">{fmtDateTime(log.created_at)}</td>
                              <td>
                                <Badge bg={log.event_type.includes("failed") ? "danger" : log.event_type.includes("admin") ? "dark" : "info"}>
                                  {log.event_type}
                                </Badge>
                              </td>
                              <td>{log.actor_email}</td>
                              <td>{log.workspace_name}</td>
                              <td className="text-muted text-truncate" style={{ maxWidth: "250px" }}>
                                {log.metadata ? JSON.stringify(log.metadata) : "—"}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </Table>
                    )}
                  </Card.Body>
                </Card>
              </div>
            )}

            {/* SETTINGS TAB */}
            {currentTab === "settings" && (
              <div>
                <div className="d-flex justify-content-between align-items-center mb-3">
                  <div>
                    <h1 className="h4 mb-1">Platform-Level Global Settings</h1>
                    <p className="text-muted small mb-0">Configure system policies, registration toggles, and global defaults.</p>
                  </div>
                </div>

                {settingsSaved && (
                  <Alert variant="success" className="mb-3">
                    Platform settings updated successfully.
                  </Alert>
                )}
                {settingsError && (
                  <Alert variant="danger" className="mb-3">
                    {settingsError}
                  </Alert>
                )}

                <Card className="border shadow-sm">
                  <Card.Body className="p-4">
                    {settingsLoading ? (
                      <Loading label="Loading settings…" />
                    ) : platformSettings ? (
                      <Form onSubmit={saveSettings}>
                        <h6 className="text-uppercase text-muted small mb-3">Tenant Registration & Access</h6>
                        <Form.Check
                          type="switch"
                          id="allow-registration"
                          label="Allow New Company Self-Registration"
                          checked={platformSettings.allow_registration}
                          onChange={(e) => setPlatformSettings({ ...platformSettings, allow_registration: e.target.checked })}
                          className="mb-3"
                        />
                        <Form.Check
                          type="switch"
                          id="maintenance-mode"
                          label="Maintenance Mode (Prevent non-admin access)"
                          checked={platformSettings.maintenance_mode}
                          onChange={(e) => setPlatformSettings({ ...platformSettings, maintenance_mode: e.target.checked })}
                          className="mb-3"
                        />
                        <Form.Check
                          type="switch"
                          id="demo-gateway"
                          label="Demo Payment Gateway Active (Enables simulated card checkout without live Stripe keys)"
                          checked={platformSettings.demo_payment_gateway}
                          onChange={(e) => setPlatformSettings({ ...platformSettings, demo_payment_gateway: e.target.checked })}
                          className="mb-4"
                        />

                        <hr />
                        <h6 className="text-uppercase text-muted small mb-3">System Announcement Banner</h6>
                        <Form.Group className="mb-4" controlId="system-banner">
                          <Form.Label>Broadcast Message (Displayed to all company owners and staff)</Form.Label>
                          <Form.Control
                            placeholder="e.g. Scheduled maintenance this Sunday at 2 AM UTC."
                            value={platformSettings.system_banner}
                            onChange={(e) => setPlatformSettings({ ...platformSettings, system_banner: e.target.value })}
                          />
                        </Form.Group>

                        <hr />
                        <h6 className="text-uppercase text-muted small mb-3">Platform Administration Contact</h6>
                        <Row className="g-3 mb-4">
                          <Col md={6}>
                            <Form.Group controlId="support-email">
                              <Form.Label>Platform Support Email</Form.Label>
                              <Form.Control
                                type="email"
                                value={platformSettings.support_email}
                                onChange={(e) => setPlatformSettings({ ...platformSettings, support_email: e.target.value })}
                              />
                            </Form.Group>
                          </Col>
                        </Row>

                        <Button type="submit" variant="primary" disabled={settingsSaving}>
                          {settingsSaving ? "Saving Settings…" : "Save Platform Settings"}
                        </Button>
                      </Form>
                    ) : null}
                  </Card.Body>
                </Card>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Modals */}
      <CompanyDetailModal
        companyId={selectedCompanyId}
        show={Boolean(selectedCompanyId)}
        onHide={() => setSelectedCompanyId(null)}
        onUpdated={loadCompanies}
      />
      <ChangePlanModal
        workspace={planModalWs}
        show={Boolean(planModalWs)}
        onHide={() => setPlanModalWs(null)}
        onPlanUpdated={() => {
          loadCompanies();
          loadSubscriptions();
        }}
      />
    </div>
  );
}
