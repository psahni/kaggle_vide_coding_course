# Troubleshooting Guide

Common issues and how to resolve them.

## Table of Contents

1. [Setup Issues](#setup-issues)
2. [Deployment Issues](#deployment-issues)
3. [Runtime Issues](#runtime-issues)
4. [Data Issues](#data-issues)
5. [Performance Issues](#performance-issues)

## Setup Issues

### Issue: "gcloud: command not found"

**Cause**: Google Cloud SDK is not installed or not in PATH

**Solution**:
1. Install from: https://cloud.google.com/sdk/docs/install
2. Verify installation:
   ```bash
   gcloud --version
   ```

### Issue: "Error: No Google Cloud project is currently selected"

**Cause**: gcloud is not configured with a project

**Solution**:
```bash
# List your projects
gcloud projects list

# Set your project
gcloud config set project YOUR_PROJECT_ID

# Verify
gcloud config list
```

### Issue: "Permission denied" during setup

**Cause**: Your Google account doesn't have sufficient permissions

**Solution**:
1. Verify your account role in the GCP Console
2. You need at minimum:
   - Editor role on the project, OR
   - Custom role with permissions to create Cloud Run, Pub/Sub, BigQuery, Storage, IAM resources
3. Ask your project administrator to grant the necessary role

### Issue: "Billing account is not set"

**Cause**: The GCP project doesn't have billing enabled

**Solution**:
1. Go to https://console.cloud.google.com/billing
2. Create or select a billing account
3. Link it to your project
4. Re-run the setup script

## Deployment Issues

### Issue: setup.sh fails with "bq command not found"

**Cause**: The `bq` CLI is not in PATH

**Solution** (Windows Git Bash):
```bash
# The script should auto-find bq.cmd
# If not, ensure gcloud is properly installed with bq

# Manual workaround:
bq() { 
  bq.cmd "$@"
}
```

### Issue: Cloud Run deployment times out

**Cause**: First deployment can take 2-3 minutes

**Solution**:
1. Wait longer (5+ minutes)
2. Check deployment status:
   ```bash
   gcloud run operations list --region us-central1
   ```
3. Check for errors in Cloud Build:
   ```bash
   gcloud builds list
   ```

### Issue: "Service account creation failed"

**Cause**: Service account with that name already exists

**Solution**:
```bash
# Check existing service accounts
gcloud iam service-accounts list

# If already exists, the script will continue
# Run the script again and it will skip creation
```

### Issue: BigQuery table creation fails

**Cause**: Schema file not found or invalid JSON

**Solution**:
1. Verify schema.json exists in app/ directory
2. Validate JSON:
   ```bash
   python3 -m json.tool app/schema.json
   ```
3. Ensure processed_at field is TIMESTAMP type
4. Run setup.sh again

## Runtime Issues

### Issue: No records appearing in BigQuery after uploading files

**Symptoms**: Files appear in bucket but not in BigQuery after 5+ minutes

**Diagnosis Steps**:

```bash
# 1. Check if Cloud Run service is running
gcloud run services describe doc-processor-service --region us-central1

# 2. Check recent logs
gcloud run logs read doc-processor-service --region us-central1 --limit 50

# 3. Check if service is actually receiving requests
# Look for "Received GCS Event" or similar in logs
```

**Possible Causes & Solutions**:

#### Cloud Run Service Not Responding

**Check logs**:
```bash
gcloud run logs read doc-processor-service --region us-central1 --limit 100
```

**Look for**:
- Error messages
- Stack traces
- Authentication failures

**Common Log Errors**:

| Error | Cause | Fix |
|-------|-------|-----|
| `401 Unauthorized` | Service account permissions | Re-run setup.sh to fix IAM |
| `404 NOT_FOUND` for BigQuery | Wrong table name | Check BQ_DATASET and BQ_TABLE env vars |
| `403 Permission denied` | Service account lacks permissions | Verify IAM roles are set |

#### Pub/Sub Subscription Not Working

**Check subscription**:
```bash
# Describe subscription
gcloud pubsub subscriptions describe docs-upload-topic-sub

# Check for push endpoint
# Should point to your Cloud Run URL
```

**Verify Pub/Sub can reach Cloud Run**:
```bash
# Get Cloud Run URL
gcloud run services describe doc-processor-service --region us-central1 --format='value(status.url)'

# The subscription push endpoint should match this URL
```

**Test Pub/Sub directly**:
```bash
# Publish a test message
gcloud pubsub topics publish docs-upload-topic --message "test"

# Check if it gets pulled
gcloud pubsub subscriptions pull docs-upload-topic-sub --auto-ack --limit 1
```

#### GCS Notifications Not Firing

**Check if notification exists**:
```bash
PROJECT_ID=$(gcloud config get-value project)
BUCKET_NAME="${PROJECT_ID}-docs-ingest"
gcloud storage buckets notifications list "gs://$BUCKET_NAME"
```

**If notification doesn't exist**:
```bash
# Recreate it
gcloud storage buckets notifications create "gs://$BUCKET_NAME" \
  --topic="docs-upload-topic" \
  --event-types="OBJECT_FINALIZE"
```

**Verify bucket has publish permission**:
```bash
# Check bucket's service account has pubsub.publisher role
# The service account is: service-{PROJECT_NUMBER}@gs-project-accounts.iam.gserviceaccount.com

PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format="value(projectNumber)")
GCS_SA="service-${PROJECT_NUMBER}@gs-project-accounts.iam.gserviceaccount.com"

gcloud projects get-iam-policy $PROJECT_ID \
  --flatten="bindings[].members" \
  --filter="bindings.members:$GCS_SA"
```

### Issue: 500 Error when processing files

**Cause**: Usually BigQuery insertion failure

**Check logs**:
```bash
gcloud run logs read doc-processor-service --region us-central1 --limit 50 | grep -A 5 -B 5 "500\|error"
```

**Common Causes**:

1. **Wrong BigQuery dataset/table name**:
   ```bash
   # Verify env vars in Cloud Run
   gcloud run services describe doc-processor-service --region us-central1
   # Look for BQ_DATASET and BQ_TABLE
   ```

2. **BigQuery quota exceeded**:
   ```bash
   # Check quota in Cloud Console
   # Usually not an issue for small deployments
   ```

3. **Service account lacks BigQuery permissions**:
   ```bash
   # Verify service account has these roles:
   # - roles/bigquery.dataEditor
   # - roles/bigquery.user
   
   PROJECT_ID=$(gcloud config get-value project)
   gcloud projects get-iam-policy $PROJECT_ID \
     --flatten="bindings[].members" \
     --filter="bindings.members:doc-processor-sa*"
   ```

### Issue: 400 Bad Request errors

**Cause**: Invalid message format from Pub/Sub

**Check logs**:
```bash
gcloud run logs read doc-processor-service --region us-central1 --limit 20
```

**Look for**:
- "Invalid Pub/Sub message format"
- "Failed to decode"

**Solution**: This usually means the Pub/Sub -> Cloud Run integration isn't working properly. Re-run setup.sh.

## Data Issues

### Issue: Incorrect word counts

**Cause**: Whitespace handling or non-text files

**Solution**:
- Word count uses Python's `str.split()` which splits on any whitespace
- For PDF/images, the mock OCR generates synthetic text
- If you need accurate OCR, integrate Google Cloud Vision API

### Issue: Tags not being assigned correctly

**Cause**: Keywords are case-sensitive in current implementation

**Check**:
```bash
# Keywords are searched in lowercase
# The file content is converted to lowercase
# But keywords must match exactly (case-insensitive)
```

**Solution**:
1. Add more keywords to app/main.py `KEYWORD_TAGS`
2. Redeploy the service:
   ```bash
   gcloud run deploy doc-processor-service --source ./app --region us-central1
   ```

### Issue: Files appearing as "unclassified"

**Cause**: No matching keywords found in document

**Solution**:
1. Check if file content contains keyword terms
2. Add more keywords to KEYWORD_TAGS
3. For PDF/images, the mock OCR tries to extract from filename
4. Integrate real OCR for better accuracy

### Issue: Timestamp format incorrect in BigQuery

**Cause**: String vs TIMESTAMP type mismatch

**Check**:
- app/main.py should use `isoformat() + "Z"` format
- BigQuery schema.json should have TIMESTAMP type

**Solution**:
- Already fixed in current version
- If still seeing issues, update the timestamp format:
  ```python
  "processed_at": datetime.utcnow().isoformat() + "Z"
  ```

## Performance Issues

### Issue: Very slow processing (>1 minute per file)

**Cause**: Usually Cloud Run startup time (cold start)

**Solution**:
1. This is normal for first request after deployment
2. Subsequent requests are faster
3. To reduce cold starts:
   ```bash
   # Set minimum instances (costs more but faster)
   gcloud run deploy doc-processor-service \
     --min-instances 1 \
     --source ./app \
     --region us-central1
   ```

### Issue: Processing many files, some fail

**Cause**: Transient errors, typically Pub/Sub retries

**Solution**:
1. This is normal behavior
2. Pub/Sub automatically retries failed messages (up to 7 days)
3. Check logs for specific errors:
   ```bash
   gcloud run logs read doc-processor-service --region us-central1 --limit 100
   ```
4. Adjust Pub/Sub subscription retry settings if needed

### Issue: BigQuery storage filling up too quickly

**Cause**: Processing too many files or storing unnecessary data

**Solution**:
1. Set up BigQuery data expiration:
   ```bash
   bq update --expiration 7776000 \
     docs_metadata.processed_docs
   ```
2. Archive old data to Cloud Storage
3. Delete unnecessary records:
   ```bash
   bq query --use_legacy_sql=false \
     "DELETE FROM \`PROJECT_ID.docs_metadata.processed_docs\` WHERE processed_at < '2025-01-01'"
   ```

## Debugging Tips

### Enable Debug Logging

Modify app/main.py:
```python
logging.basicConfig(level=logging.DEBUG)  # Change from INFO to DEBUG
```

Then redeploy:
```bash
gcloud run deploy doc-processor-service --source ./app --region us-central1
```

### Test Messages Manually

```bash
# Create a test GCS event
cat > test_event.json << 'EOF'
{
  "bucket": "your-bucket-name",
  "name": "test_invoice.txt",
  "size": "1024",
  "contentType": "text/plain"
}
EOF

# Encode it
ENCODED=$(python3 -c "import base64, json; print(base64.b64encode(open('test_event.json', 'rb').read()).decode())")

# Publish to Pub/Sub
gcloud pubsub topics publish docs-upload-topic --message "$ENCODED"
```

### Query BigQuery for Errors

```bash
# Find processing errors
PROJECT_ID=$(gcloud config get-value project)
bq query --use_legacy_sql=false \
  "SELECT filename, processed_at FROM \`$PROJECT_ID.docs_metadata.processed_docs\` WHERE tags LIKE '%error%' OR word_count = 0"
```

## Asking for Help

If you need to report an issue:

1. **Gather information**:
   ```bash
   # Get logs
   gcloud run logs read doc-processor-service --region us-central1 --limit 100 > logs.txt
   
   # Get service status
   gcloud run services describe doc-processor-service --region us-central1 > service.txt
   
   # Get subscription status
   gcloud pubsub subscriptions describe docs-upload-topic-sub > subscription.txt
   ```

2. **Include**:
   - Error messages from logs
   - Steps you took before the error
   - When the issue started
   - Which files you were processing

3. **Resources**:
   - [Cloud Run Documentation](https://cloud.google.com/run/docs)
   - [Pub/Sub Documentation](https://cloud.google.com/pubsub/docs)
   - [BigQuery Documentation](https://cloud.google.com/bigquery/docs)

---

**Still having issues?** Check the README.md for additional resources and documentation.
