# Project Index - Event-Driven Document Processing Pipeline

## Quick Navigation

### 🚀 Getting Started (Pick Your Path)

| Goal | Document | Time |
|------|----------|------|
| Deploy in 5 minutes | [QUICK_START.md](QUICK_START.md) | 5 min |
| Understand everything | [README.md](README.md) | 20 min |
| Track deployment | [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md) | 10 min |
| Fix problems | [TROUBLESHOOTING.md](TROUBLESHOOTING.md) | As needed |
| Understand files | [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) | 5 min |

---

## Project Files

### 📦 Application (`app/`)

| File | Purpose | Size | Role |
|------|---------|------|------|
| [app/main.py](app/main.py) | Flask application | 179 lines | **Core** |
| [app/requirements.txt](app/requirements.txt) | Python dependencies | 4 lines | Config |
| [app/Dockerfile](app/Dockerfile) | Container config | 19 lines | Config |
| [app/schema.json](app/schema.json) | BigQuery schema | 39 lines | Config |

### ⚙️ Deployment & Setup

| File | Purpose | Command | Role |
|------|---------|---------|------|
| [setup.sh](setup.sh) | GCP provisioning | `./setup.sh` | **Critical** |
| [Makefile](Makefile) | Convenience commands | `make help` | Optional |

### 🧪 Testing

| File | Purpose | Command | When |
|------|---------|---------|------|
| [test_local.sh](test_local.sh) | Local tests | `./test_local.sh` | Before deploy |
| [test_cloud.sh](test_cloud.sh) | Cloud tests | `./test_cloud.sh` | After deploy |

### 📚 Documentation

| File | Purpose | Best For | Read Time |
|------|---------|----------|-----------|
| [README.md](README.md) | Complete guide | Everything | 20 min |
| [QUICK_START.md](QUICK_START.md) | Fast start | New users | 5 min |
| [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md) | Verification | Deploy tracking | 10 min |
| [TROUBLESHOOTING.md](TROUBLESHOOTING.md) | Problem solving | Debug issues | As needed |
| [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) | File overview | Understanding code | 5 min |
| [INDEX.md](INDEX.md) | This file | Navigation | 2 min |

### ⚙️ Configuration

| File | Purpose |
|------|---------|
| [.gitignore](.gitignore) | Version control exclusions |

---

## Deployment Steps

```
1. Authenticate:     gcloud auth login
2. Set Project:      gcloud config set project YOUR_PROJECT_ID
3. Run Setup:        ./setup.sh
4. Test Cloud:       ./test_cloud.sh
5. Upload Files:     gsutil cp file.txt gs://your-bucket/
6. View Results:     bq query --nouse_legacy_sql "SELECT * FROM..."
```

---

## Common Commands

### Deployment
```bash
./setup.sh          # Deploy everything
make deploy         # Redeploy service only
```

### Testing
```bash
./test_local.sh     # Test locally
./test_cloud.sh     # Test on cloud
```

### Monitoring
```bash
make status         # Check service status
make logs           # View recent logs
make tail-logs      # Follow logs live
make query          # Query BigQuery
```

### Management
```bash
make cleanup        # Delete all resources
gcloud run logs read doc-processor-service --region us-central1
gcloud pubsub subscriptions describe docs-upload-topic-sub
```

---

## Architecture

```
Cloud Storage Bucket
    ↓
Pub/Sub Topic
    ↓
Cloud Run Service
(app/main.py)
    ↓
BigQuery Table
(app/schema.json)
```

---

## File Purposes at a Glance

**Must Have**:
- ✅ `app/main.py` - The application
- ✅ `app/requirements.txt` - Python packages
- ✅ `app/Dockerfile` - Container image
- ✅ `app/schema.json` - Database schema
- ✅ `setup.sh` - Infrastructure setup

**Helpful**:
- ✅ `test_local.sh` - Local testing
- ✅ `test_cloud.sh` - Cloud testing
- ✅ `Makefile` - Quick commands

**Documentation** (Pick 1-2):
- ✅ `QUICK_START.md` - If in a hurry
- ✅ `README.md` - For full understanding
- ✅ `DEPLOYMENT_CHECKLIST.md` - While deploying
- ✅ `TROUBLESHOOTING.md` - If issues occur

---

## First Time? Start Here

### Option 1: Fast Track (5 minutes)
1. Read [QUICK_START.md](QUICK_START.md)
2. Run `./setup.sh`
3. Run `./test_cloud.sh`
4. Done! ✓

### Option 2: Understanding Track (20 minutes)
1. Read [README.md](README.md) - Full overview
2. Run `./test_local.sh` - Understand code
3. Read code in [app/main.py](app/main.py)
4. Run `./setup.sh` - Deploy
5. Run `./test_cloud.sh` - Verify

### Option 3: Methodical Track (1 hour)
1. Review [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)
2. Read [README.md](README.md)
3. Study [app/main.py](app/main.py)
4. Review [setup.sh](setup.sh)
5. Use [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md) while deploying
6. Keep [TROUBLESHOOTING.md](TROUBLESHOOTING.md) handy

---

## Need Help?

| Issue | Resource |
|-------|----------|
| How do I start? | [QUICK_START.md](QUICK_START.md) |
| How does it work? | [README.md](README.md) |
| What went wrong? | [TROUBLESHOOTING.md](TROUBLESHOOTING.md) |
| Am I done deploying? | [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md) |
| Where are the files? | [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) |

---

## Project Statistics

**Total Files**: 15
- Application: 4 files
- Setup/Deployment: 2 files
- Testing: 2 files
- Documentation: 6 files
- Config: 1 file

**Total Code**: ~300 lines
**Total Docs**: ~1000 lines

---

## Technology Stack

- **Language**: Python 3.11
- **Framework**: Flask
- **Server**: Gunicorn
- **Container**: Docker
- **Compute**: Google Cloud Run
- **Messaging**: Google Pub/Sub
- **Storage**: Google Cloud Storage
- **Database**: Google BigQuery

---

## Key Files Breakdown

### core Application
`app/main.py` - Processes documents (100+ lines of logic)

### Cloud Configuration
`setup.sh` - Automated infrastructure provisioning

### Testing & Validation
`test_local.sh` + `test_cloud.sh` - Ensure everything works

### Documentation
`README.md` - Everything you need to know

---

## Version Info

- **Created**: 2025-06-16
- **Python**: 3.11
- **Flask**: 3.0.0
- **Cloud Run**: Latest

---

## What's Included

✅ Complete application code
✅ Docker containerization
✅ Infrastructure-as-code provisioning
✅ Automated testing scripts
✅ Comprehensive documentation
✅ Troubleshooting guides
✅ Quick start guides
✅ Deployment checklists

---

**Ready to get started?** → [QUICK_START.md](QUICK_START.md)

**Want to understand everything?** → [README.md](README.md)
