import { Nav } from "react-bootstrap";
import { NavLink, Outlet, useParams } from "react-router";
import { all } from "../../api/client";
import { ErrorAlert, Loading } from "../../components/common";
import { PM_UP, useWorkspace } from "../../context/WorkspaceContext";
import useFetch from "../../hooks/useFetch";
import { useEffect, useState, useCallback } from "react";

/** Loads project-wide reference data once and shares it with every project tab via Outlet context. */
export default function ProjectLayout() {
  const { projectId } = useParams();
  const { base: wsBase, can } = useWorkspace();
  const base = `${wsBase}/projects/${projectId}`;
  const project = useFetch(`${base}/`, null, [base]);
  const [ref, setRef] = useState({ members: [], statuses: [], transitions: [], loading: true, error: null });

  const loadRef = useCallback(async () => {
    try {
      const [members, statuses, transitions] = await Promise.all([
        all(`${base}/members/`), all(`${base}/statuses/`), all(`${base}/transitions/`)]);
      setRef({ members, statuses, transitions, loading: false, error: null });
    } catch {
      setRef((r) => ({ ...r, loading: false, error: "Could not load project data." }));
    }
  }, [base]);
  useEffect(() => { loadRef(); }, [loadRef]);

  if (project.loading || ref.loading) return <Loading />;
  if (project.error) return <ErrorAlert error="This project was not found or you do not have access to it." />;

  const link = ({ isActive }) => `nav-link${isActive ? " active" : ""}`;
  return (
    <>
      <h1 className="h4 mb-1">{project.data.name} <small className="text-muted">{project.data.key}</small></h1>
      <Nav variant="pills" className="mb-3 flex-wrap gap-1" aria-label="Project sections">
        <NavLink to="board" className={link}>Board</NavLink>
        <NavLink to="issues" className={link}>Issues</NavLink>
        <NavLink to="sprints" className={link}>Sprints</NavLink>
        <NavLink to="workflow" className={link}>Workflow</NavLink>
        <NavLink to="members" className={link}>Members</NavLink>
        {can(PM_UP) && <NavLink to="reports" className={link}>Reports</NavLink>}
      </Nav>
      <ErrorAlert error={ref.error} onRetry={loadRef} />
      <Outlet context={{ base, project: project.data, ...ref, reloadRef: loadRef, canManage: can(PM_UP) }} />
    </>
  );
}
