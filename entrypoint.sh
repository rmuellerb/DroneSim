#!/bin/sh
set -e

# Only run Django DB/static setup for the web process (gunicorn)
if echo "$*" | grep -q "gunicorn"; then
  echo "Running migrations + collectstatic (web only)..."

  # Retry migrate to survive DB startup races
  until python manage.py migrate --no-input; do
    echo "migrate failed (db not ready yet) - retrying..."
    sleep 1
  done

  python manage.py collectstatic --no-input --clear
fi

exec "$@"
