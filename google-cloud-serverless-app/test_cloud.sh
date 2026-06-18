#!/usr/bin/env bash

# Test the deployed pipeline on Google Cloud
# This script uploads test files to GCS and queries BigQuery to verify processing

set -e

echo "=========================================================="
echo "Cloud Testing: Event-Driven Document Processor"
echo "=========================================================="

# Get project ID
PROJECT_ID=$(gcloud config get-value project 2>/dev/null)
if [ -z "$PROJECT_ID" ] || [ "$PROJECT_ID" = "(unset)" ]; then
  echo "Error: No Google Cloud project is currently selected."
  echo "Please set your project using: gcloud config set project YOUR_PROJECT_ID"
  exit 1
fi

BUCKET_NAME="${PROJECT_ID}-docs-ingest"
DATASET_NAME="docs_metadata"
TABLE_NAME="processed_docs"
REGION="us-central1"

echo "Project ID:      $PROJECT_ID"
echo "Bucket:          $BUCKET_NAME"
echo "BigQuery Table:  $DATASET_NAME.$TABLE_NAME"
echo "=========================================================="

# 1. Create test files
echo ""
echo "1. Creating test files..."

TEMP_DIR=$(mktemp -d)
trap "rm -rf $TEMP_DIR" EXIT

# Create a text file with keywords
cat > "$TEMP_DIR/invoice_001.txt" << 'EOF'
INVOICE #001
Date: 2025-06-16
Customer: Acme Corporation
Item 1: Service Fee - $100
Item 2: Processing Fee - $50
Total Amount Due: $150
Payment Terms: Net 30 days
This is an official invoice for services rendered.
EOF

# Create another text file with different content
cat > "$TEMP_DIR/report_q2_2025.txt" << 'EOF'
QUARTERLY REPORT - Q2 2025
Executive Summary:
This report provides a detailed analysis of business metrics for Q2 2025.
Key Performance Indicators:
- Revenue: $500,000
- Profit Margin: 35%
- Growth Rate: 15% YoY
Operational Details:
The logistics and shipping operations have improved significantly.
Customer Statement as of 2025-06-16.
EOF

# Create a receipt file
cat > "$TEMP_DIR/receipt_20250616.txt" << 'EOF'
RECEIPT
Transaction ID: TXN-20250616-001
Items purchased:
1. Product A - $25.99
2. Product B - $14.50
Subtotal: $40.49
Tax: $3.24
Total: $43.73
Payment Method: Credit Card
Receipt Date: 2025-06-16
Thank you for your business!
EOF

echo "   Created test files:"
ls -lh "$TEMP_DIR/"

# 2. Upload files to GCS
echo ""
echo "2. Uploading test files to gs://$BUCKET_NAME/..."

for file in "$TEMP_DIR"/*; do
  filename=$(basename "$file")
  echo "   Uploading $filename..."
  gcloud storage cp "$file" "gs://$BUCKET_NAME/$filename"
done

echo "   ✓ Files uploaded"

# 3. Wait for processing
echo ""
echo "3. Waiting for files to be processed (this may take 10-30 seconds)..."
sleep 15

# 4. Query BigQuery
echo ""
echo "4. Querying BigQuery results..."
echo ""

# Check if table has data
QUERY="SELECT COUNT(*) as record_count FROM \`$PROJECT_ID.$DATASET_NAME.$TABLE_NAME\`"
COUNT_RESULT=$(python3 ./query_bigquery.py "$PROJECT_ID" "$QUERY" json)
RESULT=$(echo "$COUNT_RESULT" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data[0]['record_count'] if data else 0)" 2>/dev/null || echo "0")

echo "Total records in table: $RESULT"

if [ "$RESULT" != "0" ] && [ -n "$RESULT" ]; then
  echo ""
  echo "Recent processed documents:"
  echo "=========================================================="

  DETAIL_QUERY="
    SELECT
      filename,
      processed_at,
      word_count,
      ARRAY_LENGTH(tags) as tag_count,
      ARRAY_TO_STRING(tags, ', ') as tags,
      file_size
    FROM \`$PROJECT_ID.$DATASET_NAME.$TABLE_NAME\`
    ORDER BY processed_at DESC
    LIMIT 10
  "

  python3 ./query_bigquery.py "$PROJECT_ID" "$DETAIL_QUERY"

  echo ""
  echo "=========================================================="
  echo "✓ Pipeline test successful!"
  echo ""
  echo "View the full BigQuery table:"
  echo "  bq show -t $PROJECT_ID:$DATASET_NAME.$TABLE_NAME"
  echo ""
  echo "Run custom queries in BigQuery Console:"
  echo "  https://console.cloud.google.com/bigquery"
else
  echo ""
  echo "⚠ No records found in BigQuery table."
  echo "Possible reasons:"
  echo "  1. Cloud Run service is still initializing"
  echo "  2. Pub/Sub messages haven't been processed yet"
  echo "  3. There was an error processing the files"
  echo ""
  echo "Check Cloud Run logs:"
  echo "  gcloud run logs read doc-processor-service --region $REGION --limit 50"
  echo ""
  echo "Check Pub/Sub subscription:"
  echo "  gcloud pubsub subscriptions describe docs-upload-topic-sub"
fi

echo ""
echo "=========================================================="
