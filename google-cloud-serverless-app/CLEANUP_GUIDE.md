# GCP Resource Cleanup Guide - Complete Removal

**WARNING:** This guide will DELETE all resources. This cannot be undone. Backup any data first!

---

## Overview: What Will Be Deleted

```
┌─────────────────────────────────────────────────┐
│     Resources to be Removed (in order)          │
├─────────────────────────────────────────────────┤
│ 1. Cloud Run Service                            │
│ 2. Pub/Sub Subscription                         │
│ 3. Pub/Sub Topic                                │
│ 4. GCS Notification                             │
│ 5. Cloud Storage Bucket (ALL FILES DELETED)     │
│ 6. BigQuery Dataset & Table (DATA DELETED)      │
│ 7. Service Accounts                             │
│ 8. (Optional) Disable APIs                      │
└─────────────────────────────────────────────────┘
```

---

## Prerequisites

```bash
# Set project variables
export PROJECT_ID="ps-my-document-processor"
export REGION="us-central1"
export BUCKET_NAME="${PROJECT_ID}-docs-ingest"
export DATASET_NAME="docs_metadata"
export TABLE_NAME="processed_docs"
export SERVICE_NAME="doc-processor-service"
```

---

## Step 1: Delete Cloud Run Service

### What This Does
- Removes the Flask application container
- Stops processing documents
- Frees up compute resources

### Delete Command
```bash
gcloud run services delete $SERVICE_NAME \
  --region $REGION \
  --quiet
```

**Output:**
```
Deleting service [doc-processor-service] in region [us-central1]...done
```

### Verify Deletion
```bash
gcloud run services list --region $REGION

# Should NOT show doc-processor-service anymore
```

---

## Step 2: Delete Pub/Sub Subscription

### What This Does
- Removes the push subscription
- Stops Cloud Run invocations from Pub/Sub

### Delete Command
```bash
gcloud pubsub subscriptions delete docs-upload-topic-sub \
  --quiet
```

**Output:**
```
Deleted subscription [docs-upload-topic-sub].
```

### Verify Deletion
```bash
gcloud pubsub subscriptions list

# Should NOT show docs-upload-topic-sub
```

---

## Step 3: Delete Pub/Sub Topic

### What This Does
- Removes the message queue
- Stops event routing

### Delete Command
```bash
gcloud pubsub topics delete docs-upload-topic \
  --quiet
```

**Output:**
```
Deleted topic [docs-upload-topic].
```

### Verify Deletion
```bash
gcloud pubsub topics list

# Should NOT show docs-upload-topic
```

---

## Step 4: Delete GCS Notification

### What This Does
- Removes the connection between Cloud Storage and Pub/Sub
- Cloud Storage upload events no longer trigger processing

### Get Notification ID
```bash
NOTIF_ID=$(gcloud storage buckets notifications list \
  gs://$BUCKET_NAME \
  --format="value(name)")

echo "Notification ID: $NOTIF_ID"
```

### Delete Notification
```bash
if [ -n "$NOTIF_ID" ]; then
  gcloud storage buckets notifications delete $NOTIF_ID \
    --bucket-name=$BUCKET_NAME
  echo "Notification deleted"
else
  echo "No notifications found"
fi
```

### Verify Deletion
```bash
gcloud storage buckets notifications list gs://$BUCKET_NAME

# Should return empty or "No notifications found"
```

---

## Step 5: Delete Cloud Storage Bucket

### ⚠️ WARNING: ALL FILES WILL BE DELETED

```bash
# This will DELETE all files in the bucket permanently
# There is no recovery!
```

### Delete Command
```bash
# First, empty the bucket
gcloud storage rm gs://$BUCKET_NAME --recursive --quiet

# Then, delete the bucket itself
gcloud storage buckets delete gs://$BUCKET_NAME \
  --quiet
```

**Output:**
```
Deleting objects in gs://ps-my-document-processor-docs-ingest/...
Deleting bucket gs://ps-my-document-processor-docs-ingest/...done
```

### Verify Deletion
```bash
gcloud storage buckets list

# Should NOT show ps-my-document-processor-docs-ingest
```

---

## Step 6: Delete BigQuery Dataset & Table

### ⚠️ WARNING: ALL DATA WILL BE DELETED

```bash
# This will DELETE all metadata permanently
# There is no recovery!
```

### Option A: Delete Only Table (Keep Dataset)
```bash
bq rm --table \
  --force \
  $PROJECT_ID:$DATASET_NAME.$TABLE_NAME

echo "Table $TABLE_NAME deleted"
```

### Option B: Delete Entire Dataset (Recommended)
```bash
bq rm --dataset \
  --recursive \
  --force \
  --project_id=$PROJECT_ID \
  $DATASET_NAME

echo "Dataset $DATASET_NAME and all tables deleted"
```

### Verify Deletion
```bash
# Check if dataset exists
bq ls -d --project_id=$PROJECT_ID | grep $DATASET_NAME

# Should NOT show docs_metadata
```

---

## Step 7: Delete Service Accounts

### What This Does
- Removes bot accounts that services used
- Frees up identities for future use

### List Service Accounts to Delete
```bash
gcloud iam service-accounts list --project=$PROJECT_ID

# Should show:
# doc-processor-sa@...
# pubsub-invoker-sa@...
```

### Delete Service Accounts
```bash
# Delete doc-processor-sa
gcloud iam service-accounts delete \
  doc-processor-sa@${PROJECT_ID}.iam.gserviceaccount.com \
  --quiet

# Delete pubsub-invoker-sa
gcloud iam service-accounts delete \
  pubsub-invoker-sa@${PROJECT_ID}.iam.gserviceaccount.com \
  --quiet

echo "Service accounts deleted"
```

### Verify Deletion
```bash
gcloud iam service-accounts list --project=$PROJECT_ID

# Should show empty list or no custom service accounts
```

---

## Step 8 (Optional): Disable APIs

### What This Does
- Stops charges for API calls
- Reduces complexity if you're not using GCP for other projects

### Check Enabled APIs
```bash
gcloud services list --enabled --project=$PROJECT_ID | \
  grep -E "storage|pubsub|run|bigquery|cloudbuild|artifactregistry"
```

### Disable Individual APIs (Optional)

```bash
# Only disable if you're NOT using these for other projects!

# Storage API
gcloud services disable storage.googleapis.com --project=$PROJECT_ID

# Pub/Sub API
gcloud services disable pubsub.googleapis.com --project=$PROJECT_ID

# Cloud Run API
gcloud services disable run.googleapis.com --project=$PROJECT_ID

# BigQuery API
gcloud services disable bigquery.googleapis.com --project=$PROJECT_ID

# Cloud Build API
gcloud services disable cloudbuild.googleapis.com --project=$PROJECT_ID

# Artifact Registry API
gcloud services disable artifactregistry.googleapis.com --project=$PROJECT_ID
```

### Verify Disabled APIs
```bash
gcloud services list --enabled --project=$PROJECT_ID

# Should not show the above APIs
```

---

## Complete Cleanup Script

Run all steps at once (use with caution!):

```bash
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
```

Save this as `cleanup.sh`:
```bash
chmod +x cleanup.sh
./cleanup.sh
```

---

## Cost Impact: Before vs After

### Before Cleanup (Monthly Costs)
```
Cloud Storage:        ~$1-5    (storage + API calls)
Pub/Sub:              ~$0.50   (message publishing)
Cloud Run:            ~$0.50   (function invocations)
BigQuery:             ~$1-10   (storage + queries)
────────────────────
Total (approx):       ~$3-20/month
```

### After Cleanup
```
All services:         $0
────────────────────
Total:                $0
```

**Additional Savings:**
- No Cloud Build costs for deployments
- No Artifact Registry storage
- No data transfer costs

---

## Verification Checklist

After cleanup, verify everything is removed:

### Cloud Run
```bash
gcloud run services list --region us-central1
# Should be empty or not show doc-processor-service
```

### Pub/Sub
```bash
gcloud pubsub topics list
gcloud pubsub subscriptions list
# Both should be empty or not show our resources
```

### Cloud Storage
```bash
gcloud storage buckets list
# Should not show ps-my-document-processor-docs-ingest
```

### BigQuery
```bash
bq ls -d
# Should not show docs_metadata
```

### Service Accounts
```bash
gcloud iam service-accounts list
# Should not show doc-processor-sa or pubsub-invoker-sa
```

---

## If You Want To Keep Some Resources

### Keep Only BigQuery (for historical data)

```bash
# Delete everything except BigQuery
# Run steps 1-5 above
# Skip step 6 (BigQuery deletion)
```

### Keep Only Cloud Storage (archive data)

```bash
# Delete everything except Cloud Storage
# Run steps 1-4, 6-7 above
# Skip step 5 (bucket deletion)

# But disable notifications and subscriptions first
```

---

## Recovery Options

**If you deleted something by mistake:**

### Deleted Cloud Storage Files
- ⚠️ **No recovery possible** (unless you have backups)
- Google Cloud has no undo for deleted objects
- Lesson: Always backup important data first

### Deleted BigQuery Data
- ⚠️ **No recovery possible** (unless you have backups)
- Data is permanently deleted
- Use BigQuery snapshots/backups in future

### Deleted Cloud Run Service
- ✅ **Easy to recover** - redeploy using setup.sh
- Code is still in git
- No data loss (data stored in BigQuery)

---

## Cleanup Tips

### Before Cleanup
```bash
# Export BigQuery data for backup
bq extract \
  ps-my-document-processor:docs_metadata.processed_docs \
  gs://${BUCKET_NAME}/backup/data.csv

# Or export to local file
bq query --format=csv \
  "SELECT * FROM \`ps-my-document-processor.docs_metadata.processed_docs\`" \
  > processed_docs_backup.csv
```

### Staged Cleanup (Safer)

Run each step separately and verify:

```bash
# Step 1: Delete Cloud Run
gcloud run services delete doc-processor-service --region us-central1
# Verify: gcloud run services list

# Step 2: Delete subscriptions
gcloud pubsub subscriptions delete docs-upload-topic-sub --quiet
# Verify: gcloud pubsub subscriptions list

# ... continue step by step
```

---

## Frequently Asked Questions

**Q: Can I recover deleted resources?**
- Cloud Run: Yes (redeploy from code)
- Pub/Sub: Yes (recreate topics/subscriptions)
- Cloud Storage: NO (gone forever)
- BigQuery: NO (gone forever)

**Q: Will I still be charged after deletion?**
- No, once deleted, no charges
- Verify: Check Cloud Billing dashboard

**Q: How long until charges stop?**
- Immediately (charges are based on active resources)
- Current billing cycle still charges for time used

**Q: Can I keep the project but remove resources?**
- Yes, you can delete resources but keep the project
- Project itself is free

**Q: Should I delete the entire project?**
```bash
# Only if you want to start completely fresh
gcloud projects delete $PROJECT_ID

# WARNING: This is permanent and affects all resources in the project!
```

---

## Final Verification

After completing cleanup:

```bash
# Check project summary
gcloud projects describe ps-my-document-processor

# List all remaining resources
echo "=== Cloud Run ==="
gcloud run services list --project=$PROJECT_ID

echo "=== Pub/Sub Topics ==="
gcloud pubsub topics list --project=$PROJECT_ID

echo "=== Pub/Sub Subscriptions ==="
gcloud pubsub subscriptions list --project=$PROJECT_ID

echo "=== Storage Buckets ==="
gcloud storage buckets list --project=$PROJECT_ID

echo "=== BigQuery Datasets ==="
bq ls -d --project_id=$PROJECT_ID

echo "=== Service Accounts ==="
gcloud iam service-accounts list --project=$PROJECT_ID
```

All should be empty or show only resources you intentionally kept.

---

**Document Version:** 1.0  
**Last Updated:** 2026-06-17  
**For:** Safe Resource Cleanup
