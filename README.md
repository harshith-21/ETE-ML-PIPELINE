# 🚀 ETE-ML-PIPELINE

**End-to-End ML Pipeline** - A production-ready machine learning infrastructure for continuous training, model versioning, and inference with full model provenance tracking.

## 🎯 Project Overview

ETE-ML-PIPELINE is a complete end-to-end machine learning pipeline that demonstrates production-grade MLOps practices for **Criteo Click-Through Rate (CTR) prediction** using:

- **Apache Airflow** - Orchestration and workflow management
- **MinIO** - S3-compatible object storage for artifacts and logs
- **MLflow** - Experiment tracking and model registry
- **BentoML** - Model serving with version tracking
- **FastAPI** - User-facing frontend with prediction UI
- **PostgreSQL** - Backend storage for Airflow and MLflow
- **Kubernetes** - Container orchestration platform

## 📊 Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Data Flow                               │
└─────────────────────────────────────────────────────────────────┘

   ┌──────────────┐
   │   Frontend   │──► User inputs features
   │  (FastAPI)   │◄── Returns predictions + model provenance
   └──────┬───────┘
          │
          ▼
   ┌──────────────┐
   │   BentoML    │──► Loads model from MLflow
   │  (Serving)   │    Tracks: version, run_id, run_name, artifact_uri
   └──────┬───────┘
          │
          ▼
   ┌──────────────┐
   │   MLflow     │──► Model registry + experiment tracking
   │  (Registry)  │    Manages: Production/Staging stages
   └──────┬───────┘
          │
          ▼
   ┌──────────────┐
   │   Airflow    │──► Orchestrates training pipeline
   │ (Scheduler)  │    DAGs: criteo_training_pipeline
   └──────┬───────┘
          │
          ▼
   ┌──────────────┐
   │    MinIO     │──► Stores: training data, models, logs
   │  (Storage)   │    Buckets: criteo-data, criteo-logs, mlflow-artifacts
   └──────────────┘
```

## ✨ Key Features

### 🔍 **Model Provenance Tracking**
- Every prediction shows which exact model made it
- Displays: Run Name (MLflow nickname), Run ID (hash), Artifact URI
- Full traceability from MinIO artifact path to prediction result

### 🔄 **Automated Training Pipeline**
- Periodic model retraining with Airflow
- XGBoost model training on Criteo CTR dataset
- Automatic model registration and promotion in MLflow

### 📦 **Model Versioning**
- All models tracked in MLflow registry
- Production/Staging stage management
- BentoML automatically loads latest Production model

### 🎨 **User-Friendly Frontend**
- Web UI for making predictions
- Real-time model information display
- Shows all registered model versions and their stages

## 🚀 Quick Start

### Prerequisites

- Kubernetes cluster (minikube, kind, or cloud provider)
- kubectl configured with cluster access
- Docker (for building custom images)
- Docker Hub account (for pushing images)

### 1. Deploy Infrastructure

```bash
# Deploy all services at once
./main.sh start all

# Or deploy step-by-step
./main.sh start postgres    # PostgreSQL for Airflow + MLflow
./main.sh start minio        # Object storage
./main.sh start airflow      # Orchestration (includes DAGs in ConfigMaps)
./main.sh start mlflow       # Model registry
./main.sh start bento        # Model serving
./main.sh start frontend     # User interface
```

### 2. Access Services

Set up port forwarding to access the UIs:

```bash
# Airflow UI (admin/admin)
kubectl port-forward -n harshith svc/airflow-webserver 8080:8080

# MinIO Console (minio/minio123)
kubectl port-forward -n harshith svc/minio 9090:9090

# MLflow UI
kubectl port-forward -n harshith svc/mlflow 5000:5000

# Frontend (Make Predictions!)
kubectl port-forward -n harshith svc/frontend 8081:8081
```

Then visit:
- **Airflow**: http://localhost:8080
- **MinIO**: http://localhost:9090
- **MLflow**: http://localhost:5000
- **Frontend**: http://localhost:8081 ⭐

### 3. Run Training Pipeline

1. Navigate to Airflow UI (http://localhost:8080)
2. Find the `criteo_training_pipeline` DAG
3. Click "Trigger DAG" to start training
4. Watch the pipeline: ingest → process → train → register → promote
5. Model appears in MLflow and BentoML automatically loads it

### 4. Make Predictions

1. Open the Frontend (http://localhost:8081)
2. Use sample inputs from `sample_input_frontend.txt`
3. Click "🚀 Predict CTR"
4. See prediction with full model provenance:
   - Model version
   - Run name (e.g., "glamorous-goose-948")
   - Run ID hash (e.g., "6820c410efef...")
   - Artifact URI in MinIO

## 📦 Custom Docker Images

All custom images are multi-platform (linux/amd64, linux/arm64) and hosted on Docker Hub.

### Airflow (`harshith21/ete-ml-pipeline-airflow:latest`)

Custom Airflow 2.10.1 with Python 3.11 and ML dependencies:
- MLflow 2.9.2
- XGBoost 2.0.3
- scikit-learn 1.4.2
- pandas 2.1.3
- boto3 (for S3/MinIO)

### BentoML (`harshith21/ete-ml-pipeline-bento:latest`)

Custom BentoML service that:
- Loads models from MLflow registry
- Tracks model metadata (version, run_id, run_name)
- Exposes /predict, /health, /model_info endpoints
- Automatically uses Production stage models

### Frontend (`harshith21/ete-ml-pipeline-frontend:latest`)

FastAPI application with:
- Beautiful prediction UI
- Model provenance display
- Sample data loader
- Real-time model information

### Building Images

```bash
cd custom_dockerfiles

# Build individual service
cd airflow && ./build.sh
cd bento && ./build.sh
cd frontend && ./build.sh

# Or build all at once
./build-all.sh
```

Images are automatically pushed to Docker Hub during build.

## 🛠️ Management Commands

The `main.sh` script provides unified service management:

```bash
./main.sh <action> <service>
```

### Actions
- `start` - Deploy/start a service
- `stop` - Stop a service (scale to 0)
- `restart` - Restart a service
- `cleanup` - Remove a service completely (deployments + services + configmaps)
- `status` - Show service status
- `deploy_all` - Deploy all services
- `cleanup_all` - Remove everything

### Services
- `postgres` - PostgreSQL databases
- `minio` - MinIO object storage
- `airflow` - Airflow (scheduler + webserver)
- `mlflow` - MLflow tracking server
- `bento` - BentoML model serving
- `frontend` - FastAPI frontend
- `all` - All services at once

### Examples

```bash
# Start services
./main.sh start postgres
./main.sh start airflow

# Restart to pick up changes
./main.sh restart airflow
./main.sh restart bento

# Check status
./main.sh status all

# Full cleanup
./main.sh cleanup all
```

## 📁 Project Structure

```
.
├── README.md                       # This file
├── main.sh                         # Service management script
├── sample_input_frontend.txt       # Sample inputs for testing
├── adminkubeconfig.yaml            # Kubernetes config (gitignored)
│
├── infra-k8s/                      # Kubernetes manifests
│   ├── 0.namespace.yaml            # Namespace: harshith
│   ├── 1.postgres.yaml             # PostgreSQL for Airflow + MLflow
│   ├── 2.airflow.yaml              # Airflow webserver + scheduler
│   ├── 2a.airflowconfigmaps.yaml   # DAGs (criteo_training_pipeline)
│   ├── 2b.Minio.yaml               # MinIO S3-compatible storage
│   ├── 3.mlflow.yaml               # MLflow tracking + registry
│   ├── 4.bento.yaml                # BentoML serving (with ConfigMap)
│   └── 5.frontend.yaml             # FastAPI frontend
│
└── custom_dockerfiles/             # Custom Docker images
    ├── README.md
    ├── build-all.sh
    ├── push-all.sh
    │
    ├── airflow/                    # Custom Airflow image
    │   ├── Dockerfile
    │   ├── build.sh
    │   ├── build-local.sh
    │   ├── push.sh
    │   ├── README.md
    │   └── README-BUILD.md
    │
    ├── bento/                      # Custom BentoML image
    │   ├── Dockerfile
    │   ├── service.py              # BentoML service definition
    │   ├── requirements.txt
    │   ├── build.sh
    │   ├── push.sh
    │   └── README.md
    │
    └── frontend/                   # Custom Frontend image
        ├── Dockerfile
        ├── app.py                  # FastAPI application
        ├── requirements.txt
        ├── build.sh
        ├── templates/
        │   └── index.html          # Prediction UI
        └── .dockerignore
```

## 🎓 Use Case: Criteo CTR Prediction

The pipeline demonstrates a complete ML workflow for predicting click-through rates:

### 1. **Data Ingestion** (Airflow DAG)
- Downloads Criteo CTR dataset
- Processes and prepares training data
- Stores in MinIO buckets

### 2. **Model Training** (XGBoost)
- Trains on 39 features (13 integer + 26 categorical)
- Logs metrics, parameters, and artifacts to MLflow
- Handles categorical feature encoding automatically

### 3. **Model Registration** (MLflow)
- Registers model with version tracking
- Stores in MinIO (`mlflow-artifacts` bucket)
- Promotes to Production stage

### 4. **Model Serving** (BentoML)
- Loads Production model from MLflow
- Captures metadata: version, run_id, run_name, artifact_uri
- Exposes REST API for predictions

### 5. **User Interface** (FastAPI)
- Accepts 39 feature values
- Returns CTR prediction (%)
- Shows full model provenance

## 🔍 Model Provenance Example

When you make a prediction, you see:

```
✅ Prediction: 2.45% CTR

🔍 Model Provenance:
├─ Model Name: criteo_ctr_model
├─ Version: 2
├─ Stage: Production
├─ Run Name: glamorous-goose-948  (MLflow nickname)
├─ Run ID: 6820c410efef45449fbb6ab1044f340c
└─ Artifact URI: s3://mlflow-artifacts/1/6820c410efef45449fbb6ab1044f340c/artifacts/model
```

This hash (`6820c410efef...`) matches exactly what you see in MinIO at:
`http://minio:9090/browser/mlflow-artifacts/1/6820c410efef45449fbb6ab1044f340c/`

## 🔧 Configuration

### Kubernetes Namespace
All services run in the `harshith` namespace.

### Storage Configuration
- **Airflow logs**: MinIO bucket `criteo-logs`
- **Training data**: MinIO bucket `criteo-data`
- **Model artifacts**: MinIO bucket `mlflow-artifacts`

### Default Credentials
- **PostgreSQL (Airflow)**: airflow / airflow
- **PostgreSQL (MLflow)**: mlflow / mlflow
- **MinIO**: minio / minio123
- **Airflow Admin**: admin / admin

### Environment Variables
All services configured via K8s env vars in manifests. Key configurations:
- `MLFLOW_TRACKING_URI`: http://mlflow.harshith.svc.cluster.local:5000
- `MLFLOW_S3_ENDPOINT_URL`: http://minio.harshith.svc.cluster.local:9000
- `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY`: MinIO credentials

## 📚 Documentation

- [Custom Docker Images](custom_dockerfiles/README.md)
- [Airflow Image Details](custom_dockerfiles/airflow/README.md)
- [BentoML Service](custom_dockerfiles/bento/README.md)
- [Sample Inputs](sample_input_frontend.txt)

## 🐛 Troubleshooting

### Pods not starting?
```bash
kubectl get pods -n harshith
kubectl describe pod <pod-name> -n harshith
kubectl logs <pod-name> -n harshith
```

### Image pull errors?
Ensure images are built for correct platform (linux/amd64 or linux/arm64).
Use `./build.sh` which builds multi-platform images automatically.

### Can't access services?
Check port-forward is running and namespace is correct:
```bash
kubectl port-forward -n harshith svc/<service-name> <local-port>:<service-port>
```

### Training pipeline fails?
Check Airflow logs:
```bash
kubectl logs -n harshith -l app=airflow-scheduler --tail=100
```

Check MLflow is running:
```bash
kubectl get pods -n harshith -l app=mlflow
```

---
---

In a shocking plot twist that surprised absolutely no one (least of all me), a kubeconfig accidentally made its way into the repository.
Don’t worry — the token has been obliterated, yeeted into the void, ritually deleted, and no longer grants access to anything more powerful than a 404 page.

Mistakes were made.
But hey — I fix my mistakes before they become security incidents.
Call it personal growth, call it self-preservation, call it “please don’t revoke my cluster access.”

The important part:
The leaked kubeconfig is now about as effective as shouting “kubectl apply” at a brick wall.

---
---

## 🤝 Contributing

This is a learning/demonstration project showcasing MLOps best practices. Feel free to:
- Fork and adapt for your needs
- Add new features (e.g., A/B testing, canary deployments)
- Improve the pipeline (e.g., add data validation, model monitoring)

## 📝 License

MIT License

## 🔗 Links

- **Docker Hub Organization**: https://hub.docker.com/u/harshith21
- **Airflow Image**: https://hub.docker.com/r/harshith21/ete-ml-pipeline-airflow
- **BentoML Image**: https://hub.docker.com/r/harshith21/ete-ml-pipeline-bento
- **Frontend Image**: https://hub.docker.com/r/harshith21/ete-ml-pipeline-frontend

---

**ETE-ML-PIPELINE** - End-to-End Machine Learning Pipeline with Full Model Provenance 🚀

Built with ❤️ for MLOps learning and demonstration.
