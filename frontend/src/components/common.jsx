import { useState } from "react";
import { Alert, Button, Form, InputGroup, Modal, Spinner } from "react-bootstrap";

export function Loading({ label = "Loading…" }) {
  return (
    <div className="d-flex align-items-center gap-2 py-4 justify-content-center" role="status">
      <Spinner animation="border" size="sm" /> <span>{label}</span>
    </div>
  );
}

export function ErrorAlert({ error, onRetry }) {
  if (!error) return null;
  return (
    <Alert variant="danger" className="d-flex justify-content-between align-items-center" role="alert">
      <span>{error}</span>
      {onRetry && <Button size="sm" variant="outline-danger" onClick={onRetry}>Retry</Button>}
    </Alert>
  );
}

export function EmptyState({ title, children }) {
  return (
    <div className="text-center text-muted py-5">
      <h2 className="h6">{title}</h2>
      <div>{children}</div>
    </div>
  );
}

export function ConfirmModal({ show, title, body, confirmLabel = "Delete", confirmVariant = "danger", onConfirm, onCancel, busy }) {
  return (
    <Modal show={show} onHide={onCancel} centered>
      <Modal.Header closeButton><Modal.Title as="h2" className="h5">{title}</Modal.Title></Modal.Header>
      <Modal.Body>{body}</Modal.Body>
      <Modal.Footer>
        <Button variant="outline-secondary" onClick={onCancel}>Cancel</Button>
        <Button variant={confirmVariant} onClick={onConfirm} disabled={busy}>{busy ? "Working…" : confirmLabel}</Button>
      </Modal.Footer>
    </Modal>
  );
}

export function PasswordInput({ id, label, value, onChange, error, autoComplete, required = true }) {
  const [shown, setShown] = useState(false);
  return (
    <Form.Group className="mb-3" controlId={id}>
      <Form.Label>{label}</Form.Label>
      <InputGroup hasValidation>
        <Form.Control type={shown ? "text" : "password"} value={value} onChange={onChange} required={required}
          autoComplete={autoComplete} isInvalid={Boolean(error)} />
        <Button variant="outline-secondary" type="button" onClick={() => setShown((s) => !s)}
          aria-label={shown ? "Hide password" : "Show password"} aria-pressed={shown}>
          {shown ? "Hide" : "Show"}
        </Button>
        <Form.Control.Feedback type="invalid">{error}</Form.Control.Feedback>
      </InputGroup>
    </Form.Group>
  );
}

export const statusVariant = { todo: "secondary", in_progress: "warning", done: "success" };
export const fmtDate = (v) => (v ? new Date(v).toLocaleDateString() : "—");
export const fmtDateTime = (v) => (v ? new Date(v).toLocaleString() : "—");
