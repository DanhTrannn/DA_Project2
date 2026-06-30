#!/usr/bin/env bash

set -euo pipefail

export HOST_UID="${HOST_UID:-$(id -u)}"
export HOST_GID="${HOST_GID:-$(id -g)}"

docker compose up -d db dbt
docker compose exec -T dbt dbt build \
  --project-dir /app/dbt \
  --profiles-dir /app/dbt

if curl -fsS http://localhost:8088/health >/dev/null 2>&1; then
  python3 superset/bootstrap_tv4.py
else
  echo "Superset is not running; start it and run: python3 superset/bootstrap_tv4.py"
fi

echo "TV4 pipeline completed."
echo "Inspect audit.source_to_dw_reconciliation and audit.data_quality_summary."
