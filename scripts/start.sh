#!/usr/bin/env bash
# Production entrypoint: apply migrations (when a database is configured) then
# serve the API on the platform-provided $PORT.
set -euo pipefail

if [ -n "${MYTHOSTACK_DATABASE_URL:-}" ]; then
  echo "==> Applying database migrations"
  alembic upgrade head
elif [ -n "${CHATOY_DATABASE_URL:-}" ]; then
  echo "==> Applying database migrations (legacy env)"
  alembic upgrade head
else
  echo "==> Database URL not set; skipping migrations (in-memory stores)"
fi

echo "==> Starting API on port ${PORT:-8000}"
echo "==> Debugging Python environment"
pip freeze
python -c "import sys; print(sys.path)"
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
