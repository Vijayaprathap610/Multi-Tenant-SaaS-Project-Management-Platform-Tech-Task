import { useCallback, useEffect, useState } from "react";
import { api, errorMessage } from "../api/client";

/** GET a url (null = skip). Returns { data, loading, error, reload, setData }. */
export default function useFetch(url, params, deps = []) {
  const [state, setState] = useState({ data: null, loading: Boolean(url), error: null });
  const key = JSON.stringify(params || {});

  const load = useCallback(async () => {
    if (!url) return setState({ data: null, loading: false, error: null });
    setState((s) => ({ ...s, loading: true, error: null }));
    try {
      const res = await api.get(url, { params });
      setState({ data: res.data, loading: false, error: null });
    } catch (err) {
      setState({ data: null, loading: false, error: errorMessage(err) });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [url, key, ...deps]);

  useEffect(() => {
    let alive = true;
    (async () => { if (alive) await load(); })();
    return () => { alive = false; };
  }, [load]);

  return { ...state, reload: load, setData: (data) => setState((s) => ({ ...s, data })) };
}
