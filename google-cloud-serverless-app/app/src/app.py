"""Flask application for document processing."""

import os
import base64
import json
import logging
from flask import Flask, request, jsonify

from gcs_helper import download_file_content
from bq_helper import insert_metadata_row
from processor import process_document

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configuration from environment variables
DATASET_ID = os.environ.get("BQ_DATASET", "docs_metadata")
TABLE_ID = os.environ.get("BQ_TABLE", "processed_docs")


@app.route("/", methods=["POST"])
def process_event():
    """
    Receive and process Pub/Sub push messages containing GCS events.

    Expected message format:
    {
        "message": {
            "data": "base64-encoded-gcs-event-json"
        }
    }

    Returns:
        200: Successfully processed
        204: Message skipped (folder, test notification, etc.)
        400: Invalid message format
        500: Processing error
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
        # Decode the Pub/Sub message data payload
        data_bytes = base64.b64decode(pubsub_message["data"])
        data_str = data_bytes.decode("utf-8")
        event_data = json.loads(data_str)
        logger.info(f"Received GCS Event Data: {json.dumps(event_data)}")
    except Exception as e:
        logger.error(f"Failed to decode or parse Pub/Sub message data: {e}")
        return "", 204

    # Extract bucket and object details from GCS event
    bucket_name = event_data.get("bucket")
    object_name = event_data.get("name")

    if not bucket_name or not object_name:
        kind = event_data.get("kind")
        if kind == "storage#notification" or not object_name:
            logger.info("Received a test or storage notification setup event. Acknowledging.")
            return "", 204
        logger.error("Missing bucket or object name in GCS event data.")
        return "", 204

    # Skip directory placeholder objects
    if object_name.endswith("/"):
        logger.info(f"Skipping folder placeholder object: {object_name}")
        return "", 204

    logger.info(f"Processing file: gs://{bucket_name}/{object_name}")

    try:
        file_size = int(event_data.get("size", 0))
        content_type = event_data.get("contentType", "")
        is_text_file = (
            object_name.lower().endswith(".txt") or
            content_type == "text/plain"
        )

        # Download file content
        if is_text_file:
            logger.info(f"Reading text file: gs://{bucket_name}/{object_name}")
            file_content = download_file_content(bucket_name, object_name)
        else:
            logger.info(f"Binary file detected: gs://{bucket_name}/{object_name}")
            file_content = ""  # Will be simulated in processor

        # Process document and extract metadata
        metadata = process_document(
            filename=object_name,
            file_content=file_content,
            bucket_name=bucket_name,
            file_size=file_size,
            is_text_file=is_text_file
        )

        # Stream metadata to BigQuery
        success = insert_metadata_row(DATASET_ID, TABLE_ID, metadata)

        if not success:
            logger.error("Failed to insert metadata into BigQuery")
            return jsonify({"error": "BigQuery insertion failed"}), 500

        logger.info(
            f"Successfully processed gs://{bucket_name}/{object_name} "
            f"and recorded metadata"
        )
        return jsonify({"status": "success", "processed_file": object_name}), 200

    except Exception as e:
        logger.error(f"Error processing document: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint."""
    return jsonify({"status": "healthy"}), 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)
