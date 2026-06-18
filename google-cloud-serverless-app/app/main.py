import os
import base64
import json
import logging
from datetime import datetime
from flask import Flask, request, jsonify
from google.cloud import storage
from google.cloud import bigquery

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Initialize clients (they will use the service account credentials when running in Cloud Run)
storage_client = storage.Client()
bigquery_client = bigquery.Client()

# Configuration from environment variables
DATASET_ID = os.environ.get("BQ_DATASET", "docs_metadata")
TABLE_ID = os.environ.get("BQ_TABLE", "processed_docs")

# Dictionary of keywords to search in text to generate tags
KEYWORD_TAGS = {
    "invoice": "invoice",
    "receipt": "receipt",
    "report": "report",
    "payment": "payment",
    "statement": "statement",
    "logistics": "logistics",
    "shipping": "shipping",
    "contract": "contract",
    "resume": "resume",
    "memo": "memo"
}

@app.route("/", methods=["POST"])
def process_event():
    """
    Receives Pub/Sub push messages containing Cloud Storage event notifications.
    """
    envelope = request.get_json()
    if not envelope:
        msg = "No Pub/Sub message received"
        logger.error(msg)
        return jsonify({"error": msg}), 400

    if not isinstance(envelope, dict) or "message" not in envelope:
        msg = "Invalid Pub/Sub message format"
        logger.error(msg)
        return jsonify({"error": msg}), 400

    pubsub_message = envelope["message"]
    
    # Check for base64 encoded data
    if "data" not in pubsub_message:
        logger.info("Pub/Sub message contains no data payload. Skipping.")
        return "", 204

    try:
        # Decode the pubsub message data payload
        data_bytes = base64.b64decode(pubsub_message["data"])
        data_str = data_bytes.decode("utf-8")
        event_data = json.loads(data_str)
        logger.info(f"Received GCS Event Data: {json.dumps(event_data)}")
    except Exception as e:
        logger.error(f"Failed to decode or parse Pub/Sub message data: {e}")
        # Acknowledge the message to avoid continuous retries of invalid data format
        return "", 204

    # Extract bucket and object details
    # The GCS event payload details: https://cloud.google.com/storage/docs/pubsub-notifications#payload
    bucket_name = event_data.get("bucket")
    object_name = event_data.get("name")
    
    if not bucket_name or not object_name:
        # Check if it's a test notification
        kind = event_data.get("kind")
        if kind == "storage#notification" or not object_name:
            logger.info("Received a test or storage notification setup event. Acknowledging.")
            return "", 204
        logger.error("Missing bucket or object name in GCS event data.")
        return "", 204

    # Skip directory placeholder objects (usually ends with '/')
    if object_name.endswith("/"):
        logger.info(f"Skipping folder placeholder object: {object_name}")
        return "", 204

    logger.info(f"Processing file: gs://{bucket_name}/{object_name}")

    try:
        file_size = int(event_data.get("size", 0))
        content_type = event_data.get("contentType", "")
        
        # 1. OCR Simulation / Extraction
        text = ""
        is_txt_file = object_name.lower().endswith(".txt") or content_type == "text/plain"

        if is_txt_file:
            # Download and read text file directly
            logger.info(f"Reading text file content from GCS: gs://{bucket_name}/{object_name}")
            bucket = storage_client.bucket(bucket_name)
            blob = bucket.blob(object_name)
            text = blob.download_as_text()
        else:
            # Mock OCR processing for PDFs, images, etc.
            logger.info(f"Simulating OCR for non-text file: gs://{bucket_name}/{object_name}")
            # Generate mock text based on the file name/type
            file_ext = object_name.split(".")[-1].lower() if "." in object_name else "unknown"
            
            # Formulate mock OCR text containing keywords dynamically based on filename
            object_name_lower = object_name.lower()
            mock_keywords = []
            for kw in KEYWORD_TAGS.keys():
                if kw in object_name_lower:
                    mock_keywords.append(kw)
            
            if not mock_keywords:
                mock_keywords = ["report", "statement"] # default mock text context
                
            text = f"This is a simulated OCR text extracted from the document {object_name}. " \
                   f"The content refers to details of: {', '.join(mock_keywords)}. " \
                   f"The file type is {file_ext} and has size {file_size} bytes."

        # 2. Extract Metadata
        # Calculate word count
        word_count = len(text.split())
        
        # Scan text for tags
        tags = []
        text_lower = text.lower()
        for keyword, tag in KEYWORD_TAGS.items():
            if keyword in text_lower:
                tags.append(tag)
        
        if not tags:
            tags.append("unclassified")

        logger.info(f"Extracted metadata: word_count={word_count}, tags={tags}")

        # 3. Stream Metadata to BigQuery
        # Construct row
        row = {
            "filename": object_name,
            "processed_at": datetime.utcnow().isoformat() + "Z",
            "tags": tags,
            "word_count": word_count,
            "bucket": bucket_name,
            "file_size": file_size
        }

        # Insert into BigQuery table
        # We construct the fully qualified table name
        project = bigquery_client.project
        table_ref = f"{project}.{DATASET_ID}.{TABLE_ID}"
        
        logger.info(f"Streaming metadata to BigQuery table {table_ref}...")
        errors = bigquery_client.insert_rows_json(table_ref, [row])
        
        if errors:
            logger.error(f"Failed to insert row into BigQuery: {errors}")
            # Return 500 so Pub/Sub retries the event if it was a temporary DB issue
            return jsonify({"error": "BigQuery insertion failed", "details": errors}), 500
            
        logger.info(f"Successfully processed gs://{bucket_name}/{object_name} and recorded metadata.")
        return jsonify({"status": "success", "processed_file": object_name}), 200

    except Exception as e:
        logger.error(f"Error processing document: {e}", exc_info=True)
        # Return 500 for general exceptions to let Pub/Sub retry
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    # Get port from environment or default to 8080
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)
