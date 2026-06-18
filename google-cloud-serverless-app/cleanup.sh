#!/bin/bash

# Exit on any error to prevent partial deletion
set -e

PROJECT_ID="ps-my-document-processor"
REGION="us-central1"
BUCKET_NAME="${PROJECT_ID}-docs-ingest"
DATASET_NAME="docs_metadata"

echo "=========================================="
echo "DELETING ALL GCP RESOURCES"
echo "This cannot be undone!"
echo "=========================================="
echo ""

# Confirm deletion
read -p "Type 'DELETE' to confirm: " CONFIRM
if [ "$CONFIRM" != "DELETE" ]; then
  echo "Cleanup cancelled"
  exit 0
fi

echo ""
echo "1. Deleting Cloud Run service..."
gcloud run services delete doc-processor-service \
  --region $REGION --quiet || echo "Cloud Run service not found"

echo ""
echo "2. Deleting Pub/Sub subscription..."
gcloud pubsub subscriptions delete docs-upload-topic-sub \
  --quiet || echo "Subscription not found"

echo ""
echo "3. Deleting Pub/Sub topic..."
gcloud pubsub topics delete docs-upload-topic \
  --quiet || echo "Topic not found"

echo ""
echo "4. Deleting GCS notification..."
NOTIF_ID=$(gcloud storage buckets notifications list \
  gs://$BUCKET_NAME --format="value(name)" 2>/dev/null || echo "")
if [ -n "$NOTIF_ID" ]; then
  gcloud storage buckets notifications delete $NOTIF_ID \
    --bucket-name=$BUCKET_NAME 2>/dev/null || echo "Notification not found"
else
  echo "No notifications found"
fi

echo ""
echo "5. Deleting Cloud Storage bucket (and all files)..."
gcloud storage rm gs://$BUCKET_NAME --recursive --quiet || echo "Bucket already empty"
gcloud storage buckets delete gs://$BUCKET_NAME --quiet || echo "Bucket not found"

echo ""
echo "6. Deleting BigQuery dataset (and all data)..."
bq rm --dataset --recursive --force \
  --project_id=$PROJECT_ID $DATASET_NAME || echo "Dataset not found"

echo ""
echo "7. Deleting service accounts..."
gcloud iam service-accounts delete \
  doc-processor-sa@${PROJECT_ID}.iam.gserviceaccount.com \
  --quiet || echo "doc-processor-sa not found"

gcloud iam service-accounts delete \
  pubsub-invoker-sa@${PROJECT_ID}.iam.gserviceaccount.com \
  --quiet || echo "pubsub-invoker-sa not found"

echo ""
echo "=========================================="
echo "✓ Cleanup Complete!"
echo "=========================================="
echo ""
echo "Remaining in project:"
gcloud storage buckets list --project=$PROJECT_ID
bq ls -d --project_id=$PROJECT_ID
gcloud run services list --project=$PROJECT_ID

