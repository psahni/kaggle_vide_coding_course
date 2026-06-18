# Quick Start Guide

Get your event-driven document processing pipeline running in 5 minutes!

## Prerequisites Checklist

Before starting, verify you have:

- [ ] Google Cloud Account
- [ ] GCP Project created
- [ ] Billing enabled on your project
- [ ] `gcloud` CLI installed (`gcloud --version`)
- [ ] Logged into gcloud (`gcloud auth login`)
- [ ] Project set (`gcloud config set project YOUR_PROJECT_ID`)

## Step 1: Verify Your Setup (1 minute)

```bash
# Check gcloud is installed and configured
gcloud config list

# You should see something like:
# [core]
# account = your-email@gmail.com
# project = your-project-id
```

## Step 2: Deploy Everything (2-3 minutes)

```bash
# Make sure you're in the project directory
cd google-cloud-serverless-app

# Run the setup script
chmod +x setup.sh
./setup.sh
```

This will automatically:
- Enable required GCP APIs
- Create Cloud Storage bucket
- Create BigQuery dataset and table
- Set up Pub/Sub topic
- Deploy Cloud Run service
- Configure all permissions

**Note**: First-time Cloud Run deployment may take 2-3 minutes.

## Step 3: Test the Pipeline (30 seconds)

```bash
# Use the cloud test script
chmod +x test_cloud.sh
./test_cloud.sh
```

This will:
- Create 3 sample documents
- Upload them to your Cloud Storage bucket
- Wait for processing
- Show you the results from BigQuery

## Step 4: View Results

```bash
# Quick way to see your data
PROJECT_ID=$(gcloud config get-value project)
bq query --use_legacy_sql=false \
  "SELECT filename, word_count, ARRAY_LENGTH(tags) as tag_count FROM \`$PROJECT_ID.docs_metadata.processed_docs\` ORDER BY processed_at DESC"
```

## 🎉 You're Done!

Your pipeline is now processing documents. Here's what you can do next:

### Upload Your Own Files

```bash
PROJECT_ID=$(gcloud config get-value project)
gsutil cp your_document.txt gs://${PROJECT_ID}-docs-ingest/
```

### Monitor Processing

```bash
# Watch logs in real-time
gcloud alpha run logs tail doc-processor-service --region us-central1 --follow
```

### Check BigQuery Regularly

```bash
PROJECT_ID=$(gcloud config get-value project)
bq query --use_legacy_sql=false \
  "SELECT * FROM \`$PROJECT_ID.docs_metadata.processed_docs\` ORDER BY processed_at DESC LIMIT 5"
```

## Using Make Commands (Easier!)

If you have `make` installed, these are easier:

```bash
make status      # Check everything is running
make logs        # View recent logs
make query       # Query BigQuery
make test-cloud  # Run tests again
make cleanup     # Delete everything (if you want to stop)
```

## Troubleshooting

### "gcloud: command not found"
Install the Google Cloud SDK: https://cloud.google.com/sdk/docs/install

### "Project is not set"
Run: `gcloud config set project YOUR_PROJECT_ID`

### "No records in BigQuery after 5 minutes"
```bash
# Check if Cloud Run service is getting errors
gcloud run logs read doc-processor-service --region us-central1 --limit 20
```

### "Permission denied" errors
Your service account may not have the right permissions. Check your IAM roles in the GCP Console.

## Next Steps

1. **Customize Keywords**: Edit `app/main.py` and modify `KEYWORD_TAGS`
2. **Add Real OCR**: Integrate Google Cloud Vision API instead of simulated OCR
3. **Scale Up**: Process thousands of documents per day
4. **Integrate**: Connect to your applications using BigQuery queries

## Cost

This setup should cost less than $1/month for testing. See [README.md](README.md#cost-estimation) for cost details.

## Need Help?

- Check [README.md](README.md) for detailed documentation
- View Cloud Run logs: `gcloud run logs read doc-processor-service --region us-central1`
- Check Pub/Sub: `gcloud pubsub subscriptions describe docs-upload-topic-sub`

## Key Resources

| Resource | View/Manage |
|----------|------------|
| Cloud Run Service | https://console.cloud.google.com/run |
| Cloud Storage Bucket | https://console.cloud.google.com/storage/browser |
| BigQuery Dataset | https://console.cloud.google.com/bigquery |
| Pub/Sub Topic | https://console.cloud.google.com/pubsub/topics |
| Cloud Logs | https://console.cloud.google.com/logs |

---

Happy document processing! 📄✨
