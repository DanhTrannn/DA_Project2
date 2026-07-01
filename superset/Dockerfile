FROM apache/superset:latest

USER root
RUN uv pip install --python /app/.venv/bin/python psycopg2-binary
COPY superset_config.py /app/pythonpath/superset_config.py
COPY bootstrap_executive_dashboard.py bootstrap_product_dashboard.py bootstrap_sales_dashboard.py /app/bootstrap/
COPY dashboard_export_20260630T071534.zip /app/bootstrap/tv1_customer_dashboard.zip
COPY --chmod=755 import_tv1_dashboard.sh /app/bootstrap/import_tv1_dashboard.sh
COPY configure_customer_dashboard.py /app/bootstrap/configure_customer_dashboard.py
COPY prepare_dashboard_archive.py /app/bootstrap/prepare_dashboard_archive.py
USER superset

CMD ["/usr/bin/run-server.sh"]
