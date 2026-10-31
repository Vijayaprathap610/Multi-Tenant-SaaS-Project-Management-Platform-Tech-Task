import { useState } from "react";
import { Alert, Button, Card, ProgressBar } from "react-bootstrap";
import { useSearchParams } from "react-router";
import { api, errorMessage } from "../api/client";
import { ErrorAlert, Loading, fmtDate } from "../components/common";
import { MANAGE, useWorkspace } from "../context/WorkspaceContext";
import useFetch from "../hooks/useFetch";

const LIMIT_LABELS = { members: "Members", projects: "Projects", webhooks: "Webhooks", storage_mb: "Storage (MB)" };

export default function BillingPage() {
  const { base, can } = useWorkspace();
  const [params] = useSearchParams();
  const { data, loading, error, reload } = useFetch(`${base}/billing/`, null, [base]);
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);

  if (!can(MANAGE)) return <Alert variant="warning">Only workspace owners and admins can view billing.</Alert>;
  if (loading) return <Loading />;
  if (error) return <ErrorAlert error={error} onRetry={reload} />;

  const redirect = async (path, body) => {
    setBusy(true);
    setErr("");
    try { const r = await api.post(`${base}/billing/${path}/`, body); window.location.assign(r.data.url); }
    catch (e) { setErr(errorMessage(e)); setBusy(false); }
  };
  const cancel = async () => {
    setBusy(true);
    try { await api.post(`${base}/billing/cancel/`); await reload(); } catch (e) { setErr(errorMessage(e)); }
    setBusy(false);
  };

  return (
    <>
      <h1 className="h4 mb-3">Subscription and billing</h1>
      <Alert variant="secondary" className="small">Test mode: payments use Stripe test cards only; no real money is charged.</Alert>
      {params.get("checkout") === "success" && <Alert variant="success">Checkout completed. Your plan updates as soon as Stripe confirms it.</Alert>}
      {params.get("checkout") === "cancelled" && <Alert variant="warning">Checkout was cancelled.</Alert>}
      <ErrorAlert error={err} />
      <Card className="mb-3"><Card.Body>
        <h2 className="h6">Current plan: {data.plan_name} <small className="text-muted">({data.status})</small></h2>
        {data.current_period_end && <p className="mb-1 small">Renews / ends {fmtDate(data.current_period_end)}{data.cancel_at_period_end && " · cancels at period end"}</p>}
        {Object.keys(LIMIT_LABELS).map((k) => {
          const limit = data.limits[k];
          const used = data.usage[k];
          return (
            <div key={k} className="mb-2">
              <div className="d-flex justify-content-between small"><span>{LIMIT_LABELS[k]}</span><span>{used} / {limit ?? "unlimited"}</span></div>
              {limit != null && <ProgressBar now={Math.min(100, (used / limit) * 100)} variant={used >= limit ? "danger" : "primary"} aria-label={LIMIT_LABELS[k]} />}
            </div>
          );
        })}
        {data.can_manage && data.plan !== "free" && (
          <div className="d-flex gap-2 mt-3">
            <Button variant="outline-primary" disabled={busy} onClick={() => redirect("portal")}>Manage in Stripe portal</Button>
            {!data.cancel_at_period_end && <Button variant="outline-danger" disabled={busy} onClick={cancel}>Cancel subscription</Button>}
          </div>
        )}
      </Card.Body></Card>
      <div className="row g-3">
        {data.plans.map((p) => (
          <div className="col-md-4" key={p.key}>
            <Card className="h-100" border={p.key === data.plan ? "primary" : undefined}><Card.Body>
              <h2 className="h6">{p.name}</h2>
              <ul className="small ps-3">
                {Object.keys(LIMIT_LABELS).map((k) => <li key={k}>{LIMIT_LABELS[k]}: {p.limits[k] ?? "unlimited"}</li>)}
              </ul>
              {p.key === data.plan ? <Button disabled variant="outline-primary" className="w-100">Current plan</Button>
                : p.key !== "free" && data.can_manage && data.plan === "free" && (
                  <Button className="w-100" disabled={busy || !data.stripe_configured} onClick={() => redirect("checkout", { plan: p.key })}>
                    {data.stripe_configured ? `Upgrade to ${p.name}` : "Stripe not configured"}
                  </Button>)}
            </Card.Body></Card>
          </div>
        ))}
      </div>
      {!data.can_manage && <p className="small text-muted mt-3">Only the workspace owner can change the subscription.</p>}
    </>
  );
}
