import os

SECRET_KEY = os.getenv("SUPERSET_SECRET_KEY", "change-this-secret-key")
SQLALCHEMY_DATABASE_URI = "sqlite:////app/superset_home/superset.db"
FEATURE_FLAGS = {"ENABLE_TEMPLATE_PROCESSING": True}

THEME = {
    "token": {
        "colorBgBase": "#ffffff",
        "colorBgContainer": "#ffffff",
        "colorBgLayout": "#ffffff",
        "colorBgElevated": "#ffffff",
        "colorBgSpotlight": "#ffffff",
        "colorTextBase": "#000000",
        "colorTextSecondary": "#333333",
        "colorBorder": "#e8e8e8",
        "colorBorderSecondary": "#f0f0f0",
    }
}

