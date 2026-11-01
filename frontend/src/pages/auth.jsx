import { useState } from "react";
import { Alert, Button, Card, Form } from "react-bootstrap";
import { Link, Navigate, useLocation, useNavigate, useSearchParams } from "react-router";
import { api, errorMessage, fieldErrors } from "../api/client";
import { PasswordInput } from "../components/common";
import { AuthLayout } from "../components/layouts";
import { useAuth } from "../context/AuthContext";
import { useWorkspace } from "../context/WorkspaceContext";

function Shell({ title, children }) {
  return (
    <AuthLayout>
      <Card><Card.Body className="p-4">
        <h1 className="h4 mb-3">{title}</h1>
        {children}
      </Card.Body></Card>
    </AuthLayout>
  );
}

export function Login() {
  const { login, user } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [params] = useSearchParams();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const next = location.state?.from || params.get("next");

  if (user && !busy) return <Navigate to={next || "/app"} replace />;

  const submit = async (e) => {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      const u = await login(email.trim(), password);
      if (u.is_platform_admin) {
        navigate("/platform-admin", { replace: true });
      } else {
        navigate(next || (u.memberships?.length ? "/app" : "/onboarding"), { replace: true });
      }
    } catch (err) {
      setError(errorMessage(err));
      setBusy(false);
    }
  };

  return (
    <Shell title="Log in">
      {location.state?.notice && <Alert variant="success">{location.state.notice}</Alert>}
      {error && <Alert variant="danger" role="alert">{error}</Alert>}
      <Form onSubmit={submit} noValidate={false}>
        <Form.Group className="mb-3" controlId="email">
          <Form.Label>Email</Form.Label>
          <Form.Control type="email" required autoComplete="email" value={email} onChange={(e) => setEmail(e.target.value)} />
        </Form.Group>
        <PasswordInput id="password" label="Password" value={password} autoComplete="current-password"
          onChange={(e) => setPassword(e.target.value)} />
        <Button type="submit" className="w-100" disabled={busy}>{busy ? "Signing in…" : "Log in"}</Button>
      </Form>
      <div className="d-flex justify-content-between mt-3 small">
        <Link to="/forgot-password">Forgot password?</Link>
        <Link to="/register">Create an account</Link>
      </div>
    </Shell>
  );
}

export function Register() {
  const navigate = useNavigate();
  const [form, setForm] = useState({ first_name: "", last_name: "", email: "", password: "", confirm: "" });
  const [errors, setErrors] = useState({});
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }));

  const submit = async (e) => {
    e.preventDefault();
    setError("");
    if (form.password !== form.confirm) return setErrors({ confirm: "Passwords do not match." });
    setErrors({});
    setBusy(true);
    try {
      await api.post("/auth/register/", {
        email: form.email.trim(),
        password: form.password,
        first_name: form.first_name,
        last_name: form.last_name,
      });
      navigate("/login", { state: { notice: "Account created. Please log in." } });
    } catch (err) {
      setErrors(fieldErrors(err));
      setError(errorMessage(err));
      setBusy(false);
    }
  };

  return (
    <Shell title="Create your account">
      {error && <Alert variant="danger" role="alert">{error}</Alert>}
      <Form onSubmit={submit}>
        <div className="row g-2 mb-3">
          <Form.Group className="col-6" controlId="first_name">
            <Form.Label>First name</Form.Label>
            <Form.Control value={form.first_name} onChange={set("first_name")} autoComplete="given-name" />
          </Form.Group>
          <Form.Group className="col-6" controlId="last_name">
            <Form.Label>Last name</Form.Label>
            <Form.Control value={form.last_name} onChange={set("last_name")} autoComplete="family-name" />
          </Form.Group>
        </div>
        <Form.Group className="mb-3" controlId="email">
          <Form.Label>Email</Form.Label>
          <Form.Control type="email" required value={form.email} onChange={set("email")} autoComplete="email"
            isInvalid={Boolean(errors.email)} />
          <Form.Control.Feedback type="invalid">{errors.email}</Form.Control.Feedback>
        </Form.Group>
        <PasswordInput id="password" label="Password" value={form.password} onChange={set("password")}
          autoComplete="new-password" error={errors.password} />
        <PasswordInput id="confirm" label="Confirm password" value={form.confirm} onChange={set("confirm")}
          autoComplete="new-password" error={errors.confirm} />
        <Button type="submit" className="w-100" disabled={busy}>{busy ? "Creating…" : "Create account"}</Button>
      </Form>
      <p className="mt-3 mb-0 small">Already registered? <Link to="/login">Log in</Link></p>
    </Shell>
  );
}

export function ForgotPassword() {
  const [email, setEmail] = useState("");
  const [sent, setSent] = useState(false);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      await api.post("/auth/password-reset/", { email: email.trim() });
      setSent(true);
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setBusy(false);
    }
  };

  return (
    <Shell title="Reset your password">
      {sent ? (
        <Alert variant="success">If that address has an account, a reset link is on its way. It expires in one hour.</Alert>
      ) : (
        <Form onSubmit={submit}>
          {error && <Alert variant="danger" role="alert">{error}</Alert>}
          <Form.Group className="mb-3" controlId="email">
            <Form.Label>Email</Form.Label>
            <Form.Control type="email" required value={email} onChange={(e) => setEmail(e.target.value)} />
          </Form.Group>
          <Button type="submit" className="w-100" disabled={busy}>{busy ? "Sending…" : "Send reset link"}</Button>
        </Form>
      )}
      <p className="mt-3 mb-0 small"><Link to="/login">Back to log in</Link></p>
    </Shell>
  );
}

export function ResetPassword() {
  const [params] = useSearchParams();
  const [pw, setPw] = useState("");
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState("");
  const [fieldErr, setFieldErr] = useState({});
  const [done, setDone] = useState(false);
  const [busy, setBusy] = useState(false);
  const uid = params.get("uid");
  const token = params.get("token");

  const submit = async (e) => {
    e.preventDefault();
    setError("");
    if (pw !== confirm) return setFieldErr({ confirm: "Passwords do not match." });
    setFieldErr({});
    setBusy(true);
    try {
      await api.post("/auth/password-reset/confirm/", { uid, token, new_password: pw });
      setDone(true);
    } catch (err) {
      setFieldErr({ new_password: fieldErrors(err).new_password });
      setError(errorMessage(err));
    } finally {
      setBusy(false);
    }
  };

  if (!uid || !token) return <Shell title="Reset your password"><Alert variant="danger">This reset link is incomplete. <Link to="/forgot-password">Request a new one.</Link></Alert></Shell>;
  return (
    <Shell title="Choose a new password">
      {done ? (
        <Alert variant="success">Password updated. <Link to="/login">Log in</Link></Alert>
      ) : (
        <Form onSubmit={submit}>
          {error && <Alert variant="danger" role="alert">{error}</Alert>}
          <PasswordInput id="new_password" label="New password" value={pw} onChange={(e) => setPw(e.target.value)}
            autoComplete="new-password" error={fieldErr.new_password} />
          <PasswordInput id="confirm" label="Confirm password" value={confirm} onChange={(e) => setConfirm(e.target.value)}
            autoComplete="new-password" error={fieldErr.confirm} />
          <Button type="submit" className="w-100" disabled={busy}>{busy ? "Saving…" : "Update password"}</Button>
        </Form>
      )}
    </Shell>
  );
}

export function AcceptInvite() {
  const [params] = useSearchParams();
  const token = params.get("token");
  const { user, loading, refresh } = useAuth();
  const { setActive } = useWorkspace();
  const navigate = useNavigate();
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const here = `/accept-invite?token=${encodeURIComponent(token || "")}`;

  const accept = async () => {
    setBusy(true);
    setError("");
    try {
      const res = await api.post("/invitations/accept/", { token });
      await refresh();
      setActive(res.data.workspace_id);
      navigate("/app", { replace: true });
    } catch (err) {
      setError(errorMessage(err));
      setBusy(false);
    }
  };

  return (
    <Shell title="Workspace invitation">
      {!token && <Alert variant="danger">This invitation link is incomplete.</Alert>}
      {token && loading && <p>Checking your session…</p>}
      {token && !loading && !user && (
        <>
          <p>Sign in or create an account using the email address that received this invitation.</p>
          <div className="d-flex gap-2">
            <Link className="btn btn-primary" to={`/login?next=${encodeURIComponent(here)}`}>Log in</Link>
            <Link className="btn btn-outline-primary" to="/register">Register</Link>
          </div>
        </>
      )}
      {token && user && (
        <>
          {error && <Alert variant="danger" role="alert">{error}</Alert>}
          <p>Signed in as <strong>{user.email}</strong>. Accept the invitation to join the workspace.</p>
          <Button onClick={accept} disabled={busy}>{busy ? "Joining…" : "Accept invitation"}</Button>
        </>
      )}
    </Shell>
  );
}
