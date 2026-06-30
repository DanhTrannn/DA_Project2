#!/usr/bin/env bash

set -Eeuo pipefail

ROOT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

export HOST_UID="${HOST_UID:-$(id -u)}"
export HOST_GID="${HOST_GID:-$(id -g)}"

on_error() {
  local exit_code=$?
  echo "ERROR: Full pipeline stopped at line ${BASH_LINENO[0]} (exit ${exit_code})." >&2
  echo "Run 'docker compose ps' and 'docker compose logs <service>' for details." >&2
  exit "$exit_code"
}
trap on_error ERR

require_command() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "ERROR: Required command not found: $1" >&2
    exit 1
  fi
}

published_port() {
  local service=$1
  local container_port=$2
  local binding

  binding="$(docker compose port "$service" "$container_port" | head -n 1)"
  if [[ -z "$binding" ]]; then
    echo "ERROR: No published port found for ${service}:${container_port}." >&2
    return 1
  fi
  printf '%s\n' "${binding##*:}"
}

wait_http() {
  local service=$1
  local url=$2
  local attempts=${3:-120}
  local attempt

  echo "Waiting for ${service}: ${url}"
  for ((attempt = 1; attempt <= attempts; attempt++)); do
    if curl -fsS --max-time 5 "$url" >/dev/null 2>&1; then
      echo "${service} is ready."
      return 0
    fi
    sleep 5
  done

  echo "ERROR: ${service} was not ready after $((attempts * 5)) seconds." >&2
  docker compose ps "$service" >&2
  docker compose logs --tail=100 "$service" >&2
  return 1
}

run_model() {
  local member=$1
  local module=$2

  echo
  echo "=== Running ${member}: ${module} ==="
  docker compose run --rm --no-deps streamlit python -m "$module"
}

verify_output() {
  local label=$1
  local table=$2
  local minimum_rows=$3
  local row_count

  row_count="$(
    docker compose exec -T db psql \
      -U "${POSTGRES_USER:-postgres}" \
      -d "${SOURCE_DATABASE:-Adventureworks}" \
      -Atqc "select count(*) from ${table};"
  )"
  row_count="${row_count//[[:space:]]/}"

  if [[ ! "$row_count" =~ ^[0-9]+$ ]] || ((row_count < minimum_rows)); then
    echo "ERROR: ${label} produced ${row_count:-no} rows; expected at least ${minimum_rows}." >&2
    return 1
  fi
  echo "${label}: ${row_count} rows."
}

validate_streamlit_page() {
  local page=$1

  docker compose exec -T streamlit python - "$page" <<'PY'
import sys

from streamlit.testing.v1 import AppTest

page = sys.argv[1]
app = AppTest.from_file(page)
app.run(timeout=120)
if app.exception:
    for exception in app.exception:
        print(exception.value, file=sys.stderr)
    raise SystemExit(f"Streamlit validation failed: {page}")
print(f"Streamlit page passed: {page}")
PY
}

require_command docker
require_command curl
docker compose version >/dev/null
docker info >/dev/null

echo "=== 1/7 Starting PostgreSQL, dbt, MLflow and Superset ==="
docker compose up -d --build db dbt mlflow superset

mlflow_port="$(published_port mlflow 5000)"
superset_port="$(published_port superset 8088)"
wait_http "MLflow" "http://localhost:${mlflow_port}/health"

echo
echo "=== 2/7 Refreshing macro data ==="
if ! docker compose exec -T dbt python /app/dbt/scripts/load_world_bank_macro.py; then
  echo "WARNING: Macro refresh failed; dbt will use the cached macro seed." >&2
fi

echo
echo "=== 3/7 Building and testing the complete dbt warehouse ==="
docker compose exec -T dbt dbt build \
  --project-dir /app/dbt \
  --profiles-dir /app/dbt

echo
echo "=== 4/7 Building the Data Mining runtime ==="
docker compose build streamlit
run_model "TV1 customer segmentation" "aw_analytics.segmentation"
run_model "TV2 FP-Growth market basket analysis" "aw_analytics.market_basket"
run_model "TV3 sales forecasting" "aw_analytics.tv3_sales_intelligence"

echo
echo "=== 5/7 Verifying model outputs ==="
verify_output "TV1 customer segments" "analytics.customer_segment" 1
verify_output "TV2 association rules" "analytics.product_association_rules" 10
verify_output "TV3 sales forecast" "analytics.sales_forecast" 1

echo
echo "=== 6/7 Bootstrapping the Superset dashboards ==="
wait_http "Superset" "http://localhost:${superset_port}/health"
docker compose exec -T superset python /app/bootstrap/bootstrap_tv4.py
docker compose exec -T superset python /app/bootstrap/bootstrap_tv2.py
docker compose exec -T superset python /app/bootstrap/bootstrap_tv3.py

echo
echo "=== 7/7 Starting and validating analytics applications ==="
docker compose build dbt-docs prefect-server
docker compose up -d streamlit dbt-docs prefect-server

streamlit_port="$(published_port streamlit 8501)"
dbt_docs_port="$(published_port dbt-docs 8080)"
prefect_port="$(published_port prefect-server 4200)"

wait_http "Streamlit" "http://localhost:${streamlit_port}/_stcore/health"
wait_http "dbt Docs" "http://localhost:${dbt_docs_port}"
wait_http "Prefect" "http://localhost:${prefect_port}/api/health"

validate_streamlit_page "/app/streamlit/pages/1_Customer_Analytics.py"
validate_streamlit_page "/app/streamlit/pages/2_Market_Basket.py"
validate_streamlit_page "/app/streamlit/pages/3_Sales_Intelligence.py"

echo
echo "Full pipeline completed successfully."
echo "Streamlit : http://localhost:${streamlit_port}"
echo "Superset  : http://localhost:${superset_port} (admin/admin by default)"
echo "TV1 BI    : http://localhost:${superset_port}/superset/dashboard/tv1-customer-analytics/"
echo "TV2 BI    : http://localhost:${superset_port}/superset/dashboard/adventureworks-tv2-product-analytics/"
echo "TV3 BI    : http://localhost:${superset_port}/superset/dashboard/adventureworks-tv3-sales-forecast/"
echo "TV4 BI    : http://localhost:${superset_port}/superset/dashboard/adventureworks-tv4-executive-macro/"
echo "MLflow    : http://localhost:${mlflow_port}"
echo "dbt Docs  : http://localhost:${dbt_docs_port}"
echo "Prefect   : http://localhost:${prefect_port}"
