#!/bin/sh

set -eu

archive="${1:-/app/bootstrap/tv1_customer_dashboard.zip}"
username="${SUPERSET_ADMIN_USER:-admin}"
prepared_archive="/tmp/tv1_customer_dashboard_import.zip"

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

/app/.venv/bin/python /app/bootstrap/prepare_dashboard_archive.py \
  "$archive" \
  "$prepared_archive" \
  "$SUPERSET_SOURCE_URI"

superset import-dashboards \
  --path "$prepared_archive" \
  --username "$username"

rm -f "$prepared_archive"

/app/.venv/bin/python /app/bootstrap/configure_customer_dashboard.py

echo "TV1 dashboard imported: $archive"
