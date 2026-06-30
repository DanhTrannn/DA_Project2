#!/bin/sh

set -eu

archive="${1:-/app/bootstrap/tv1_customer_dashboard.zip}"
username="${SUPERSET_ADMIN_USER:-admin}"

restore_connection() {
  superset set-database-uri \
    --database_name "${SUPERSET_SOURCE_DATABASE_NAME:-Adventureworks}" \
    --uri "${SUPERSET_SOURCE_URI}"
}

trap restore_connection EXIT

if [ ! -f "$archive" ]; then
  echo "TV1 dashboard archive not found: $archive" >&2
  exit 1
fi

superset import-dashboards \
  --path "$archive" \
  --username "$username"

/app/.venv/bin/python /app/bootstrap/configure_tv1_dashboard.py

echo "TV1 dashboard imported: $archive"
