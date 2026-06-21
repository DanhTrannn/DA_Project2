from __future__ import annotations

import os

import mlflow


def configure_mlflow(experiment_name: str) -> None:
    mlflow.set_tracking_uri(os.getenv("MLFLOW_TRACKING_URI", "http://mlflow:5000"))
    mlflow.set_experiment(experiment_name)

