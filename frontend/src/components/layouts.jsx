import { useEffect, useState } from "react";
import { Badge, Container, Dropdown, Nav, Navbar } from "react-bootstrap";
import { Link, NavLink, Navigate, Outlet, useLocation, useNavigate } from "react-router";
import { api } from "../api/client";
import { useAuth } from "../context/AuthContext";
import { useWorkspace } from "../context/WorkspaceContext";
import Logo from "./Logo";
import { Loading } from "./common";

/** Logo-only header for login / register / reset pages (no site navigation). */
export function AuthLayout({ children }) {
  return (
    <div className="tt-auth-wrap">
      <header className="py-4 text-center bg-white border-bottom"><Logo size={40} /></header>
      <main className="flex-grow-1 d-flex align-items-center justify-content-center p-3">
        <div className="tt-auth-card">{children}</div>
      </main>
    </div>
  );
}

export function ProtectedRoute({ children }) {
  const { user, loading } = useAuth();
  const location = useLocation();
  if (loading) return <Loading label="Checking your session…" />;
  if (!user) return <Navigate to="/login" replace state={{ from: location.pathname + location.search }} />;
  return children;
}

function Bell() {
  const { base } = useWorkspace();
  const [count, setCount] = useState(0);
  useEffect(() => {
    if (!base) return undefined;
    let alive = true;
    const poll = () => api.get(`${base}/notifications/`, { params: { unread: "true", page_size: 1 } })
      .then((r) => alive && setCount(r.data.count)).catch(() => {});
    poll();
    const t = setInterval(poll, 60000);
    return () => { alive = false; clearInterval(t); };
  }, [base]);
  return (
    <Nav.Link as={Link} to="/app/notifications" aria-label={`Notifications, ${count} unread`}>
      Notifications {count > 0 && <Badge bg="danger" pill>{count}</Badge>}
    </Nav.Link>
  );
}

export function AppLayout() {
  const { user, logout } = useAuth();
  const { memberships, workspace, setActive, can } = useWorkspace();
  const navigate = useNavigate();
  const location = useLocation();

  if (!workspace) return <Navigate to="/onboarding" replace />;

  const doLogout = async () => { await logout(); navigate("/login"); };
  const link = ({ isActive }) => `tt-sidebar-link${isActive ? " active" : ""}`;

  return (
    <>
      <Navbar expand="md" className="tt-navbar" sticky="top">
        <Container fluid>
          <Navbar.Brand as="span"><Logo size={30} to="/app" /></Navbar.Brand>
          <Navbar.Toggle aria-controls="main-nav" />
          <Navbar.Collapse id="main-nav">
            <Nav className="me-auto align-items-md-center">
              <Dropdown as={Nav.Item}>
                <Dropdown.Toggle as={Nav.Link} id="ws-switcher" aria-label="Switch workspace">
                  {workspace.workspace_name}
                </Dropdown.Toggle>
                <Dropdown.Menu>
                  {memberships.map((m) => (
                    <Dropdown.Item key={m.workspace_id} active={m.workspace_id === workspace.workspace_id}
                      onClick={() => { setActive(m.workspace_id); navigate("/app"); }}>
                      {m.workspace_name} <small className="text-muted">({m.role.replace("_", " ")})</small>
                    </Dropdown.Item>
                  ))}
                  <Dropdown.Divider />
                  <Dropdown.Item as={Link} to="/onboarding">Create workspace</Dropdown.Item>
                </Dropdown.Menu>
              </Dropdown>
              <Bell />
            </Nav>
            <Dropdown align="end">
              <Dropdown.Toggle variant="outline-primary" size="sm" id="user-menu">{user.email}</Dropdown.Toggle>
              <Dropdown.Menu>
                <Dropdown.Item as={Link} to="/app/profile">Profile</Dropdown.Item>
                <Dropdown.Divider />
                <Dropdown.Item onClick={doLogout}>Log out</Dropdown.Item>
              </Dropdown.Menu>
            </Dropdown>
          </Navbar.Collapse>
        </Container>
      </Navbar>
      <Container fluid className="py-3">
        <div className="row g-3">
          <nav className="col-md-2" aria-label="Workspace">
            <NavLink
              end
              to="/app"
              className={() => `tt-sidebar-link${location.pathname === "/app" && !location.search.includes("tab=team") ? " active" : ""}`}
            >
              Dashboard
            </NavLink>
            {can(["owner", "admin", "project_manager"]) && (
              <NavLink
                to="/app?tab=team"
                className={() => `tt-sidebar-link${location.pathname === "/app" && location.search.includes("tab=team") ? " active" : ""}`}
              >
                👥 Team Management
              </NavLink>
            )}
            <NavLink to="/app/notifications" className={link}>Notifications</NavLink>
            {can(["owner", "admin"]) && <NavLink to="/app/settings" className={link}>Workspace settings</NavLink>}
            {can(["owner", "admin"]) && <NavLink to="/app/billing" className={link}>Billing</NavLink>}
            <NavLink to="/app/profile" className={link}>Profile</NavLink>
            <div className="mt-4 pt-3 border-top">
              <Link to="/platform-admin/login" className="btn btn-outline-dark btn-sm w-100 fw-semibold text-start">
                🛡️ Platform Admin
              </Link>
            </div>
          </nav>
          <main className="col-md-10"><Outlet /></main>
        </div>
      </Container>
    </>
  );
}
