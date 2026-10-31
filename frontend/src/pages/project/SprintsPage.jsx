import { useState } from "react";
import { Alert, Badge, Button, Card, Form, Modal, ProgressBar } from "react-bootstrap";
import { useOutletContext } from "react-router";
import { all, api, errorMessage } from "../../api/client";
import { EmptyState, ErrorAlert, Loading, fmtDate } from "../../components/common";
import useFetch from "../../hooks/useFetch";

const variant = { planned: "secondary", active: "success", completed: "dark" };

function SprintCard({ sprint, base, canManage, sprints, backlog, onChange }) {
  const [report, setReport] = useState(null);
  const [err, setErr] = useState("");
  const [assign, setAssign] = useState(false);
  const [picked, setPicked] = useState([]);
  const [completing, setCompleting] = useState(false);
  const [rollover, setRollover] = useState("");
  const url = `${base}/sprints/${sprint.id}/`;

  const act = async (fn) => {
    setErr("");
    try { await fn(); onChange(); } catch (e) { setErr(errorMessage(e)); }
  };
  const loadReport = () => act(async () => { setReport((await api.get(`${url}report/`)).data); });

  return (
    <Card className="mb-3"><Card.Body>
      <div className="d-flex justify-content-between flex-wrap gap-2">
        <div>
          <h2 className="h6 mb-0">{sprint.name} <Badge bg={variant[sprint.status]}>{sprint.status}</Badge></h2>
          <small className="text-muted">{fmtDate(sprint.start_date)} – {fmtDate(sprint.end_date)}</small>
          {sprint.goal && <div>{sprint.goal}</div>}
        </div>
        <div className="d-flex gap-1 align-items-start">
          <Button size="sm" variant="outline-primary" onClick={loadReport}>Report</Button>
          {canManage && sprint.status === "planned" && <>
            <Button size="sm" variant="outline-primary" onClick={() => setAssign(true)}>Add issues</Button>
            <Button size="sm" onClick={() => act(() => api.post(`${url}start/`))}>Start</Button>
            <Button size="sm" variant="outline-danger" onClick={() => act(() => api.delete(url))}>Delete</Button>
          </>}
          {canManage && sprint.status === "active" && <>
            <Button size="sm" variant="outline-primary" onClick={() => setAssign(true)}>Add issues</Button>
            <Button size="sm" onClick={() => setCompleting(true)}>Complete</Button>
          </>}
        </div>
      </div>
      <ErrorAlert error={err} />
      {report && (
        <div className="mt-3">
          <ProgressBar now={report.completion_rate * 100} label={`${Math.round(report.completion_rate * 100)}%`} aria-label="Completion" />
          <small>{report.total_issues} issues · to do {report.by_category.todo} · in progress {report.by_category.in_progress} · done {report.by_category.done}</small>
        </div>
      )}
      <Modal show={assign} onHide={() => setAssign(false)} centered>
        <Modal.Header closeButton><Modal.Title as="h2" className="h5">Add backlog issues to {sprint.name}</Modal.Title></Modal.Header>
        <Modal.Body>
          {backlog.length === 0 && <p className="text-muted mb-0">The backlog is empty.</p>}
          {backlog.map((i) => (
            <Form.Check key={i.id} id={`pick-${i.id}`} label={`${i.key} ${i.title}`} checked={picked.includes(i.id)}
              onChange={(e) => setPicked(e.target.checked ? [...picked, i.id] : picked.filter((x) => x !== i.id))} />
          ))}
        </Modal.Body>
        <Modal.Footer>
          <Button disabled={!picked.length} onClick={() => act(async () => { await api.post(`${url}issues/`, { issue_ids: picked }); setAssign(false); setPicked([]); })}>
            Add {picked.length || ""} issue(s)
          </Button>
        </Modal.Footer>
      </Modal>
      <Modal show={completing} onHide={() => setCompleting(false)} centered>
        <Modal.Header closeButton><Modal.Title as="h2" className="h5">Complete {sprint.name}</Modal.Title></Modal.Header>
        <Modal.Body>
          <Form.Group controlId="rollover">
            <Form.Label>Move unfinished issues to</Form.Label>
            <Form.Select value={rollover} onChange={(e) => setRollover(e.target.value)}>
              <option value="">Backlog</option>
              {sprints.filter((s) => s.status === "planned").map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}
            </Form.Select>
          </Form.Group>
        </Modal.Body>
        <Modal.Footer>
          <Button onClick={() => act(async () => { await api.post(`${url}complete/`, { move_incomplete_to: rollover || null }); setCompleting(false); })}>Complete sprint</Button>
        </Modal.Footer>
      </Modal>
    </Card.Body></Card>
  );
}

export default function SprintsPage() {
  const { base, canManage } = useOutletContext();
  const sprints = useFetch(`${base}/sprints/`, { page_size: 100 }, [base]);
  const backlog = useFetch(`${base}/issues/`, { backlog: "true", page_size: 100 }, [base]);
  const [show, setShow] = useState(false);
  const [form, setForm] = useState({ name: "", goal: "", start_date: "", end_date: "" });
  const [error, setError] = useState("");

  const reloadAll = () => { sprints.reload(); backlog.reload(); };
  const create = async (e) => {
    e.preventDefault();
    setError("");
    try { await api.post(`${base}/sprints/`, form); setShow(false); setForm({ name: "", goal: "", start_date: "", end_date: "" }); reloadAll(); }
    catch (err) { setError(errorMessage(err)); }
  };
  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  return (
    <>
      <div className="d-flex justify-content-between mb-3">
        <h2 className="h5">Sprints</h2>
        {canManage && <Button onClick={() => setShow(true)}>New sprint</Button>}
      </div>
      <ErrorAlert error={sprints.error} onRetry={sprints.reload} />
      {sprints.loading && <Loading />}
      {sprints.data?.results.length === 0 && <EmptyState title="No sprints">{canManage ? "Create a sprint to start planning." : "No sprints have been planned yet."}</EmptyState>}
      {sprints.data?.results.map((s) => (
        <SprintCard key={s.id} sprint={s} base={base} canManage={canManage} sprints={sprints.data.results}
          backlog={(backlog.data?.results || [])} onChange={reloadAll} />
      ))}
      <Modal show={show} onHide={() => setShow(false)} centered>
        <Form onSubmit={create}>
          <Modal.Header closeButton><Modal.Title as="h2" className="h5">New sprint</Modal.Title></Modal.Header>
          <Modal.Body>
            {error && <Alert variant="danger" role="alert">{error}</Alert>}
            <Form.Group className="mb-3" controlId="s-name"><Form.Label>Name</Form.Label>
              <Form.Control required value={form.name} onChange={set("name")} /></Form.Group>
            <Form.Group className="mb-3" controlId="s-goal"><Form.Label>Goal</Form.Label>
              <Form.Control as="textarea" rows={2} value={form.goal} onChange={set("goal")} /></Form.Group>
            <div className="row">
              <Form.Group className="col-6" controlId="s-start"><Form.Label>Start</Form.Label>
                <Form.Control type="date" required value={form.start_date} onChange={set("start_date")} /></Form.Group>
              <Form.Group className="col-6" controlId="s-end"><Form.Label>End</Form.Label>
                <Form.Control type="date" required value={form.end_date} onChange={set("end_date")} /></Form.Group>
            </div>
          </Modal.Body>
          <Modal.Footer><Button type="submit">Create sprint</Button></Modal.Footer>
        </Form>
      </Modal>
    </>
  );
}
