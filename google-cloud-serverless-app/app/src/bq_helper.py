"""Google BigQuery helper functions."""

import logging
from typing import List, Dict, Any
from google.cloud import bigquery

logger = logging.getLogger(__name__)

bigquery_client = bigquery.Client()


def insert_metadata_row(
    dataset_id: str,
    table_id: str,
    row: Dict[str, Any]
) -> bool:
    """
    Insert a metadata row into BigQuery.

    Args:
        dataset_id: BigQuery dataset ID
        table_id: BigQuery table ID
        row: Dictionary containing the row data

    Returns:
        True if successful, False otherwise
    """
    try:
        project = bigquery_client.project
        table_ref = f"{project}.{dataset_id}.{table_id}"

        logger.info(f"Inserting row into {table_ref}")
        logger.debug(f"Row data: {row}")

        errors = bigquery_client.insert_rows_json(table_ref, [row])

        if errors:
            logger.error(f"Failed to insert row: {errors}")
            return False

        logger.info("Row inserted successfully")
        return True

    except Exception as e:
        logger.error(f"Error inserting row into BigQuery: {e}")
        raise


def insert_multiple_rows(
    dataset_id: str,
    table_id: str,
    rows: List[Dict[str, Any]]
) -> bool:
    """
    Insert multiple metadata rows into BigQuery.

    Args:
        dataset_id: BigQuery dataset ID
        table_id: BigQuery table ID
        rows: List of dictionaries containing row data

    Returns:
        True if all successful, False if any failed
    """
    try:
        project = bigquery_client.project
        table_ref = f"{project}.{dataset_id}.{table_id}"

        logger.info(f"Inserting {len(rows)} rows into {table_ref}")

        errors = bigquery_client.insert_rows_json(table_ref, rows)

        if errors:
            logger.error(f"Failed to insert {len(errors)} rows: {errors}")
            return False

        logger.info(f"All {len(rows)} rows inserted successfully")
        return True

    except Exception as e:
        logger.error(f"Error inserting rows into BigQuery: {e}")
        raise


def get_table_schema(dataset_id: str, table_id: str) -> List[bigquery.SchemaField]:
    """
    Get the schema of a BigQuery table.

    Args:
        dataset_id: BigQuery dataset ID
        table_id: BigQuery table ID

    Returns:
        List of SchemaField objects
    """
    try:
        project = bigquery_client.project
        table_ref = f"{project}.{dataset_id}.{table_id}"
        table = bigquery_client.get_table(table_ref)
        return table.schema
    except Exception as e:
        logger.error(f"Error getting table schema: {e}")
        raise
