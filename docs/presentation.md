# 10-Minute Final Presentation: Tech Task SaaS Platform

**Platform:** Tech Task — Multi-Tenant SaaS Project Management Platform  
**Target Duration:** 10 minutes (9 slides + 3-minute live demonstration)  
**Speaker:** Lead Full-Stack Software Architect & Engineering Interns  

---

## Slide 1: Problem Statement & Value Proposition (0:45)
- **Title:** Tech Task: Enterprise Multi-Tenant Project Management
- **The Core Problem:** Modern software teams require powerful Jira-like project tracking (configurable workflows, drag-and-drop Kanban, sprint planning), but multi-tenant SaaS environments frequently suffer from Broken Object-Level Authorization (BOLA/IDOR), leading to catastrophic data leakage across organizations.
- **The Mission:** Build a unified, high-performance platform capable of serving multiple independent organizations on a shared infrastructure while strictly guaranteeing logical tenant isolation, backend authorization enforcement, and audit immutability.
- **Speaker Notes:** *"Welcome everyone. Today we are presenting Tech Task, a production-quality SaaS project management platform. Our primary mandate was not just delivering Jira-grade agility tools like custom workflows and drag-and-drop Kanban boards, but solving the hardest engineering problem in multi-tenancy: absolute tenant isolation where no company can ever access another company's data under any circumstance."*

---

## Slide 2: Project Objectives & Requirements Traceability (0:45)
- **Title:** Requirements & Acceptance Criteria
- **Mandatory FS-04 Scope:** 21 requirements spanning 5 core disciplines:
  1. *Architecture & Tenancy:* Shared schema with server-side tenant derivation (`TenantModel`, `TenantScopedMixin`).
  2. *Project Management Core:* Workspaces, Projects, Boards, Issues, Sprints, Custom Workflows.
  3. *Collaboration & Security:* Role-based access control, Comments, Malware-safe Attachments, Immutable Audit Logs.
  4. *Asynchronous Systems & Integrations:* Celery background jobs, HMAC-SHA256 signed Webhooks, Stripe Billing (test mode).
  5. *DevOps & Delivery:* Dockerized stack, GitHub Actions CI/CD pipeline, automated testing, and comprehensive documentation.
- **Traceability Status:** 100% of the audit checklist verified with automated scripts (`scripts/audit.py`: 24/24 checks passed).
- **Speaker Notes:** *"We established a formal Requirements Traceability Matrix connecting each functional and security requirement to its code location and test evidence. Every requirement has been verified against our automated audit harness."*

---

## Slide 3: Architecture & Technology Stack (1:15)
- **Title:** Modern, Scalable Full-Stack Architecture
- **Frontend Stack:** React 18, Vite 8, React Router v7, React Bootstrap / Bootstrap 5, `@hello-pangea/dnd` for accessible drag-and-drop interactions.
- **Backend Stack:** Django 6.1, Django REST Framework 3.18, PostgreSQL 16, Celery 5.5, Redis 7, Stripe SDK.
- **Infrastructure:** Docker Compose multi-container deployment (PostgreSQL, Redis, Celery Worker, Celery Beat, Django Gunicorn WSGI, Vite/Nginx frontend).
- **Architecture Highlights:**
  - Same-origin architecture with reverse proxy eliminating CORS attack surface.
  - Constant query count on Kanban loads (`select_related` and `prefetch_related`).
  - Immutable append-only audit logging and signed webhooks with SSRF loopback protections.
- **Speaker Notes:** *"Our architecture leverages Django REST Framework and React 18. We chose a shared-database architecture with workspace-scoped queries. A key optimization is our Kanban endpoint, which loads up to 500 cards in a constant number of queries regardless of volume, avoiding N+1 bottlenecks."*

---

## Slide 4: Multi-Tenant Isolation & Security Model (1:30)
- **Title:** Zero-Trust Tenant Isolation & RBAC
- **Tenant Scoping Guarantee:**
  - Workspace is the tenant boundary. Every tenant-owned model inherits `TenantModel`.
  - Membership is resolved server-side from the session and URL parameter. Client-provided `tenant_id` or `role` headers are strictly ignored.
  - Foreign IDs return `404 Not Found` rather than `403 Forbidden` to prevent resource enumeration.
- **Role-Based Access Control:**
  - *Platform Administrator:* Isolated console managing aggregate metrics; cannot browse private tenant content.
  - *Workspace Owner & Admin:* Workspace configuration, billing, invitations, webhooks.
  - *Project Manager:* Project creation, issue assignments, sprint planning, reports.
  - *Developer / Member:* Scoped issue updates, comments, and attachments.
- **Supply Chain Security:** Strict dependency pinning, `.npmrc` with `save-exact=true`, and post-Axios compromise verification.
- **Speaker Notes:** *"Tenant isolation is enforced in the backend query layer. If a user from Company A attempts to access an issue belonging to Company B, our backend returns a 404, revealing nothing about existence. Furthermore, all foreign keys in request bodies are validated against the workspace boundary."*

---

## Slide 5: Core Features & User Experience (1:15)
- **Title:** End-to-End Agile Workflow Management
- **Interactive Kanban Board:** Fluid drag-and-drop powered by `@hello-pangea/dnd` with optimistic UI updates and instant rollback if the transition violates project workflow rules. Keyboard navigation fully supported.
- **Configurable Workflows:** Project managers define custom statuses and an allowed transition matrix. Direct API bypasses are rejected.
- **Sprint Management:** Creation, activation (one active sprint rule), issue assignment, and automated rollover of unfinished tasks.
- **Collaboration & Attachments:** Sanitized file uploads with magic-byte verification, served only via authenticated, sandboxed endpoints.
- **Speaker Notes:** *"Users experience an enterprise-grade interface. When moving an issue card on the board, the UI updates optimistically, but if a transition is disallowed by the workflow, the card snaps back with an explanatory message."*

---

## Slide 6: Live Product Demonstration (3:00)
- **Title:** Live Demonstration Script
- **Step 1: Workspace Dashboard & Kanban Drag-and-Drop:**
  - Log in as workspace owner. View the executive KPI dashboard and project overview.
  - Open project board. Drag card from *To Do* to *In Progress* (persists successfully).
- **Step 2: Workflow Enforcement & Reversion:**
  - Attempt to drag card directly from *To Do* to *Done*.
  - Observe immediate API rejection (400 Bad Request) and automatic UI rollback.
- **Step 3: Comments, Attachments & Audit Log:**
  - Open issue detail view. Post a comment and upload a specification document.
  - Navigate to *Workspace Settings → Audit Log* to display the immutable event trail.
- **Step 4: Cross-Tenant Isolation Verification:**
  - Open private browsing session as a different company tenant. Attempt direct URL access to the first company's project.
  - Confirm `404 Not Found` response with private data shielded.
- **Step 5: Stripe Billing in Test Mode:**
  - Open *Billing* tab. Display plan usage limits and test-mode Stripe checkout flow.
- **Speaker Notes:** *(Follow the live demonstration steps with timer checking).*

---

## Slide 7: Engineering Challenges & Solutions (1:00)
- **Title:** Architectural Challenges & Technical Solutions
- **Challenge 1: Safe File Handling without Public Storage URLs:**
  - *Solution:* Stored files under randomized UUID paths and implemented an authenticated download endpoint sending `Content-Disposition: attachment`, `X-Content-Type-Options: nosniff`, and a restrictive sandboxed Content Security Policy.
- **Challenge 2: Webhook SSRF Vulnerabilities:**
  - *Solution:* Built hostname resolution checks verifying that webhook destinations are not loopback (`127.0.0.1`), link-local, or RFC 1918 private IP subnets before dispatch.
- **Challenge 3: Optimistic Concurrency & Webhook Idempotency:**
  - *Solution:* Implemented `dedupe_key` constraints on notifications and `StripeEvent` tables to ensure retried webhooks or tasks produce zero side effects.
- **Speaker Notes:** *"We encountered real challenges, particularly preventing SSRF via webhooks and ensuring secure file downloads. We resolved this by building pre-dispatch IP validators and streaming downloads with sandboxed headers."*

---

## Slide 8: Verification, Testing & Performance Evidence (0:45)
- **Title:** Verification Evidence & Benchmarks
- **Test Evidence:**
  - *Backend Unit & API Tests:* 74 automated tests covering accounts, tenancy, projects, and webhooks (`docs/test-results/backend.txt`).
  - *Frontend Unit Tests:* 18 tests covering Kanban logic and auth validation (`docs/test-results/frontend.txt`).
  - *End-to-End Tests:* 12 Playwright tests verifying registration, multi-tenancy boundaries, and Kanban drag-and-drop (`docs/test-results/e2e.txt`).
- **Performance Benchmarks:**
  - p50 read latency: `4.2ms` on authentication, `14.1ms` on 500-card Kanban boards.
  - Throughput: >210 req/s on standard hardware with 0 query degradation.
- **Speaker Notes:** *"All claims are backed by executable evidence. Our automated test suites cover 74 backend cases and 18 frontend cases, with sub-15ms p50 read latency on Kanban boards."*

---

## Slide 9: Roadmap & Next Steps (0:30)
- **Title:** Future Enhancements & Production Roadmap
- **Short-Term Next Steps:**
  - Implement PostgreSQL Row-Level Security (RLS) policies as a second defense layer under Django ORM.
  - Add field-level encryption for stored webhook signing secrets (e.g., using HashiCorp Vault).
- **Long-Term Features:**
  - Real-time collaborative board synchronization via WebSockets (Django Channels).
  - Advanced agile reporting: Burndown charts, velocity tracking, and Cumulative Flow Diagrams (CFD).
- **Conclusion:** Tech Task is ready for multi-tenant deployment, fully compliant with FS-04 requirements.
- **Speaker Notes:** *"Thank you for your time. We are now open for questions regarding the architecture, security model, and implementation."*
