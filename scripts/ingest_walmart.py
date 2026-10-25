import csv
import os
import re
from pathlib import Path

REQUIRED_COLUMNS = (
    "Store",
    "Date",
    "Weekly_Sales",
    "Holiday_Flag",
    "Temperature",
    "Fuel_Price",
    "CPI",
    "Unemployment",
)
IDENTIFIER_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
CSV_FILENAME_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*\.csv$", re.IGNORECASE)


def validate_csv(csv_path: Path) -> int:
    """Validate the source headers and return its number of data rows."""
    with csv_path.open(newline="", encoding="utf-8-sig") as source:
        reader = csv.DictReader(source)
        headers = reader.fieldnames
        if headers is None:
            raise ValueError(f"CSV has no header row: {csv_path}")

        if tuple(headers) != REQUIRED_COLUMNS:
            raise ValueError(
                "CSV columns must match the required names and order: "
                + ", ".join(REQUIRED_COLUMNS)
            )

        row_count = sum(1 for _ in reader)
        if row_count == 0:
            raise ValueError(f"CSV has no data rows: {csv_path}")
        return row_count


def _identifier(value: str, name: str) -> str:
    if not IDENTIFIER_PATTERN.fullmatch(value):
        raise ValueError(f"{name} must be a simple SQL identifier, got {value!r}")
    return f"`{value}`"


def ingest() -> None:
    csv_path = Path(os.environ.get("WALMART_CSV_PATH", "data/raw/walmart_sales.csv"))
    if not csv_path.is_absolute():
        csv_path = Path(__file__).resolve().parents[1] / csv_path
    if not csv_path.is_file():
        raise FileNotFoundError(f"Walmart CSV not found: {csv_path.resolve()}")
    row_count = validate_csv(csv_path)

    host = os.environ["DATABRICKS_HOST"].rstrip("/")
    token = os.environ["DATABRICKS_TOKEN"]
    http_path = os.environ["DATABRICKS_HTTP_PATH"]
    catalog = _identifier(os.environ["DATABRICKS_CATALOG"], "DATABRICKS_CATALOG")
    schema = _identifier(os.environ["DATABRICKS_SCHEMA"], "DATABRICKS_SCHEMA")
    volume = _identifier(os.environ.get("DATABRICKS_VOLUME", "walmart_landing"), "DATABRICKS_VOLUME")
    table_name = f"{catalog}.{schema}.`raw_walmart_sales`"
    volume_dir = f"/Volumes/{catalog.strip('`')}/{schema.strip('`')}/{volume.strip('`')}"
    source_name = csv_path.name
    if not CSV_FILENAME_PATTERN.fullmatch(source_name):
        raise ValueError("WALMART_CSV_PATH must have a simple .csv filename")
    volume_path = f"{volume_dir}/{source_name}"

    from databricks.sdk import WorkspaceClient
    from databricks.sql import connect

    workspace = WorkspaceClient(host=host, token=token)
    with connect(
        server_hostname=host.removeprefix("https://").removeprefix("http://"),
        http_path=http_path,
        access_token=token,
    ) as connection:
        with connection.cursor() as cursor:
            cursor.execute(f"CREATE VOLUME IF NOT EXISTS {catalog}.{schema}.{volume}")

    with csv_path.open("rb") as source:
        workspace.files.upload(volume_path, source, overwrite=True)

    with connect(
        server_hostname=host.removeprefix("https://").removeprefix("http://"),
        http_path=http_path,
        access_token=token,
    ) as connection:
        with connection.cursor() as cursor:
            cursor.execute(f"CREATE VOLUME IF NOT EXISTS {catalog}.{schema}.{volume}")
            cursor.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {table_name} (
                    store INT,
                    sale_date STRING,
                    weekly_sales DOUBLE,
                    holiday_flag INT,
                    temperature DOUBLE,
                    fuel_price DOUBLE,
                    cpi DOUBLE,
                    unemployment DOUBLE
                )
                USING DELTA
                """
            )
            cursor.execute(
                f"""
                COPY INTO {table_name}
                FROM '{volume_path}'
                FILEFORMAT = CSV
                FORMAT_OPTIONS ('header' = 'true')
                """
            )

    print(f"Validated {row_count} rows; loaded source file to {table_name}.")


if __name__ == "__main__":
    ingest()
