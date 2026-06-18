# Event-Driven Document Processing Pipeline on Google Cloud

A serverless, fully managed pipeline for document ingestion, processing, and metadata extraction using Google Cloud Platform (GCP).

## Architecture

```
Cloud Storage Bucket
        ↓
   (File Upload)
        ↓
   Pub/Sub Topic
        ↓
  (Event Trigger)
        ↓
   Cloud Run Service
   (Flask Application)
        ↓
   (Process Document)
   (Extract Metadata)
        ↓
   BigQuery Dataset
        ↓
   (Store Metadata)
```

### Components

- **Cloud Storage**: Ingestion point for document uploads
- **Pub/Sub**: Event messaging service that triggers processing on file uploads
- **Cloud Run**: Serverless compute platform running a Python Flask application
- **BigQuery**: Data warehouse for storing extracted metadata

## Features

- **Simulated OCR**: Extracts text from documents and analyzes content
- **Keyword Tagging**: Automatically tags documents (invoice, report, receipt, etc.)
- **Metadata Extraction**: Records filename, word count, file size, processing timestamp
- **Serverless**: No infrastructure management required
- **Scalable**: Automatically scales based on demand
- **Cost-Effective**: Pay only for what you use

## Prerequisites

Before you begin, ensure you have:

1. **Google Cloud Project**: Create one at https://console.cloud.google.com
2. **gcloud CLI**: Install from https://cloud.google.com/sdk/docs/install
3. **bq CLI**: Installed with gcloud SDK
4. **Billing Enabled**: Your GCP project must have billing enabled
5. **Appropriate IAM Permissions**: Permission to create Cloud Run services, Pub/Sub topics, BigQuery datasets, etc.

### Setup gcloud

```bash
# Install gcloud if not already installed
# Then authenticate and set your project
gcloud auth login
gcloud config set project YOUR_PROJECT_ID
```

## Quick Start

### 1. Deploy the Pipeline

```bash
# From the project root directory
chmod +x setup.sh
./setup.sh
```

This script will:
- Enable required GCP APIs
- Create a Cloud Storage bucket for document ingestion
- Create a BigQuery dataset and table for storing metadata
- Create a Pub/Sub topic for event notifications
- Deploy the Cloud Run service
- Set up all necessary IAM permissions
- Create the Pub/Sub push subscription

### 2. Upload a Test File

```bash
# Set your project ID
PROJECT_ID=$(gcloud config get-value project)
BUCKET_NAME="${PROJECT_ID}-docs-ingest"

# Create and upload a test file
echo "This is an invoice document with payment terms." > test_invoice.txt
gcloud storage cp test_invoice.txt gs://$BUCKET_NAME/
```

### 3. Verify Processing

```bash
# Check Cloud Run logs
gcloud run logs read doc-processor-service --region us-central1 --limit 20

# Query BigQuery results
PROJECT_ID=$(gcloud config get-value project)
bq query --use_legacy_sql=false \
  "SELECT filename, word_count, tags, processed_at FROM \`$PROJECT_ID.docs_metadata.processed_docs\` LIMIT 10"
```

## Testing

### Local Testing

Test the Flask application locally without deploying to Cloud Run:

```bash
chmod +x test_local.sh
./test_local.sh
```

This tests:
- Message parsing
- Invalid message handling
- Folder placeholder skipping

### Cloud Testing

After deployment, run the full end-to-end test:

```bash
chmod +x test_cloud.sh
./test_cloud.sh
```

This script will:
- Create test files
- Upload them to GCS
- Wait for processing
- Query BigQuery for results

## Project Structure

```
google-cloud-serverless-app/
├── app/
│   ├── main.py              # Flask application entry point
│   ├── requirements.txt      # Python dependencies
│   ├── Dockerfile           # Docker image configuration
│   └── schema.json          # BigQuery table schema
├── setup.sh                 # Infrastructure provisioning script
├── test_local.sh            # Local testing script
├── test_cloud.sh            # Cloud testing script
└── README.md                # This file
```

## Application Details

### Flask Application (`app/main.py`)

The Core service that:

1. **Receives Events**: Listens for Pub/Sub push messages
2. **Extracts Data**: Reads GCS event metadata
3. **Processes Files**: 
   - Downloads and reads text files
   - Simulates OCR for binary files
4. **Extracts Metadata**:
   - Counts words in document
   - Identifies tags based on keywords
5. **Stores Results**: Inserts metadata into BigQuery

### Supported Keywords

The application recognizes the following keywords for tagging:
- invoice
- receipt
- report
- payment
- statement
- logistics
- shipping
- contract
- resume
- memo

Files with these keywords in their content are automatically tagged.

### BigQuery Schema

The `processed_docs` table stores:

| Column | Type | Description |
|--------|------|-------------|
| filename | STRING | Name of the processed file |
| processed_at | TIMESTAMP | When the file was processed |
| tags | STRING (REPEATED) | Array of tags assigned to the document |
| word_count | INTEGER | Total words in the document |
| bucket | STRING | GCS bucket name |
| file_size | INTEGER | File size in bytes |

## Configuration

### Environment Variables

Set in `setup.sh`:

```bash
REGION="us-central1"                    # GCP region
TOPIC_NAME="docs-upload-topic"          # Pub/Sub topic name
DATASET_NAME="docs_metadata"            # BigQuery dataset name
TABLE_NAME="processed_docs"             # BigQuery table name
SERVICE_NAME="doc-processor-service"    # Cloud Run service name
```

### Cloud Run Configuration

Modify these in `setup.sh`:

```bash
--region "$REGION"              # Deployment region
--no-allow-unauthenticated     # Require authentication
--service-account "$SA_EMAIL"  # Service account for running service
```

## Monitoring and Troubleshooting

### Check Service Status

```bash
# Check Cloud Run service
gcloud run services describe doc-processor-service --region us-central1

# Check recent logs
gcloud run logs read doc-processor-service --region us-central1 --limit 50
```

### View Pub/Sub Subscription

```bash
# Describe subscription
gcloud pubsub subscriptions describe docs-upload-topic-sub

# Pull messages (for debugging)
gcloud pubsub subscriptions pull docs-upload-topic-sub --auto-ack --limit 5
```

### Query BigQuery

```bash
# List all records
bq query --use_legacy_sql=false "SELECT * FROM \`YOUR_PROJECT.docs_metadata.processed_docs\`"

# Count records
bq query --use_legacy_sql=false "SELECT COUNT(*) FROM \`YOUR_PROJECT.docs_metadata.processed_docs\`"

# Find documents with specific tags
bq query --use_legacy_sql=false \
  "SELECT filename, tags FROM \`YOUR_PROJECT.docs_metadata.processed_docs\` WHERE 'invoice' IN UNNEST(tags)"
```

### Common Issues

#### Issue: Service returns 500 error

**Cause**: Usually BigQuery insertion failure

**Solution**:
1. Check service account permissions
2. Verify table schema matches
3. Check BigQuery quota
4. View Cloud Run logs for specific error

```bash
gcloud run logs read doc-processor-service --region us-central1 --limit 20
```

#### Issue: No messages appearing in BigQuery

**Cause**: Pub/Sub subscription not receiving messages

**Solution**:
1. Check GCS notification configuration
2. Verify Pub/Sub topic exists
3. Check subscription push endpoint

```bash
# Verify GCS notification
gcloud storage buckets notifications list gs://$BUCKET_NAME

# Test Pub/Sub directly
echo "test message" | gcloud pubsub topics publish docs-upload-topic --message "test"
```

#### Issue: Files not appearing in BigQuery after 5+ minutes

**Possible Causes**:
1. Cloud Run service not responding
2. Pub/Sub subscription not configured correctly
3. BigQuery table quota exceeded
4. Service account permissions issue

**Debug Steps**:
```bash
# 1. Check Cloud Run logs
gcloud run logs read doc-processor-service --region us-central1 --limit 50

# 2. Check Pub/Sub subscription status
gcloud pubsub subscriptions describe docs-upload-topic-sub

# 3. Manually check if file is in bucket
gsutil ls gs://$BUCKET_NAME/

# 4. Verify service account permissions
gcloud projects get-iam-policy $PROJECT_ID --flatten="bindings[].members" \
  --filter="bindings.members:serviceAccount:*doc-processor*"
```

## Cleanup

To delete all resources created by this pipeline:

```bash
# Note: This will delete all data
PROJECT_ID=$(gcloud config get-value project)

# Delete Cloud Run service
gcloud run services delete doc-processor-service --region us-central1 --quiet

# Delete Pub/Sub topic and subscription
gcloud pubsub subscriptions delete docs-upload-topic-sub --quiet
gcloud pubsub topics delete docs-upload-topic --quiet

# Delete BigQuery dataset (with all tables)
bq rm --recursive --dataset --force "$PROJECT_ID:docs_metadata"

# Delete Cloud Storage bucket (empty it first if it has data)
gsutil -m rm -r "gs://${PROJECT_ID}-docs-ingest"

# Delete service accounts
gcloud iam service-accounts delete "doc-processor-sa@${PROJECT_ID}.iam.gserviceaccount.com" --quiet
gcloud iam service-accounts delete "pubsub-invoker-sa@${PROJECT_ID}.iam.gserviceaccount.com" --quiet

# Disable APIs
gcloud services disable \
  storage.googleapis.com \
  pubsub.googleapis.com \
  run.googleapis.com \
  bigquery.googleapis.com \
  artifactregistry.googleapis.com \
  cloudbuild.googleapis.com
```

## Advanced Usage

### Adding Custom Keywords

Edit `app/main.py` and modify the `KEYWORD_TAGS` dictionary:

```python
KEYWORD_TAGS = {
    "invoice": "invoice",
    "receipt": "receipt",
    "your_keyword": "your_tag",
    # ... add more keywords
}
```

Then redeploy:
```bash
gcloud run deploy doc-processor-service --source ./app --region us-central1
```

### Scaling Configuration

Modify Cloud Run scaling in `setup.sh`:

```bash
# Add to gcloud run deploy command:
--min-instances 0           # Minimum instances (0 for cost optimization)
--max-instances 100         # Maximum instances
--cpu 1                     # CPU per instance
--memory 512Mi              # Memory per instance
```

### Batch Processing

To process multiple files efficiently:

```bash
# Upload multiple files at once
for file in ./documents/*; do
  gcloud storage cp "$file" gs://$BUCKET_NAME/
done
```

## Cost Estimation

Typical costs (estimated monthly for 1000 document uploads):

- **Cloud Storage**: ~$0.02 (storage) + minimal request costs
- **Pub/Sub**: ~$0.40 (1,000 messages)
- **Cloud Run**: ~$0.20-2.00 (based on processing time and CPU)
- **BigQuery**: ~$0.01 (1,000 rows, if under 1TB free tier)

Total: ~$0.60-2.40/month for light usage

See [GCP Pricing Calculator](https://cloud.google.com/products/calculator) for detailed estimates.

## Security Considerations

1. **Service Accounts**: Uses least-privilege IAM roles
2. **Authentication**: Cloud Run service requires authentication from Pub/Sub
3. **Network**: Not publicly accessible (no-allow-unauthenticated flag)
4. **Data**: Files are stored in Cloud Storage with standard GCP encryption
5. **Audit**: All operations are logged in Cloud Audit Logs

## API Reference

### POST /

Endpoint that receives Pub/Sub push messages.

**Request Format**:
```json
{
  "message": {
    "data": "base64-encoded-gcs-event"
  }
}
```

**Response**:
- `200 OK`: Successfully processed
- `204 No Content`: Skipped (folder, test notification, etc.)
- `400 Bad Request`: Invalid message format
- `500 Internal Server Error`: Processing error

## Contributing

To extend this pipeline:

1. **Add new keywords**: Modify `KEYWORD_TAGS` in `app/main.py`
2. **Enhanced OCR**: Replace simulated OCR with actual OCR service (Vision API)
3. **Additional metadata**: Modify BigQuery schema and extraction logic
4. **Custom processing**: Implement additional processors in Cloud Run

## Resources

- [Google Cloud Documentation](https://cloud.google.com/docs)
- [Cloud Storage Events](https://cloud.google.com/storage/docs/pubsub-notifications)
- [Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Pub/Sub Documentation](https://cloud.google.com/pubsub/docs)
- [BigQuery Documentation](https://cloud.google.com/bigquery/docs)
- [Vision API for Real OCR](https://cloud.google.com/vision/docs)

## License

This project is provided as-is for demonstration and educational purposes.

## Support

For issues or questions:

1. Check the [Troubleshooting](#monitoring-and-troubleshooting) section
2. Review Cloud Run logs
3. Verify all prerequisites are met
4. Check your GCP project permissions
