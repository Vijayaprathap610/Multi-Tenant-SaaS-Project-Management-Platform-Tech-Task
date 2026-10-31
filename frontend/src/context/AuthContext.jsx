import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { api, ensureCsrf } from "../api/client";

const AuthContext = createContext(null);
export const useAuth = () => useContext(AuthContext);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    try {
      const res = await api.get("/auth/me/");
      setUser(res.data);
    } catch {
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { ensureCsrf().catch(() => {}).finally(refresh); }, [refresh]);

  const login = useCallback(async (email, password) => {
    const res = await api.post("/auth/login/", { email, password });
    setUser(res.data);
    return res.data;
  }, []);

  const logout = useCallback(async () => {
    try { await api.post("/auth/logout/"); } finally { setUser(null); }
  }, []);

  const value = useMemo(() => ({ user, loading, login, logout, refresh }), [user, loading, login, logout, refresh]);
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
