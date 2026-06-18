# GCP Cost Analysis - Keeping Services Running

**Important:** Understanding costs helps you decide whether to keep or delete resources.

---

## Monthly Cost Breakdown

### 1. Cloud Storage (Bucket with no files)

```
Minimum Cost: $0.23/month (just the bucket existing)
```

**Breakdown:**
- Storage charges: Based on data stored
  - First 1 GB free per month
  - After that: $0.020/GB/month
  - With NO files uploaded: ~$0 (just bucket overhead)

**Example:**
```
Empty bucket:           $0
10 test files (1MB):    $0 (under 1GB free tier)
100 files (100MB):      $0 (under 1GB free tier)
1GB+ of documents:      $0.020 × (size over 1GB)
```

**Cost Trigger:** File uploads and storage duration

---

### 2. Pub/Sub (Topic + Subscription)

```
Minimum Cost: $0 (if no messages)
Cost if using: $0.40 per million messages
```

**Breakdown:**
- Idle topic/subscription: **FREE** (no charge for existing)
- Only charged when messages flow through

**Example (Monthly):**
```
No file uploads:              $0
10 file uploads:              $0 (negligible)
1,000 file uploads:           $0.0004 (1k messages × $0.40/1M)
10,000 file uploads:          $0.004
100,000 file uploads:         $0.04
1 million file uploads:       $0.40
```

**Cost Trigger:** Only when files are uploaded

---

### 3. Cloud Run (Flask Service)

```
Minimum Cost: $0 (if idle)
Cost when invoked: $0.00002400 per vCPU-second
```

**Breakdown:**
- Idle service: **FREE** (no charge)
- Only charged when handling requests
- Default: 1 vCPU, 512 MB memory

**Example (Monthly with 100 file uploads):**
```
Processing time per file:     ~2 seconds
Total vCPU seconds:           100 files × 2 sec = 200 seconds
Cost:                         200 × $0.00002400 = $0.0048

Cost for 1,000 uploads:       $0.048
Cost for 10,000 uploads:      $0.48
Cost for 100,000 uploads:     $4.80
```

**Cost Trigger:** Only when processing files

---

### 4. BigQuery (Dataset + Table)

```
Minimum Cost: $0 (free tier covers up to 1TB/month)
Cost per query: $0.01 per GB scanned (if over free tier)
```

**Breakdown:**
- Storage: First 1TB free per month
  - After that: $0.02/GB/month
- Queries: First 1TB free per month
  - After that: $0.01/GB queried

**Example (Monthly with 100 documents processed):**
```
Metadata stored:              ~0.1 GB (100 rows × ~1MB each)
Cost:                         $0 (within free 1TB tier)

Metadata stored:              ~100 GB (large documents)
Cost:                         $0 (still within 1TB free tier)

Metadata stored:              ~1.5 TB
Storage cost:                 0.5TB × $0.02 = $0.01
Query costs:                  (if you run analysis queries)
```

**Cost Trigger:** Data storage and query execution

---

### 5. Cloud Build (Container builds)

```
Minimum Cost: FREE (up to 120 build-minutes/day)
Cost after free tier: $0.003 per build-minute
```

**Breakdown:**
- First 120 minutes per day: **FREE**
- Beyond that: $0.003 per minute

**Example (Monthly):**
```
One deployment:               $0 (uses ~5 min of free tier)
Multiple deployments:         $0 (120 min = 2 hrs/day free!)
50 deployments in a month:    $0 (still within free tier)
```

**Cost Trigger:** Only when you redeploy Cloud Run

---

### 6. Artifact Registry (Container storage)

```
Minimum Cost: $0.10/GB/month
```

**Breakdown:**
- Stores Docker images
- One image per deployment: ~500 MB
- Cost: ~$0.05/month per image

**Example:**
```
1 image:    $0.05/month
5 images:   $0.25/month
10 images:  $0.50/month
```

**Cost Trigger:** Container image storage

---

## Realistic Monthly Cost Scenarios

### Scenario 1: Development/Testing (MOST COMMON)

```
Usage Pattern:
- Few test file uploads per day
- No production traffic
- Occasional queries

Monthly Breakdown:
├─ Cloud Storage:      $0.00  (mostly empty)
├─ Pub/Sub:           $0.00  (few messages)
├─ Cloud Run:         $0.01  (few invocations)
├─ BigQuery:          $0.00  (within free tier)
├─ Cloud Build:       $0.00  (free tier)
└─ Artifact Registry: $0.05  (1 image)
─────────────────────────────
TOTAL:                $0.06/month (~$0.70/year)
```

---

### Scenario 2: Small Production (100 files/day)

```
Usage Pattern:
- 100 file uploads per day (3,000/month)
- Regular queries
- Active monitoring

Monthly Breakdown:
├─ Cloud Storage:      $0.05  (small documents, free tier)
├─ Pub/Sub:           $0.00  (3k messages)
├─ Cloud Run:         $0.15  (3k × 2sec processing)
├─ BigQuery:          $0.00  (within free tier)
├─ Cloud Build:       $0.00  (free tier)
└─ Artifact Registry: $0.05  (1 image)
─────────────────────────────
TOTAL:                $0.25/month (~$3/year)
```

---

### Scenario 3: Medium Production (10,000 files/day)

```
Usage Pattern:
- 10,000 file uploads per day (300k/month)
- High query volume
- 5GB data stored

Monthly Breakdown:
├─ Cloud Storage:      $0.10  (5GB, within free tier)
├─ Pub/Sub:           $0.12  (300k messages)
├─ Cloud Run:         $15.00 (300k × 2sec × $0.00002400)
├─ BigQuery:          $0.00  (within free tier, lots of queries)
├─ Cloud Build:       $0.00  (free tier)
└─ Artifact Registry: $0.05  (1 image)
─────────────────────────────
TOTAL:                $15.27/month (~$183/year)
```

**Note:** Cloud Run becomes the major cost factor at scale.

---

### Scenario 4: Idle (Services deployed but unused)

```
Usage Pattern:
- No file uploads
- No queries
- No processing

Monthly Breakdown:
├─ Cloud Storage:      $0.00  (idle, free)
├─ Pub/Sub:           $0.00  (idle, free)
├─ Cloud Run:         $0.00  (idle, free)
├─ BigQuery:          $0.00  (idle, free)
├─ Cloud Build:       $0.00  (idle, free)
└─ Artifact Registry: $0.05  (image storage only)
─────────────────────────────
TOTAL:                $0.05/month (~$0.60/year)
```

**This is important:** If you're not using it, costs are nearly $0!

---

## GCP Free Tier Benefits

Your account gets **free tier** resources per month:

| Service | Free Tier | Your Usage |
|---------|-----------|-----------|
| Cloud Storage | 5 GB/month | Tiny compared to 5GB |
| Pub/Sub | 10 GB/month | Negligible |
| Cloud Run | 2M invocations/month | Most testing fits here |
| BigQuery | 1 TB/month | Usually covered |
| Cloud Build | 120 build-minutes/day | Most testing fits here |

**Result:** For **development/testing**, you'll likely stay within free tier!

---

## Cost Monitoring

### Check Current Billing

```bash
# View billing in console
# https://console.cloud.google.com/billing/projects

# Or use gcloud
gcloud billing projects describe ps-my-document-processor
```

### Set Up Budget Alerts

```bash
# Create a budget alert at $10/month
gcloud billing budgets create \
  --billing-account=YOUR_BILLING_ACCOUNT_ID \
  --display-name="Alert at $10" \
  --budget-amount=10 \
  --threshold-rule=percent=100 \
  --threshold-rule=percent=90 \
  --threshold-rule=percent=50
```

### Export Billing Data

```bash
# View detailed costs
# https://console.cloud.google.com/billing/reports
```

---

## Cost Optimization Tips

### 1. Use Cloud Run Auto-Scaling

```bash
# Already configured (scales to 0 when idle)
# Cost: Only charged when processing
```

### 2. Set Cloud Run Timeout

```bash
# Keep processing time short
# More time = more cost
gcloud run deploy doc-processor-service \
  --timeout=30s \  # Fail fast if processing takes >30s
```

### 3. Delete Unused Artifacts

```bash
# Check artifact registry size
gcloud artifacts repositories list --location=us-central1

# Delete old images
gcloud artifacts docker images delete \
  us-central1-docker.pkg.dev/ps-my-document-processor/...
```

### 4. Archive Old BigQuery Data

```bash
# Move old data to Cloud Storage (cheaper)
bq extract \
  ps-my-document-processor:docs_metadata.processed_docs \
  gs://ps-my-document-processor-docs-ingest/archive/2025-*.csv

# Then delete from BigQuery
bq rm --table ps-my-document-processor:docs_metadata.processed_docs
```

### 5. Set Storage Lifecycle Policies

```bash
# Delete old files automatically
gsutil lifecycle set - gs://ps-my-document-processor-docs-ingest << 'EOF'
{
  "lifecycle": {
    "rule": [
      {
        "action": {"type": "Delete"},
        "condition": {"age": 90}  # Delete files older than 90 days
      }
    ]
  }
}
EOF
```

---

## Decision Matrix: Keep or Delete?

### Delete If...

```
✓ Project is just for learning/testing
✓ You have limited budget (<$1/month)
✓ You won't use it for months
✓ Data is not important
✓ You have frequent budget reviews
```

**Cost saved:** ~$0.05-0.50/month

---

### Keep If...

```
✓ Active development ongoing
✓ Showing to team/stakeholders
✓ Planning to test more
✓ Want to monitor production setup
✓ Data is valuable for learning
```

**Cost:** ~$0.06-0.25/month (development)

---

### Hybrid Approach: Pause but Don't Delete

```bash
# Delete high-cost resources, keep cheap ones
# Keep: BigQuery (free tier coverage)
# Keep: Artifact Registry (cheap)
# Delete: Cloud Run (redeploy later easily)
# Delete: Pub/Sub subscription (recreate in 30 seconds)
# Keep: Cloud Storage (nearly free, has your data)

# This way:
# - Costs drop to ~$0.10/month
# - Can quickly restart when needed
# - Data is preserved
```

---

## Real Cost Examples from GCP Users

### Example 1: Learning Project
```
"Spent $0.47 over 3 months of occasional testing"
→ Stayed in free tier mostly
```

### Example 2: Small Startup Pilot
```
"$2.50/month for 1,000 file uploads, 2M BigQuery queries"
→ Still within free tier ranges
```

### Example 3: Medium Load
```
"$45/month for 100k daily uploads with heavy processing"
→ Cloud Run costs dominated (~$40)
```

---

## TL;DR - Bottom Line

| Scenario | Monthly Cost | Keep or Delete? |
|----------|-------------|-----------------|
| Development/Testing (your case) | **$0.06** | KEEP* |
| Idle (no usage) | **$0.05** | DELETE |
| Small production | **$0.25** | KEEP |
| Medium production | **$15** | EVALUATE |
| High production | **$100+** | NEEDS OPTIMIZATION |

**\*For your learning project, keeping it costs less than a coffee! ☕**

---

## Monitoring Your Project

```bash
# Check what you're actually using
echo "=== Storage Usage ==="
gsutil du -s gs://ps-my-document-processor-docs-ingest/

echo "=== BigQuery Storage ==="
bq show --format=prettyjson ps-my-document-processor:docs_metadata | grep -E "creationTime|tableSize"

echo "=== Cloud Run Invocations (last 7 days) ==="
gcloud monitoring time-series list \
  --filter='metric.type="run.googleapis.com/request_count"'

echo "=== Check Billing Dashboard ==="
echo "https://console.cloud.google.com/billing/projects"
```

---

## Recommendation

For your **learning/development project**:

```
✅ RECOMMENDATION: KEEP IT RUNNING

Why?
1. Costs ~$0.06/month (practically free)
2. Can test anytime without redeployment
3. Data is preserved for learning
4. Cloud Run auto-scales to 0 when idle
5. Free tier covers most usage

When to delete?
- If you won't touch it for 6+ months
- If you're worried about any charge at all
- If creating a new project for different purpose
```

---

**Document Version:** 1.0  
**Last Updated:** 2026-06-17  
**For:** Cost Awareness & Decision Making
