# Individual reflection: Lead Full-Stack Architect & Intern

1. **Modules or features I personally owned**:
   - Multi-tenant architecture and isolation enforcement (`backend/tenancy/`, `tenancy/mixins.py`, `tenancy/query.py`, `tenancy/permissions.py`, `backend/tenancy/test_cross_tenant.py`).
   - Core domain models and relationships (`workspaces`, `projects`, `workflows`, `boards`, `sprints`, `issues`).
   - Drag-and-drop Kanban board frontend and transition logic (`frontend/src/kanban/`, `frontend/src/pages/project/BoardPage.jsx`, `frontend/src/kanban/logic.js`).
   - Configurable workflow engine and status transition validation (`backend/workflows/`, `backend/issues/services.py`).
   - Audit logging subsystem and immutable audit trails (`backend/audit/`).
   - Webhook signing, HMAC-SHA256 delivery with exponential backoff, and Celery background workers (`backend/webhooks/`, `backend/notifications/`).
   - Stripe Billing in test mode and workspace usage limit enforcement (`backend/billing/`).
   - Production Docker containerization, docker-compose orchestration, and GitHub Actions CI/CD workflows.

2. **What I implemented**:
   - Implemented tenant-scoping mechanisms using `TenantModel` and `TenantScopedMixin` where every tenant resource is strictly derived from the server-validated workspace context and authenticated user membership, preventing IDOR vulnerabilities.
   - Built a custom React drag-and-drop Kanban board using the maintained `@hello-pangea/dnd` library, featuring optimistic UI updates with automatic rollback on rejection or network failure, keyboard navigation (Space/Arrows), and constant query count backend fetching (`boards/views.py`).
   - Designed and built the role-based permission system (`WorkspaceOwner`, `WorkspaceAdmin`, `ProjectManager`, `Member`) across all endpoints with separate, secure Platform Administrator login and dashboard.
   - Integrated signed webhooks with timestamped HMAC-SHA256 headers (`X-TechTask-Signature`), unique delivery IDs (`X-TechTask-Delivery`) for deduplication, and protection against Server-Side Request Forgery (SSRF) by blocking private/loopback IP ranges.
   - Created automated unit, component, API, and cross-tenant isolation test suites covering read, create, update, delete, search, and bulk operations.
   - Designed the complete Tech Task branding system adhering to the specification's color palette (Coffee Brown `#4B2E1E`, Brown `#7A5236`, Warm Copper `#B8906B`, Warm Off-White `#F6F3EF`, Charcoal `#4B4B4B`).

3. **What I learned**:
   - Multi-tenant isolation cannot rely on client-provided IDs; strict server-side scoping and object-level permission checks are paramount to protect sensitive business data.
   - The criticality of software supply-chain security, especially after vulnerabilities such as the March 2026 Axios account compromise, demonstrating why exact package pinning (`.npmrc` with `save-exact=true`, hash verification, and `npm ci --ignore-scripts`) is vital.
   - Optimistic UI updates require careful state synchronization and seamless failure recovery to maintain trust in interactive tools like Kanban boards.
   - Safe file attachment handling requires defense-in-depth: content-type validation, magic-byte inspection, randomized non-executable storage paths, and serving files via authenticated download endpoints with strict sandboxed CSP and `nosniff` headers.

4. **Challenges I faced and how I addressed them**:
   - *Challenge*: Balancing reactive UI updates with strict workflow validation rules (e.g., preventing To Do -> Done without passing through In Progress).
     *Solution*: Created a centralized transition validator in `issues/services.py` utilized by both the REST API PATCH endpoint and the specialized `/move/` Kanban endpoint, while the React board computes valid drop targets and handles 400 Bad Request by rolling back optimistic movements with visual feedback.
   - *Challenge*: Avoiding N+1 queries when loading Kanban boards with hundreds of issue cards.
     *Solution*: Optimized the Kanban API queryset using `select_related("project", "assignee", "status")` and `prefetch_related`, ensuring constant query counts regardless of issue volume.
   - *Challenge*: Preventing SSRF attacks via user-configured webhooks.
     *Solution*: Implemented IP address resolution and validation on webhook endpoints during creation and right before dispatch, refusing loopback and RFC 1918 private subnets unless local development flags are explicitly toggled.

5. **What I would improve next**:
   - Implement PostgreSQL Row-Level Security (RLS) as an additional defense-in-depth layer beneath Django ORM.
   - Introduce database encryption for webhook signing secrets (e.g., using `django-cryptography` or HashiCorp Vault).
   - Add real-time WebSocket updates via Django Channels for collaborative Kanban board synchronization across multiple simultaneous users.
   - Implement burndown and cumulative flow diagrams in the reporting engine.

6. **Work I did not do / relied on others or AI assistance for**:
   - Leveraged AI pair programming to formulate test matrices, desk-check edge cases, cross-check API contract URL patterns, and refine documentation templates.
   - Relied on official upstream libraries: `@hello-pangea/dnd` for drag-and-drop primitives and Django REST Framework for core serialization and viewset foundations.

