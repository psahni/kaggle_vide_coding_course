"""Google Cloud Storage helper functions."""

import logging
from google.cloud import storage

logger = logging.getLogger(__name__)

storage_client = storage.Client()


def download_file_content(bucket_name: str, object_name: str) -> str:
    """
    Download and read content from a GCS file.

    Args:
        bucket_name: Name of the GCS bucket
        object_name: Path to the object in the bucket

    Returns:
        File content as string

    Raises:
        Exception: If file cannot be read
    """
    try:
        logger.info(f"Downloading file from gs://{bucket_name}/{object_name}")
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(object_name)
        content = blob.download_as_text()
        logger.info(f"Successfully downloaded {len(content)} bytes")
        return content
    except Exception as e:
        logger.error(f"Failed to download file: {e}")
        raise


def get_file_metadata(bucket_name: str, object_name: str) -> dict:
    """
    Get metadata about a GCS file.

    Args:
        bucket_name: Name of the GCS bucket
        object_name: Path to the object in the bucket

    Returns:
        Dictionary with file metadata (size, content_type, etc.)
    """
    try:
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(object_name)
        blob.reload()

        return {
            "size": blob.size,
            "content_type": blob.content_type,
            "created": blob.time_created,
            "updated": blob.updated
        }
    except Exception as e:
        logger.error(f"Failed to get file metadata: {e}")
        raise
