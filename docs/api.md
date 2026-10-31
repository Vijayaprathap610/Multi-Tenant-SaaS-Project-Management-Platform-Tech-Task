# API reference

Base URL `/api/`. Auth: Django session cookie (`sessionid`, HttpOnly) plus `X-CSRFToken` header on writes
(call `GET /api/auth/csrf/` first). Lists are paginated: `?page=N&page_size=M` (default 25, max 200) and return
`{count, next, previous, results}`.

**Error conventions**
| Status | Meaning |
|---|---|
| 400 | Validation error: `{"field": ["message"]}` or `{"detail": "..."}` |
| 401/403 | Not authenticated / role too low. Plan limits return 403 with `{"detail", "code": "plan_limit", "resource"}` |
| 404 | Not found **or not visible to you** (other tenant's ids look identical to missing ones) |
| 429 | Throttled |

Roles: **O**wner, **A**dmin, **PM** project manager, **M** member. "Project access" = O/A, or added as a project member.
All paths below are relative to `/api/workspaces/<workspace_id>/` unless they start with `/`.

## Authentication and accounts
| Method | Path | Auth | Notes |
|---|---|---|---|
| GET | `/auth/csrf/` | none | sets CSRF cookie |
| POST | `/auth/register/` | none | `{email, password, first_name?}`; identical response if the email exists; throttled |
| POST | `/auth/login/` | none | `{email, password}` returns user + memberships; generic failure message; throttled 10/min |
| POST | `/auth/logout/` | session | |
| GET/PATCH | `/auth/me/` | session | PATCH changes `first_name` only |
| POST | `/auth/change-password/` | session | other sessions are invalidated |
| POST | `/auth/password-reset/` | none | always 202; email via Celery; token valid 1 h, single use |
| POST | `/auth/password-reset/confirm/` | none | `{uid, token, new_password}` |
| POST | `/platform-admin/login/` | none | only the Platform Administrator can succeed here |
| GET | `/platform-admin/stats/` | Platform Admin | aggregate counts only |

## Workspaces, members, invitations, audit
| Method | Path | Roles | Notes |
|---|---|---|---|
| GET/POST | `/workspaces/` (absolute) | any user | list own workspaces / create one (creator becomes Owner) |
| GET/PATCH | `/workspaces/<id>/` (absolute) | member / O,A | |
| GET | `members/` | all | |
| PATCH/DELETE | `members/<membership_id>/` | O,A | Admins cannot touch Owners/Admins or grant them; last Owner protected |
| GET/POST | `invitations/` | O,A | POST `{email, role in admin\|project_manager\|member}`; plan member limit applies |
| DELETE | `invitations/<id>/` | O,A | revoke |
| POST | `/invitations/accept/` (absolute) | invited user | `{token}`; token is signed, 7 days, bound to workspace+role+email |
| GET | `audit/` | O,A | read-only, newest first |

## Projects and structure
| Method | Path | Roles |
|---|---|---|
| GET / POST | `projects/` | all (scoped to access) / O,A (plan limit) |
| GET / PATCH / DELETE | `projects/<pid>/` | all / PM+ / O,A |
| GET / POST | `projects/<pid>/members/` | all / PM+ (`{membership_id}`) |
| DELETE | `projects/<pid>/members/<id>/` | PM+ |
| GET / POST | `projects/<pid>/statuses/` , `.../statuses/<id>/` (PATCH, DELETE) | all (read) / PM+ |
| GET / POST | `projects/<pid>/transitions/` , DELETE `.../transitions/<id>/` | all (read) / PM+ |
| GET / POST | `projects/<pid>/boards/` , `.../boards/<bid>/` | all (read) / PM+ |
| GET | `projects/<pid>/boards/<bid>/kanban/?q=&assignee=&priority=` | all |
| GET / POST | `projects/<pid>/boards/<bid>/columns/` , `.../columns/<id>/` | all (read) / PM+ |

## Issues, comments, attachments
| Method | Path | Roles | Notes |
|---|---|---|---|
| GET / POST | `projects/<pid>/issues/` | all | filters: `status, sprint, assignee, priority, label, q, backlog=true`; `ordering` in created_at, updated_at, priority, due_date, number, title (prefix `-`) |
| GET / PATCH / DELETE | `projects/<pid>/issues/<id>/` | all; delete: PM+ or own (M) | status changes obey the workflow |
| POST | `projects/<pid>/issues/<id>/move/` | all | `{status, before_issue_id?}`: Kanban drop; 400 if transition not allowed |
| GET / POST | `.../issues/<id>/comments/` ; PATCH/DELETE `.../comments/<cid>/` | all | edit: author only; delete: author or PM+ |
| GET / POST | `.../issues/<id>/attachments/` | all | multipart `file`; extension allowlist, 10 MB, magic-byte check, optional scanner |
| GET | `.../attachments/<aid>/download/` | all with project access | sent as attachment, `nosniff`, sandbox CSP |
| DELETE | `.../attachments/<aid>/` | uploader or PM+ | |

## Sprints and reports
| Method | Path | Roles |
|---|---|---|
| GET / POST | `projects/<pid>/sprints/` | all / PM+ |
| GET / PATCH / DELETE | `projects/<pid>/sprints/<id>/` | all / PM+ / PM+ (planned only) |
| POST | `.../sprints/<id>/start/` | PM+ (one active sprint per project) |
| POST | `.../sprints/<id>/complete/` | PM+ `{move_incomplete_to?}` |
| POST | `.../sprints/<id>/issues/` | PM+ `{issue_ids: [...]}` (all-or-nothing) |
| GET | `.../sprints/<id>/report/` | all |
| POST / GET | `projects/<pid>/reports/` , `.../reports/<id>/` | PM+ (asynchronous; 202 then poll) |
| GET | `projects/<pid>/reports/export/issues/` | PM+ (CSV, formula-injection safe) |

## Notifications, webhooks, billing
| Method | Path | Roles | Notes |
|---|---|---|---|
| GET | `notifications/?unread=true` | all | own notifications only |
| POST | `notifications/<id>/read/` , `notifications/read-all/` | all | |
| GET / POST | `webhooks/` | O,A | POST returns `secret` once |
| GET / PATCH / DELETE | `webhooks/<id>/` | O,A | |
| POST | `webhooks/<id>/rotate-secret/` , `webhooks/<id>/test/` | O,A | |
| GET | `webhooks/<id>/deliveries/` | O,A | |
| GET | `billing/` | O,A | plan, limits, usage |
| POST | `billing/checkout/` `{plan}` , `billing/portal/` , `billing/cancel/` | O | Stripe test mode |
| POST | `/billing/webhook/` (absolute) | Stripe signature | idempotent on event id |

## Webhook delivery format (outgoing)
Headers: `X-TechTask-Event`, `X-TechTask-Delivery` (use to de-duplicate), `X-TechTask-Signature: t=<unix>,v1=<hex>`
where `v1 = HMAC_SHA256(secret, "<t>." + raw_body)`. Verify the signature, then reject timestamps older than 5 minutes.
Body: `{"id","type","workspace_id","created_at","data":{...}}`. Events: `issue.created`, `issue.assigned`,
`issue.status_changed`, `issue.deleted`, `comment.created`, `attachment.uploaded`, `sprint.started`, `sprint.completed`, `ping`.
