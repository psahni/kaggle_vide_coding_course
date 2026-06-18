# Project Structure

Complete overview of all files in the event-driven document processing pipeline.

## Directory Layout

```
google-cloud-serverless-app/
├── app/                          # Cloud Run Application
│   ├── main.py                  # Flask application (core logic)
│   ├── requirements.txt          # Python dependencies
│   ├── Dockerfile               # Docker image configuration
│   └── schema.json              # BigQuery table schema
├── setup.sh                      # Infrastructure provisioning script
├── test_local.sh                # Local testing script
├── test_cloud.sh                # Cloud integration testing script
├── Makefile                      # Convenience commands
├── .gitignore                    # Git ignore file
├── README.md                     # Full documentation
├── QUICK_START.md               # 5-minute quick start guide
├── DEPLOYMENT_CHECKLIST.md      # Deployment verification checklist
├── TROUBLESHOOTING.md           # Common issues and solutions
└── PROJECT_STRUCTURE.md         # This file
```

## File Descriptions

### Application Code

#### `app/main.py`
**Purpose**: Flask application that processes documents

**Key Features**:
- Receives Pub/Sub push messages
- Parses GCS event data
- Downloads and reads text files
- Simulates OCR for binary files
- Extracts metadata (word count, tags)
- Streams results to BigQuery

**Key Functions**:
- `process_event()`: Main endpoint receiving Pub/Sub messages
- Keyword matching for auto-tagging
- BigQuery row insertion

**Size**: ~179 lines

#### `app/requirements.txt`
**Purpose**: Python package dependencies

**Packages**:
- `Flask==3.0.0` - Web framework
- `gunicorn==21.2.0` - WSGI server
- `google-cloud-storage==2.13.0` - GCS client
- `google-cloud-bigquery==3.13.0` - BigQuery client

#### `app/Dockerfile`
**Purpose**: Container image definition for Cloud Run

**Configuration**:
- Base: `python:3.11-slim`
- Installs Python dependencies
- Runs application with gunicorn
- Binds to $PORT (8080)

#### `app/schema.json`
**Purpose**: BigQuery table schema definition

**Fields**:
- `filename` (STRING, REQUIRED) - File name
- `processed_at` (TIMESTAMP, REQUIRED) - Processing time
- `tags` (STRING, REPEATED) - Array of tags
- `word_count` (INTEGER, REQUIRED) - Document word count
- `bucket` (STRING, REQUIRED) - GCS bucket name
- `file_size` (INTEGER, REQUIRED) - File size in bytes

### Infrastructure & Deployment

#### `setup.sh`
**Purpose**: Complete infrastructure provisioning

**What It Does**:
1. Enables required GCP APIs
2. Creates Cloud Storage bucket
3. Creates BigQuery dataset and table
4. Creates Pub/Sub topic
5. Creates service accounts
6. Sets up IAM permissions
7. Builds and deploys Cloud Run service
8. Creates GCS Pub/Sub notification
9. Creates Pub/Sub push subscription

**Size**: ~211 lines

**Usage**: `./setup.sh` (run once to deploy everything)

### Testing Scripts

#### `test_local.sh`
**Purpose**: Test the Flask application locally without GCP deployment

**What It Does**:
- Creates Python virtual environment
- Installs dependencies
- Runs message format tests
- Tests invalid message handling
- Tests folder placeholder skipping

**Tests**: Basic parsing (no GCS/BigQuery access needed)

**Size**: ~140 lines

**Usage**: `./test_local.sh`

#### `test_cloud.sh`
**Purpose**: End-to-end testing on deployed GCP infrastructure

**What It Does**:
- Creates test files (invoice, report, receipt)
- Uploads to Cloud Storage
- Waits for processing
- Queries BigQuery for results
- Displays processed documents

**Tests**: Full pipeline including GCS and BigQuery

**Size**: ~130 lines

**Usage**: `./test_cloud.sh`

### Configuration & Build

#### `Makefile`
**Purpose**: Convenient commands for common operations

**Commands**:
- `make setup` - Deploy pipeline
- `make test-local` - Run local tests
- `make test-cloud` - Run cloud tests
- `make deploy` - Redeploy service only
- `make logs` - View recent logs
- `make tail-logs` - Follow logs live
- `make status` - Check service status
- `make query` - Run BigQuery query
- `make cleanup` - Delete all resources

**Size**: ~70 lines

#### `.gitignore`
**Purpose**: Specify files to exclude from version control

**Excludes**:
- Python cache and virtual environments
- IDE configuration
- Environment files
- Temporary test files

### Documentation

#### `README.md` (Comprehensive Guide)
**Sections**:
- Architecture overview with diagram
- Features list
- Prerequisites
- Quick start (3 steps)
- Project structure
- Application details
- Configuration options
- Monitoring and troubleshooting
- Cleanup instructions
- Advanced usage
- Cost estimation
- Security considerations
- Resources and references

**Size**: ~450 lines

**Best For**: Detailed understanding of the system

#### `QUICK_START.md` (5-Minute Guide)
**Sections**:
- Prerequisites checklist
- 4-step deployment
- Testing the pipeline
- Viewing results
- Common operations
- Using Make commands
- Basic troubleshooting
- Next steps

**Size**: ~100 lines

**Best For**: Getting started immediately

#### `DEPLOYMENT_CHECKLIST.md`
**Sections**:
- Pre-deployment checklist
- Deployment checklist
- Post-deployment verification (by component)
- Functionality testing
- Monitoring setup
- Configuration review
- Production readiness
- Optional enhancements
- Ongoing operations
- Cleanup checklist

**Size**: ~150 lines

**Best For**: Tracking deployment progress

#### `TROUBLESHOOTING.md` (Detailed Issues)
**Sections**:
- Setup issues
- Deployment issues
- Runtime issues
- Data issues
- Performance issues
- Debugging tips
- Asking for help

**Size**: ~350 lines

**Best For**: Solving problems when things go wrong

#### `PROJECT_STRUCTURE.md`
This file - Complete overview of all project files and their purposes.

## File Statistics

| Category | Count | Total Lines |
|----------|-------|------------|
| Application Code | 4 files | ~300 lines |
| Deployment/Setup | 1 file | ~211 lines |
| Testing | 2 files | ~270 lines |
| Configuration | 2 files | ~70 lines |
| Documentation | 6 files | ~1000 lines |
| **Total** | **15 files** | **~1850 lines** |

## Data Flow Through Files

```
User Request
    ↓
test_cloud.sh / Manual Upload
    ↓
Cloud Storage (bucket in setup.sh config)
    ↓
Pub/Sub Notification (setup.sh creates)
    ↓
Cloud Run Service (app/main.py)
    ├── Reads config from setup.sh env vars
    ├── Downloads file from GCS
    ├── Processes using app/main.py logic
    ├── Matches keywords (in app/main.py)
    └── Inserts into BigQuery
         ↓
      BigQuery Table
      (schema from app/schema.json)
         ↓
   Query Results (via test_cloud.sh / bq CLI)
```

## Usage Flowchart

```
START
  ↓
[1] First Time Setup?
  YES → Run ./setup.sh (configures via setup.sh)
  NO  → Skip
  ↓
[2] Test Locally?
  YES → Run ./test_local.sh
  NO  → Skip
  ↓
[3] Deploy to Cloud?
  YES → setup.sh already did this
  NO  → Skip
  ↓
[4] Test on Cloud?
  YES → Run ./test_cloud.sh
  NO  → Skip
  ↓
[5] Upload Documents
  → Use Cloud Console or gsutil
  ↓
[6] Monitor
  → Check logs: make logs
  → Query results: make query
  ↓
[7] Issues?
  YES → Check TROUBLESHOOTING.md
  NO  → ✓ Done!
```

## File Relationships

```
setup.sh
├── Uses configuration from (CONFIG BLOCK)
├── Deploys app/ directory to Cloud Run
├── References app/schema.json for BigQuery
└── Configures services for test scripts

app/main.py
├── Uses requirements.txt for imports
├── Runs in Docker (from Dockerfile)
├── Expects BQ_DATASET and BQ_TABLE env vars (from setup.sh)
└── Processes events triggered by setup.sh

test_local.sh
├── Tests app/main.py locally
└── Creates temporary test_runner.py

test_cloud.sh
├── Uses PROJECT_ID from gcloud config
├── Uploads to bucket created by setup.sh
└── Queries table created by setup.sh

Documentation files
├── README.md - Complete reference
├── QUICK_START.md - First-time users
├── DEPLOYMENT_CHECKLIST.md - Verification
├── TROUBLESHOOTING.md - Problem solving
└── PROJECT_STRUCTURE.md - This file
```

## Key Configuration Points

### Variables Set in `setup.sh`
```bash
REGION="us-central1"
TOPIC_NAME="docs-upload-topic"
DATASET_NAME="docs_metadata"
TABLE_NAME="processed_docs"
SERVICE_NAME="doc-processor-service"
```

### Environment Variables Passed to Cloud Run
```bash
BQ_DATASET="docs_metadata"
BQ_TABLE="processed_docs"
```

### Keywords Defined in `app/main.py`
```python
KEYWORD_TAGS = {
    "invoice": "invoice",
    "receipt": "receipt",
    "report": "report",
    # ... more keywords
}
```

## Where to Start

**First time?**
→ Read [QUICK_START.md](QUICK_START.md)

**Want full details?**
→ Read [README.md](README.md)

**Deploying?**
→ Use [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md)

**Having issues?**
→ Check [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

**Want to understand everything?**
→ Start with this file, then README.md

---

**Last Updated**: 2025-06-16
