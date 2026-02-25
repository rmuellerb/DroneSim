#!/bin/sh
set -e

is_postgres=false
case "${SQL_ENGINE:-}" in
  *postgresql*) is_postgres=true ;;
esac

# Wait for Postgres TCP readiness (important during initdb/bootstrap)
if [ "$is_postgres" = "true" ] && [ -n "${SQL_HOST:-}" ]; then
  echo "Waiting for postgres TCP (${SQL_HOST}:${SQL_PORT:-5432})..."

  # pg_isready returns 0 only when server accepts connections
  until pg_isready -h "$SQL_HOST" -p "${SQL_PORT:-5432}" -U "${SQL_USER:-postgres}" >/dev/null 2>&1; do
    sleep 0.5
  done

  echo "PostgreSQL is accepting connections"
fi

# Only run Django DB/static setup for the web process (gunicorn)
if echo "$*" | grep -q "gunicorn"; then
  echo "Running migrations + collectstatic (web only)..."

  # Retry migrate to survive brief startup races
  until python manage.py migrate --no-input; do
    echo "migrate failed (db not ready yet) - retrying..."
    sleep 1
  done

  python manage.py collectstatic --no-input --clear
fi

exec "$@"
