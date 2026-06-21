#!/usr/bin/env bash

set -euo pipefail

docker compose up -d db dbt
if ! docker compose exec -T dbt python /app/dbt/scripts/load_world_bank_macro.py; then
  echo "WARNING: World Bank refresh failed; continuing with cached/empty macro seed."
fi
docker compose exec -T dbt dbt seed \
  --project-dir /app/dbt \
  --profiles-dir /app/dbt
docker compose exec -T dbt dbt build \
  --project-dir /app/dbt \
  --profiles-dir /app/dbt

if curl -fsS http://localhost:8088/health >/dev/null 2>&1; then
  python3 superset/bootstrap_tv4.py
else
  echo "Superset is not running; start it and run: python3 superset/bootstrap_tv4.py"
fi

echo "TV4 pipeline completed."
echo "Inspect audit.source_to_dw_reconciliation and mart_macro.business_kpi_macro_period."
