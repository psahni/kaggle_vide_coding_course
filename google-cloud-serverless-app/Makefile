.PHONY: help setup deploy test test-local test-cloud logs tail-logs status query cleanup

help:
	@echo "Event-Driven Document Processing Pipeline"
	@echo ""
	@echo "Available commands:"
	@echo "  make setup          - Deploy the entire pipeline to GCP"
	@echo "  make test-local     - Run local tests without GCP deployment"
	@echo "  make test-cloud     - Run cloud tests (upload files and verify processing)"
	@echo "  make deploy         - Redeploy Cloud Run service only"
	@echo "  make logs           - Show Cloud Run service logs"
	@echo "  make tail-logs      - Follow Cloud Run service logs in real-time"
	@echo "  make status         - Check service status"
	@echo "  make query          - Run a BigQuery query (interactive)"
	@echo "  make cleanup        - Delete all GCP resources (DESTRUCTIVE)"

setup:
	@echo "Setting up event-driven document processing pipeline..."
	@chmod +x setup.sh
	@./setup.sh

deploy:
	@echo "Redeploying Cloud Run service..."
	@gcloud run deploy doc-processor-service \
		--source ./app \
		--region us-central1 \
		--no-allow-unauthenticated

test-local:
	@echo "Running local tests..."
	@chmod +x test_local.sh
	@./test_local.sh

test-cloud:
	@echo "Running cloud tests..."
	@chmod +x test_cloud.sh
	@./test_cloud.sh

logs:
	@PROJECT_ID=$$(gcloud config get-value project); \
	echo "Fetching logs for last 50 entries..."; \
	gcloud run logs read doc-processor-service --region us-central1 --limit 50

tail-logs:
	@PROJECT_ID=$$(gcloud config get-value project); \
	echo "Tailing logs (Ctrl+C to exit)..."; \
	gcloud alpha run logs tail doc-processor-service --region us-central1 --follow

status:
	@PROJECT_ID=$$(gcloud config get-value project); \
	BUCKET_NAME="$${PROJECT_ID}-docs-ingest"; \
	echo "=== Service Status ==="; \
	gcloud run services describe doc-processor-service --region us-central1 | grep -E "url|status"; \
	echo ""; \
	echo "=== Storage Bucket ==="; \
	echo "gs://$${BUCKET_NAME}"; \
	gcloud storage buckets describe "gs://$${BUCKET_NAME}" 2>/dev/null | grep -E "name|timeCreated" || echo "Bucket not found"; \
	echo ""; \
	echo "=== BigQuery Table ==="; \
	bq ls -t "$${PROJECT_ID}:docs_metadata" 2>/dev/null | grep processed_docs || echo "Table not found"; \
	echo ""; \
	echo "=== Pub/Sub Status ==="; \
	gcloud pubsub subscriptions describe docs-upload-topic-sub | grep -E "name|topic|expirationPolicy" || echo "Subscription not found"

query:
	@PROJECT_ID=$$(gcloud config get-value project); \
	echo "Running BigQuery query..."; \
	bq query --use_legacy_sql=false \
		"SELECT filename, processed_at, word_count, ARRAY_LENGTH(tags) as tag_count FROM \`$${PROJECT_ID}.docs_metadata.processed_docs\` ORDER BY processed_at DESC LIMIT 20"

cleanup:
	@echo "WARNING: This will delete all GCP resources created by this pipeline."
	@echo "This action cannot be undone!"
	@read -p "Are you sure? Type 'yes' to confirm: " confirm; \
	if [ "$$confirm" = "yes" ]; then \
		PROJECT_ID=$$(gcloud config get-value project); \
		echo "Deleting resources..."; \
		gcloud run services delete doc-processor-service --region us-central1 --quiet 2>/dev/null || true; \
		gcloud pubsub subscriptions delete docs-upload-topic-sub --quiet 2>/dev/null || true; \
		gcloud pubsub topics delete docs-upload-topic --quiet 2>/dev/null || true; \
		bq rm --recursive --dataset --force "$${PROJECT_ID}:docs_metadata" 2>/dev/null || true; \
		gsutil -m rm -r "gs://$${PROJECT_ID}-docs-ingest" 2>/dev/null || true; \
		gcloud iam service-accounts delete "doc-processor-sa@$${PROJECT_ID}.iam.gserviceaccount.com" --quiet 2>/dev/null || true; \
		gcloud iam service-accounts delete "pubsub-invoker-sa@$${PROJECT_ID}.iam.gserviceaccount.com" --quiet 2>/dev/null || true; \
		echo "Cleanup complete."; \
	else \
		echo "Cleanup cancelled."; \
	fi
