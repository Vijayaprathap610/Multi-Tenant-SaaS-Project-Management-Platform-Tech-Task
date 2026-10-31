import { createContext, useCallback, useContext, useMemo, useState } from "react";
import { useAuth } from "./AuthContext";

const WorkspaceContext = createContext(null);
export const useWorkspace = () => useContext(WorkspaceContext);

const KEY = "tt.workspace"; // only a non-sensitive UI hint; the server re-checks membership on every request
export const MANAGE = ["owner", "admin"];
export const PM_UP = ["owner", "admin", "project_manager"];

export function WorkspaceProvider({ children }) {
  const { user } = useAuth();
  const [stored, setStored] = useState(() => localStorage.getItem(KEY));
  const memberships = user?.memberships || [];
  const active = memberships.find((m) => m.workspace_id === stored) || memberships[0] || null;

  const setActive = useCallback((id) => { localStorage.setItem(KEY, id); setStored(id); }, []);

  const value = useMemo(() => ({
    memberships,
    workspace: active,
    workspaceId: active?.workspace_id,
    role: active?.role,
    base: active ? `/workspaces/${active.workspace_id}` : null,
    can: (roles) => Boolean(active && roles.includes(active.role)),
    setActive,
  }), [memberships, active, setActive]);

  return <WorkspaceContext.Provider value={value}>{children}</WorkspaceContext.Provider>;
}
