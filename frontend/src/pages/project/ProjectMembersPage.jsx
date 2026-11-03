import { useState } from "react";
import { Button, Card, Form, ListGroup } from "react-bootstrap";
import { useOutletContext } from "react-router";
import { all, api, errorMessage } from "../../api/client";
import { ErrorAlert } from "../../components/common";
import { useWorkspace } from "../../context/WorkspaceContext";
import useFetch from "../../hooks/useFetch";

export default function ProjectMembersPage() {
  const { base, members, canManage, reloadRef } = useOutletContext();
  const { base: wsBase } = useWorkspace();
  const wsMembers = useFetch(canManage ? `${wsBase}/members/` : null, { page_size: 200 }, [wsBase]);
  const [pick, setPick] = useState("");
  const [error, setError] = useState("");
  const inProject = new Set(members.map((m) => m.email));
  const candidates = (wsMembers.data?.results || []).filter((m) => !inProject.has(m.email));

  const add = async (e) => {
    e.preventDefault();
    setError("");
    try { await api.post(`${base}/members/`, { membership_id: pick }); setPick(""); await reloadRef(); wsMembers.reload(); }
    catch (err) { setError(errorMessage(err)); }
  };
  const remove = async (id) => {
    setError("");
    try { await api.delete(`${base}/members/${id}/`); await reloadRef(); } catch (err) { setError(errorMessage(err)); }
  };

  return (
    <Card><Card.Body>
      <h2 className="h6">Project members</h2>
      <p className="small text-muted">Owners and admins can access every project. Project managers and members see only projects they are added to.</p>
      <ErrorAlert error={error} />
      <ListGroup variant="flush" className="mb-3">
        {members.map((m) => (
          <ListGroup.Item key={m.id} className="d-flex justify-content-between align-items-center">
            <div>
              <span className="fw-semibold">{m.full_name || m.email}</span>
              {m.full_name && <small className="text-muted ms-2">({m.email})</small>}
              {m.designation && <span className="badge bg-light text-dark border ms-2">{m.designation}</span>}
            </div>
            {canManage && <Button size="sm" variant="outline-danger" onClick={() => remove(m.id)}>Remove</Button>}
          </ListGroup.Item>
        ))}
      </ListGroup>
      {canManage && (
        <Form onSubmit={add} className="d-flex gap-2">
          <Form.Group controlId="add-member" className="flex-grow-1">
            <Form.Label className="visually-hidden">Workspace member to add</Form.Label>
            <Form.Select value={pick} onChange={(e) => setPick(e.target.value)}>
              <option value="">Add a workspace member…</option>
              {candidates.map((m) => (
                <option key={m.id} value={m.id}>
                  {m.full_name ? `${m.full_name} (${m.email})` : m.email} — {m.role?.replace("_", " ")}{m.designation ? ` [${m.designation}]` : ""}
                </option>
              ))}
            </Form.Select>
          </Form.Group>
          <Button type="submit" disabled={!pick}>Add</Button>
        </Form>
      )}
    </Card.Body></Card>
  );
}
