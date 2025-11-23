# 📘 MASTER DOCUMENTATION - ETE-ML-PIPELINE

**Complete Technical Guide** - Deep dive into the End-to-End ML Pipeline architecture and components

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [System Architecture](#2-system-architecture)
3. [Component Deep Dive](#3-component-deep-dive)
4. [Data Flow & Pipeline Workflow](#4-data-flow--pipeline-workflow)
5. [Deployment Architecture](#5-deployment-architecture)

---

## 1. Project Overview

### What is This Project?

**ETE-ML-PIPELINE** is a production-grade MLOps system demonstrating how real-world machine learning pipelines are built. It implements a complete workflow from raw data ingestion to serving predictions via a web UI.

**Use Case:** Predicting Click-Through Rates (CTR) for online advertising using the Criteo dataset

**Key Features:**
- ✅ Automated data ingestion and chunking from 45M+ row dataset
- ✅ Scheduled model training every 10 minutes
- ✅ Automatic model versioning and promotion to Production
- ✅ Real-time model serving with full provenance tracking
- ✅ Modern web interface for predictions
- ✅ Complete traceability: every prediction shows exact model version, run ID, and artifact location

---

## 2. System Architecture

### Architecture Diagram

<!-- TODO: Add architecture diagram -->
![System Architecture](docs/images/architecture-overview.png)

### Component Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                         KUBERNETES CLUSTER                          │
│                         Namespace: harshith                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐          │
│  │  PostgreSQL  │◄───┤   Airflow    │───►│    MinIO     │          │
│  │  (Metadata)  │    │ (Orchestrate)│    │  (Storage)   │          │
│  └──────────────┘    └──────┬───────┘    └──────┬───────┘          │
│                              │                    │                │
│                              │                    │                │
│                              ▼                    ▼                │
│                       ┌──────────────┐    ┌──────────────┐          │
│                       │   MLflow     │◄───┤   Training   │          │
│                       │  (Registry)  │    │    (Task)    │          │
│                       └──────┬───────┘    └──────────────┘          │
│                              │                                       │
│                              ▼                                       │
│                       ┌──────────────┐                              │
│                       │   BentoML    │                              │
│                       │  (Serving)   │                              │
│                       └──────┬───────┘                              │
│                              │                                       │
│                              ▼                                       │
│                       ┌──────────────┐                              │
│                       │   Frontend   │                              │
│                       │   (FastAPI)  │                              │
│                       └──────────────┘                              │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Data Flow

```
Raw Data (Criteo) → Download → MinIO (raw/) → Chunk Producer → MinIO (chunks/)
                                                                      ↓
                                                              Cumulative Builder
                                                                      ↓
                                                              MinIO (cumulative/)
                                                                      ↓
                                                              Training Task
                                                                      ↓
                                                              MLflow Registry
                                                                      ↓
                                                              BentoML Service
                                                                      ↓
                                                              Frontend UI
```

---

## 3. Component Deep Dive

### 3.1 PostgreSQL

<!-- TODO: Add PostgreSQL diagram -->
![PostgreSQL Setup](docs/images/postgres-setup.png)

**Purpose:** Backend database for Airflow and MLflow metadata

**What It Does:**
- Stores Airflow DAG runs, task states, connections, and variables
- Stores MLflow experiment metadata, runs, parameters, and metrics
- Provides ACID-compliant storage for critical metadata

**Deployment Details:**
- **Image:** `postgres:13`
- **Port:** 5432
- **Databases Created:**
  - `airflow` - Airflow metadata
  - `mlflow` - MLflow tracking server metadata
- **Credentials:** postgres/postgres
- **Persistence:** Uses Kubernetes PVC (optional, currently using emptyDir)

**Why PostgreSQL?**
- Industry standard for OLTP workloads
- Strong consistency guarantees
- Well-supported by Airflow and MLflow
- Easy to backup and restore

---

### 3.2 MinIO

<!-- TODO: Add MinIO architecture diagram -->
![MinIO Storage Layout](docs/images/minio-layout.png)

**Purpose:** S3-compatible object storage for data and model artifacts

**What It Does:**
MinIO acts as the central data lake for the entire pipeline, storing:
- **Raw data:** Original Criteo dataset (`raw/train.txt.gz`) - ~4GB compressed
- **Chunked data:** Incremental 1M-line chunks (`chunks/chunk_000000.txt`)
- **Parquet data:** Processed cumulative datasets (`cumulative/cumulative_000000.parquet`)
- **Model artifacts:** Trained XGBoost models from MLflow (`mlflow-artifacts/`)
- **State files:** Pipeline state tracking (`state/next_line.txt`, `state/total_lines.txt`)

**Storage Layout:**
```
criteo-bucket/
├── raw/
│   ├── train.txt.gz           # Original 45M line dataset
│   └── .keep
├── chunks/
│   ├── chunk_000000.txt       # 1M lines each
│   ├── chunk_000001.txt
│   └── ...
├── cumulative/
│   ├── cumulative_000000.parquet
│   ├── cumulative_000001.parquet
│   └── ...
├── mlflow-artifacts/
│   └── 1/
│       └── <run_id>/
│           └── artifacts/
│               └── model/
│                   ├── model.xgb
│                   ├── MLmodel
│                   └── ...
└── state/
    ├── next_line.txt          # Tracks next line to chunk
    ├── total_lines.txt        # Total lines in dataset
    └── last_agg_idx.txt       # Last aggregated chunk
```

**Deployment Details:**
- **Image:** `minio/minio:latest`
- **Ports:** 9000 (API), 9090 (Console)
- **Credentials:** minio/minio123
- **Buckets:** `criteo-bucket` (auto-created)
- **Storage:** Kubernetes PVC or emptyDir

**Why MinIO?**
- S3-compatible API (works with boto3, MLflow, etc.)
- Self-hosted alternative to AWS S3
- Fast, lightweight, perfect for on-prem Kubernetes
- Direct integration with MLflow for artifact storage

---

### 3.3 Apache Airflow

<!-- TODO: Add Airflow DAG diagram -->
![Airflow DAG Visualization](docs/images/airflow-dag.png)

**Purpose:** Workflow orchestration and scheduling

**What It Does:**
Airflow is the brain of the pipeline. It orchestrates all data processing and training tasks:

**DAGs Deployed:**

1. **`criteo_master_pipeline`** (Main Pipeline - Runs every 10 minutes)
   - Task 1: `produce_chunk` - Download raw data, chunk into 1M lines
   - Task 2: `build_cumulative` - Convert chunks to Parquet format
   - Task 3: `train_model` - Train XGBoost, log to MLflow, register model
   - Task 4: `reload_bento` - Trigger BentoML to reload new model

2. **`criteo_chunk_producer`** (Manual)
   - Downloads Criteo dataset
   - Splits into manageable chunks
   - Uploads to MinIO

3. **`criteo_cumulative_builder`** (Manual)
   - Reads new chunks from MinIO
   - Converts TSV to Parquet
   - Stores cumulative datasets

4. **`criteo_training_pipeline`** (Manual)
   - Standalone training DAG
   - Reads all cumulative data
   - Trains and registers model

**Custom Airflow Image:**
- **Base:** `apache/airflow:2.10.1-python3.11`
- **Added Dependencies:**
  - MLflow 2.9.2 (for model logging)
  - XGBoost 2.0.3 (for training)
  - boto3 (for S3/MinIO access)
  - pandas, pyarrow, scikit-learn

**Deployment Details:**
- **Components:**
  - Webserver (UI on port 8080)
  - Scheduler (executes tasks)
- **Executor:** LocalExecutor (single-node)
- **Backend:** PostgreSQL
- **Logs:** Stored in MinIO or local volume
- **Credentials:** admin/admin

**How Airflow Works Here:**
1. Scheduler monitors DAGs and creates task instances
2. Tasks execute Python functions that interact with MinIO, MLflow, etc.
3. State is persisted in PostgreSQL
4. Logs are captured and stored
5. On failure, tasks can retry automatically

**Why Airflow?**
- Industry standard for data orchestration
- DAG-based workflow definition (Python code)
- Rich UI for monitoring and debugging
- Built-in retry logic and error handling
- Extensive integrations (S3, databases, APIs)

---

### 3.4 MLflow

<!-- TODO: Add MLflow UI screenshot -->
![MLflow Model Registry](docs/images/mlflow-registry.png)

**Purpose:** ML experiment tracking and model registry

**What It Does:**

**1. Experiment Tracking:**
- Records every training run with unique run ID
- Logs hyperparameters (max_depth, eta, objective)
- Logs metrics (train_rows, accuracy, etc.)
- Assigns auto-generated run names (e.g., "glamorous-goose-948")

**2. Artifact Storage:**
- Saves trained models to MinIO via S3 protocol
- Stores model files (model.xgb), dependencies, metadata
- Maintains artifact URI for each run

**3. Model Registry:**
- Registers models with name `criteo_ctr_model`
- Versions models automatically (v1, v2, v3, ...)
- Manages stages: None → Staging → Production
- Archives old Production models when promoting new ones

**MLflow Run Lifecycle:**
```python
with mlflow.start_run():
    # 1. Set experiment
    mlflow.set_experiment("criteo_ctr")
    
    # 2. Log params
    mlflow.log_params({"max_depth": 8, "eta": 0.15})
    
    # 3. Train model
    model = xgb.train(params, dtrain, num_boost_round=200)
    
    # 4. Log model to MinIO
    mlflow.xgboost.log_model(model, artifact_path="model")
    
    # 5. Register model
    mlflow.register_model("runs:/{}/model".format(run_id), "criteo_ctr_model")
    
    # 6. Promote to Production
    client.transition_model_version_stage(
        name="criteo_ctr_model",
        version=version,
        stage="Production",
        archive_existing_versions=True
    )
```

**Model Provenance Captured:**
- Run ID (e.g., `6820c410efef45449fbb6ab1044f340c`)
- Run Name (e.g., `glamorous-goose-948`)
- Version (e.g., `3`)
- Stage (`Production`)
- Artifact URI (`s3://mlflow-artifacts/1/6820c410.../artifacts/model`)
- Training timestamp, parameters, metrics

**Deployment Details:**
- **Image:** `ghcr.io/mlflow/mlflow:v2.9.2`
- **Port:** 5000
- **Backend Store:** PostgreSQL (metadata)
- **Artifact Store:** MinIO S3 (model files)
- **Default Artifact Root:** `s3://mlflow-artifacts`

**Environment Variables:**
```bash
MLFLOW_S3_ENDPOINT_URL=http://minio:9000
AWS_ACCESS_KEY_ID=minio
AWS_SECRET_ACCESS_KEY=minio123
```

**Why MLflow?**
- De facto standard for ML experiment tracking
- Built-in model registry with versioning
- S3-compatible artifact storage
- REST API for model serving
- Language-agnostic (Python, R, Java, etc.)

---

### 3.5 BentoML Service

<!-- TODO: Add BentoML architecture diagram -->
![BentoML Service Architecture](docs/images/bento-architecture.png)

**Purpose:** Model serving with production-ready APIs

**What It Does:**
BentoML loads the Production model from MLflow and exposes REST APIs for predictions:

**API Endpoints:**

1. **`POST /predict`** - Make predictions
   ```json
   Request:
   {
     "features": [[feat1, feat2, ..., feat39], ...]
   }
   
   Response:
   {
     "predictions": [0.0234, 0.0156, ...],
     "model_name": "criteo_ctr_model",
     "model_stage": "Production",
     "num_samples": 2
   }
   ```

2. **`POST /health`** - Health check
   ```json
   {
     "status": "healthy",
     "model_name": "criteo_ctr_model",
     "model_stage": "Production",
     "mlflow_uri": "http://mlflow:5000"
   }
   ```

3. **`POST /model_info`** - Model metadata
   ```json
   {
     "model_name": "criteo_ctr_model",
     "model_stage": "Production",
     "versions": [
       {
         "version": "3",
         "stage": "Production",
         "run_id": "6820c410efef...",
         "creation_timestamp": "1234567890"
       }
     ]
   }
   ```

**How BentoML Loads Models:**
```python
# 1. Connect to MLflow
mlflow.set_tracking_uri("http://mlflow:5000")

# 2. Load Production model
model_uri = f"models:/criteo_ctr_model/Production"
model = mlflow.xgboost.load_model(model_uri)

# 3. Serve via BentoML
@svc.api(input=JSON(), output=JSON())
def predict(input_data: dict) -> dict:
    features = input_data["features"]
    dmatrix = xgb.DMatrix(np.array(features))
    predictions = model.predict(dmatrix)
    return {"predictions": predictions.tolist()}
```

**Model Reload Strategy:**
- **Initial Load:** Model loaded at service startup
- **Reload Trigger:** After training completes, `reload_bento` task calls `/reload` endpoint
- **Hot Reload:** Service reloads model without restart (future enhancement)
- **Fallback:** If Production model not found, loads latest version

**Deployment Details:**
- **Image:** `harshith21/ete-ml-pipeline-bento:latest`
- **Port:** 3000
- **Dependencies:** BentoML 1.3.8, MLflow, XGBoost
- **Service File:** `service.py` mounted via ConfigMap

**Why BentoML?**
- Built for production ML serving
- Automatic API generation
- Performance optimizations (batching, caching)
- Easy integration with MLflow
- Supports multiple ML frameworks

---

### 3.6 Frontend (FastAPI)

<!-- TODO: Add Frontend UI screenshot -->
![Frontend Prediction UI](docs/images/frontend-ui.png)

**Purpose:** User-friendly web interface for predictions

**What It Does:**
Provides a beautiful web UI for users to interact with the ML model:

**Features:**
1. **Model Information Display**
   - Shows current Production model version
   - Lists all registered model versions
   - Displays model metadata (run ID, stage, etc.)

2. **Sample Data Loading**
   - One-click button to load example features
   - Pre-loaded with valid 39-feature samples

3. **Prediction Interface**
   - Input: 39 feature values (I1-I13, C1-C26)
   - Output: CTR probability (0-100%)
   - Shows raw probability and percentage

4. **Model Provenance**
   - Every prediction shows:
     - Model version
     - Run ID (links to MinIO artifact)
     - Run name
     - Stage (Production/Staging)
     - Artifact URI

**Frontend Architecture:**
```python
# FastAPI app
app = FastAPI()

@app.get("/")
async def home():
    # Render HTML UI
    return templates.TemplateResponse("index.html")

@app.post("/api/predict")
async def predict(request: Request):
    data = await request.json()
    
    # Call BentoML service
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BENTO_URL}/predict",
            json={"features": data["features"]}
        )
    
    return response.json()

@app.get("/api/model-info")
async def get_model_info():
    # Query BentoML for model info
    response = await client.post(f"{BENTO_URL}/model_info")
    return response.json()
```

**UI Stack:**
- **Backend:** FastAPI (Python async web framework)
- **Frontend:** HTML + Vanilla JavaScript
- **Styling:** Custom CSS with gradient design
- **HTTP Client:** httpx (async requests)

**Deployment Details:**
- **Image:** `harshith21/ete-ml-pipeline-frontend:latest`
- **Port:** 8081
- **Backend:** FastAPI + Uvicorn
- **Templates:** Jinja2 HTML templates

**Why FastAPI?**
- Modern Python web framework (per user preference)
- Async support for high concurrency
- Automatic API documentation (Swagger)
- Type hints and validation
- Fast and lightweight

---

## 4. Data Flow & Pipeline Workflow

### 4.1 Complete Pipeline Flow

<!-- TODO: Add pipeline flow diagram -->
![Complete Pipeline Flow](docs/images/pipeline-flow.png)

**End-to-End Journey:**

```
1. DATA INGESTION
   ↓
   Criteo Dataset (45M rows, 4GB compressed)
   ↓
   Download via requests library
   ↓
   Upload to MinIO (raw/train.txt.gz)
   
2. CHUNKING
   ↓
   Read raw file with gzip
   ↓
   Split into 1M-line chunks
   ↓
   Upload chunks to MinIO (chunks/chunk_*.txt)
   ↓
   Track state: next_line = 0 → 1M → 2M → ...
   
3. AGGREGATION
   ↓
   Read chunks from MinIO
   ↓
   Parse TSV format (tab-separated)
   ↓
   Convert to Parquet (columnar, compressed)
   ↓
   Upload to MinIO (cumulative/cumulative_*.parquet)
   
4. TRAINING
   ↓
   Load all Parquet files
   ↓
   Concat into single DataFrame
   ↓
   Feature engineering (categorical → numeric)
   ↓
   Train XGBoost (200 rounds)
   ↓
   Log to MLflow (params, metrics, model)
   ↓
   Register in Model Registry
   ↓
   Promote to Production stage
   
5. SERVING
   ↓
   BentoML loads Production model
   ↓
   Exposes /predict API
   ↓
   Frontend calls BentoML
   ↓
   User gets prediction + provenance
```

### 4.2 Criteo Dataset Format

**Original Format (TSV):**
```
<label>\t<I1>\t<I2>\t...\t<I13>\t<C1>\t<C2>\t...\t<C26>
0       1       2       ...     13      a1      b2      ...     z26
1       5       0       ...     42      a3      b1      ...     z12
```

**Features:**
- **Label:** 0 (no click) or 1 (click)
- **Integer Features (I1-I13):** Numeric features (e.g., counts, IDs)
- **Categorical Features (C1-C26):** Hashed categorical values

**After Processing:**
- Categorical features converted to numeric codes
- 39 total features for XGBoost training
- Stored as Parquet for efficient columnar access

### 4.3 Master Pipeline DAG

**`criteo_master_pipeline` - Runs Every 10 Minutes**

```
┌─────────────────┐
│ produce_chunk   │  Download raw, chunk 1M lines, upload
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│build_cumulative │  Convert chunks to Parquet
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  train_model    │  Train XGBoost, register in MLflow
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ reload_bento    │  Trigger BentoML reload (hot reload)
└─────────────────┘
```

**Task Details:**

**Task 1: produce_chunk**
- Downloads Criteo dataset if not present
- Counts total lines (one-time operation)
- Reads state: next_line (defaults to 0)
- Extracts 1M lines starting from next_line
- Uploads chunk to MinIO
- Updates next_line state (+1M)

**Task 2: build_cumulative**
- Lists all chunks in MinIO
- Reads state: last_agg_idx (defaults to -1)
- Processes only new chunks (idx > last_agg_idx)
- Parses TSV format
- Converts to Parquet with PyArrow
- Uploads cumulative Parquet
- Updates last_agg_idx state

**Task 3: train_model**
- Loads all cumulative Parquet files
- Concatenates into single DataFrame
- Separates features (X) and labels (y)
- Converts categorical columns to numeric codes
- Creates XGBoost DMatrix
- Trains with params: `max_depth=8, eta=0.15, objective=binary:logistic`
- Logs to MLflow (params, metrics, model artifact)
- Registers model as `criteo_ctr_model`
- Promotes to Production stage (archives old versions)

**Task 4: reload_bento**
- Sends POST request to BentoML `/reload` endpoint
- BentoML reloads Production model from MLflow
- On failure, logs warning (model still in registry)

### 4.4 State Management

**Why State Tracking?**
- Prevents reprocessing same data
- Enables incremental updates
- Supports idempotent task execution

**State Files in MinIO:**

1. **`state/total_lines.txt`**
   - Contains total lines in raw dataset
   - Computed once during first run
   - Example: `45840617`

2. **`state/next_line.txt`**
   - Tracks next line to chunk
   - Updated after each chunk produced
   - Example: `2000000` (2M lines processed)

3. **`state/last_agg_idx.txt`**
   - Tracks last aggregated chunk index
   - Updated after each chunk converted to Parquet
   - Example: `1` (chunk_000001 processed)

---

## 5. Deployment Architecture

### 5.1 Kubernetes Setup

**Namespace:** `harshith`

**Resources:**
```yaml
Namespace: harshith
├── ConfigMaps:
│   ├── airflow-dags        # DAG Python files
│   └── bento-service       # BentoML service.py
├── Deployments:
│   ├── postgres            # 1 replica
│   ├── minio               # 1 replica
│   ├── airflow-webserver   # 1 replica
│   ├── airflow-scheduler   # 1 replica
│   ├── mlflow              # 1 replica
│   ├── bento-svc           # 1 replica
│   └── frontend            # 1 replica
└── Services:
    ├── postgres (5432)
    ├── minio (9000, 9090)
    ├── airflow-webserver (8080)
    ├── mlflow (5000)
    ├── bento-svc (3000)
    └── frontend (8081)
```

### 5.2 Service Dependencies

```
postgres (start first)
    ↓
minio (needs to be ready)
    ↓
airflow (needs postgres + minio)
    ↓
mlflow (needs postgres + minio)
    ↓
bento (needs mlflow + minio)
    ↓
frontend (needs bento)
```

### 5.3 Environment Variables

**Airflow + Training:**
```bash
AWS_ENDPOINT_URL=http://minio.harshith.svc.cluster.local:9000
AWS_ACCESS_KEY_ID=minio
AWS_SECRET_ACCESS_KEY=minio123
S3_BUCKET=criteo-bucket
MLFLOW_TRACKING_URI=http://mlflow.harshith.svc.cluster.local:5000
```

**MLflow:**
```bash
MLFLOW_S3_ENDPOINT_URL=http://minio.harshith.svc.cluster.local:9000
AWS_ACCESS_KEY_ID=minio
AWS_SECRET_ACCESS_KEY=minio123
```

**BentoML:**
```bash
MLFLOW_TRACKING_URI=http://mlflow.harshith.svc.cluster.local:5000
MLFLOW_S3_ENDPOINT_URL=http://minio.harshith.svc.cluster.local:9000
MODEL_NAME=criteo_ctr_model
MODEL_STAGE=Production
```

**Frontend:**
```bash
BENTO_URL=http://bento-svc.harshith.svc.cluster.local:3000
```

### 5.4 Port Forwarding

**Access Services Locally:**
```bash
# Terminal 1: Airflow UI
kubectl port-forward -n harshith svc/airflow-webserver 8080:8080

# Terminal 2: MLflow UI
kubectl port-forward -n harshith svc/mlflow 5000:5000

# Terminal 3: MinIO Console
kubectl port-forward -n harshith svc/minio 9090:9090

# Terminal 4: Frontend UI
kubectl port-forward -n harshith svc/frontend 8081:8081
```

### 5.5 Docker Images

**Custom Images (Multi-platform: amd64/arm64):**

1. **`harshith21/ete-ml-pipeline-airflow:latest`**
   - Base: `apache/airflow:2.10.1-python3.11`
   - Added: MLflow, XGBoost, boto3, pandas, pyarrow
   - Size: ~1.5GB

2. **`harshith21/ete-ml-pipeline-bento:latest`**
   - Base: `python:3.11-slim`
   - Added: BentoML, MLflow, XGBoost, numpy
   - Includes: service.py
   - Size: ~800MB

3. **`harshith21/ete-ml-pipeline-frontend:latest`**
   - Base: `python:3.11-slim`
   - Added: FastAPI, uvicorn, httpx, jinja2
   - Includes: app.py, templates/
   - Size: ~400MB

**Official Images:**
- `postgres:13`
- `minio/minio:latest`
- `ghcr.io/mlflow/mlflow:v2.9.2`

### 5.6 Troubleshooting Common Issues

**Issue 1: Model Not Loaded in BentoML**
- **Cause:** BentoML starts before first model is trained
- **Solution:** Restart BentoML after training completes
  ```bash
  ./main.sh restart bento
  ```

**Issue 2: Airflow DAG Not Running**
- **Cause:** DAG is paused by default
- **Solution:** Unpause in Airflow UI or CLI
  ```bash
  kubectl exec -n harshith deploy/airflow-scheduler -- \
    airflow dags unpause criteo_master_pipeline
  ```

**Issue 3: MinIO Connection Refused**
- **Cause:** MinIO pod not ready
- **Solution:** Wait for pod to be Running
  ```bash
  kubectl get pods -n harshith -l app=minio
  ```

**Issue 4: Training Fails with "No data found"**
- **Cause:** No cumulative Parquet files in MinIO
- **Solution:** Run chunk producer and aggregator first
  ```bash
  # Trigger in Airflow UI or via CLI
  kubectl exec -n harshith deploy/airflow-scheduler -- \
    airflow dags trigger criteo_chunk_producer
  ```

---

## Summary

This MLOps pipeline demonstrates:

✅ **Production MLOps Architecture** - Microservices, containers, orchestration  
✅ **Industry-Standard Tools** - Airflow, MLflow, BentoML, Kubernetes  
✅ **Full Automation** - Scheduled training, auto-deployment, hot reload  
✅ **Model Governance** - Versioning, staging, promotion, archival  
✅ **Complete Traceability** - Every prediction links to exact training run  
✅ **Scalable Design** - Kubernetes-native, cloud-ready  
✅ **Production-Ready** - Error handling, logging, monitoring hooks  

**Key Takeaways:**
- **Airflow** orchestrates the entire pipeline
- **MinIO** provides centralized S3-compatible storage
- **MLflow** tracks experiments and manages model registry
- **BentoML** serves models with production APIs
- **FastAPI** provides user-friendly prediction interface
- **PostgreSQL** stores metadata for Airflow and MLflow
- **Kubernetes** provides scalable, resilient infrastructure

---

**Built with ❤️ for learning and demonstration**
