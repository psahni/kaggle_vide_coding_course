import re
import html
from datetime import datetime

import feedparser
import requests
from flask import Flask, jsonify, render_template
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

BQ_FEED_URL = "https://docs.cloud.google.com/feeds/bigquery-release-notes.xml"


def clean_html(raw_html: str) -> str:
    """Strip HTML tags and decode entities for plain-text tweet content."""
    text = re.sub(r"<[^>]+>", " ", raw_html or "")
    text = html.unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def parse_feed() -> list[dict]:
    """Fetch and parse the BigQuery Atom/RSS feed, returning a list of entries."""
    try:
        response = requests.get(BQ_FEED_URL, timeout=15)
        response.raise_for_status()
    except requests.RequestException as exc:
        raise RuntimeError(f"Failed to fetch feed: {exc}") from exc

    feed = feedparser.parse(response.content)

    entries: list[dict] = []
    for entry in feed.entries:
        raw_summary = getattr(entry, "summary", "") or ""
        plain_summary = clean_html(raw_summary)

        # Parse published / updated date
        pub = getattr(entry, "published_parsed", None) or getattr(
            entry, "updated_parsed", None
        )
        if pub:
            pub_str = datetime(*pub[:6]).strftime("%B %d, %Y")
        else:
            pub_str = "Unknown date"

        entries.append(
            {
                "id": getattr(entry, "id", ""),
                "title": getattr(entry, "title", "No title"),
                "published": pub_str,
                "link": getattr(entry, "link", "#"),
                "summary_html": raw_summary,
                "summary_plain": plain_summary,
            }
        )

    return entries


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/release-notes")
def release_notes():
    try:
        entries = parse_feed()
        return jsonify({"success": True, "entries": entries, "count": len(entries)})
    except RuntimeError as exc:
        return jsonify({"success": False, "error": str(exc)}), 500


if __name__ == "__main__":
    app.run(debug=True, port=5000)
