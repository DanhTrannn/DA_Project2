from superset.app import create_app


DASHBOARD_TITLE = "TV1 - Customer Analytics"
DASHBOARD_SLUG = "tv1-customer-analytics"


def main() -> None:
    app = create_app()
    with app.app_context():
        from superset import db
        from superset.models.dashboard import Dashboard

        dashboard = (
            db.session.query(Dashboard)
            .filter(Dashboard.dashboard_title == DASHBOARD_TITLE)
            .one()
        )
        dashboard.slug = DASHBOARD_SLUG
        db.session.commit()
        print(f"TV1 dashboard slug ready: {DASHBOARD_SLUG}")


if __name__ == "__main__":
    main()
