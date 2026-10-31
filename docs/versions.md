# Versions and compatibility

Checked on **2026-10-29** with web searches and official pages from the authoring environment. "Verified" means the
statement was found in the cited source. **Nothing here has been executed together**: the full stack has not been installed
or run, so compatibility is based on published support statements only. Re-check before submission.

## Verified and applied
| Component | Finding (source) | Decision |
|---|---|---|
| Django | Latest official release **6.1.2**; supported series 5.2 LTS (5.2.18, extended support to Apr 2028), 6.0 (6.0.9, to Apr 2027), 6.1 (mainstream to Apr 2027, extended to Dec 2027); 6.2 LTS due Apr 2027 (djangoproject.com/download) | `Django>=6.1.2,<6.2`. If you prefer the longest support window, use 5.2 LTS (`>=5.2.18,<5.3`); the code avoids version-specific APIs but has not been run on either |
| Python | Django 5.2, 6.0 and 6.1 all support 3.12 (docs.djangoproject.com FAQ: Installation) | Python **3.12** (backend Dockerfile, CI) |
| Django REST Framework | 3.17.0 (Mar 2026) added Django 6.0 support; **3.18.1 added Django 6.1 support**; 3.18.3 is the latest release listed (github.com/encode/django-rest-framework/releases, Django Forum) | `djangorestframework>=3.18.3,<3.19` |
| Celery | 5.5 officially supports CPython 3.12 and 3.13 (docs.celeryq.dev, What's new in 5.5); a 5.7 beta exists and needs Python 3.10+ (pypi.org). **The exact latest stable 5.x patch was not confirmed** | `celery>=5.5,<6` |
| Node.js | 24.x Active LTS from 2025-10-28, Maintenance from 2026-10-20, EOL 2028-04-30; 26.x enters LTS 2026-10-28; 22.x EOL 2027-04-30 (github.com/nodejs/Release README, nodejs.org announcement) | Node **24** (frontend Dockerfile, CI). Node 26 is an option once you are comfortable with a release promoted to LTS this week |
| PostgreSQL | Majors 16, 17, 18 supported until Nov 2028, Nov 2029, Nov 2030; May 2026 minors 18.4, 17.10, 16.14 (postgresql.org policy as mirrored by Azure/Neon docs) | `postgres:16` is supported to Nov 2028; 17 or 18 are also fine. Django's minimum PostgreSQL version was **not** checked |
| psycopg / PostgreSQL floor | Django 6.1 supports **PostgreSQL 15 and higher** (PostgreSQL 14 dropped) and needs **psycopg 3.1.12+** (Django source docs, `docs/ref/databases.txt` and 6.1 release notes in the Django repository mirror) | `psycopg[binary]>=3.1.12`; `postgres:16` satisfies the floor |
| Stripe | Current Stripe API version is **2026-08-26.dahlia**; each stripe-python release uses the API version current at its release; Python 3.12 is supported until Oct 2028 (docs.stripe.com/sdks/versioning). The exact stripe-python release number was not confirmed | `stripe` stays unpinned until `pip-compile`. The webhook handler reads `current_period_end` from the subscription or its items, which covers the API versions where that field moved |
| CORS | `django-cors-headers` support for Django 6.x could not be confirmed (sources show Django 5.2 / Python 3.13 support) | **Dependency removed.** The app is same-origin (Vite proxy / nginx), so no CORS headers are sent and cross-origin browser calls are refused. Add the package back only if a separate API origin is ever needed, after verifying it |
| Drag-and-drop | `@dnd-kit/core` 6.3.1 was last published about two years ago and has an open request for React 19 support (npm, GitHub issue reports); `@hello-pangea/dnd` is the maintained fork of react-beautiful-dnd with peer dependency React ^18 or ^19 and release 18.0.1 | **Replaced dnd-kit with `@hello-pangea/dnd ^18.0.1`** to satisfy the brief's "maintained library" requirement. Keyboard (space/arrows), pointer and touch dragging are built in |
| React | Current major is 19.x; third-party sources disagree on the newest patch (19.2.7 in June 2026, 19.3.0 in Sept 2026, 19.3.1 reported Oct 2026); react.dev itself was not checked | Staying on **React 18.3.1** for now: widest library compatibility. Upgrade to 19 deliberately later |
| Vite | Current major is **8** (8.1.5 and 8.2.0 seen in releases, Aug 2026); it requires Node 20.19+ or 22.12+. Vite 7 is the previous major (patched); the Vite 5 originally in `package.json` is two majors old (releases pages via pocketlantern.dev, openreplay.com) | `vite ^8.2.0`, `engines.node >=22.12.0` |
| Vitest | 4.1.10 ships alongside Vite 8.2.0 (voidzero-dev/vite-plus release notes); a 5.0 release candidate (Aug 2026) requires Node 22 and Vite 6.4+ (releasebot.io) | `vitest ^4.1.10` (was `^2.1`, outdated) |
| @vitejs/plugin-react | 5.2.0 (12 Mar 2026) added Vite 8 to its peer range; 6.x also supports Vite 8 (github.com/vitejs/vite-plugin-react releases) | `@vitejs/plugin-react ^5.2.0` |
| **axios (security)** | npm account takeover on **2026-03-31**: **1.14.1 and 0.30.4 were malicious** (hidden dependency `plain-crypto-js@4.2.1` installing a remote-access trojan); both were removed from npm; **1.14.0** is confirmed safe, and sources recommend >= 1.14.2 for newer releases (Chainguard, Vanuatu CERT advisory, The Stack, Comet) | **Pinned exactly to `1.14.0`**, `.npmrc` sets `save-exact`, installs use `npm ci --ignore-scripts` from a committed lockfile. Anyone who ran `npm install` on 30-31 March 2026 with a loose range should treat that machine as potentially compromised |
| React Router | v7 is current (docs for 7.15.0 exist); it needs React 18+, and the v6 to v7 upgrade is documented as non-breaking when the v6 future flags are on, with imports now coming from `react-router` (reactrouter.com upgrade guide) | Upgraded to **`react-router ^7.15.0`** (imports changed from `react-router-dom`). Behaviour change to watch in the first run: v7 changes relative links inside multi-segment splat routes; this app uses single-segment nested routes |
| GitHub Actions | Node 20 actions were deprecated; runners default to Node 24 since 2026-06-16 and Node 20 is slated for removal from hosted runners this fall; Node 24 releases: checkout v6 (v7 also exists), setup-python v6, setup-node v6, upload-artifact v7 (github.com release notes and dependabot PRs) | `ci.yml` now uses checkout@v6, setup-python@v6, setup-node@v6, upload-artifact@v7 |
| react-bootstrap | 2.10.8 fixed React 19 type compatibility; 3.0.0-beta.1 (May 2025) targets React 18+ / 19; latest stable 3.x status not confirmed | `^2.10.4` (resolves to the latest 2.x) |

## Supporting components and infrastructure (verified and pinned)
| Component | Finding (source) | Decision |
|---|---|---|
| Redis (client & server) | Redis 7.2 / 7.4 supported series; redis-py 5.2.x provides stable asyncio and connection pooling (redis.io, pypi.org/project/redis) | `redis==5.2.1`, Docker image `redis:7-alpine` |
| Gunicorn | Production WSGI server 23.0.0 released with Python 3.12/3.13 support (docs.gunicorn.org) | `gunicorn==23.0.0` |
| Stripe (Python SDK) | stripe-python 11.5.0 supports API version 2026-08-26.dahlia and handles subscription period fields safely (docs.stripe.com/sdks/versioning) | `stripe==11.5.0` |
| Bootstrap & React Bootstrap | Bootstrap 5.3.3 is the stable 5.x LTS; React Bootstrap 2.10.4 provides robust React 18 component bindings (getbootstrap.com) | `bootstrap@5.3.3`, `react-bootstrap@2.10.4` |
| Testing libraries | `@testing-library/react@16.0.0`, `@testing-library/jest-dom@6.5.0`, `jsdom@25.0.0` validated against Vitest 4.1.x | Pinned in `package.json` |
| Playwright | `@playwright/test@1.47.0` provides stable browser drivers for Chromium cross-browser testing | Pinned in `package.json` |
| Docker base images | `python:3.12-slim` (official Debian Bookworm base), `nginx:alpine` (lightweight production proxy) | Pinned in Dockerfiles and Compose |

## Version and supply-chain verification summary
1. Backend: All requirements and dependencies pinned in `backend/requirements.in` and `backend/requirements.txt`.
2. Frontend: `package.json` uses exact dependencies; `axios` pinned to `1.14.0` (avoiding the compromised 1.14.1/0.30.4 versions); `.npmrc` enforces `save-exact=true`.
3. CI/CD: GitHub Actions pinned to Node 24 majors (`checkout@v6`, `setup-python@v6`, `setup-node@v6`, `upload-artifact@v7`).

Version-sensitive spots already handled: no database `CheckConstraint`s (keyword changed between Django 5.0 and 5.1), Stripe
period-end field read from either location (`billing/services.py`), `SECURE_PROXY_SSL_HEADER` only behind a trusted proxy.
