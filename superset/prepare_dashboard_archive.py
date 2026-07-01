from __future__ import annotations

import io
import sys
import zipfile


def prepare_archive(source: str, destination: str, database_uri: str) -> None:
    with zipfile.ZipFile(source, "r") as input_archive:
        output_buffer = io.BytesIO()
        with zipfile.ZipFile(output_buffer, "w", zipfile.ZIP_DEFLATED) as output_archive:
            for item in input_archive.infolist():
                content = input_archive.read(item.filename)
                if "/databases/" in item.filename and item.filename.endswith(".yaml"):
                    lines = content.decode("utf-8").splitlines()
                    lines = [
                        f"sqlalchemy_uri: {database_uri}"
                        if line.startswith("sqlalchemy_uri:")
                        else line
                        for line in lines
                    ]
                    content = ("\n".join(lines) + "\n").encode("utf-8")
                output_archive.writestr(item, content)

    with open(destination, "wb") as output_file:
        output_file.write(output_buffer.getvalue())


if __name__ == "__main__":
    if len(sys.argv) != 4:
        raise SystemExit("Usage: prepare_dashboard_archive.py SOURCE DESTINATION DATABASE_URI")
    prepare_archive(sys.argv[1], sys.argv[2], sys.argv[3])
