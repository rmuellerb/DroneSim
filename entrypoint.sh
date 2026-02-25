#!/bin/sh
set -e

# Only run Django DB/static setup for the web process (gunicorn)
if echo "$*" | grep -q "gunicorn"; then
  echo "Running migrations + bootstrap_oidc + collectstatic (web only)..."

  until python manage.py migrate --noinput; do
    echo "migrate failed (db not ready yet) - retrying..."
    sleep 1
  done

  echo "Bootstrapping OIDC (idempotent)..."
  i=0
  until python manage.py bootstrap_oidc; do
    i=$((i+1))
    if [ "$i" -ge 10 ]; then
      echo "bootstrap_oidc failed 10 times, continuing without it"
      break
    fi
    echo "bootstrap_oidc failed - retrying..."
    sleep 1
  done

  python manage.py collectstatic --noinput
fi

exec "$@"
