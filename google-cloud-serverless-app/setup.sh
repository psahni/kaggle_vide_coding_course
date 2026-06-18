#!/usr/bin/env bash

# Exit immediately if a command exits with a non-zero status
set -e

# ==========================================
# CONFIGURATION - Feel free to adjust these
# ==========================================
REGION="us-central1"
TOPIC_NAME="docs-upload-topic"
DATASET_NAME="docs_metadata"
TABLE_NAME="processed_docs"
SERVICE_NAME="doc-processor-service"
SA_NAME="doc-processor-sa"
PUBSUB_SA_NAME="pubsub-invoker-sa"

# Ensure gcloud and bq CLIs are available
# If not in PATH, try to find in Windows LocalAppData since we are on Windows running Git Bash
if ! command -v gcloud &> /dev/null; then
  echo "gcloud CLI not found in PATH. Checking default Windows installation paths..."
  if [ -n "$LOCALAPPDATA" ]; then
    UNIX_LOCALAPPDATA=$(echo "$LOCALAPPDATA" | sed 's/\\/\//g' | sed 's/^\([A-Za-z]\):/\/\L\1/')
    LOCAL_GCLOUD_PATH="$UNIX_LOCALAPPDATA/Google/Cloud SDK/google-cloud-sdk/bin/gcloud"
    if [ -f "$LOCAL_GCLOUD_PATH" ]; then
      echo "Found gcloud at $LOCAL_GCLOUD_PATH"
      gcloud() { "$LOCAL_GCLOUD_PATH" "$@"; }
    elif [ -f "${LOCAL_GCLOUD_PATH}.cmd" ]; then
      echo "Found gcloud.cmd at ${LOCAL_GCLOUD_PATH}.cmd"
      gcloud() { "${LOCAL_GCLOUD_PATH}.cmd" "$@"; }
    fi
  fi
fi

if ! command -v gcloud &> /dev/null; then
  echo "Error: gcloud CLI is not installed or not in PATH."
  exit 1
fi

# Locate bq relative to gcloud if not in path
if ! command -v bq &> /dev/null; then
  # Try to find bq.cmd in the same directory as gcloud
  GCLOUD_BIN_DIR=$(dirname "$(which gcloud 2>/dev/null || echo "$LOCAL_GCLOUD_PATH")")
  if [ -f "$GCLOUD_BIN_DIR/bq.cmd" ]; then
    bq() { "$GCLOUD_BIN_DIR/bq.cmd" "$@"; }
  elif [ -f "$GCLOUD_BIN_DIR/bq" ]; then
    bq() { "$GCLOUD_BIN_DIR/bq" "$@"; }
  fi
fi

# Get project ID
PROJECT_ID=$(gcloud config get-value project 2>/dev/null)
if [ -z "$PROJECT_ID" ] || [ "$PROJECT_ID" = "(unset)" ]; then
  echo "Error: No Google Cloud project is currently selected."
  echo "Please set your project using: gcloud config set project YOUR_PROJECT_ID"
  exit 1
fi

BUCKET_NAME="${PROJECT_ID}-docs-ingest"
SA_EMAIL="${SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"
PUBSUB_SA_EMAIL="${PUBSUB_SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"

echo "=========================================================="
echo "Starting event-driven pipeline setup for project: $PROJECT_ID"
echo "Region:         $REGION"
echo "Bucket Name:    gs://$BUCKET_NAME"
echo "Pub/Sub Topic:  $TOPIC_NAME"
echo "BigQuery Table: $DATASET_NAME.$TABLE_NAME"
echo "Cloud Run:      $SERVICE_NAME"
echo "=========================================================="

# 1. Enable Required Services
echo "1. Enabling required Google Cloud APIs..."
gcloud services enable \
  storage.googleapis.com \
  pubsub.googleapis.com \
  run.googleapis.com \
  bigquery.googleapis.com \
  artifactregistry.googleapis.com \
  cloudbuild.googleapis.com

# Get project number for service account names
PROJECT_NUMBER=$(gcloud projects describe "$PROJECT_ID" --format="value(projectNumber)")

# 2. Create Storage Bucket
if gcloud storage buckets describe "gs://$BUCKET_NAME" &>/dev/null; then
  echo "2. Storage Bucket gs://$BUCKET_NAME already exists."
else
  echo "2. Creating Storage Bucket: gs://$BUCKET_NAME..."
  gcloud storage buckets create "gs://$BUCKET_NAME" --location="$REGION" --public-access-prevention
fi

# 3. Create BigQuery Dataset and Table
echo "3. Creating BigQuery Dataset & Table..."
python3 ./create_bigquery.py "$PROJECT_ID" "$DATASET_NAME" "$TABLE_NAME" ./app/schema.json "$REGION"
if [ $? -ne 0 ]; then
  echo "Error: Failed to create BigQuery resources"
  exit 1
fi

# 4. Create Pub/Sub Topic
if gcloud pubsub topics describe "$TOPIC_NAME" &>/dev/null; then
  echo "4. Pub/Sub Topic $TOPIC_NAME already exists."
else
  echo "4. Creating Pub/Sub Topic: $TOPIC_NAME..."
  gcloud pubsub topics create "$TOPIC_NAME"
fi

# 5. Create Service Accounts & Set Up IAM Permissions
echo "5. Setting up Service Accounts and IAM permissions..."

# A. Cloud Run Service Account
if gcloud iam service-accounts describe "$SA_EMAIL" &>/dev/null; then
  echo "   Cloud Run Service Account $SA_EMAIL already exists."
else
  gcloud iam service-accounts create "$SA_NAME" \
    --display-name="Service Account for Cloud Run Document Processor"
fi

# B. Pub/Sub Invoker Service Account
if gcloud iam service-accounts describe "$PUBSUB_SA_EMAIL" &>/dev/null; then
  echo "   Pub/Sub Invoker Service Account $PUBSUB_SA_EMAIL already exists."
else
  gcloud iam service-accounts create "$PUBSUB_SA_NAME" \
    --display-name="Service Account for Pub/Sub Cloud Run Invoker"
fi

# C. Grant permissions to Cloud Run Service Account
echo "   Granting storage.objectViewer and bigquery.dataEditor to $SA_EMAIL..."
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:$SA_EMAIL" \
  --role="roles/storage.objectViewer" > /dev/null

gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:$SA_EMAIL" \
  --role="roles/bigquery.dataEditor" > /dev/null

gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:$SA_EMAIL" \
  --role="roles/bigquery.user" > /dev/null

# D. Grant Service Account Token Creator to Pub/Sub System Service Account
echo "   Allowing Pub/Sub system agent to create tokens..."
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:service-$PROJECT_NUMBER@gcp-sa-pubsub.iam.gserviceaccount.com" \
  --role="roles/iam.serviceAccountTokenCreator" > /dev/null

# E. Grant run.invoker to the Pub/Sub invoker service account
echo "   Granting run.invoker to $PUBSUB_SA_EMAIL..."
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:$PUBSUB_SA_EMAIL" \
  --role="roles/run.invoker" > /dev/null

# F. Grant pubsub.publisher to GCS System Service Account
echo "   Granting pubsub.publisher to GCS service agent..."
GCS_SA_EMAIL="service-$PROJECT_NUMBER@gs-project-accounts.iam.gserviceaccount.com"
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:$GCS_SA_EMAIL" \
  --role="roles/pubsub.publisher" > /dev/null

# 6. Build and Deploy Cloud Run Service
echo "6. Building and deploying Cloud Run Service: $SERVICE_NAME..."
gcloud run deploy "$SERVICE_NAME" \
  --source ./app \
  --region "$REGION" \
  --no-allow-unauthenticated \
  --service-account "$SA_EMAIL" \
  --set-env-vars BQ_DATASET="$DATASET_NAME",BQ_TABLE="$TABLE_NAME"

# Retrieve Cloud Run Service URL
SERVICE_URL=$(gcloud run services describe "$SERVICE_NAME" --region "$REGION" --format="value(status.url)")
echo "   Cloud Run URL: $SERVICE_URL"

# 7. Create Cloud Storage Notification
echo "7. Creating GCS Pub/Sub Notification..."
# Delete existing notification if there's any config to avoid duplicates (ignoring errors if none exist)
# Currently gcloud storage buckets notifications create doesn't support overwrite, so we list and verify
EXISTING_NOTIF=$(gcloud storage buckets notifications list "gs://$BUCKET_NAME" --format="value(name)" 2>/dev/null || true)
if [ -n "$EXISTING_NOTIF" ]; then
  echo "   A GCS notification configuration already exists on gs://$BUCKET_NAME. Skipping creation."
else
  gcloud storage buckets notifications create "gs://$BUCKET_NAME" \
    --topic="$TOPIC_NAME" \
    --event-types="OBJECT_FINALIZE"
fi

# 8. Create Pub/Sub Push Subscription pointing to Cloud Run
SUBSCRIPTION_NAME="${TOPIC_NAME}-sub"
if gcloud pubsub subscriptions describe "$SUBSCRIPTION_NAME" &>/dev/null; then
  echo "8. Pub/Sub Subscription $SUBSCRIPTION_NAME already exists. Updating endpoint to $SERVICE_URL..."
  gcloud pubsub subscriptions update "$SUBSCRIPTION_NAME" \
    --push-endpoint="$SERVICE_URL"
else
  echo "8. Creating Pub/Sub Subscription: $SUBSCRIPTION_NAME..."
  gcloud pubsub subscriptions create "$SUBSCRIPTION_NAME" \
    --topic "$TOPIC_NAME" \
    --push-endpoint "$SERVICE_URL" \
    --push-auth-service-account "$PUBSUB_SA_EMAIL"
fi

echo "=========================================================="
echo "Deployment successful!"
echo "You can now upload files to gs://$BUCKET_NAME to process them."
echo "Check progress in the BigQuery table: $DATASET_NAME.$TABLE_NAME"
echo "=========================================================="

# SERVICE URL
# https://doc-processor-service-798696075142.us-central1.run.app

# export PROJECT_ID="ps-my-document-processor"
# export REGION="us-central1"
# export SA_EMAIL="doc-processor-sa@${PROJECT_ID}.iam.gserviceaccount.com"
# export PUBSUB_SA_EMAIL="pubsub-invoker-sa@${PROJECT_ID}.iam.gserviceaccount.com"
# export TOPIC_NAME="docs-upload-topic"
# export SERVICE_NAME="doc-processor-service"
# export DATASET_NAME="docs_metadata"
# export TABLE_NAME="processed_docs"