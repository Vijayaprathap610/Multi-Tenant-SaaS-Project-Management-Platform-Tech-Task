# Security and tenant isolation design

## Strategy
Shared database and schema; the **workspace is the tenant**. Every tenant-owned table inherits `TenantModel`
(non-null `workspace` FK, never writable through serializers). One company = one workspace in v1; a user can belong to
several workspaces. PostgreSQL row-level security was considered and **not implemented**; isolation is enforced in the
application layer and verified by tests (a documented next step is RLS as defence in depth).

## How isolation is enforced
1. `WorkspaceMembershipPermission` resolves the caller's `Membership` from the URL workspace id **on the server** on every
   request. No membership = 404 (existence is not revealed). Insufficient role = 403. Views declare `required_roles` per
   HTTP method; an unlisted method is denied.
2. `TenantScopedMixin` filters every queryset by the verified workspace; `ProjectScopedMixin` adds the project and checks
   project access (O/A, or project member).
3. Creates stamp workspace/project from the verified context, never from the body.
4. Every id in a request body (status, sprint, assignee, issue ids, membership id) is validated against the same project or
   workspace; foreign ids fail as "invalid".
5. Files live outside any served path under random names; downloads pass through the scoped view.
6. Background jobs re-validate: notifications check the issue belongs to the stated workspace and the recipient still has
   project access; reports re-check the requester's access; webhook fan-out only reads the event's own workspace endpoints;
   Celery arguments carry ids only, never tokens or secrets.
7. Platform Administrator is a separate login and endpoint; it returns aggregates only and is not a member of any tenant.

## Role matrix as implemented
| Capability | Owner | Admin | Project Manager | Member |
|---|---|---|---|---|
| Workspace settings, audit log, webhooks | yes | yes | no | no |
| Invite / remove / change roles | all | not Owner/Admin | no | no |
| Billing | manage | view | no | no |
| Create / delete projects | yes | yes | no | no |
| Edit project, boards, workflow, sprints, reports | yes | yes | assigned projects | read only |
| Issues: create / edit / move | yes | yes | yes | yes (assigned projects) |
| Issues: delete | yes | yes | yes | own only |
| Comments: edit | author | author | author | author |
| Comments / attachments: delete | any | any | any | own only |

## Authentication hardening
Django password hashing and validators; session cookie HttpOnly, SameSite=Lax, Secure when DEBUG is off; CSRF enforced for
session-authenticated writes; rate limits on login (10/min), registration, password reset, Platform Admin login; generic
responses to prevent account enumeration; reset tokens expire (1 h) and are single use; password change invalidates other
sessions; the session key rotates on login. A DB constraint allows at most one active Platform Administrator, created only by
`manage.py create_platform_admin` (password from env or prompt).

## Other controls
The Django admin site is **not installed** (smaller attack surface; it would otherwise be a second login path to raw tenant data). The Platform Administrator is not a Django staff user.
Same-origin deployment: no CORS headers are sent, so browsers refuse cross-origin calls; CSRF-trusted origins come from `TRUSTED_ORIGINS`; security headers via Django and nginx; webhook SSRF guard (https only,
private/loopback/link-local refused, re-checked at delivery, redirects not followed); webhook signatures; Stripe signature
verification and event-id idempotency; CSV formula-injection neutralisation; audit log is append-only at the model level.

## Known limitations (be upfront about these)
- Webhook secrets are stored unencrypted (needed to sign requests); field-level encryption is a next step.
- The malware-scan hook is a command integration that is **off by default**; no scanner is bundled or tested here.
- Audit immutability is enforced in Django, not by database permissions.
- `QuerySet.update/delete` on `AuditEvent` bypasses model-level protection; restrict DB privileges in production.
- No email verification at registration (the invitation flow binds to the invited address instead).
- Not yet done: dependency pinning and vulnerability review, penetration testing, load testing beyond the provided script.
