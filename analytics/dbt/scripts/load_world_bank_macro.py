from __future__ import annotations

import csv
import json
import os
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path


COUNTRIES = {
    "US": ("USA", "United States"),
    "CA": ("CAN", "Canada"),
    "GB": ("GBR", "United Kingdom"),
    "FR": ("FRA", "France"),
    "DE": ("DEU", "Germany"),
    "AU": ("AUS", "Australia"),
}

INDICATORS = {
    "FP.CPI.TOTL.ZG": ("Inflation, consumer prices", "annual %"),
    "NY.GDP.MKTP.KD.ZG": ("GDP growth", "annual %"),
    "SL.UEM.TOTL.ZS": ("Unemployment, total", "% of total labor force"),
}

FIELDNAMES = [
    "country_code",
    "country_name",
    "year",
    "indicator_code",
    "indicator_name",
    "value",
    "unit",
    "source_name",
    "source_url",
    "retrieved_at",
]


def has_cached_rows(path: Path) -> bool:
    if not path.exists():
        return False
    with path.open(encoding="utf-8") as cached_file:
        return sum(1 for _ in cached_file) > 1


def detect_sales_year_range() -> tuple[int, int]:
    import psycopg

    with psycopg.connect(
        host=os.getenv("SOURCE_HOST", "db"),
        port=int(os.getenv("SOURCE_INTERNAL_PORT", "5432")),
        dbname=os.getenv("SOURCE_DATABASE", "Adventureworks"),
        user=os.getenv("POSTGRES_USER", "postgres"),
        password=os.getenv("POSTGRES_PASSWORD", "postgres"),
    ) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                select
                    extract(year from min(orderdate))::integer,
                    extract(year from max(orderdate))::integer
                from sales.salesorderheader
                """
            )
            start_year, end_year = cursor.fetchone()
    if start_year is None or end_year is None:
        raise RuntimeError("AdventureWorks sales date range is empty")
    return start_year, end_year


def fetch_indicator(
    country_code: str,
    iso3: str,
    country_name: str,
    indicator_code: str,
    indicator_name: str,
    unit: str,
    start_year: int,
    end_year: int,
) -> list[dict[str, object]]:
    query = urllib.parse.urlencode(
        {
            "date": f"{start_year}:{end_year}",
            "format": "json",
            "per_page": "1000",
        }
    )
    url = (
        f"https://api.worldbank.org/v2/country/{iso3}/indicator/"
        f"{indicator_code}?{query}"
    )
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "AdventureWorks-Analytics/1.0"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        payload = json.load(response)

    observations = payload[1] if isinstance(payload, list) and len(payload) > 1 else []
    rows: list[dict[str, object]] = []
    for observation in observations or []:
        if observation.get("value") is None:
            continue
        rows.append(
            {
                "country_code": country_code,
                "country_name": country_name,
                "year": int(observation["date"]),
                "indicator_code": indicator_code,
                "indicator_name": indicator_name,
                "value": observation["value"],
                "unit": unit,
                "source_name": "World Bank Indicators API",
                "source_url": url,
                "retrieved_at": date.today().isoformat(),
            }
        )
    return rows


def main() -> int:
    detected_start_year, detected_end_year = detect_sales_year_range()
    start_year = int(os.getenv("MACRO_START_YEAR", detected_start_year))
    end_year = int(os.getenv("MACRO_END_YEAR", detected_end_year))
    output_path = Path(
        os.getenv(
            "MACRO_OUTPUT",
            Path(__file__).resolve().parents[1] / "seeds" / "macro_observations.csv",
        )
    )

    rows: list[dict[str, object]] = []
    try:
        for country_code, (iso3, country_name) in COUNTRIES.items():
            for indicator_code, (indicator_name, unit) in INDICATORS.items():
                rows.extend(
                    fetch_indicator(
                        country_code,
                        iso3,
                        country_name,
                        indicator_code,
                        indicator_name,
                        unit,
                        start_year,
                        end_year,
                    )
                )
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        if has_cached_rows(output_path):
            print(
                f"World Bank download failed; keeping cached seed: {exc}",
                file=sys.stderr,
            )
            return 0
        print(f"World Bank download failed: {exc}", file=sys.stderr)
        return 1

    if not rows:
        print("World Bank API returned no macro observations", file=sys.stderr)
        return 1

    rows.sort(key=lambda row: (row["country_code"], row["year"], row["indicator_code"]))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w",
        newline="",
        encoding="utf-8",
        dir=output_path.parent,
        delete=False,
    ) as temporary_file:
        writer = csv.DictWriter(
            temporary_file,
            fieldnames=FIELDNAMES,
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)
        temporary_path = Path(temporary_file.name)

    temporary_path.replace(output_path)
    print(f"Wrote {len(rows)} observations to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
