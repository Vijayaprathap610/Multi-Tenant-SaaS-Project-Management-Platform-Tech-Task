import { useState } from "react";
import { Alert, Badge, Button, Card, Form, Modal, ProgressBar, Spinner } from "react-bootstrap";
import { useSearchParams } from "react-router";
import { api, errorMessage } from "../api/client";
import { ErrorAlert, Loading, fmtDate } from "../components/common";
import { MANAGE, useWorkspace } from "../context/WorkspaceContext";
import useFetch from "../hooks/useFetch";

const LIMIT_LABELS = {
  members: "Members",
  projects: "Projects",
  webhooks: "Webhooks",
  storage_mb: "Storage (MB)",
};

export default function BillingPage() {
  const { base, can } = useWorkspace();
  const [params] = useSearchParams();
  const { data, loading, error, reload } = useFetch(`${base}/billing/`, null, [
    base,
  ]);
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);
  const [successMsg, setSuccessMsg] = useState("");
  const [demoModalPlan, setDemoModalPlan] = useState(null);
  const [cardName, setCardName] = useState("Jane Doe");
  const [cardNumber, setCardNumber] = useState("4242 •••• •••• 4242");
  const [cardExpiry, setCardExpiry] = useState("12/28");
  const [cardCvc, setCardCvc] = useState("123");

  if (!can(MANAGE))
    return (
      <Alert variant="warning">
        Only workspace owners and admins can view billing.
      </Alert>
    );
  if (loading) return <Loading />;
  if (error) return <ErrorAlert error={error} onRetry={reload} />;

  const redirect = async (path, body) => {
    setBusy(true);
    setErr("");
    try {
      const r = await api.post(`${base}/billing/${path}/`, body);
      if (r.data.demo || !r.data.url?.startsWith("http")) {
        await reload();
        setSuccessMsg(`Plan updated successfully to ${body?.plan || "new plan"} via Demo Payment Gateway!`);
      } else {
        window.location.assign(r.data.url);
      }
    } catch (e) {
      setErr(errorMessage(e));
      setBusy(false);
    }
  };

  const cancel = async (immediate = false) => {
    setBusy(true);
    setErr("");
    try {
      await api.post(`${base}/billing/cancel/`, immediate ? { immediate: true } : {});
      await reload();
      setSuccessMsg(immediate ? "Subscription reverted back to Free plan." : "Subscription cancellation requested.");
    } catch (e) {
      setErr(errorMessage(e));
    }
    setBusy(false);
  };

  const handleDemoPaymentSubmit = async (e) => {
    e.preventDefault();
    if (!demoModalPlan) return;
    setBusy(true);
    setErr("");
    try {
      await api.post(`${base}/billing/checkout/`, {
        plan: demoModalPlan.key,
        demo: true,
      });
      setDemoModalPlan(null);
      await reload();
      setSuccessMsg(`Success! Upgraded to ${demoModalPlan.name} plan via Demo Payment Gateway.`);
    } catch (e) {
      setErr(errorMessage(e));
    } finally {
      setBusy(false);
    }
  };

  return (
    <>
      <div className="d-flex justify-content-between align-items-center mb-3">
        <h1 className="h4 mb-0">Subscription and billing</h1>
        {!data.stripe_configured && (
          <Badge bg="info" className="p-2">
            💳 Demo Payment Gateway Active
          </Badge>
        )}
      </div>

      {!data.stripe_configured ? (
        <Alert variant="info" className="small d-flex align-items-center justify-content-between">
          <div>
            <strong>Demo Mode:</strong> Live Stripe keys are not configured, so the <strong>Demo Payment Gateway</strong> is enabled. You can test all subscription upgrades and cancellations without real charges.
          </div>
        </Alert>
      ) : (
        <Alert variant="secondary" className="small">
          Test mode: payments use Stripe test cards only; no real money is charged.
        </Alert>
      )}

      {(params.get("checkout") === "success" || successMsg) && (
        <Alert variant="success" dismissible onClose={() => setSuccessMsg("")}>
          {successMsg || "Checkout completed. Your plan has been successfully updated."}
        </Alert>
      )}
      {params.get("checkout") === "cancelled" && (
        <Alert variant="warning">Checkout was cancelled.</Alert>
      )}
      <ErrorAlert error={err} />

      <Card className="mb-3">
        <Card.Body>
          <div className="d-flex justify-content-between align-items-start mb-2">
            <h2 className="h6 mb-0">
              Current plan: <span className="text-primary fw-bold">{data.plan_name}</span>{" "}
              <Badge bg={data.status === "active" ? "success" : "secondary"}>
                {data.status}
              </Badge>
            </h2>
          </div>
          {data.current_period_end && (
            <p className="mb-2 small text-muted">
              Renews / ends {fmtDate(data.current_period_end)}
              {data.cancel_at_period_end && " · cancels at period end"}
            </p>
          )}
          {Object.keys(LIMIT_LABELS).map((k) => {
            const limit = data.limits[k];
            const used = data.usage[k];
            return (
              <div key={k} className="mb-2">
                <div className="d-flex justify-content-between small">
                  <span>{LIMIT_LABELS[k]}</span>
                  <span>
                    {used} / {limit ?? "unlimited"}
                  </span>
                </div>
                {limit != null && (
                  <ProgressBar
                    now={Math.min(100, (used / limit) * 100)}
                    variant={used >= limit ? "danger" : "primary"}
                    aria-label={LIMIT_LABELS[k]}
                  />
                )}
              </div>
            );
          })}
          {data.can_manage && data.plan !== "free" && (
            <div className="d-flex flex-wrap gap-2 mt-3">
              {data.stripe_configured && (
                <Button
                  variant="outline-primary"
                  size="sm"
                  disabled={busy}
                  onClick={() => redirect("portal")}
                >
                  Manage in Stripe portal
                </Button>
              )}
              {!data.cancel_at_period_end && (
                <Button
                  variant="outline-danger"
                  size="sm"
                  disabled={busy}
                  onClick={() => cancel(false)}
                >
                  Cancel subscription
                </Button>
              )}
              <Button
                variant="outline-secondary"
                size="sm"
                disabled={busy}
                onClick={() => cancel(true)}
              >
                Reset to Free Plan (Demo)
              </Button>
            </div>
          )}
        </Card.Body>
      </Card>

      <div className="row g-3">
        {data.plans.map((p) => (
          <div className="col-md-4" key={p.key}>
            <Card
              className="h-100 shadow-sm"
              border={p.key === data.plan ? "primary" : undefined}
            >
              <Card.Header className="bg-white d-flex justify-content-between align-items-center">
                <span className="fw-bold">{p.name}</span>
                {p.key === data.plan && <Badge bg="primary">Current</Badge>}
              </Card.Header>
              <Card.Body className="d-flex flex-column">
                <div className="mb-3">
                  <span className="fs-4 fw-bold">
                    {p.key === "free" ? "$0" : p.key === "pro" ? "$29" : "$99"}
                  </span>
                  <span className="text-muted small"> / month</span>
                </div>
                <ul className="small ps-3 flex-grow-1">
                  {Object.keys(LIMIT_LABELS).map((k) => (
                    <li key={k} className="mb-1">
                      {LIMIT_LABELS[k]}: <strong>{p.limits[k] ?? "unlimited"}</strong>
                    </li>
                  ))}
                </ul>
                {p.key === data.plan ? (
                  <Button disabled variant="outline-primary" className="w-100 mt-2">
                    ✓ Current Plan
                  </Button>
                ) : (
                  p.key !== "free" &&
                  data.can_manage && (
                    <Button
                      variant={p.key === "business" ? "dark" : "primary"}
                      className="w-100 mt-2"
                      disabled={busy}
                      onClick={() => {
                        if (!data.stripe_configured) {
                          setDemoModalPlan(p);
                        } else {
                          redirect("checkout", { plan: p.key });
                        }
                      }}
                    >
                      {data.stripe_configured ? `Upgrade to ${p.name}` : `💳 Upgrade to ${p.name} (Demo)`}
                    </Button>
                  )
                )}
              </Card.Body>
            </Card>
          </div>
        ))}
      </div>

      {!data.can_manage && (
        <p className="small text-muted mt-3">
          Only the workspace owner can change the subscription.
        </p>
      )}

      {/* Demo Payment Gateway Modal */}
      <Modal show={!!demoModalPlan} onHide={() => !busy && setDemoModalPlan(null)} centered>
        <Modal.Header closeButton={!busy} className="bg-light">
          <Modal.Title className="h5 mb-0 d-flex align-items-center gap-2">
            <span>💳</span>
            <span>Demo Payment Gateway</span>
            <Badge bg="warning" text="dark">Sandbox</Badge>
          </Modal.Title>
        </Modal.Header>
        <Form onSubmit={handleDemoPaymentSubmit}>
          <Modal.Body>
            <div className="bg-light p-3 rounded mb-3 border">
              <div className="d-flex justify-content-between align-items-center">
                <strong className="fs-5">{demoModalPlan?.name} Plan Subscription</strong>
                <span className="fs-5 fw-bold text-primary">
                  {demoModalPlan?.key === "pro" ? "$29.00" : "$99.00"}
                  <small className="text-muted fs-6">/mo</small>
                </span>
              </div>
              <p className="text-muted small mb-0 mt-1">
                Workspace: <strong>{data.plan_name}</strong> &rarr; <strong>{demoModalPlan?.name}</strong>
              </p>
            </div>

            <Alert variant="info" className="py-2 small mb-3">
              💡 <strong>Simulated Gateway:</strong> No real transaction will occur. Submit this form to simulate credit card processing and immediate plan entitlement.
            </Alert>

            <Form.Group className="mb-2">
              <Form.Label className="small mb-1">Cardholder Name</Form.Label>
              <Form.Control
                size="sm"
                value={cardName}
                onChange={(e) => setCardName(e.target.value)}
                required
              />
            </Form.Group>

            <Form.Group className="mb-2">
              <Form.Label className="small mb-1">Card Number</Form.Label>
              <Form.Control
                size="sm"
                value={cardNumber}
                onChange={(e) => setCardNumber(e.target.value)}
                required
              />
            </Form.Group>

            <div className="row g-2 mb-3">
              <div className="col-6">
                <Form.Label className="small mb-1">Expiry (MM/YY)</Form.Label>
                <Form.Control
                  size="sm"
                  value={cardExpiry}
                  onChange={(e) => setCardExpiry(e.target.value)}
                  required
                />
              </div>
              <div className="col-6">
                <Form.Label className="small mb-1">CVC</Form.Label>
                <Form.Control
                  size="sm"
                  value={cardCvc}
                  onChange={(e) => setCardCvc(e.target.value)}
                  required
                />
              </div>
            </div>
          </Modal.Body>
          <Modal.Footer className="bg-light">
            <Button variant="secondary" size="sm" disabled={busy} onClick={() => setDemoModalPlan(null)}>
              Cancel
            </Button>
            <Button variant="success" size="sm" type="submit" disabled={busy}>
              {busy ? (
                <>
                  <Spinner animation="border" size="sm" className="me-2" />
                  Processing...
                </>
              ) : (
                `Pay ${demoModalPlan?.key === "pro" ? "$29.00" : "$99.00"} & Upgrade`
              )}
            </Button>
          </Modal.Footer>
        </Form>
      </Modal>
    </>
  );
}
