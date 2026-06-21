from __future__ import annotations

import subprocess

from prefect import flow, task


@task(retries=2, retry_delay_seconds=10)
def run_command(command: list[str]) -> None:
    subprocess.run(command, check=True)


@task
def refresh_macro_data() -> None:
    result = subprocess.run(
        ["python", "/app/dbt/scripts/load_world_bank_macro.py"],
        check=False,
    )
    if result.returncode != 0:
        print(
            "Macro refresh failed; continuing with the cached/empty seed. "
            "Macro coverage will be reported as a warning."
        )


DBT_BASE_COMMAND = [
    "--project-dir",
    "/app/dbt",
    "--profiles-dir",
    "/app/dbt",
]


@flow(name="adventureworks-analytics-pipeline", log_prints=True)
def analytics_pipeline() -> None:
    refresh_macro_data()
    run_command(["dbt", "seed", *DBT_BASE_COMMAND])
    run_command(
        [
            "dbt",
            "build",
            *DBT_BASE_COMMAND,
        ]
    )


@flow(name="adventureworks-staging-pipeline", log_prints=True)
def staging_pipeline() -> None:
    run_command(
        ["dbt", "build", "--select", "path:models/staging", *DBT_BASE_COMMAND]
    )


if __name__ == "__main__":
    analytics_pipeline()
