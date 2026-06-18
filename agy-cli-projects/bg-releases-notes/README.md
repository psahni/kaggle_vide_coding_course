# BigQuery Release Notes Viewer

A lightweight internal tool that pulls the live **Google BigQuery Atom/RSS feed** and presents it in a polished dark-mode web UI — with category filtering, card expand/collapse, and one-click sharing to **X (Twitter)**.

![Stack](https://img.shields.io/badge/stack-Python%20%7C%20Flask%20%7C%20Vanilla%20JS-blue)
![License](https://img.shields.io/badge/license-MIT-green)

---

## ✨ Features

| Feature | Description |
|---|---|
| 🔄 **Live Feed Refresh** | Fetches release notes on demand from Google Cloud with a loading spinner and shimmer skeleton cards |
| 🏷️ **Auto Category Badges** | Each card is tagged automatically — *New Feature*, *Changed*, *Fixed*, *Deprecated*, or *Update* — via keyword matching |
| 🔍 **Client-side Filtering** | Filter chips (All / New Feature / Changed / Fixed / Deprecated) narrow the list instantly with no extra network call |
| 📖 **Card Expand / Collapse** | Cards clip long content to 120px; "Read more" animates them open smoothly |
| 🐦 **Share on X (Twitter)** | A modal pre-composes a 280-character tweet from the card title, summary, and hashtags — opens Twitter Web Intent in a popup |

---

## 🗂️ Project Structure

```
bg-releases-notes/
├── app.py               # Flask server — feed fetching, parsing, API routes
├── requirements.txt     # Python dependencies
├── README.md            # This file
└── templates/
    └── index.html       # Single-page frontend (inline CSS + HTML + JS)
```

---

## 🚀 Quick Start

### 1. Clone / navigate to the project

```bash
cd bg-releases-notes
```

### 2. Create and activate a virtual environment *(recommended)*

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the development server

```bash
python app.py
```

Open your browser at **[http://127.0.0.1:5000](http://127.0.0.1:5000)**

---

## 🧰 Tech Stack

| Layer | Technology |
|---|---|
| **Backend** | Python 3.10+ · Flask 3.x |
| **Feed parsing** | `feedparser` 6.x |
| **HTTP client** | `requests` 2.x |
| **CORS** | `flask-cors` 4.x |
| **Frontend** | Vanilla HTML · CSS · JavaScript (no framework) |
| **Font** | [Inter](https://fonts.google.com/specimen/Inter) via Google Fonts |
| **Data source** | [Google Cloud BigQuery Release Notes feed](https://docs.cloud.google.com/feeds/bigquery-release-notes.xml) |

---

## ⚙️ How It Works

```
Browser                      Flask (app.py)             Google Cloud
   │                              │                           │
   │── GET / ───────────────────▶│                           │
   │◀─ index.html ───────────────│                           │
   │                              │                           │
   │── GET /api/release-notes ──▶│                           │
   │                              │── GET Atom/RSS XML ──────▶│
   │                              │◀─ XML response ───────────│
   │                              │  feedparser.parse()       │
   │                              │  clean_html() per entry   │
   │◀─ JSON {success, entries} ──│                           │
   │  renderNotes() → DOM cards   │                           │
```

1. **Server** fetches the public Atom/RSS feed from Google Cloud (acts as a CORS proxy).
2. Each entry is parsed into a structured dict containing both `summary_html` (for rich card display) and `summary_plain` (for tweet composition and badge detection).
3. **Client** receives JSON and renders interactive cards entirely in the browser.
4. Filter chips and card expand/collapse work **client-side only** — no additional network requests.

---

## 🔌 API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Serves the main single-page UI |
| `GET` | `/api/release-notes` | Returns parsed release notes as JSON |

### `/api/release-notes` — Success Response

```json
{
  "success": true,
  "count": 47,
  "entries": [
    {
      "id":            "tag:google.com,...",
      "title":         "BigQuery Omni: cross-cloud joins GA",
      "published":     "June 17, 2026",
      "link":          "https://cloud.google.com/bigquery/docs/...",
      "summary_html":  "<p>Cross-cloud joins are now <strong>GA</strong>...</p>",
      "summary_plain": "Cross-cloud joins are now GA..."
    }
  ]
}
```

### `/api/release-notes` — Error Response

```json
{
  "success": false,
  "error": "Failed to fetch feed: ..."
}
```

---

## 🗺️ UI Sections

| Section | Element | Description |
|---|---|---|
| Header | `<header>` | Logo badge + gradient title + subtitle |
| Controls | `.controls-bar` | Entry count, last-updated time, Refresh button |
| Filter chips | `#filterRow` | Category tabs — hidden until first load |
| Error banner | `#errorBanner` | Red alert on API failure |
| Skeleton loaders | `#skeletonList` | Shimmer placeholders during fetch |
| Notes list | `#notesList` | Dynamically rendered `<article>` cards |
| Empty state | `#emptyState` | Shown when a filter returns zero results |
| Tweet modal | `#tweetModal` | Overlay for composing and posting a tweet |

---

## 🏷️ Badge Detection Logic

Badges are assigned by running a regex over each entry's title and plain-text summary:

| Badge | Keywords matched |
|---|---|
| 🟢 **New Feature** | `new feature`, `new release` |
| 🔵 **Changed** | `changed`, `updated`, `modified` |
| 🟣 **Fixed** | `fixed`, `fix`, `bug fix`, `patch` |
| 🟡 **Deprecated** | `deprecated`, `deprecation` |
| ⚪ **Update** | *(fallback for everything else)* |

---

## ♿ Accessibility

- `lang="en"` on `<html>` for screen-reader language detection
- Tweet modal uses `role="dialog"`, `aria-modal="true"`, `aria-labelledby`
- Cards use `<article role="listitem">` with `<h2>` heading hierarchy
- Expand buttons carry dynamic `aria-expanded` state
- `escapeHtml()` prevents XSS on all user-facing strings injected into the DOM

---

## ⚠️ Known Limitations

| # | Limitation | Potential Fix |
|---|---|---|
| 1 | No server-side caching — feed fetched on every request | Add `functools.lru_cache` or a Redis TTL cache (5–15 min) |
| 2 | No pagination | Add virtual scrolling or page-based navigation |
| 3 | Badge detection is keyword-based | Use structured feed categories if Google exposes them |
| 4 | Twitter sharing uses Web Intent (no direct post) | Upgrade to Twitter API v2 for true programmatic posting |
| 5 | Single monolithic HTML file | Split into `static/style.css` + `static/app.js` for scale |

---

## 📦 Dependencies

```
flask>=3.0.0
flask-cors>=4.0.0
feedparser>=6.0.11
requests>=2.31.0
```

---

## 📄 License

MIT — free to use, modify, and distribute.
