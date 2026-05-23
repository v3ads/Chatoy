#!/usr/bin/env bash
# Production entrypoint: apply migrations (when a database is configured) then
# serve the API on the platform-provided $PORT.
set -euo pipefail

if [ -n "${MYTHOSTACK_DATABASE_URL:-}" ]; then
  echo "==> Applying database migrations"
  alembic upgrade head
else
  echo "==> MYTHOSTACK_DATABASE_URL not set; skipping migrations (in-memory stores)"
fi

echo "==> Starting API on port ${PORT:-8080}"
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8080}"
