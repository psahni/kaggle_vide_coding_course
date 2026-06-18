import sys
import os
from pathlib import Path

# Set UTF-8 encoding for output
os.environ['PYTHONIOENCODING'] = 'utf-8'

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / "app" / "src"))

# Test core processor module (no GCP dependencies)
from processor import (
    extract_text_from_file,
    count_words,
    extract_tags,
    KEYWORD_TAGS
)


def test_word_count():
    """Test word counting."""
    text = "This is a test document with ten words in this sentence"
    count = count_words(text)
    assert count == 11, f"Expected 11 words, got {count}"
    print("[PASS] Word count test passed")


def test_extract_tags_with_keywords():
    """Test tag extraction with keywords."""
    text = "This is an invoice document with payment information"
    tags = extract_tags(text)
    assert "invoice" in tags, f"Expected 'invoice' in {tags}"
    assert "payment" in tags, f"Expected 'payment' in {tags}"
    print("[PASS] Tag extraction test passed")


def test_extract_tags_unclassified():
    """Test tag extraction without keywords."""
    text = "This is a random document with no matching keywords"
    tags = extract_tags(text)
    assert "unclassified" in tags, f"Expected 'unclassified' in {tags}"
    print("[PASS] Unclassified tag test passed")


def test_extract_text_from_text_file():
    """Test text extraction from actual text file."""
    filename = "test.txt"
    content = "Hello World Test Content"
    result = extract_text_from_file(filename, content, is_text_file=True)
    assert result == content, "Text file content should be returned as-is"
    print("[PASS] Text file extraction test passed")


def test_extract_text_from_binary_file():
    """Test simulated OCR for binary files."""
    filename = "invoice_001.pdf"
    result = extract_text_from_file(filename, "", is_text_file=False)
    assert "invoice" in result.lower(), "Invoice keyword should be in OCR text"
    assert "simulated OCR" in result, "Should indicate simulated OCR"
    print("[PASS] Binary file OCR simulation test passed")


def test_all_keywords_present():
    """Test that all keywords are properly defined."""
    expected_keywords = [
        "invoice", "receipt", "report", "payment", "statement",
        "logistics", "shipping", "contract", "resume", "memo"
    ]
    for keyword in expected_keywords:
        assert keyword in KEYWORD_TAGS, f"Missing keyword: {keyword}"
    print(f"[PASS] All {len(KEYWORD_TAGS)} keywords are defined")


def test_multiple_tags():
    """Test extracting multiple tags from same text."""
    text = "This invoice is a shipping report with payment statement details"
    tags = extract_tags(text)
    assert len(tags) >= 3, f"Expected at least 3 tags, got {len(tags)}"
    assert "invoice" in tags
    assert "shipping" in tags
    assert "report" in tags
    print("[PASS] Multiple tags extraction test passed")


def test_case_insensitivity():
    """Test that tag matching is case-insensitive."""
    text = "This is an INVOICE with PAYMENT info"
    tags = extract_tags(text)
    assert "invoice" in tags, "Tags should match case-insensitive"
    assert "payment" in tags, "Tags should match case-insensitive"
    print("[PASS] Case insensitivity test passed")


if __name__ == "__main__":
    try:
        print("\n" + "=" * 60)
        print("Testing Processor Module")
        print("=" * 60)
        test_word_count()
        test_extract_tags_with_keywords()
        test_extract_tags_unclassified()
        test_extract_text_from_text_file()
        test_extract_text_from_binary_file()
        test_all_keywords_present()
        test_multiple_tags()
        test_case_insensitivity()

        print("\n" + "=" * 60)
        print("SUCCESS: All processor tests passed!")
        print("=" * 60)
    except AssertionError as e:
        print(f"\nFAILED: Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\nFAILED: Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
