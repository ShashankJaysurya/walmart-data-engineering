# Walmart Data Engineering Pipeline

An end-to-end example that ingests Walmart weekly sales CSV data into a
Databricks Unity Catalog volume and Delta table, transforms it with dbt, and
orchestrates the workflow with Apache Airflow.

## Architecture

```text
data/raw/walmart_sales.csv
        | Airflow DAG
        v
Unity Catalog Volume -> raw_walmart_sales (Delta)
                              | dbt
                              +-> stg_walmart_sales
                              +-> store_weekly_sales
                              +-> store_sales_summary
```

The included CSV is a small, synthetic sample for validating the pipeline
structure. Replace it with the Walmart dataset you are authorized to use. It
must have these columns in this order:

`Store,Date,Weekly_Sales,Holiday_Flag,Temperature,Fuel_Price,CPI,Unemployment`

## Prerequisites

- Docker Compose
- A Databricks SQL warehouse and a Unity Catalog catalog/schema
- A Databricks token with permission to create a volume and table, upload files
  to the volume, and run SQL on the warehouse

Create the catalog and schema in Databricks before running the pipeline. Set
their names, the volume name, warehouse HTTP path, host, and token in `.env`.
Keep `.env` private; it is ignored by Git.

## Run locally

1. Copy `.env.example` to `.env` and fill in the Databricks connection values.
2. Optionally replace `data/raw/walmart_sales.csv` with your source CSV.
3. Build and start Airflow:

   ```powershell
   docker compose up --build -d
   ```

4. Create an Airflow UI account:

   ```powershell
   docker compose exec airflow-webserver airflow users create `
     --username admin --firstname Airflow --lastname Admin `
     --role Admin --email admin@example.com --password admin
   ```

5. Open `http://localhost:8080`, sign in, and trigger `walmart_sales_pipeline`.
   The DAG uploads the CSV, loads it into the raw Delta table, then runs
   `dbt build` (models and tests).

Stop the local services with `docker compose down`. Add `-v` only if you also
intend to remove the local Airflow/Postgres state.

## Databricks setup and refreshes

The configured catalog and schema must already exist. The ingestion task creates
the configured Unity Catalog volume and raw table if needed. The Airflow
identity needs `USE CATALOG`, `USE SCHEMA`, volume creation/write permissions,
and permission to use the SQL warehouse.

`COPY INTO` tracks files it has loaded. To load a changed source again, set
`WALMART_CSV_PATH` to a new CSV filename and place that file in `data/raw/`.
Do not overwrite a previously loaded filename expecting it to be reprocessed.

## Project layout

- `dags/`: Airflow orchestration
- `scripts/`: CSV validation and Databricks ingestion
- `models/`: dbt source, staging, and mart models
- `tests/`: local unit tests for CSV validation
- `data/raw/`: sample input data

Run the local validation tests with `python -m unittest discover -s tests`.
To run dbt directly, install `requirements.txt` and set the Databricks
environment variables in your shell (dbt does not load `.env` automatically),
then run:

```powershell
dbt build --project-dir dbt --profiles-dir .
```

The dbt models target the catalog/schema configured by the Databricks profile;
intermediate and mart models are written to schemas named
`<configured-schema>_staging` and `<configured-schema>_marts`.
