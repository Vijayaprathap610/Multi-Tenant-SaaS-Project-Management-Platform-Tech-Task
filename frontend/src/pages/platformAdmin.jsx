import { useEffect, useState } from "react";
import { Alert, Button, Card, Form, Table } from "react-bootstrap";
import { Link, Navigate, useNavigate } from "react-router";
import { api, ensureCsrf, errorMessage } from "../api/client";
import { Loading, PasswordInput } from "../components/common";
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
      <Card><Card.Body className="p-4">
        <h1 className="h4 mb-3">Platform administrator</h1>
        {error && <Alert variant="danger" role="alert">{error}</Alert>}
        <Form onSubmit={submit}>
          <Form.Group className="mb-3" controlId="email"><Form.Label>Email</Form.Label>
            <Form.Control type="email" required autoComplete="username" value={email} onChange={(e) => setEmail(e.target.value)} /></Form.Group>
          <PasswordInput id="password" label="Password" value={password} autoComplete="current-password" onChange={(e) => setPassword(e.target.value)} />
          <Button type="submit" className="w-100" disabled={busy}>{busy ? "Signing in…" : "Sign in"}</Button>
        </Form>
        <div className="text-center mt-3 pt-2 border-top">
          <Link to="/login" className="btn btn-outline-primary btn-sm w-100">
            &larr; Go to General Login (Company & Staff)
          </Link>
        </div>
      </Card.Body></Card>
    </AuthLayout>
  );
}

export function PlatformAdminDashboard() {
  const navigate = useNavigate();
  const [state, setState] = useState({ loading: true, data: null, denied: false, error: "" });

  useEffect(() => {
    api.get("/platform-admin/stats/")
      .then((r) => setState({ loading: false, data: r.data, denied: false, error: "" }))
      .catch((err) => setState({ loading: false, data: null, denied: [401, 403].includes(err.response?.status), error: errorMessage(err) }));
  }, []);

  const logout = async () => { await api.post("/auth/logout/").catch(() => {}); navigate("/platform-admin/login"); };

  if (state.loading) return <Loading />;
  if (state.denied) return <Navigate to="/platform-admin/login" replace />;
  const d = state.data;
  return (
    <>
      <header className="tt-navbar py-3 d-flex justify-content-between align-items-center px-4">
        <Logo size={32} to="/platform-admin" />
        <Button variant="outline-primary" size="sm" onClick={logout}>Log out</Button>
      </header>
      <main className="container py-4">
        <h1 className="h4 mb-3">Platform overview</h1>
        {state.error && <Alert variant="danger">{state.error}</Alert>}
        {d && (
          <>
            <div className="row g-3 mb-4">
              {[["Registered users", d.total_users], ["Workspaces", d.total_workspaces], ["Memberships", d.total_memberships]].map(([t, v]) => (
                <div className="col-md-4" key={t}><Card><Card.Body><div className="text-muted small">{t}</div><div className="display-6">{v}</div></Card.Body></Card></div>
              ))}
            </div>
            <Card><Card.Body>
              <h2 className="h6">Subscriptions</h2>
              {d.subscriptions.length === 0 ? <p className="text-muted mb-0">No paid subscriptions yet.</p> : (
                <Table size="sm" className="mb-0"><thead><tr><th>Plan</th><th>Status</th><th>Workspaces</th></tr></thead>
                  <tbody>{d.subscriptions.map((s) => <tr key={`${s.plan}-${s.status}`}><td>{s.plan}</td><td>{s.status}</td><td>{s.count}</td></tr>)}</tbody></Table>
              )}
            </Card.Body></Card>
            <p className="small text-muted mt-3">Aggregate figures only. Tenant content is not accessible from this console.</p>
          </>
        )}
      </main>
    </>
  );
}
