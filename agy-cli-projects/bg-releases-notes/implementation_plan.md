# BigQuery Release Notes Viewer — Implementation Plan

A lightweight internal tool that pulls the live BigQuery Atom/RSS feed from Google Cloud and presents it in a polished, dark-mode web UI with one-click sharing to X (Twitter).

---

## Overview

| Attribute       | Value                                                                                |
|-----------------|--------------------------------------------------------------------------------------|
| **Project name**| `bg-releases-notes`                                                                  |
| **Stack**       | Python (Flask) · Vanilla HTML / CSS / JavaScript                                     |
| **Status**      | ✅ Running in production (local dev server)                                          |
| **Entry point** | `python app.py` → `http://127.0.0.1:5000`                                            |
| **Feed source** | `https://docs.cloud.google.com/feeds/bigquery-release-notes.xml`                     |

---

## Project Structure

```
bg-releases-notes/
├── app.py               # Flask server — feed fetching, parsing, API routes
├── requirements.txt     # Python dependencies
└── templates/
    └── index.html       # Single-page frontend (CSS + HTML + JS, inline)
```

---

## Backend — `app.py`

### Dependencies (`requirements.txt`)

| Package         | Version    | Role                                        |
|-----------------|------------|---------------------------------------------|
| `flask`         | ≥ 3.0.0    | Web framework — routing, template rendering |
| `flask-cors`    | ≥ 4.0.0    | CORS headers (safe for local dev)           |
| `feedparser`    | ≥ 6.0.11   | Atom/RSS feed parsing                       |
| `requests`      | ≥ 2.31.0   | HTTP client for fetching the feed URL       |

### Key Functions

#### `clean_html(raw_html: str) → str`
- **Purpose:** Strips HTML tags and decodes HTML entities to produce plain text suitable for tweets.
- **How it works:**
  1. `re.sub(r"<[^>]+>", " ", ...)` — replaces every HTML tag with a space.
  2. `html.unescape(...)` — decodes `&amp;`, `&#39;`, etc.
  3. `re.sub(r"\s+", " ", ...).strip()` — collapses whitespace.

#### `parse_feed() → list[dict]`
- **Purpose:** Fetches and parses the BigQuery Atom/RSS feed and returns structured entry objects.
- **Design decisions:**
  - Uses `requests.get` (not `feedparser.parse(url)` directly) to allow explicit `timeout=15` and proper `raise_for_status()` error handling.
  - Both `published_parsed` and `updated_parsed` are checked to handle feeds that use either field.
  - Returns both `summary_html` (for rich card rendering) and `summary_plain` (for tweet text + badge detection).
- **Error handling:** Wraps network errors in a `RuntimeError` so the API route can return a structured JSON error response.

#### Entry schema returned per item

```json
{
  "id":            "<unique feed entry ID>",
  "title":         "<release note title>",
  "published":     "June 17, 2026",
  "link":          "<URL to the official docs page>",
  "summary_html":  "<raw HTML from the feed>",
  "summary_plain": "<cleaned plain text>"
}
```

### API Routes

| Method | Path                  | Returns                                                      |
|--------|-----------------------|--------------------------------------------------------------|
| `GET`  | `/`                   | Renders `templates/index.html` via Jinja2                    |
| `GET`  | `/api/release-notes`  | JSON `{success, entries[], count}` or `{success, error}` 500 |

---

## Frontend — `templates/index.html`

The entire frontend is a single self-contained HTML file with inline `<style>` and `<script>` blocks. No build tools, no external JS frameworks.

### Design System (CSS Custom Properties)

```css
:root {
  --bg-base:       #080c14;   /* deep navy page background    */
  --bg-surface:    #0d1220;   /* modal surface                */
  --bg-card:       #111827;   /* release note cards           */
  --bg-card-hover: #151e30;
  --border:        rgba(99, 179, 237, 0.12);
  --border-hover:  rgba(99, 179, 237, 0.35);
  --accent-blue:   #4fa8ff;
  --accent-cyan:   #38bdf8;
  --accent-green:  #34d399;
  --accent-purple: #a78bfa;
  --accent-tweet:  #1d9bf0;   /* X/Twitter brand colour       */
  --text-primary:  #f0f6ff;
  --text-secondary:#94a3b8;
  --text-muted:    #4b5e7a;
}
```

- **Font:** `Inter` (Google Fonts, weights 300–800) — loaded via `<link>` preconnect.
- **Ambient orbs:** Two `body::before` / `::after` pseudo-elements create radial gradient glows at the top-left and bottom-right corners without impacting layout.

### UI Sections

| Section              | Element ID / Class     | Description                                                |
|----------------------|------------------------|------------------------------------------------------------|
| Header               | `header`               | Logo badge (inline SVG) + gradient h1 + subtitle           |
| Controls bar         | `.controls-bar`        | Meta info label + Refresh button                           |
| Filter chips         | `#filterRow`           | Keyword-based category tabs (hidden until first load)      |
| Error banner         | `#errorBanner`         | Dismissible red alert shown on API failure                 |
| Skeleton loaders     | `#skeletonList`        | 3 shimmer-animated placeholder cards during fetch          |
| Release notes list   | `#notesList`           | Dynamically populated `<article>` cards                    |
| Empty state          | `#emptyState`          | Shown when filters produce zero results                    |
| Footer               | `.page-footer`         | Attribution link to Google Cloud feed                      |
| Tweet modal          | `#tweetModal`          | Overlay dialog for composing and sending a tweet           |

---

## Feature 1 — Refresh Button with Spinner

### UX Behaviour
1. User clicks **Refresh**.
2. Button is disabled; the refresh SVG icon is hidden; a CSS-animated spinner (`border-top-color` trick) appears inside the button.
3. Skeleton cards fade in to indicate loading.
4. On success, cards are rendered and the meta label shows the count and timestamp.
5. On failure, the error banner appears with the error message.

### Key Implementation Details

**CSS spinner pattern:**
```css
/* Spinner element — hidden by default */
.spinner-icon {
  border: 2px solid rgba(255,255,255,0.3);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
  display: none;
}

/* Parent button gets .loading class during fetch */
.loading .spinner-icon { display: block; }
.loading .refresh-icon { display: none; }
```

**JS state management:**
```js
function setLoading(on) {
  btn.disabled = on;
  btn.classList.toggle('loading', on);
  if (on) {
    skeleton.classList.add('visible');
    list.innerHTML = '';          // clear old cards
  } else {
    skeleton.classList.remove('visible');
  }
}
```

**Async fetch flow:**
```js
async function fetchNotes() {
  setLoading(true);
  hideError();
  try {
    const res  = await fetch('/api/release-notes');
    const data = await res.json();
    if (!data.success) throw new Error(data.error);
    allEntries = data.entries;
    renderNotes(allEntries);
  } catch (err) {
    showError(err.message);
  } finally {
    setLoading(false);   // always restores button
  }
}
```

---

## Feature 2 — Tweet / Share on X (Twitter)

### UX Behaviour
1. Each release note card has a **Tweet** button in its footer.
2. Clicking opens a modal overlay with a pre-composed tweet draft (editable textarea).
3. A live character counter shows remaining characters; it turns **yellow** below 30 and **red** if over 280.
4. **Post Tweet** opens `twitter.com/intent/tweet` in a small popup window and closes the modal.
5. Modal closes on: `× button`, **Cancel** button, `Escape` key, or clicking the backdrop.

### Tweet Draft Composition Logic
```js
function openTweetModal(idx) {
  const entry   = allEntries[idx];
  const title   = entry.title.length > 100
                    ? entry.title.substring(0, 97) + '…'
                    : entry.title;
  const snippet = entry.summary_plain.length > 120
                    ? entry.summary_plain.substring(0, 117) + '…'
                    : entry.summary_plain;
  const tags    = '#BigQuery #GoogleCloud';
  let draft     = `📢 ${title}\n\n${snippet}\n\n${tags}`;

  // Append source link only if it fits within 280 chars
  if ((draft + '\n' + entry.link).length <= 280) draft += '\n' + entry.link;

  draft = draft.substring(0, 280);   // hard cap
  document.getElementById('tweetText').value = draft;
}
```

**Key decision:** `summary_plain` (not `summary_html`) is used for tweets to avoid raw HTML in the tweet compose window.

### Twitter Web Intent
```js
function openTwitter() {
  const text = document.getElementById('tweetText').value.trim();
  const url  = `https://twitter.com/intent/tweet?text=${encodeURIComponent(text)}`;
  window.open(url, '_blank', 'noopener,width=600,height=500');
  closeTweetModal();
}
```

Uses the Twitter Web Intent API — no OAuth or API keys required.

---

## Feature 3 — Category Badge Detection & Filtering

### Badge Auto-Detection
Each card automatically receives a colour-coded badge based on keyword matching against the entry title + plain summary:

| Badge      | CSS Class          | Keywords matched (regex)                       |
|------------|--------------------|------------------------------------------------|
| New Feature| `badge-new`        | `new feature`, `new release`                   |
| Changed    | `badge-changed`    | `changed`, `updated`, `modified`               |
| Fixed      | `badge-fixed`      | `fixed`, `fix`, `bug fix`, `patch`             |
| Deprecated | `badge-deprecated` | `deprecated`, `deprecation`                    |
| Update     | `badge-update`     | *(fallback)*                                   |

### Filter Chips
Filter tabs (All / New feature / Changed / Fixed / Deprecated) are hidden until the first successful data load. Clicking a chip re-runs `renderNotes()` against the in-memory `allEntries` array — **no additional network request**.

---

## Feature 4 — Card Expand / Collapse

Cards default to `max-height: 120px` with a gradient fade overlay to indicate truncation. Clicking **Read more** toggles the `expanded` class, animates `max-height` to `2000px`, and hides the fade overlay. The button label switches between "Read more" and "Show less".

---

## Application Startup

```bash
# Install dependencies (once)
pip install -r requirements.txt

# Run development server
python app.py
# → http://127.0.0.1:5000
```

The app runs in Flask's built-in dev server (`debug=True`, port `5000`). CORS is enabled globally via `flask-cors` to support any front-end origin during development.

---

## Data Flow Diagram

```
Browser                        Flask (app.py)              Google Cloud
   │                                │                            │
   │──── GET / ────────────────────▶│                            │
   │◀─── index.html ───────────────│                            │
   │                                │                            │
   │  [page load / Refresh click]   │                            │
   │──── GET /api/release-notes ───▶│                            │
   │                                │──── GET feed XML ─────────▶│
   │                                │◀─── Atom/RSS XML ──────────│
   │                                │  feedparser.parse()        │
   │                                │  clean_html() per entry    │
   │◀─── JSON {success, entries} ──│                            │
   │  renderNotes() → DOM cards     │                            │
```

---

## SEO & Accessibility Notes

- `<meta name="description">` — describes the page purpose for search indexers.
- `lang="en"` on `<html>` for screen-reader language identification.
- Tweet modal has `role="dialog"`, `aria-modal="true"`, `aria-labelledby="modalTitle"`.
- Cards use `<article role="listitem">` and `<h2>` for heading hierarchy.
- Expand buttons use `aria-expanded` toggled dynamically.
- `escapeHtml()` utility prevents XSS when inserting user-facing strings into card innerHTML.

---

## Known Limitations & Potential Improvements

| # | Limitation                          | Potential fix                                            |
|---|-------------------------------------|----------------------------------------------------------|
| 1 | No server-side caching              | Add `functools.lru_cache` or a Redis TTL cache            |
| 2 | Feed fetched fresh on every request | Cache response for ~5–15 min to reduce external calls    |
| 3 | No pagination                       | Add virtual scrolling or page-based navigation           |
| 4 | Filter chips rely on regex keywords | Improve with structured feed categories if available     |
| 5 | Twitter Web Intent (no auth)        | Upgrade to Twitter API v2 for direct posting             |
| 6 | Single HTML file (no separation)    | Split into `static/style.css` + `static/app.js` for scale|
