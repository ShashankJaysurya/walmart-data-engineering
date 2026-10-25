from datetime import datetime

from airflow import DAG
from airflow.operators.bash import BashOperator

PROJECT_DIR = "/opt/airflow/project"
DBT_DIR = f"{PROJECT_DIR}/dbt"

with DAG(
    dag_id="walmart_sales_pipeline",
    description="Load Walmart weekly sales into Databricks and build dbt marts",
    start_date=datetime(2024, 1, 1),
    schedule=None,
    catchup=False,
    tags=["walmart", "databricks", "dbt"],
) as dag:
    ingest = BashOperator(
        task_id="ingest_to_databricks",
        bash_command=f"python {PROJECT_DIR}/scripts/ingest_walmart.py",
    )

    transform_and_test = BashOperator(
        task_id="dbt_build",
        bash_command=f"dbt build --project-dir {DBT_DIR} --profiles-dir {PROJECT_DIR}",
    )

    ingest >> transform_and_test
