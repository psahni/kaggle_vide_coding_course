# Deployment Checklist

Use this checklist to ensure your pipeline is properly deployed and configured.

## Pre-Deployment

- [ ] Google Cloud Project created
- [ ] Billing enabled on the project
- [ ] `gcloud` CLI installed and updated
- [ ] Authenticated with gcloud (`gcloud auth login`)
- [ ] Project set (`gcloud config set project YOUR_PROJECT_ID`)
- [ ] Sufficient IAM permissions (Editor role minimum)

## Deployment

- [ ] Cloned/downloaded the project repository
- [ ] Navigated to project root directory
- [ ] Made setup script executable (`chmod +x setup.sh`)
- [ ] Ran deployment script (`./setup.sh`)
- [ ] Waited for Cloud Run deployment to complete (2-3 minutes)
- [ ] Deployment completed without errors

## Post-Deployment Verification

### Cloud Run Service
- [ ] Service deployed: `gcloud run services describe doc-processor-service --region us-central1`
- [ ] Service URL is accessible (check Cloud Console)
- [ ] Authentication is enabled (--no-allow-unauthenticated is set)

### Cloud Storage Bucket
- [ ] Bucket created: `gsutil ls`
- [ ] Bucket name follows pattern: `{PROJECT_ID}-docs-ingest`
- [ ] Public access prevention is enabled

### BigQuery
- [ ] Dataset created: `bq ls`
- [ ] Dataset name is `docs_metadata`
- [ ] Table created: `bq ls docs_metadata`
- [ ] Table name is `processed_docs`
- [ ] Schema has 6 columns: filename, processed_at, tags, word_count, bucket, file_size

### Pub/Sub
- [ ] Topic created: `gcloud pubsub topics list`
- [ ] Topic name is `docs-upload-topic`
- [ ] Subscription created: `gcloud pubsub subscriptions list`
- [ ] Subscription name is `docs-upload-topic-sub`
- [ ] Push endpoint points to Cloud Run URL
- [ ] Push authentication service account is configured

### Service Accounts & IAM
- [ ] Cloud Run service account created: `doc-processor-sa`
- [ ] Pub/Sub invoker service account created: `pubsub-invoker-sa`
- [ ] Cloud Run SA has roles:
  - [ ] `roles/storage.objectViewer` (read GCS objects)
  - [ ] `roles/bigquery.dataEditor` (insert rows)
  - [ ] `roles/bigquery.user` (use BigQuery)
- [ ] Pub/Sub SA has `roles/run.invoker`
- [ ] GCS system SA has `roles/pubsub.publisher`

### GCS Notifications
- [ ] Pub/Sub notification created on bucket
- [ ] Notification points to correct topic
- [ ] Event type is `OBJECT_FINALIZE`

## Functionality Testing

### Local Testing
- [ ] Ran local tests: `./test_local.sh`
- [ ] Message parsing tests passed
- [ ] Invalid message handling works

### Cloud Testing
- [ ] Ran cloud tests: `./test_cloud.sh`
- [ ] Test files uploaded successfully
- [ ] Files appeared in GCS bucket
- [ ] Files processed by Cloud Run (check logs)
- [ ] Metadata recorded in BigQuery
- [ ] Word counts are correct
- [ ] Tags are properly assigned

### Manual Testing
- [ ] Created and uploaded a test file manually
- [ ] File appeared in BigQuery within 2 minutes
- [ ] Metadata is complete and correct

## Monitoring Setup

- [ ] Reviewed Cloud Run logs: `gcloud run logs read doc-processor-service --region us-central1`
- [ ] Understand how to check logs in real-time: `gcloud alpha run logs tail ...`
- [ ] Verified BigQuery data quality
- [ ] Set up alerts (optional) in Cloud Console

## Documentation Review

- [ ] Read README.md for full documentation
- [ ] Understood the architecture and data flow
- [ ] Reviewed the application code (app/main.py)
- [ ] Understood BigQuery schema
- [ ] Reviewed supported keywords for tagging

## Configuration Review

- [ ] Noted your bucket name: `_________________`
- [ ] Noted your BigQuery dataset: `docs_metadata`
- [ ] Noted your Cloud Run region: `us-central1`
- [ ] Reviewed keyword tags in main.py
- [ ] Considered any custom configuration needed

## Ready for Production?

If all above items are checked, your pipeline is ready. However, consider:

### Before Production Use

- [ ] Have you tested with actual document types you'll process?
- [ ] Do you need to add custom keywords for your domain?
- [ ] Should you implement real OCR (Vision API) instead of simulated?
- [ ] Do you need to store original files longer term?
- [ ] Have you reviewed costs for your expected volume?
- [ ] Do you have appropriate backups for BigQuery data?
- [ ] Have you set up monitoring/alerting for failures?

### Optional Enhancements

- [ ] Integrate Vision API for real OCR
- [ ] Add error notification (email via Cloud Tasks)
- [ ] Implement document classification beyond keywords
- [ ] Add metadata enrichment (user info, context, etc.)
- [ ] Set up scheduled exports to other systems
- [ ] Implement data retention policies
- [ ] Add custom metrics to Cloud Monitoring
- [ ] Create dashboards in Looker Studio

## Ongoing Operations

### Daily Checks
- [ ] Monitor Cloud Run logs for errors
- [ ] Check BigQuery data volume and quality
- [ ] Verify no backlog in Pub/Sub

### Weekly Checks
- [ ] Review error rates in Cloud Logging
- [ ] Check storage bucket usage
- [ ] Query BigQuery for data insights
- [ ] Review costs in Google Cloud Billing

### Monthly Reviews
- [ ] Analyze document processing patterns
- [ ] Review and optimize keywords
- [ ] Check for performance improvements
- [ ] Plan any enhancements or scaling

## Cleanup (If Needed)

When ready to remove everything:

```bash
make cleanup
# or
./setup.sh  # Note: There's no automated cleanup in setup.sh currently
# or manually via Cloud Console
```

Checklist for cleanup:
- [ ] Deleted Cloud Run service
- [ ] Deleted Pub/Sub topic and subscriptions
- [ ] Deleted BigQuery dataset
- [ ] Deleted Cloud Storage bucket
- [ ] Deleted service accounts
- [ ] Verified all resources are gone in Cloud Console
- [ ] Disabled GCP APIs (optional)

## Support Resources

If you encounter issues:

1. **Check logs**: `gcloud run logs read doc-processor-service --region us-central1 --limit 50`
2. **Read README.md**: Full documentation and troubleshooting guide
3. **GCP Documentation**: 
   - Cloud Run: https://cloud.google.com/run/docs
   - Pub/Sub: https://cloud.google.com/pubsub/docs
   - BigQuery: https://cloud.google.com/bigquery/docs
   - Cloud Storage: https://cloud.google.com/storage/docs

---

**Deployment Date**: _______________

**Project ID**: _______________

**Notes**:
```
_________________________________________________________________

_________________________________________________________________

_________________________________________________________________
```
