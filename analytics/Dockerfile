FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DBT_PROFILES_DIR=/app/dbt

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY dbt ./dbt
COPY src ./src
COPY orchestration ./orchestration

ENV PYTHONPATH=/app/src:/app

CMD ["python", "-m", "orchestration.pipeline_flow"]

