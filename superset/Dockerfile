FROM apache/superset:latest

USER root
RUN uv pip install --python /app/.venv/bin/python psycopg2-binary
COPY superset_config.py /app/pythonpath/superset_config.py
COPY bootstrap_tv4.py bootstrap_tv2.py bootstrap_tv3.py /app/bootstrap/
COPY dashboard_export_20260630T071534.zip /app/bootstrap/tv1_customer_dashboard.zip
COPY --chmod=755 import_tv1_dashboard.sh /app/bootstrap/import_tv1_dashboard.sh
COPY configure_tv1_dashboard.py /app/bootstrap/configure_tv1_dashboard.py
USER superset

CMD ["/usr/bin/run-server.sh"]
