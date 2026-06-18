# GCP Service Setup Guide - Complete Documentation
**For Junior Developers: Understanding Service Configuration**

---

## Table of Contents
1. [Service Accounts - Fundamentals](#service-accounts---fundamentals)
2. [1. Cloud Storage Setup](#1-cloud-storage-setup)
3. [2. Pub/Sub Topic & Subscription](#2-pubsub-topic--subscription)
4. [3. Cloud Run Service](#3-cloud-run-service)
5. [4. IAM Permissions](#4-iam-permissions)
6. [5. GCS Notification](#5-gcs-notification)
7. [6. BigQuery Setup](#6-bigquery-setup)
8. [Issues We Faced & Solutions](#issues-we-faced--solutions)
9. [Setup Verification Checklist](#setup-verification-checklist)

---

## Service Accounts - Fundamentals

### What is a Service Account?

A **service account** is a special Google Cloud identity used by applications/services instead of real users. Think of it as a "robot user" that your code uses to access GCP resources.

**Key Differences from User Accounts:**

| Aspect | User Account | Service Account |
|--------|-------------|-----------------|
| **Created for** | Human users | Applications/Services |
| **Authentication** | Username + Password | Key files or IAM roles |
| **Typical use** | Interactive access (console) | Automated tasks (APIs) |
| **Email format** | user@company.com | name@project.iam.gserviceaccount.com |
| **Lifespan** | Manual | As long as needed |

### Why Do We Need Service Accounts in This Pipeline?

In our document processing pipeline, we have multiple components that need to access GCP resources:

```
┌──────────────┐         ┌──────────────┐         ┌─────────────┐
│  Cloud Run   │ needs → │ Cloud Store  │ needs → │  BigQuery   │
│  (processor) │         │  (documents) │         │  (metadata) │
└──────────────┘         └──────────────┘         └─────────────┘
```

**Cloud Run can't use a human's credentials** because:
- Human credentials are interactive (require login)
- Cloud Run is a headless service (no UI/console)
- Human credentials shouldn't be embedded in application code (security risk!)

**Solution:** Create a service account for Cloud Run with specific permissions:
- ✅ Can read files from Cloud Storage
- ✅ Can write data to BigQuery
- ❌ Cannot access other projects or delete buckets
- ❌ Cannot manage IAM (least privilege principle)

### Service Accounts in Our Pipeline

We created **TWO service accounts** for different purposes:

#### 1. **doc-processor-sa** (Cloud Run Service Account)
```
Email: doc-processor-sa@ps-my-document-processor.iam.gserviceaccount.com

Permissions (Roles):
- roles/storage.objectViewer      → Read documents from GCS
- roles/bigquery.dataEditor       → Insert/update rows in BigQuery
- roles/bigquery.user             → Use BigQuery service
```

**Usage:** Cloud Run service uses this to authenticate API calls

#### 2. **pubsub-invoker-sa** (Pub/Sub Service Account)
```
Email: pubsub-invoker-sa@ps-my-document-processor.iam.gserviceaccount.com

Permissions (Roles):
- roles/run.invoker               → Invoke Cloud Run service
```

**Usage:** Pub/Sub uses this to call Cloud Run with authentication

### How Service Accounts Work (Technical Flow)

```
1. Service Account Created
   ↓
2. Roles Assigned (IAM Bindings)
   ↓
3. Application/Service Authenticated As Service Account
   ↓
4. Make API Calls
   ↓
5. GCP Checks: "Is this service account allowed to do this?"
   ↓
6. If YES → Operation succeeds
   If NO → Operation fails with 403 Forbidden
```

---

## 1. Cloud Storage Setup

### Purpose
Cloud Storage is the **ingestion point** where users upload documents. It triggers the entire pipeline.

### What to Create

```bash
# Create a bucket with public access prevention
gcloud storage buckets create gs://${PROJECT_ID}-docs-ingest \
  --location=us-central1 \
  --public-access-prevention
```

### Key Configuration

| Setting | Value | Why? |
|---------|-------|------|
| **Location** | us-central1 | Same region as other services (reduces latency) |
| **Public Access Prevention** | Enabled | Only authenticated users can access |
| **Uniform Bucket-Level Access** | Enabled | Consistent permissions (IAM-based, not object-level) |
| **Notification** | Enabled (next step) | Triggers Pub/Sub when files uploaded |

### Verification Commands

```bash
# List bucket
gcloud storage buckets list

# Check bucket details
gcloud storage buckets describe gs://${PROJECT_ID}-docs-ingest

# Verify uniform bucket-level access
gcloud storage buckets describe gs://${PROJECT_ID}-docs-ingest | grep uniformBucketLevelAccess

# Test upload (requires storage.objectCreator role)
echo "test" > test.txt
gcloud storage cp test.txt gs://${PROJECT_ID}-docs-ingest/
```

---

## 2. Pub/Sub Topic & Subscription

### Architecture Understanding

```
┌─────────────────────────────────────────────────────────┐
│                    Pub/Sub Service                       │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  Topic: docs-upload-topic                               │
│  └─ Where messages are published                         │
│     (receives events from GCS)                           │
│                                                          │
│  Subscription: docs-upload-topic-sub                     │
│  └─ How messages are consumed                            │
│     └─ Push Mode: Sends to Cloud Run                     │
│     └─ Service Account: pubsub-invoker-sa (auth)        │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### What is a Topic vs Subscription?

**Topic** = Message Queue (Producer publishes here)
```
GCS Event → Topic → Message stored
```

**Subscription** = Delivery Method (Consumer receives from here)
```
Topic → Subscription → Delivers to Cloud Run (HTTP POST)
```

### Setup Steps

#### Step 1: Create Topic
```bash
gcloud pubsub topics create docs-upload-topic
```

#### Step 2: Create Subscription
```bash
gcloud pubsub subscriptions create docs-upload-topic-sub \
  --topic docs-upload-topic \
  --push-endpoint https://doc-processor-service-xxx.run.app \
  --push-auth-service-account pubsub-invoker-sa@${PROJECT_ID}.iam.gserviceaccount.com
```

**Parameters explained:**
- `--topic`: Which topic to subscribe to
- `--push-endpoint`: Where to send messages (Cloud Run URL)
- `--push-auth-service-account`: WHO sends the request (uses this service account's identity)

### Why Push Mode?

There are 2 delivery modes in Pub/Sub:

| Mode | How It Works | Best For |
|------|-------------|----------|
| **Pull** | Consumer asks Pub/Sub for messages | Background jobs, workers |
| **Push** | Pub/Sub sends HTTP POST to consumer | REST APIs, webhooks |

We use **Push mode** because Cloud Run is a REST API that listens on `/` endpoint.

### Verification Commands

```bash
# List topics
gcloud pubsub topics list

# Check topic details
gcloud pubsub topics describe docs-upload-topic

# List subscriptions
gcloud pubsub subscriptions list

# Check subscription configuration
gcloud pubsub subscriptions describe docs-upload-topic-sub

# Test publish (optional)
gcloud pubsub topics publish docs-upload-topic --message "test"
```

---

## 3. Cloud Run Service

### Purpose
Cloud Run hosts the **Flask Python application** that processes documents.

### Key Characteristics

```
┌─────────────────────────────────────────┐
│         Cloud Run Service               │
├─────────────────────────────────────────┤
│ - Containerized Flask App (Python)      │
│ - Auto-scales (0 to 100+ instances)     │
│ - Serverless (no servers to manage)     │
│ - Authenticated (no public access)      │
│ - Region: us-central1                   │
│ - Service Account: doc-processor-sa     │
└─────────────────────────────────────────┘
```

### Setup Command

```bash
gcloud run deploy doc-processor-service \
  --source ./app \
  --region us-central1 \
  --no-allow-unauthenticated \
  --service-account doc-processor-sa@${PROJECT_ID}.iam.gserviceaccount.com \
  --set-env-vars BQ_DATASET=docs_metadata,BQ_TABLE=processed_docs
```

**Parameters explained:**

| Parameter | Value | Why? |
|-----------|-------|------|
| `--source ./app` | Application code location | Points to Dockerfile and requirements.txt |
| `--region us-central1` | GCP region | Same region as other services |
| `--no-allow-unauthenticated` | Disable public access | Only Pub/Sub (with service account) can call it |
| `--service-account` | doc-processor-sa | Cloud Run runs with this identity |
| `--set-env-vars` | BQ_DATASET, BQ_TABLE | Configuration passed to Python app |

### What Cloud Run Does During Deployment

```
1. Reads Dockerfile from ./app/Dockerfile
   ↓
2. Builds Docker container (uses Cloud Build)
   ↓
3. Pushes image to Artifact Registry
   ↓
4. Starts container instance
   ↓
5. Maps service account to container
   ↓
6. Exposes HTTPS endpoint: https://doc-processor-service-xxx.run.app
   ↓
7. Ready to receive POST requests from Pub/Sub
```

### Verification Commands

```bash
# List Cloud Run services
gcloud run services list --region us-central1

# Get service details
gcloud run services describe doc-processor-service --region us-central1

# Get service URL
gcloud run services describe doc-processor-service --region us-central1 \
  --format='value(status.url)'

# Check if service is authenticated
gcloud run services describe doc-processor-service --region us-central1 \
  --format='value(spec.template.metadata.annotations)'

# View recent logs
gcloud run logs read doc-processor-service --region us-central1 --limit 50

# Test health endpoint
CLOUD_RUN_URL=$(gcloud run services describe doc-processor-service \
  --region us-central1 --format='value(status.url)')
curl -H "Authorization: Bearer $(gcloud auth print-access-token)" $CLOUD_RUN_URL/health
```

---

## 4. IAM Permissions

### Overview: Principle of Least Privilege

**Principle:** Each service account should have **ONLY** the permissions it needs, nothing more.

```
❌ Bad:  doc-processor-sa has Editor role (can delete everything!)
✅ Good: doc-processor-sa has only storage.objectViewer + bigquery.dataEditor
```

### IAM Bindings Required

#### A. doc-processor-sa Permissions

```bash
# Permission 1: Read objects from Cloud Storage
gcloud projects add-iam-policy-binding ps-my-document-processor \
  --member="serviceAccount:doc-processor-sa@ps-my-document-processor.iam.gserviceaccount.com" \
  --role="roles/storage.objectViewer"

# Permission 2: Edit BigQuery dataset (insert/update rows)
gcloud projects add-iam-policy-binding ps-my-document-processor \
  --member="serviceAccount:doc-processor-sa@ps-my-document-processor.iam.gserviceaccount.com" \
  --role="roles/bigquery.dataEditor"

# Permission 3: Use BigQuery service
gcloud projects add-iam-policy-binding ps-my-document-processor \
  --member="serviceAccount:doc-processor-sa@ps-my-document-processor.iam.gserviceaccount.com" \
  --role="roles/bigquery.user"
```

**Why these roles?**

| Role | Allows | Used For |
|------|--------|----------|
| `storage.objectViewer` | Read files from GCS | Download documents |
| `bigquery.dataEditor` | Insert/update rows | Stream metadata to BigQuery |
| `bigquery.user` | Access BigQuery | Query dataset and tables |

#### B. pubsub-invoker-sa Permissions

```bash
gcloud projects add-iam-policy-binding ps-my-document-processor \
  --member="serviceAccount:pubsub-invoker-sa@ps-my-document-processor.iam.gserviceaccount.com" \
  --role="roles/run.invoker"
```

**Why?** Allows Pub/Sub to call Cloud Run with this service account's credentials.

#### C. GCS System Service Account (Auto)

```bash
# Allows GCS to publish to Pub/Sub
gcloud projects add-iam-policy-binding ps-my-document-processor \
  --member="serviceAccount:service-${PROJECT_NUMBER}@gs-project-accounts.iam.gserviceaccount.com" \
  --role="roles/pubsub.publisher"
```

**Why?** GCS notifications need to publish messages to Pub/Sub.

### Verification Commands

```bash
# View all IAM bindings
gcloud projects get-iam-policy ps-my-document-processor

# Check specific service account permissions
gcloud projects get-iam-policy ps-my-document-processor \
  --flatten="bindings[].members" \
  --filter="bindings.members:doc-processor-sa*"

# Check Pub/Sub invoker permissions
gcloud projects get-iam-policy ps-my-document-processor \
  --flatten="bindings[].members" \
  --filter="bindings.members:pubsub-invoker-sa*"
```

---

## 5. GCS Notification

### Purpose
Converts GCS events into Pub/Sub messages. When a file is uploaded → Pub/Sub notification sent.

### Architecture

```
┌──────────────────┐         ┌──────────────────┐         ┌─────────────┐
│  Cloud Storage   │         │    Pub/Sub       │         │  Cloud Run  │
│  (gs://bucket/)  │         │    (topic)       │         │  (processor)│
└────────┬─────────┘         └────────┬─────────┘         └─────────────┘
         │                            │                           ▲
         │  File Uploaded             │                           │
         ├──────────────────────────→ │ Notification Created      │
         │  (OBJECT_FINALIZE event)   │                           │
         │                            │  Message Published        │
         │                            ├──────────────────────────→│
         │                            │  (via subscription)       │
         │                            │                           │
         │                            │  HTTP POST /              │
         │                            │  (with service account)   │
         │                            │                           │
```

### Setup Command

```bash
gcloud storage buckets notifications create gs://${PROJECT_ID}-docs-ingest \
  --topic=docs-upload-topic \
  --event-types=OBJECT_FINALIZE
```

**Parameters explained:**

| Parameter | Value | Why? |
|-----------|-------|------|
| `--topic` | docs-upload-topic | Which Pub/Sub topic to publish to |
| `--event-types` | OBJECT_FINALIZE | Only notify when upload COMPLETES (not while uploading) |

### Event Types Available

| Event Type | Triggers |
|------------|----------|
| `OBJECT_FINALIZE` | ✅ When upload completes |
| `OBJECT_DELETE` | When file is deleted |
| `OBJECT_ARCHIVE` | When object is archived |
| `OBJECT_METADATA_UPDATE` | When metadata changes |

We use **OBJECT_FINALIZE** because we want to process complete files only.

### Verification Commands

```bash
# List notifications on bucket
gcloud storage buckets notifications list gs://${PROJECT_ID}-docs-ingest/

# Get notification details (if needed)
gcloud storage buckets notifications describe gs://${PROJECT_ID}-docs-ingest/ <notification-id>
```

---

## 6. BigQuery Setup

### Purpose
Centralized **data warehouse** that stores document metadata and enables SQL queries.

### Schema Design

```
Table: docs_metadata.processed_docs

┌──────────────────────────────────────────────┐
│ Column            │ Type       │ Required   │
├───────────────────┼────────────┼────────────┤
│ filename          │ STRING     │ YES        │
│ processed_at      │ TIMESTAMP  │ YES        │
│ tags              │ STRING[]   │ YES        │  (REPEATED - array)
│ word_count        │ INTEGER    │ YES        │
│ bucket            │ STRING     │ YES        │
│ file_size         │ INTEGER    │ YES        │
└──────────────────────────────────────────────┘
```

### Setup Steps

#### Step 1: Create Dataset
```bash
python3 create_bigquery.py ps-my-document-processor docs_metadata processed_docs ./app/schema.json us-central1
```

Or manually:
```bash
bq mk --dataset \
  --location=us-central1 \
  --description="Document processing pipeline" \
  ps-my-document-processor:docs_metadata
```

#### Step 2: Create Table with Schema
The `create_bigquery.py` script does this automatically using `schema.json`:

```json
[
  {"name": "filename", "type": "STRING", "mode": "REQUIRED"},
  {"name": "processed_at", "type": "TIMESTAMP", "mode": "REQUIRED"},
  {"name": "tags", "type": "STRING", "mode": "REPEATED"},
  {"name": "word_count", "type": "INTEGER", "mode": "REQUIRED"},
  {"name": "bucket", "type": "STRING", "mode": "REQUIRED"},
  {"name": "file_size", "type": "INTEGER", "mode": "REQUIRED"}
]
```

**Why REPEATED for tags?**
- Each document can have multiple tags (invoice, payment, etc.)
- REPEATED field = Array in BigQuery
- Stored as: `['invoice', 'payment']` or `['report', 'logistics']`

### Verification Commands

```bash
# List datasets
bq ls -d

# Check dataset details
bq ls -d docs_metadata

# List tables in dataset
bq ls -t -d docs_metadata

# View table schema
bq show --schema --format=prettyjson ps-my-document-processor:docs_metadata.processed_docs

# Check row count
bq query --use_legacy_sql=false \
  "SELECT COUNT(*) as count FROM \`ps-my-document-processor.docs_metadata.processed_docs\`"

# View sample data
bq query --use_legacy_sql=false \
  "SELECT * FROM \`ps-my-document-processor.docs_metadata.processed_docs\` LIMIT 5"
```

---

## Issues We Faced & Solutions

### Issue 1: "bq command not found" / "python3.14 not found"

**Problem:**
```
ERROR: (bq) python3.14: command not found
```

**Root Cause:**
- `bq` CLI is installed but internal PATH detection failed
- setup.sh tried to run bq which couldn't find Python
- Git Bash has different PATH than PowerShell

**Solution:**
```bash
# Instead of using bq CLI, use Python API directly
python3 create_bigquery.py ps-my-document-processor docs_metadata processed_docs ./app/schema.json us-central1
```

**Learning:** Don't rely on CLI tools in automated scripts. Use SDK libraries instead.

---

### Issue 2: "gcloud pubsub topics describe docs-upload-topic - NOT_FOUND"

**Problem:**
```
ERROR: (gcloud.pubsub.topics.describe) Topic 'docs-upload-topic' not found.
```

**Root Cause:**
- setup.sh script had `set -e` (exit on first error)
- BigQuery creation failed → script exited immediately
- Pub/Sub topic creation code (line 100+) was never reached

**Solution:**
```bash
# Manually create the topic after BigQuery is fixed
gcloud pubsub topics create docs-upload-topic
```

**Learning:** When using `set -e`, be careful about where early exits happen. Use proper error handling instead of just exiting.

---

### Issue 3: "gsutil command not found" in Git Bash

**Problem:**
```
Command works from PowerShell but not from Git Bash
ERROR: gsutil: command not found
```

**Root Cause:**
- PowerShell has gcloud in PATH
- Git Bash doesn't automatically inherit Windows PATH
- gsutil is part of gcloud SDK but not in UNIX-style PATH

**Solution:**
```bash
# Add to ~/.bashrc
export PATH="/c/Users/YOUR_NAME/AppData/Local/Google/Cloud SDK/google-cloud-sdk/bin:$PATH"

# Or use gcloud storage instead of gsutil (modern alternative)
gcloud storage cp file.txt gs://bucket/
```

**Learning:** Always test shell commands in the target environment (Git Bash, PowerShell, Linux). Don't assume PATH is the same everywhere.

---

### Issue 4: "GcsApiError: Task failed" during file upload

**Problem:**
```
ERROR: Task 'gs://bucket/file.txt' failed: GcsApiError('')
```

**Root Cause (Multiple Possible Causes):**

**Cause A - Wrong Account Active (Most Common)**
- Multiple accounts authenticated in gcloud
- Service account (doc-processor-sa) was ACTIVE instead of user account
- Service accounts have limited permissions (only for Cloud Run to use)

**Cause B - Missing IAM Role**
- User account didn't have storage.objectCreator role
- Bucket had public access prevention + uniform bucket-level access enabled
- Only IAM roles grant access (not bucket-level ACLs)

**Solution:**

**Step 1: Check which account is currently active**
```bash
gcloud auth list
```

Should show:
```
            ACTIVE  ACCOUNT
*                  doc-processor-sa@ps-my-document-processor.iam.gserviceaccount.com
                   techlead.ps@gmail.com
```

**Step 2: Switch to user account**
```bash
gcloud config set account 'techlead.ps@gmail.com'
```

**Step 3: Verify it's now active**
```bash
gcloud auth list
```

Should show:
```
            ACTIVE  ACCOUNT
                   doc-processor-sa@ps-my-document-processor.iam.gserviceaccount.com
*                  techlead.ps@gmail.com
```

**Step 4: If still failing, grant IAM role**
```bash
gcloud projects add-iam-policy-binding ps-my-document-processor \
  --member="user:techlead.ps@gmail.com" \
  --role="roles/storage.objectCreator"
```

**Step 5: Try upload again**
```bash
echo "test" > test.txt
gcloud storage cp test.txt gs://${PROJECT_ID}-docs-ingest/
```

**Learning:** 
- Always check which account is active: `gcloud auth list`
- Service accounts should NOT be your active account for manual testing
- User account should be active for manual uploads/testing
- Service account should only be used by Cloud Run (automated)
- The error message `GcsApiError('')` is misleading - check active account first!

---

### Issue 5: "Service account service-xxx@gs-project-accounts.iam.gserviceaccount.com does not exist"

**Problem:**
```
ERROR: Service account service-798696075142@gs-project-accounts.iam.gserviceaccount.com does not exist.
```

**Root Cause:**
- GCS service account is created automatically when you use GCS
- But it may not exist yet in a fresh project
- setup.sh tried to grant permissions before account was created

**Solution:**
```bash
# Option 1: Skip this permission, it's optional for basic pipeline
# Option 2: Let GCS create the account by using notifications first
# Option 3: Use error handling in setup.sh:

gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:$GCS_SA_EMAIL" \
  --role="roles/pubsub.publisher" || echo "GCS account not ready (will be auto-created)"
```

**Learning:** Some GCP service accounts are created on-demand. Don't assume they exist until actually used.

---

### Issue 6: "Pub/Sub subscription create with empty SERVICE_URL"

**Problem:**
```
ERROR: argument --push-endpoint: expected one argument
```

**Root Cause:**
- SERVICE_URL variable was empty
- Cloud Run service wasn't deployed yet
- Script tried to create subscription before Cloud Run was ready

**Solution:**
```bash
# Step 1: Deploy Cloud Run first
gcloud run deploy doc-processor-service \
  --source ./app \
  --region us-central1 \
  --service-account doc-processor-sa@${PROJECT_ID}.iam.gserviceaccount.com

# Step 2: Get the URL
SERVICE_URL=$(gcloud run services describe doc-processor-service \
  --region us-central1 --format='value(status.url)')

# Step 3: Verify it's not empty
echo $SERVICE_URL  # Should show https://...

# Step 4: Create subscription
gcloud pubsub subscriptions create docs-upload-topic-sub \
  --topic docs-upload-topic \
  --push-endpoint "$SERVICE_URL" \
  --push-auth-service-account pubsub-invoker-sa@${PROJECT_ID}.iam.gserviceaccount.com
```

**Learning:** Ensure dependencies are deployed before trying to reference them.

---

## Setup Verification Checklist

Use this checklist to verify each service is properly configured:

### 1. Cloud Storage ✅
```bash
# Should return bucket details
gcloud storage buckets describe gs://${PROJECT_ID}-docs-ingest

# Should show: uniformBucketLevelAccess.enabled: true
# Should show: publicAccessPrevention: enforced
```

### 2. BigQuery ✅
```bash
# Should list docs_metadata
bq ls -d

# Should list processed_docs table
bq ls -t -d docs_metadata

# Should show 6 columns with correct types
bq show --schema --format=prettyjson ps-my-document-processor:docs_metadata.processed_docs
```

### 3. Pub/Sub Topic ✅
```bash
# Should show topic details
gcloud pubsub topics describe docs-upload-topic
```

### 4. Pub/Sub Subscription ✅
```bash
# Should show subscription with push configuration
gcloud pubsub subscriptions describe docs-upload-topic-sub

# Should show:
# pushConfig:
#   pushEndpoint: https://doc-processor-service-xxx.run.app
#   oidcToken:
#     serviceAccountEmail: pubsub-invoker-sa@...
```

### 5. Cloud Run Service ✅
```bash
# Should show service details
gcloud run services describe doc-processor-service --region us-central1

# Should show:
# serviceAccountName: doc-processor-sa@...
# spec.template.spec.containers[0].env:
#   - name: BQ_DATASET
#     value: docs_metadata
#   - name: BQ_TABLE
#     value: processed_docs
```

### 6. GCS Notification ✅
```bash
# Should show notification configuration
gcloud storage buckets notifications list gs://${PROJECT_ID}-docs-ingest/
```

### 7. IAM Permissions ✅
```bash
# Should show doc-processor-sa has 3 roles
gcloud projects get-iam-policy ${PROJECT_ID} \
  --flatten="bindings[].members" \
  --filter="bindings.members:doc-processor-sa*"

# Should show pubsub-invoker-sa has 1 role
gcloud projects get-iam-policy ${PROJECT_ID} \
  --flatten="bindings[].members" \
  --filter="bindings.members:pubsub-invoker-sa*"
```

---

## Quick Reference: Service Dependencies

```
Setup Order (Dependencies):

1. Cloud Storage
   ↓
2. BigQuery (independent, but needed for Cloud Run to work)
   ↓
3. Cloud Run (needs BigQuery dataset/table to exist)
   ↓
4. Pub/Sub Topic (independent)
   ↓
5. Pub/Sub Subscription (needs Cloud Run URL)
   ↓
6. GCS Notification (links Storage → Pub/Sub)
   ↓
7. IAM Permissions (needed for all services to communicate)
```

---

## Account Management (Critical for Testing)

**IMPORTANT:** Know which account is active before running commands!

```bash
# Check all authenticated accounts
gcloud auth list

# Output example:
#              ACTIVE  ACCOUNT
# *                   doc-processor-sa@ps-my-document-processor.iam.gserviceaccount.com
#                    techlead.ps@gmail.com

# Switch to user account (for manual testing)
gcloud config set account 'techlead.ps@gmail.com'

# Switch to service account (for Cloud Run simulation)
gcloud config set account 'doc-processor-sa@ps-my-document-processor.iam.gserviceaccount.com'

# Add a new account if needed
gcloud auth login

# Remove an account
gcloud auth revoke 'service-account-email@project.iam.gserviceaccount.com'
```

**When to use which account:**

| Task | Account | Why? |
|------|---------|------|
| Manual file upload | techlead.ps@gmail.com | Has storage.objectCreator role |
| Testing pipeline | techlead.ps@gmail.com | Can trigger uploads manually |
| Check Cloud Run logs | techlead.ps@gmail.com | Has run.viewer role |
| Simulate Cloud Run (test) | doc-processor-sa | Service account identity |

---

## Common Commands Cheat Sheet

```bash
# Set variables
export PROJECT_ID="ps-my-document-processor"
export REGION="us-central1"
export SA_EMAIL="doc-processor-sa@${PROJECT_ID}.iam.gserviceaccount.com"
export PUBSUB_SA_EMAIL="pubsub-invoker-sa@${PROJECT_ID}.iam.gserviceaccount.com"

# Verify all services
echo "=== Cloud Storage ==="
gcloud storage buckets describe gs://${PROJECT_ID}-docs-ingest | grep -E "name|location"

echo "=== BigQuery ==="
bq ls -d | grep docs_metadata

echo "=== Pub/Sub ==="
gcloud pubsub topics list | grep docs-upload-topic

echo "=== Cloud Run ==="
gcloud run services list --region $REGION | grep doc-processor-service

echo "=== IAM ==="
gcloud projects get-iam-policy $PROJECT_ID --flatten="bindings[].members" | grep -E "doc-processor-sa|pubsub-invoker-sa"
```

---

## Troubleshooting Flow

```
Pipeline not working?

1. Check logs first
   gcloud run logs read doc-processor-service --region us-central1 --limit 50

2. Verify subscription is configured
   gcloud pubsub subscriptions describe docs-upload-topic-sub

3. Check if Cloud Run has permissions
   gcloud projects get-iam-policy $PROJECT_ID | grep doc-processor-sa

4. Verify BigQuery table exists
   bq show ps-my-document-processor:docs_metadata.processed_docs

5. Test file upload
   echo "test" > test.txt
   gcloud storage cp test.txt gs://${PROJECT_ID}-docs-ingest/

6. Wait 15 seconds, then check BigQuery
   bq query "SELECT COUNT(*) FROM \`${PROJECT_ID}.docs_metadata.processed_docs\`"
```

---

## Key Takeaways for Junior Developers

1. **Service Accounts are Security Boundaries**
   - Each component gets its own service account
   - Principle of least privilege: only necessary permissions
   - Never embed human credentials in code

2. **IAM is How Services Talk**
   - Storage → Pub/Sub requires pubsub.publisher
   - Pub/Sub → Cloud Run requires run.invoker
   - Cloud Run → BigQuery requires bigquery.dataEditor + bigquery.user

3. **Order Matters**
   - Deploy resources in dependency order
   - Don't reference a resource before it exists
   - Use `set -e` carefully in scripts

4. **Test Each Step**
   - Don't assume a service exists, verify it
   - Use gcloud describe commands to check configuration
   - Check logs early when troubleshooting

5. **Use SDKs, Not Just CLIs**
   - CLI tools (bq, gsutil) can have environment issues
   - Python/Go/Node SDKs are more reliable in automation
   - CLIs are good for interactive troubleshooting

---

**Document Version:** 1.0  
**Last Updated:** 2026-06-17  
**Created for:** Junior Developer Training
