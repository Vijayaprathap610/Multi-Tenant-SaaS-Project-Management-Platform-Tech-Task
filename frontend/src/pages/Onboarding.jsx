import { useState } from "react";
import { Alert, Button, Card, Form } from "react-bootstrap";
import { useNavigate } from "react-router";
import { api, errorMessage } from "../api/client";
import { AuthLayout } from "../components/layouts";
import { useAuth } from "../context/AuthContext";
import { useWorkspace } from "../context/WorkspaceContext";

export default function Onboarding() {
  const { refresh } = useAuth();
  const { setActive, memberships } = useWorkspace();
  const navigate = useNavigate();
  const [name, setName] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      const res = await api.post("/workspaces/", { name: name.trim() });
      await refresh();
      setActive(res.data.id);
      navigate("/app", { replace: true });
    } catch (err) {
      setError(errorMessage(err));
      setBusy(false);
    }
  };

  return (
    <AuthLayout>
      <Card><Card.Body className="p-4">
        <h1 className="h4">{memberships.length ? "Create another workspace" : "Create your workspace"}</h1>
        <p className="text-muted">A workspace is your company's private space for projects, boards and people. You become its Owner.</p>
        <p className="small text-muted">Were you invited? Open the link in your invitation email instead.</p>
        {error && <Alert variant="danger" role="alert">{error}</Alert>}
        <Form onSubmit={submit}>
          <Form.Group className="mb-3" controlId="ws-name">
            <Form.Label>Workspace name</Form.Label>
            <Form.Control required maxLength={120} value={name} onChange={(e) => setName(e.target.value)} />
          </Form.Group>
          <Button type="submit" className="w-100" disabled={busy || !name.trim()}>{busy ? "Creating…" : "Create workspace"}</Button>
        </Form>
      </Card.Body></Card>
    </AuthLayout>
  );
}
