#!/usr/bin/env bash

set -euo pipefail

export HOST_UID="${HOST_UID:-$(id -u)}"
export HOST_GID="${HOST_GID:-$(id -g)}"

docker compose up -d db dbt mlflow
docker compose exec -T dbt dbt build \
  --select +feature_customer_rfm \
  --project-dir /app/dbt \
  --profiles-dir /app/dbt

docker compose build streamlit
docker compose run --rm streamlit python -m aw_analytics.segmentation
docker compose up -d streamlit

echo "TV1 model output has been written to schema analytics."
echo "Open http://localhost:${STREAMLIT_PORT:-8501} to view the shared Streamlit app."
