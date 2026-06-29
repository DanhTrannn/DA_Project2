FROM apache/superset:latest

USER root
RUN uv pip install --python /app/.venv/bin/python psycopg2-binary
COPY superset_config.py /app/pythonpath/superset_config.py
COPY bootstrap_tv4.py bootstrap_tv2.py bootstrap_tv3.py /app/bootstrap/
USER superset

CMD ["/usr/bin/run-server.sh"]
