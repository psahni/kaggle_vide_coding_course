import sys
import json
import base64
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / "app" / "src"))

# Test imports
try:
    from processor import (
        extract_text_from_file,
        count_words,
        extract_tags,
        process_document,
        KEYWORD_TAGS
    )
    from gcs_helper import download_file_content, get_file_metadata
    from bq_helper import insert_metadata_row, insert_multiple_rows
    print("✓ All modules imported successfully")
except ImportError as e:
    print(f"✗ Import failed: {e}")
    sys.exit(1)


class TestProcessor:
    """Test the processor module."""

    def test_word_count(self):
        """Test word counting."""
        text = "This is a test document with ten words in this sentence"
        count = count_words(text)
        assert count == 11, f"Expected 11 words, got {count}"
        print("✓ Word count test passed")

    def test_extract_tags_with_keywords(self):
        """Test tag extraction with keywords."""
        text = "This is an invoice document with payment information"
        tags = extract_tags(text)
        assert "invoice" in tags, f"Expected 'invoice' in {tags}"
        assert "payment" in tags, f"Expected 'payment' in {tags}"
        print("✓ Tag extraction test passed")

    def test_extract_tags_unclassified(self):
        """Test tag extraction without keywords."""
        text = "This is a random document with no matching keywords"
        tags = extract_tags(text)
        assert "unclassified" in tags, f"Expected 'unclassified' in {tags}"
        print("✓ Unclassified tag test passed")

    def test_extract_text_from_text_file(self):
        """Test text extraction from actual text file."""
        filename = "test.txt"
        content = "Hello World Test Content"
        result = extract_text_from_file(filename, content, is_text_file=True)
        assert result == content, "Text file content should be returned as-is"
        print("✓ Text file extraction test passed")

    def test_extract_text_from_binary_file(self):
        """Test simulated OCR for binary files."""
        filename = "invoice_001.pdf"
        result = extract_text_from_file(filename, "", is_text_file=False)
        assert "invoice" in result.lower(), "Invoice keyword should be in OCR text"
        assert "simulated OCR" in result, "Should indicate simulated OCR"
        print("✓ Binary file OCR simulation test passed")

    def test_process_document(self):
        """Test complete document processing."""
        metadata = process_document(
            filename="test_invoice.txt",
            file_content="This is a test invoice document with payment details",
            bucket_name="test-bucket",
            file_size=1024,
            is_text_file=True
        )

        assert metadata["filename"] == "test_invoice.txt"
        assert metadata["bucket"] == "test-bucket"
        assert metadata["file_size"] == 1024
        assert metadata["word_count"] > 0
        assert "invoice" in metadata["tags"]
        assert "processed_at" in metadata
        print("✓ Document processing test passed")


class TestFlaskApp:
    """Test the Flask application."""

    def test_invalid_message(self):
        """Test handling of invalid Pub/Sub message."""
        from app import app

        with app.test_client() as client:
            response = client.post(
                "/",
                json={"invalid": "data"},
                content_type="application/json"
            )
            assert response.status_code == 400, f"Expected 400, got {response.status_code}"
            print("✓ Invalid message handling test passed")

    def test_missing_message_data(self):
        """Test handling of message without data."""
        from app import app

        with app.test_client() as client:
            response = client.post(
                "/",
                json={"message": {}},
                content_type="application/json"
            )
            assert response.status_code == 204, f"Expected 204, got {response.status_code}"
            print("✓ Missing data handling test passed")

    def test_folder_placeholder_skip(self):
        """Test skipping folder placeholders."""
        from app import app

        gcs_event = {
            "bucket": "test-bucket",
            "name": "some-folder/",
            "size": "0",
            "contentType": ""
        }

        pubsub_message = {
            "message": {
                "data": base64.b64encode(json.dumps(gcs_event).encode()).decode()
            }
        }

        with app.test_client() as client:
            response = client.post(
                "/",
                json=pubsub_message,
                content_type="application/json"
            )
            assert response.status_code == 204, f"Expected 204 for folder, got {response.status_code}"
            print("✓ Folder placeholder skip test passed")

    def test_health_check(self):
        """Test health check endpoint."""
        from app import app

        with app.test_client() as client:
            response = client.get("/health")
            assert response.status_code == 200
            data = response.get_json()
            assert data["status"] == "healthy"
            print("✓ Health check test passed")


def run_tests():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("Testing Processor Module")
    print("=" * 60)
    processor_tests = TestProcessor()
    processor_tests.test_word_count()
    processor_tests.test_extract_tags_with_keywords()
    processor_tests.test_extract_tags_unclassified()
    processor_tests.test_extract_text_from_text_file()
    processor_tests.test_extract_text_from_binary_file()
    processor_tests.test_process_document()

    print("\n" + "=" * 60)
    print("Testing Flask Application")
    print("=" * 60)
    app_tests = TestFlaskApp()
    app_tests.test_invalid_message()
    app_tests.test_missing_message_data()
    app_tests.test_folder_placeholder_skip()
    app_tests.test_health_check()

    print("\n" + "=" * 60)
    print("Testing Helper Modules (Mock)")
    print("=" * 60)
    print("ℹ gcs_helper and bq_helper require GCP credentials")
    print("ℹ Full E2E tests available with test_cloud.sh")
    print("✓ Helper modules imported successfully")


if __name__ == "__main__":
    try:
        run_tests()
        print("\n" + "=" * 60)
        print("✓ All tests passed!")
        print("=" * 60)
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
