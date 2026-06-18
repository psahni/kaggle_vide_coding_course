#!/usr/bin/env python3
"""
Query BigQuery using Python API.
This avoids bq CLI PATH issues.
"""

import sys
import json
from google.cloud import bigquery

def query_bigquery(project_id, query_str):
    """Execute a BigQuery query and return results."""
    try:
        client = bigquery.Client(project=project_id)
        results = client.query(query_str).result()

        # Convert to list of dictionaries
        rows = []
        for row in results:
            rows.append(dict(row))

        return rows
    except Exception as e:
        print(f"Error querying BigQuery: {e}", file=sys.stderr)
        return None

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python3 query_bigquery.py PROJECT_ID QUERY_STRING [json]")
        print("  Set 3rd arg to 'json' to output as JSON")
        sys.exit(1)

    project_id = sys.argv[1]
    query_str = sys.argv[2]
    output_format = sys.argv[3] if len(sys.argv) > 3 else "text"

    rows = query_bigquery(project_id, query_str)

    if rows is None:
        sys.exit(1)

    if output_format == "json":
        print(json.dumps(rows))
    else:
        # Text output
        if len(rows) == 0:
            print("No results")
        else:
            # Print header
            if rows:
                headers = list(rows[0].keys())
                print(" | ".join(headers))
                print("-" * 80)

                # Print rows
                for row in rows:
                    values = [str(row.get(h, "")) for h in headers]
                    print(" | ".join(values))

    sys.exit(0)
