# Google Cloud Services Checklist

Complete verification guide for all GCP services used in the pipeline.

---

## 1. Cloud Storage (File Ingestion)

**Service Name:** Google Cloud Storage  
**Project:** `ps-my-document-processor`  
**Resource:** Bucket `gs://ps-my-document-processor-docs-ingest`

### What to Check:

- [ ] **Bucket exists**
  ```bash
  gsutil ls gs://ps-my-document-processor-docs-ingest/
  ```

- [ ] **Bucket has public access prevention enabled**
  ```bash
  gsutil uniformbucketlevelaccess get gs://ps-my-document-processor-docs-ingest/
  ```

- [ ] **Bucket location is correct** (us-central1)
  ```bash
  gcloud storage buckets describe gs://ps-my-document-processor-docs-ingest
  ```

- [ ] **Pub/Sub notification is configured**
  ```bash
  gcloud storage buckets notifications list gs://ps-my-document-processor-docs-ingest/
  ```

- [ ] **Test file can be uploaded**
  ```bash
  echo "test" > test.txt
  gsutil cp test.txt gs://ps-my-document-processor-docs-ingest/
  ```

- [ ] **Storage API is enabled**
  ```bash
  gcloud services list --enabled | grep storage
  ```

### Console Link:
```
https://console.cloud.google.com/storage/browser/ps-my-document-processor-docs-ingest
```

---

## 2. Pub/Sub (Event Messaging)

**Service Name:** Google Cloud Pub/Sub  
**Project:** `ps-my-document-processor`

### Resources to Check:

#### Topic: `docs-upload-topic`
- [ ] **Topic exists**
  ```bash
  gcloud pubsub topics list
  ```

- [ ] **Topic has messages flowing** (if files uploaded)
  ```bash
  gcloud pubsub topics describe docs-upload-topic
  ```

#### Subscription: `docs-upload-topic-sub`
- [ ] **Subscription exists**
  ```bash
  gcloud pubsub subscriptions list
  ```

- [ ] **Push endpoint is configured correctly**
  ```bash
  gcloud pubsub subscriptions describe docs-upload-topic-sub
  ```

- [ ] **Push endpoint URL matches Cloud Run service**
  ```bash
  gcloud run services describe doc-processor-service --region us-central1 --format='value(status.url)'
  ```

- [ ] **Service account has run.invoker permission**
  ```bash
  gcloud projects get-iam-policy ps-my-document-processor \
    --flatten="bindings[].members" \
    --filter="bindings.members:pubsub-invoker-sa*"
  ```

- [ ] **Test message publishing** (optional)
  ```bash
  gcloud pubsub topics publish docs-upload-topic --message "test"
  ```

### Console Link:
```
https://console.cloud.google.com/cloudpubsub/topic/list
```

---

## 3. Cloud Run (Compute/Processing)

**Service Name:** Google Cloud Run  
**Project:** `ps-my-document-processor`  
**Service Name:** `doc-processor-service`  
**Region:** `us-central1`

### What to Check:

- [ ] **Service is deployed**
  ```bash
  gcloud run services list --region us-central1
  ```

- [ ] **Service is running** (not errored)
  ```bash
  gcloud run services describe doc-processor-service --region us-central1
  ```

- [ ] **Service has correct URL**
  ```bash
  gcloud run services describe doc-processor-service --region us-central1 \
    --format='value(status.url)'
  ```

- [ ] **Service account is assigned**
  ```bash
  gcloud run services describe doc-processor-service --region us-central1 \
    --format='value(spec.template.spec.serviceAccountName)'
  ```

- [ ] **Environment variables are set**
  ```bash
  gcloud run services describe doc-processor-service --region us-central1 \
    --format='value(spec.template.spec.containers[0].env[*])'
  ```
  Should show: `BQ_DATASET=docs_metadata` and `BQ_TABLE=processed_docs`

- [ ] **Authentication is required** (no public access)
  ```bash
  gcloud run services describe doc-processor-service --region us-central1 \
    --format='value(spec.traffic[0].percent)'
  ```

- [ ] **Check recent logs for errors**
  ```bash
  gcloud run logs read doc-processor-service --region us-central1 --limit 50
  ```

- [ ] **Health endpoint responds**
  ```bash
  CLOUD_RUN_URL=$(gcloud run services describe doc-processor-service --region us-central1 --format='value(status.url)')
  curl $CLOUD_RUN_URL/health
  ```

- [ ] **Cloud Run API is enabled**
  ```bash
  gcloud services list --enabled | grep run
  ```

### Console Link:
```
https://console.cloud.google.com/run/detail/us-central1/doc-processor-service
```

---

## 4. BigQuery (Data Warehouse)

**Service Name:** Google Cloud BigQuery  
**Project:** `ps-my-document-processor`

### Resources to Check:

#### Dataset: `docs_metadata`
- [ ] **Dataset exists**
  ```bash
  gcloud bq datasets list --project-id ps-my-document-processor
  ```

- [ ] **Dataset location is correct** (us-central1)
  ```bash
  python3 -c "
  from google.cloud import bigquery
  client = bigquery.Client(project='ps-my-document-processor')
  ds = client.get_dataset('docs_metadata')
  print(f'Location: {ds.location}')
  "
  ```

#### Table: `processed_docs`
- [ ] **Table exists**
  ```bash
  gcloud bq tables list --dataset-id docs_metadata \
    --project-id ps-my-document-processor
  ```

- [ ] **Table schema is correct**
  ```bash
  bq show --schema --format=prettyjson \
    ps-my-document-processor:docs_metadata.processed_docs
  ```

- [ ] **Table has correct columns**
  - filename (STRING, REQUIRED)
  - processed_at (TIMESTAMP, REQUIRED)
  - tags (STRING, REPEATED)
  - word_count (INTEGER, REQUIRED)
  - bucket (STRING, REQUIRED)
  - file_size (INTEGER, REQUIRED)

- [ ] **Query the table** (check if data exists)
  ```bash
  bq query --use_legacy_sql=false \
    "SELECT COUNT(*) as count FROM \`ps-my-document-processor.docs_metadata.processed_docs\`"
  ```

- [ ] **View sample data**
  ```bash
  bq query --use_legacy_sql=false \
    "SELECT * FROM \`ps-my-document-processor.docs_metadata.processed_docs\` LIMIT 5"
  ```

- [ ] **BigQuery API is enabled**
  ```bash
  gcloud services list --enabled | grep bigquery
  ```

### Console Link:
```
https://console.cloud.google.com/bigquery?project=ps-my-document-processor
```

---

## 5. Cloud IAM (Security & Access)

**Service Name:** Google Cloud Identity & Access Management

### Service Accounts to Check:

#### Service Account 1: `doc-processor-sa`
- [ ] **Service account exists**
  ```bash
  gcloud iam service-accounts list --project ps-my-document-processor
  ```

- [ ] **Email:** `doc-processor-sa@ps-my-document-processor.iam.gserviceaccount.com`

- [ ] **Has storage.objectViewer role**
  ```bash
  gcloud projects get-iam-policy ps-my-document-processor \
    --flatten="bindings[].members" \
    --filter="bindings.members:doc-processor-sa* AND bindings.role:*storage.objectViewer*"
  ```

- [ ] **Has bigquery.dataEditor role**
  ```bash
  gcloud projects get-iam-policy ps-my-document-processor \
    --flatten="bindings[].members" \
    --filter="bindings.members:doc-processor-sa* AND bindings.role:*bigquery.dataEditor*"
  ```

- [ ] **Has bigquery.user role**
  ```bash
  gcloud projects get-iam-policy ps-my-document-processor \
    --flatten="bindings[].members" \
    --filter="bindings.members:doc-processor-sa* AND bindings.role:*bigquery.user*"
  ```

#### Service Account 2: `pubsub-invoker-sa`
- [ ] **Service account exists**
  ```bash
  gcloud iam service-accounts list --project ps-my-document-processor
  ```

- [ ] **Email:** `pubsub-invoker-sa@ps-my-document-processor.iam.gserviceaccount.com`

- [ ] **Has run.invoker role**
  ```bash
  gcloud projects get-iam-policy ps-my-document-processor \
    --flatten="bindings[].members" \
    --filter="bindings.members:pubsub-invoker-sa* AND bindings.role:*run.invoker*"
  ```

### Console Link:
```
https://console.cloud.google.com/iam-admin/serviceaccounts?project=ps-my-document-processor
```

---

## 6. Cloud Build (Container Building)

**Service Name:** Google Cloud Build  
**Project:** `ps-my-document-processor`

### What to Check:

- [ ] **Cloud Build API is enabled**
  ```bash
  gcloud services list --enabled | grep cloudbuild
  ```

- [ ] **Recent builds are successful**
  ```bash
  gcloud builds list --project ps-my-document-processor --limit 5
  ```

- [ ] **Dockerfile exists in app/**
  ```bash
  ls -la app/Dockerfile
  ```

### Console Link:
```
https://console.cloud.google.com/cloud-build/builds?project=ps-my-document-processor
```

---

## 7. Artifact Registry (Container Registry)

**Service Name:** Google Artifact Registry  
**Project:** `ps-my-document-processor`  
**Location:** `us-central1`

### What to Check:

- [ ] **Artifact Registry API is enabled**
  ```bash
  gcloud services list --enabled | grep artifactregistry
  ```

- [ ] **Docker images are stored**
  ```bash
  gcloud artifacts repositories list --location us-central1 --project ps-my-document-processor
  ```

- [ ] **Cloud Run pulls from registry** (automatic)

### Console Link:
```
https://console.cloud.google.com/artifacts/docker?project=ps-my-document-processor
```

---

## 8. Cloud Logging (Monitoring & Debugging)

**Service Name:** Google Cloud Logging  
**Project:** `ps-my-document-processor`

### What to Check:

- [ ] **Cloud Run logs are available**
  ```bash
  gcloud run logs read doc-processor-service --region us-central1 --limit 20
  ```

- [ ] **No ERROR level logs**
  ```bash
  gcloud logging read "resource.type=cloud_run_revision AND severity=ERROR" \
    --project ps-my-document-processor --limit 10
  ```

- [ ] **Pub/Sub delivery logs** (if configured)
  ```bash
  gcloud logging read "resource.type=pubsub_subscription" \
    --project ps-my-document-processor --limit 10
  ```

### Console Link:
```
https://console.cloud.google.com/logs/query?project=ps-my-document-processor
```

---

## 9. APIs & Services (All APIs)

**Service Name:** Google Cloud APIs & Services

### Required APIs to Enable:

- [ ] **Cloud Storage API**
  ```bash
  gcloud services list --enabled | grep storage.googleapis.com
  ```

- [ ] **Pub/Sub API**
  ```bash
  gcloud services list --enabled | grep pubsub.googleapis.com
  ```

- [ ] **Cloud Run API**
  ```bash
  gcloud services list --enabled | grep run.googleapis.com
  ```

- [ ] **BigQuery API**
  ```bash
  gcloud services list --enabled | grep bigquery.googleapis.com
  ```

- [ ] **Cloud Build API**
  ```bash
  gcloud services list --enabled | grep cloudbuild.googleapis.com
  ```

- [ ] **Artifact Registry API**
  ```bash
  gcloud services list --enabled | grep artifactregistry.googleapis.com
  ```

### Console Link:
```
https://console.cloud.google.com/apis/dashboard?project=ps-my-document-processor
```

---

## Full Verification Script

Run this to check all services at once:

```bash
#!/bin/bash

PROJECT_ID="ps-my-document-processor"

echo "========== GCP SERVICES VERIFICATION =========="
echo ""

echo "1. Cloud Storage"
gsutil ls gs://$PROJECT_ID-docs-ingest/ && echo "✓ Bucket OK" || echo "✗ Bucket FAILED"

echo ""
echo "2. Pub/Sub Topic"
gcloud pubsub topics describe docs-upload-topic --project $PROJECT_ID > /dev/null && echo "✓ Topic OK" || echo "✗ Topic FAILED"

echo ""
echo "3. Pub/Sub Subscription"
gcloud pubsub subscriptions describe docs-upload-topic-sub --project $PROJECT_ID > /dev/null && echo "✓ Subscription OK" || echo "✗ Subscription FAILED"

echo ""
echo "4. Cloud Run Service"
gcloud run services describe doc-processor-service --region us-central1 --project $PROJECT_ID > /dev/null && echo "✓ Cloud Run OK" || echo "✗ Cloud Run FAILED"

echo ""
echo "5. BigQuery Dataset"
bq ls -d --project_id=$PROJECT_ID | grep docs_metadata > /dev/null && echo "✓ Dataset OK" || echo "✗ Dataset FAILED"

echo ""
echo "6. BigQuery Table"
bq ls -t -d docs_metadata --project_id=$PROJECT_ID | grep processed_docs > /dev/null && echo "✓ Table OK" || echo "✗ Table FAILED"

echo ""
echo "7. Service Accounts"
gcloud iam service-accounts list --project $PROJECT_ID | grep doc-processor-sa > /dev/null && echo "✓ Service Accounts OK" || echo "✗ Service Accounts FAILED"

echo ""
echo "8. APIs Enabled"
gcloud services list --enabled --project $PROJECT_ID | grep -E "storage|pubsub|run|bigquery|cloudbuild" && echo "✓ APIs OK" || echo "✗ APIs FAILED"

echo ""
echo "============== VERIFICATION COMPLETE =============="
```

---

## Quick Reference Table

| # | Service | Status | Command |
|---|---------|--------|---------|
| 1 | Cloud Storage | Check | `gsutil ls gs://ps-my-document-processor-docs-ingest/` |
| 2 | Pub/Sub Topic | Check | `gcloud pubsub topics describe docs-upload-topic` |
| 3 | Pub/Sub Sub | Check | `gcloud pubsub subscriptions describe docs-upload-topic-sub` |
| 4 | Cloud Run | Check | `gcloud run services describe doc-processor-service --region us-central1` |
| 5 | BigQuery DS | Check | `bq ls -d` |
| 6 | BigQuery Tbl | Check | `bq ls -t -d docs_metadata` |
| 7 | IAM SA | Check | `gcloud iam service-accounts list` |
| 8 | Logging | Check | `gcloud run logs read doc-processor-service --region us-central1` |

---

## Console Dashboard

View all services in one place:
```
https://console.cloud.google.com/home/dashboard?project=ps-my-document-processor
```

---

## Troubleshooting Commands

**If Cloud Run shows errors:**
```bash
gcloud run logs read doc-processor-service --region us-central1 --limit 100
```

**If Pub/Sub not delivering:**
```bash
gcloud pubsub subscriptions describe docs-upload-topic-sub
```

**If BigQuery has no data:**
```bash
bq query "SELECT COUNT(*) FROM \`ps-my-document-processor.docs_metadata.processed_docs\`"
```

**If Cloud Storage notification missing:**
```bash
gcloud storage buckets notifications list gs://ps-my-document-processor-docs-ingest/
```

---

## Cost Check

Check usage and estimated costs:
```
https://console.cloud.google.com/billing/linkedaccount?project=ps-my-document-processor
```

