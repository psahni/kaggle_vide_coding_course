# Architecture Diagram - Event-Driven Document Processing Pipeline

## System Architecture

```mermaid
graph TB
    subgraph "User & External"
        USER["👤 User/Client"]
    end

    subgraph "Google Cloud - Ingestion Layer"
        GCS["☁️ Cloud Storage Bucket<br/>gs://PROJECT-docs-ingest"]
        GCS_NOTIF["📢 GCS Notification<br/>OBJECT_FINALIZE"]
    end

    subgraph "Google Cloud - Messaging Layer"
        PUBSUB_TOPIC["📨 Pub/Sub Topic<br/>docs-upload-topic"]
        PUBSUB_SUB["📬 Pub/Sub Subscription<br/>docs-upload-topic-sub<br/>Push to Cloud Run"]
    end

    subgraph "Google Cloud - Compute Layer"
        CR_SERVICE["🚀 Cloud Run Service<br/>doc-processor-service<br/>Python Flask App"]
        
        subgraph "Flask Application"
            FLASK_APP["🔵 app.py<br/>Flask Routes<br/>- POST /<br/>- GET /health"]
            PROCESSOR["🟢 processor.py<br/>OCR & Extraction<br/>- extract_text_from_file<br/>- count_words<br/>- extract_tags<br/>- process_document<br/>Keywords: 10 types"]
            GCS_HELPER["🟡 gcs_helper.py<br/>Cloud Storage Ops<br/>- download_file_content<br/>- get_file_metadata"]
            BQ_HELPER["🟣 bq_helper.py<br/>BigQuery Ops<br/>- insert_metadata_row<br/>- insert_multiple_rows<br/>- get_table_schema"]
        end
    end

    subgraph "Google Cloud - Storage Layer"
        BQ_DATASET["💾 BigQuery Dataset<br/>docs_metadata"]
        BQ_TABLE["📊 BigQuery Table<br/>processed_docs<br/>Columns:<br/>- filename<br/>- processed_at<br/>- tags (REPEATED)<br/>- word_count<br/>- bucket<br/>- file_size"]
    end

    subgraph "Google Cloud - Security & Access"
        SA_CR["🔑 Service Account<br/>doc-processor-sa<br/>Permissions:<br/>- storage.objectViewer<br/>- bigquery.dataEditor<br/>- bigquery.user"]
        SA_PUBSUB["🔑 Service Account<br/>pubsub-invoker-sa<br/>Permissions:<br/>- run.invoker"]
        IAM["🛡️ IAM Role Bindings<br/>Least Privilege"]
    end

    subgraph "Data Flow"
        FLOW1["1️⃣ File Upload"]
        FLOW2["2️⃣ GCS Event"]
        FLOW3["3️⃣ Pub/Sub Message"]
        FLOW4["4️⃣ Cloud Run Invocation"]
        FLOW5["5️⃣ File Processing"]
        FLOW6["6️⃣ Metadata Extraction"]
        FLOW7["7️⃣ BigQuery Insert"]
    end

    %% User to GCS
    USER -->|Upload File| GCS
    FLOW1 -.->|File uploaded| GCS

    %% GCS to Pub/Sub
    GCS -->|Triggers| GCS_NOTIF
    GCS_NOTIF -->|Sends Event| PUBSUB_TOPIC
    FLOW2 -.->|GCS event created| PUBSUB_TOPIC

    %% Pub/Sub to Cloud Run
    PUBSUB_TOPIC -->|Routes to| PUBSUB_SUB
    PUBSUB_SUB -->|HTTP POST| CR_SERVICE
    FLOW3 -.->|Message published| PUBSUB_SUB
    FLOW4 -.->|Service invoked| CR_SERVICE

    %% Internal Cloud Run Flow
    FLASK_APP -->|Receives Request| PROCESSOR
    FLASK_APP -->|Calls| GCS_HELPER
    FLASK_APP -->|Calls| BQ_HELPER
    PROCESSOR -->|Extracts Metadata| GCS_HELPER
    GCS_HELPER -->|Downloads File| GCS
    PROCESSOR -->|Processes Text| BQ_HELPER
    BQ_HELPER -->|Inserts Data| BQ_TABLE
    
    FLOW5 -.->|File downloaded| GCS_HELPER
    FLOW6 -.->|Metadata extracted| PROCESSOR
    FLOW7 -.->|Row inserted| BQ_TABLE

    %% Cloud Run to BigQuery
    CR_SERVICE -->|Stream Metadata| BQ_DATASET
    BQ_DATASET -->|Contains| BQ_TABLE

    %% Security
    SA_CR -.->|Authenticates| CR_SERVICE
    SA_PUBSUB -.->|Invokes| CR_SERVICE
    IAM -.->|Manages| SA_CR
    IAM -.->|Manages| SA_PUBSUB

    %% Styling
    classDef user fill:#e1f5ff,stroke:#01579b,stroke-width:2px,color:#000
    classDef gcs fill:#fff3e0,stroke:#e65100,stroke-width:2px,color:#000
    classDef pubsub fill:#f3e5f5,stroke:#4a148c,stroke-width:2px,color:#000
    classDef compute fill:#e8f5e9,stroke:#1b5e20,stroke-width:2px,color:#000
    classDef app fill:#c8e6c9,stroke:#2e7d32,stroke-width:1px,color:#000
    classDef storage fill:#fce4ec,stroke:#880e4f,stroke-width:2px,color:#000
    classDef security fill:#ede7f6,stroke:#311b92,stroke-width:2px,color:#000
    classDef flow fill:#fff9c4,stroke:#f57f17,stroke-width:1px,color:#000

    class USER user
    class GCS,GCS_NOTIF gcs
    class PUBSUB_TOPIC,PUBSUB_SUB pubsub
    class CR_SERVICE compute
    class FLASK_APP,PROCESSOR,GCS_HELPER,BQ_HELPER app
    class BQ_DATASET,BQ_TABLE storage
    class SA_CR,SA_PUBSUB,IAM security
    class FLOW1,FLOW2,FLOW3,FLOW4,FLOW5,FLOW6,FLOW7 flow
```

## Component Interaction Diagram

```mermaid
graph LR
    subgraph "Input"
        FILE["📄 Document File<br/>(txt, pdf, image)"]
    end

    subgraph "Processing Pipeline"
        STEP1["1. Parse Event<br/>Extract bucket & file"]
        STEP2["2. Download File<br/>from Cloud Storage"]
        STEP3["3. Extract Text<br/>Real or simulated OCR"]
        STEP4["4. Count Words<br/>Process text"]
        STEP5["5. Extract Tags<br/>Keyword matching"]
        STEP6["6. Create Metadata<br/>Row object"]
        STEP7["7. Insert to BigQuery<br/>Stream data"]
    end

    subgraph "Output"
        METADATA["📊 Stored Metadata<br/>Queryable in BigQuery"]
    end

    FILE -->|Pub/Sub Event| STEP1
    STEP1 -->|GCS path| STEP2
    STEP2 -->|File content| STEP3
    STEP3 -->|Text| STEP4
    STEP4 -->|Word count| STEP5
    STEP5 -->|Tags| STEP6
    STEP6 -->|Row data| STEP7
    STEP7 -->|INSERT| METADATA

    classDef input fill:#b3e5fc,stroke:#01579b
    classDef process fill:#c8e6c9,stroke:#2e7d32
    classDef output fill:#fce4ec,stroke:#880e4f

    class FILE input
    class STEP1,STEP2,STEP3,STEP4,STEP5,STEP6,STEP7 process
    class METADATA output
```

## Data Model - BigQuery Table Schema

```mermaid
graph TB
    subgraph "processed_docs Table"
        COL1["📝 filename<br/>STRING, REQUIRED<br/>Example: invoice_001.txt"]
        COL2["⏰ processed_at<br/>TIMESTAMP, REQUIRED<br/>Example: 2025-06-16T14:30:00Z"]
        COL3["🏷️  tags<br/>STRING, REPEATED<br/>Example: ['invoice', 'payment']"]
        COL4["📊 word_count<br/>INTEGER, REQUIRED<br/>Example: 150"]
        COL5["🗂️  bucket<br/>STRING, REQUIRED<br/>Example: my-project-docs-ingest"]
        COL6["📦 file_size<br/>INTEGER, REQUIRED<br/>Example: 2048"]
    end

    COL1 ---|Row 1| COL2
    COL2 ---|Row 1| COL3
    COL3 ---|Row 1| COL4
    COL4 ---|Row 1| COL5
    COL5 ---|Row 1| COL6

    classDef schema fill:#f0f4c3,stroke:#827717,stroke-width:2px
    class COL1,COL2,COL3,COL4,COL5,COL6 schema
```

## Deployment Architecture

```mermaid
graph TB
    subgraph "Version Control"
        GIT["📦 Git Repository<br/>google-cloud-serverless-app"]
    end

    subgraph "Local Development"
        CODE["💻 Local Code<br/>- app/src/<br/>- requirements.txt<br/>- Dockerfile"]
        TESTS["🧪 Local Tests<br/>test_local.sh<br/>8/8 passing"]
    end

    subgraph "Deployment Tools"
        SETUP["⚙️  setup.sh<br/>Infrastructure<br/>Provisioning"]
        CREATE_BQ["🔧 create_bigquery.py<br/>BigQuery Setup"]
        DEPLOY["🚀 deploy.sh<br/>Deploy Wrapper"]
    end

    subgraph "Build & Container Registry"
        CB["🏗️  Cloud Build<br/>Build Docker Image"]
        AR["📦 Artifact Registry<br/>Store Container Image"]
    end

    subgraph "GCP Deployment"
        INFRA["🌐 Infrastructure<br/>- Cloud Storage<br/>- Pub/Sub<br/>- Cloud Run<br/>- BigQuery<br/>- Service Accounts"]
    end

    GIT -->|Clone| CODE
    CODE -->|Test| TESTS
    CODE -->|Deploy| SETUP
    SETUP -->|Create BQ| CREATE_BQ
    SETUP -->|Deploy| DEPLOY
    DEPLOY -->|Build| CB
    CB -->|Push| AR
    AR -->|Pull & Run| INFRA

    classDef dev fill:#e3f2fd,stroke:#0d47a1
    classDef deploy fill:#fff3e0,stroke:#e65100
    classDef build fill:#f3e5f5,stroke:#4a148c
    classDef cloud fill:#e8f5e9,stroke:#1b5e20

    class GIT,CODE,TESTS dev
    class SETUP,CREATE_BQ,DEPLOY deploy
    class CB,AR build
    class INFRA cloud
```

## Request Flow - Detailed Sequence

```mermaid
sequenceDiagram
    actor User
    participant GCS as Cloud Storage
    participant GCS_N as GCS Notification
    participant PS as Pub/Sub
    participant CR as Cloud Run
    participant Flask as Flask App
    participant Proc as Processor
    participant Helper as GCS/BQ Helper
    participant BQ as BigQuery

    User->>GCS: 1. Upload file (gsutil cp)
    activate GCS
    
    GCS->>GCS_N: 2. Trigger OBJECT_FINALIZE
    deactivate GCS
    
    activate GCS_N
    GCS_N->>PS: 3. Send event message
    deactivate GCS_N
    
    activate PS
    PS->>CR: 4. HTTP POST with message
    deactivate PS
    
    activate CR
    CR->>Flask: 5. Route to / endpoint
    
    activate Flask
    Flask->>Proc: 6. Call process_document()
    deactivate Flask
    
    activate Proc
    Proc->>Helper: 7. Call extract_text_from_file()
    activate Helper
    Helper->>GCS: 8. Download file content
    activate GCS
    GCS-->>Helper: 9. Return file content
    deactivate GCS
    Helper-->>Proc: 10. Return text
    deactivate Helper
    
    Proc->>Proc: 11. count_words()
    Proc->>Proc: 12. extract_tags()
    Proc-->>Flask: 13. Return metadata
    deactivate Proc
    
    activate Flask
    Flask->>Helper: 14. Call insert_metadata_row()
    deactivate Flask
    
    activate Helper
    Helper->>BQ: 15. INSERT row
    activate BQ
    BQ-->>Helper: 16. Acknowledge
    deactivate BQ
    Helper-->>Flask: 17. Return success
    deactivate Helper
    
    activate Flask
    Flask-->>CR: 18. Return 200 OK
    deactivate Flask
    
    CR-->>PS: 19. Acknowledge message
    deactivate CR

    User->>BQ: 20. Query results
    activate BQ
    BQ-->>User: 21. Return metadata
    deactivate BQ
```

## Security & IAM Architecture

```mermaid
graph TB
    subgraph "IAM Structure"
        PROJECT["🔐 GCP Project<br/>ps-my-document-processor"]
        
        subgraph "Service Accounts"
            SA1["👤 doc-processor-sa<br/>Runs Cloud Run Service"]
            SA2["👤 pubsub-invoker-sa<br/>Invokes Cloud Run from Pub/Sub"]
        end

        subgraph "Role Assignments"
            ROLE1["📋 roles/storage.objectViewer<br/>Read GCS objects"]
            ROLE2["📋 roles/bigquery.dataEditor<br/>Insert/Update BQ rows"]
            ROLE3["📋 roles/bigquery.user<br/>Use BigQuery"]
            ROLE4["📋 roles/run.invoker<br/>Invoke Cloud Run"]
        end

        subgraph "Resources Protected"
            RES1["🗄️  Cloud Storage Bucket<br/>gs://PROJECT-docs-ingest"]
            RES2["💾 BigQuery Dataset<br/>docs_metadata"]
            RES3["🚀 Cloud Run Service<br/>doc-processor-service"]
        end
    end

    PROJECT -->|Contains| SA1
    PROJECT -->|Contains| SA2

    SA1 -->|Has| ROLE1
    SA1 -->|Has| ROLE2
    SA1 -->|Has| ROLE3
    SA2 -->|Has| ROLE4

    ROLE1 -->|Protects| RES1
    ROLE2 -->|Protects| RES2
    ROLE3 -->|Protects| RES2
    ROLE4 -->|Protects| RES3

    classDef iam fill:#ede7f6,stroke:#311b92,stroke-width:2px
    classDef sa fill:#f3e5f5,stroke:#6a1b9a,stroke-width:2px
    classDef role fill:#e1bee7,stroke:#512da8,stroke-width:2px
    classDef resource fill:#c5cae9,stroke:#3f51b5,stroke-width:2px

    class PROJECT iam
    class SA1,SA2 sa
    class ROLE1,ROLE2,ROLE3,ROLE4 role
    class RES1,RES2,RES3 resource
```

## Processing States & Error Handling

```mermaid
stateDiagram-v2
    [*] --> ReceiveMessage: File Uploaded
    
    ReceiveMessage --> ValidateMessage: Parse Pub/Sub
    ValidateMessage --> Invalid: Invalid Format
    Invalid --> Acknowledge: Return 204
    
    ValidateMessage --> ValidateFile: Check Metadata
    ValidateFile --> SkipFolder: Is Folder?
    SkipFolder --> Acknowledge
    
    ValidateFile --> DownloadFile: Extract File Info
    DownloadFile --> ExtractText: Read Content
    ExtractText --> ProcessText: Count & Tag
    
    ProcessText --> CreateMetadata: Build Row
    CreateMetadata --> InsertBQ: Stream to BigQuery
    
    InsertBQ --> Success: Rows Inserted
    Success --> Acknowledge: Return 200
    
    InsertBQ --> Error: Insert Failed
    Error --> Retry: Pub/Sub Retries
    Retry --> InsertBQ
    
    Acknowledge --> [*]

    style ReceiveMessage fill:#c8e6c9
    style ValidateMessage fill:#c8e6c9
    style ExtractText fill:#fff9c4
    style ProcessText fill:#fff9c4
    style CreateMetadata fill:#fff9c4
    style InsertBQ fill:#ffccbc
    style Success fill:#a5d6a7
    style Error fill:#ef9a9a
    style Retry fill:#ffe082
    style Acknowledge fill:#a5d6a7
    style Invalid fill:#ef9a9a
    style SkipFolder fill:#f0f4c3
```

---

## Key Metrics

| Component | Technology | Scalability | Cost |
|-----------|------------|------------|------|
| Ingestion | Cloud Storage | Unlimited | $0.02-0.04/GB |
| Messaging | Pub/Sub | 1M+ msg/sec | $0.40/1k msgs |
| Compute | Cloud Run | Auto-scaling 0-100+ | $0.00002400/vCPU-sec |
| Storage | BigQuery | PB-scale | $0.01/row or $6.25/TB |

## Deployment Timeline

```mermaid
timeline
    title Deployment Steps
    section Setup
        1. gcloud auth login
        2. gcloud config set project
        3. python3 create_bigquery.py
    section Deployment
        4. ./deploy.sh (2-3 min)
        5. Creates Cloud Storage
        6. Creates Pub/Sub Topic
        7. Deploys Cloud Run
    section Testing
        8. ./test_cloud.sh
        9. Upload test files
        10. Query BigQuery
    section Complete
        11. Pipeline Ready!
        12. Monitor in Cloud Console
```
