import { Container } from "react-bootstrap";
import { Link } from "react-router";
import Logo from "../components/Logo";

const FEATURES = [
  ["Kanban boards", "Drag issues between columns; every move is validated by your project's workflow."],
  ["Configurable workflows", "Define statuses and which transitions are allowed, per project."],
  ["Sprints", "Plan, start and complete sprints, and roll unfinished work forward."],
  ["Roles and isolation", "Owners, admins, project managers and members, with every company's data kept separate."],
  ["Comments and attachments", "Discuss issues and attach files with server-side validation."],
  ["Webhooks and audit log", "Signed webhooks for integrations and an audit trail of important changes."],
];

export default function Landing() {
  return (
    <>
      <header className="tt-navbar py-3">
        <Container className="d-flex justify-content-between align-items-center">
          <Logo size={34} />
          <nav aria-label="Public" className="d-flex gap-2">
            <Link to="/login" className="btn btn-outline-primary">Log in</Link>
            <Link to="/register" className="btn btn-primary">Get started</Link>
          </nav>
        </Container>
      </header>
      <main>
        <Container className="py-5 text-center">
          <h1 className="display-5 fw-bold" style={{ color: "var(--tt-primary)" }}>Project management for teams that ship</h1>
          <p className="lead mx-auto" style={{ maxWidth: 640 }}>
            Plan sprints, track issues on a Kanban board and keep every company's work private on one platform.
          </p>
          <Link to="/register" className="btn btn-primary btn-lg">Create your workspace</Link>
        </Container>
        <Container className="pb-5">
          <div className="row g-3">
            {FEATURES.map(([title, text]) => (
              <div className="col-md-4" key={title}>
                <div className="card h-100"><div className="card-body">
                  <h2 className="h6">{title}</h2><p className="mb-0">{text}</p>
                </div></div>
              </div>
            ))}
          </div>
        </Container>
      </main>
      <footer className="text-center text-muted py-4 small">Tech Task</footer>
    </>
  );
}
