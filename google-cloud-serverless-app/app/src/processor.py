"""Document processing and metadata extraction logic."""

import logging
from datetime import datetime
from typing import List, Tuple

logger = logging.getLogger(__name__)

# Keywords to tags mapping for document classification
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


def extract_text_from_file(
    filename: str,
    file_content: str,
    is_text_file: bool
) -> str:
    """
    Extract or generate text from a file.

    For text files, returns the actual content.
    For binary files (PDF, images), generates simulated OCR text.

    Args:
        filename: Name of the file
        file_content: Content of the file (for text files)
        is_text_file: Whether this is a text file

    Returns:
        Extracted or simulated text content
    """
    if is_text_file:
        logger.info(f"Using actual text content from {filename}")
        return file_content
    else:
        logger.info(f"Generating simulated OCR text for {filename}")

        # For binary files, generate mock OCR text based on filename
        file_ext = filename.split(".")[-1].lower() if "." in filename else "unknown"
        filename_lower = filename.lower()

        # Extract keywords from filename
        mock_keywords = []
        for keyword in KEYWORD_TAGS.keys():
            if keyword in filename_lower:
                mock_keywords.append(keyword)

        if not mock_keywords:
            mock_keywords = ["report", "statement"]

        mock_text = (
            f"This is a simulated OCR text extracted from the document {filename}. "
            f"The content refers to details of: {', '.join(mock_keywords)}. "
            f"The file type is {file_ext}."
        )

        return mock_text


def count_words(text: str) -> int:
    """
    Count the number of words in the text.

    Args:
        text: The text to count words in

    Returns:
        Number of words
    """
    word_count = len(text.split())
    logger.debug(f"Calculated word count: {word_count}")
    return word_count


def extract_tags(text: str) -> List[str]:
    """
    Extract tags from text based on keyword matching.

    Args:
        text: The text to analyze

    Returns:
        List of tags (at least one, may be 'unclassified')
    """
    tags = []
    text_lower = text.lower()

    for keyword, tag in KEYWORD_TAGS.items():
        if keyword in text_lower:
            tags.append(tag)

    if not tags:
        tags.append("unclassified")

    # Remove duplicates while preserving order
    tags = list(dict.fromkeys(tags))

    logger.info(f"Extracted tags: {tags}")
    return tags


def process_document(
    filename: str,
    file_content: str,
    bucket_name: str,
    file_size: int,
    is_text_file: bool
) -> dict:
    """
    Process a document and extract all metadata.

    Args:
        filename: Name of the document file
        file_content: Content of the document
        bucket_name: GCS bucket name
        file_size: File size in bytes
        is_text_file: Whether this is a text file

    Returns:
        Dictionary containing extracted metadata
    """
    logger.info(f"Processing document: {filename}")

    # Extract text (actual or simulated)
    text = extract_text_from_file(filename, file_content, is_text_file)

    # Extract metadata
    word_count = count_words(text)
    tags = extract_tags(text)

    # Create metadata row
    metadata = {
        "filename": filename,
        "processed_at": datetime.utcnow().isoformat() + "Z",
        "tags": tags,
        "word_count": word_count,
        "bucket": bucket_name,
        "file_size": file_size
    }

    logger.info(f"Document processing complete. Tags: {tags}, Words: {word_count}")
    return metadata
