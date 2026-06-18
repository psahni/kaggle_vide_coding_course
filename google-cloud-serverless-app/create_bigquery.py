#!/usr/bin/env python3
"""
Create BigQuery dataset and table using Python API.
This avoids gcloud CLI issues.
"""

import sys
import json
from google.cloud import bigquery

def create_bigquery_resources(project_id, dataset_id, table_id, schema_file, region):
    """Create BigQuery dataset and table."""

    try:
        client = bigquery.Client(project=project_id)

        # 1. Create Dataset
        print(f"Creating BigQuery Dataset: {dataset_id}...")
        dataset_id_full = f"{project_id}.{dataset_id}"
        dataset = bigquery.Dataset(dataset_id_full)
        dataset.location = region

        try:
            dataset = client.create_dataset(dataset, exists_ok=True)
            print(f"   Dataset {dataset_id} created successfully")
        except Exception as e:
            if "Already Exists" in str(e) or "already exists" in str(e):
                print(f"   Dataset {dataset_id} already exists")
            else:
                raise

        # 2. Create Table
        print(f"Creating BigQuery Table: {table_id}...")

        # Read schema from file
        with open(schema_file, 'r') as f:
            schema_json = json.load(f)

        # Convert JSON schema to SchemaField objects
        schema = []
        for field in schema_json:
            schema.append(bigquery.SchemaField(
                name=field['name'],
                field_type=field['type'],
                mode=field.get('mode', 'NULLABLE'),
                description=field.get('description', '')
            ))

        table_id_full = f"{project_id}.{dataset_id}.{table_id}"
        table = bigquery.Table(table_id_full, schema=schema)

        try:
            table = client.create_table(table, exists_ok=True)
            print(f"   Table {table_id} created successfully")
        except Exception as e:
            if "Already Exists" in str(e) or "already exists" in str(e):
                print(f"   Table {table_id} already exists")
            else:
                raise

        print("✓ BigQuery resources created successfully")
        return True

    except Exception as e:
        print(f"✗ Error creating BigQuery resources: {e}")
        print("\nMake sure you have:")
        print("  1. Authenticated with gcloud: gcloud auth application-default login")
        print("  2. Set your project: gcloud config set project YOUR_PROJECT_ID")
        print("  3. BigQuery API enabled: gcloud services enable bigquery.googleapis.com")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 5:
        print("Usage: python3 create_bigquery.py PROJECT_ID DATASET_ID TABLE_ID SCHEMA_FILE [REGION]")
        sys.exit(1)

    project_id = sys.argv[1]
    dataset_id = sys.argv[2]
    table_id = sys.argv[3]
    schema_file = sys.argv[4]
    region = sys.argv[5] if len(sys.argv) > 5 else "us-central1"

    success = create_bigquery_resources(project_id, dataset_id, table_id, schema_file, region)
    sys.exit(0 if success else 1)
