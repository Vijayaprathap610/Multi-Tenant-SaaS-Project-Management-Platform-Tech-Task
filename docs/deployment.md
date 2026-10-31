# Deployment

## Local (development)
```bash
cp .env.example .env            # fill DJANGO_SECRET_KEY, POSTGRES_PASSWORD
docker compose run --rm backend python manage.py makemigrations   # first time only; commit results
docker compose up --build       # applies docker-compose.override.yml (runserver, bind mounts)
# app: http://localhost:5173   API: http://localhost:8000/api/
docker compose run --rm backend python manage.py create_platform_admin --email you@example.com
```
Stripe (test mode): put `STRIPE_SECRET_KEY`, `STRIPE_PRICE_PRO`, `STRIPE_PRICE_BUSINESS` in `.env`, then
`stripe listen --forward-to localhost:8000/api/billing/webhook/` and copy the printed signing secret into
`STRIPE_WEBHOOK_SECRET`. Use Stripe test cards only.

## Server (production-style)
Use only the base file: `docker compose -f docker-compose.yml up -d --build`.
Requirements: `DJANGO_DEBUG=false`; strong `DJANGO_SECRET_KEY`; `DJANGO_ALLOWED_HOSTS`, `TRUSTED_ORIGINS`
set to your https origin; a TLS-terminating reverse proxy in front of the `frontend` container that sets
`X-Forwarded-Proto: https` (Django redirects to https and marks cookies Secure when DEBUG is false).

## GitHub Actions deploy job
Runs on pushes to `main` after backend, frontend and docker jobs pass. It stays inert until these repository
secrets exist: `DEPLOY_HOST`, `DEPLOY_USER`, `DEPLOY_SSH_KEY` (and the server needs the repo cloned at
`/opt/techtask` with a production `.env`). Create a protected `production` environment for approvals.
A workflow file alone does not mean a deployment exists: record the deployed URL or a screen recording as evidence.

## Backup and recovery
- Database: `docker compose exec db pg_dump -U $POSTGRES_USER $POSTGRES_DB > backup.sql` (schedule daily, store off-host).
  Restore: `psql` into an empty database, then `manage.py migrate --check`.
- Files: back up the `media` volume (attachments) together with the database dump.
- Platform Admin credential rotation: deactivate the old admin in the Django shell
  (`User.objects.filter(is_platform_admin=True).update(is_active=False)`), then run `create_platform_admin` again.
