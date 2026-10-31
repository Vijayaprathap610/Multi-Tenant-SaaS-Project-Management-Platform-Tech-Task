import axios from "axios";

function getCookie(name) {
  const row = document.cookie.split("; ").find((r) => r.startsWith(name + "="));
  return row ? decodeURIComponent(row.split("=")[1]) : null;
}

// Session cookie auth (HttpOnly, set by Django). No credentials are kept in browser storage.
export const api = axios.create({ baseURL: "/api", withCredentials: true });

api.interceptors.request.use((cfg) => {
  const method = (cfg.method || "get").toLowerCase();
  if (!["get", "head", "options"].includes(method)) {
    const token = getCookie("csrftoken");
    if (token) cfg.headers["X-CSRFToken"] = token;
  }
  return cfg;
});

export const ensureCsrf = () => api.get("/auth/csrf/");

/** Turn a DRF error response into one readable sentence. */
export function errorMessage(err) {
  const d = err?.response?.data;
  if (!err?.response) return "Network error. Please check your connection and try again.";
  if (err.response.status === 429) return "Too many attempts. Please wait a moment and try again.";
  if (!d) return "Something went wrong.";
  if (typeof d === "string") return d;
  if (d.detail) return typeof d.detail === "string" ? d.detail : "Request failed.";
  const [field, val] = Object.entries(d)[0] || [];
  if (!field) return "Request failed.";
  const msg = Array.isArray(val) ? val[0] : typeof val === "string" ? val : JSON.stringify(val);
  return field === "non_field_errors" ? msg : `${field}: ${msg}`;
}

/** Field-level errors for forms: { fieldName: "message" } */
export function fieldErrors(err) {
  const d = err?.response?.data;
  if (!d || typeof d !== "object") return {};
  return Object.fromEntries(
    Object.entries(d).filter(([k]) => k !== "detail").map(([k, v]) => [k, Array.isArray(v) ? v[0] : String(v)]),
  );
}

export const all = (url, params = {}) =>
  api.get(url, { params: { page_size: 200, ...params } }).then((r) => r.data.results);
