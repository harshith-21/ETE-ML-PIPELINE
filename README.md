# ETE-ML-PIPELINE

**End-to-End ML Pipeline** - A production-ready machine learning infrastructure for continuous training and deployment.

## 🎯 Project Overview

ETE-ML-PIPELINE is a complete end-to-end machine learning pipeline that demonstrates production-grade MLOps practices using:

- **Airflow** - Orchestration and workflow management
- **MinIO** - S3-compatible object storage
- **MLflow** - Experiment tracking and model registry
- **BentoML** - Model serving and deployment
- **FastAPI** - Frontend API
- **PostgreSQL** - Backend storage for Airflow and MLflow
- **Kubernetes** - Container orchestration

## 📊 Architecture

```
┌─────────────┐
│   Airflow   │ ──► Orchestrates data ingestion and training
└─────────────┘
      │
      ▼
┌─────────────┐
│    MinIO    │ ──► Stores raw data, chunks, and artifacts
└─────────────┘
      │
      ▼
┌─────────────┐
│   MLflow    │ ──► Tracks experiments and manages models
└─────────────┘
      │
      ▼
┌─────────────┐
│   BentoML   │ ──► Serves model predictions
└─────────────┘
      │
      ▼
┌─────────────┐
│  Frontend   │ ──► User interface for predictions
└─────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Kubernetes cluster (minikube, kind, or cloud provider)
- kubectl configured
- Docker (for building custom images)

### 1. Deploy Infrastructure

```bash
# Deploy all services
./main.sh start all

# Or deploy individually
./main.sh start postgres
./main.sh start minio
./main.sh start airflow
./main.sh start mlflow
./main.sh start bento
./main.sh start frontend
```

### 2. Build Custom Docker Images

```bash
cd custom_dockerfiles

# Build and push Airflow image
cd airflow
./build.sh
docker login
./push.sh

# Or build all at once
cd ..
./build-all.sh
./push-all.sh
```

### 3. Access Services

- **Airflow UI**: Port 8080 (admin/admin)
- **MinIO Console**: Port 9090 (minio/minio123)
- **MLflow UI**: Port 5000
- **Frontend**: Port 8081

## 📦 Custom Docker Images

### Airflow (`harshith21/ete-ml-pipeline-airflow:latest`)

Custom Airflow image with ML dependencies:
- MLflow 2.9.2
- XGBoost 2.0.3
- scikit-learn 1.4.2
- pandas 2.1.3
- pyarrow 14.0.2
- boto3, psycopg2-binary, and more

See [custom_dockerfiles/airflow/README.md](custom_dockerfiles/airflow/README.md) for details.

## 🛠️ Management Commands

The `main.sh` script provides a unified interface for managing all services:

```bash
./main.sh <action> <service>
```

### Actions
- `start` - Deploy and start a service
- `stop` - Stop a service (scale to 0)
- `restart` - Restart a service
- `cleanup` - Remove a service completely
- `status` - Show service status

### Services
- `postgres` - PostgreSQL databases
- `minio` - MinIO object storage
- `airflow` - Airflow (scheduler + web)
- `mlflow` - MLflow tracking server
- `bento` - BentoML model serving
- `frontend` - FastAPI frontend
- `all` - All services

### Examples

```bash
# Start services
./main.sh start postgres
./main.sh start airflow

# Restart services
./main.sh restart airflow

# Check status
./main.sh status all

# Clean up
./main.sh cleanup minio
./main.sh cleanup all
```

## 📁 Project Structure

```
.
├── README.md                  # This file
├── main.sh                    # Management script
├── adminkubeconfig.yaml       # Kubernetes config
├── infra-k8s/                 # Kubernetes manifests
│   ├── 0.namespace.yaml
│   ├── 1.postgres.yaml
│   ├── 2.airflow.yaml
│   ├── 2a.airflowconfigmaps.yaml
│   ├── 2b.Minio.yaml
│   ├── 3.mlflow.yaml
│   ├── 4.bento.yaml
│   └── 5.frontend.yaml
├── dags/                      # Airflow DAGs
│   ├── airflow_criteo_ingest_minio.py
│   ├── v2criteo_chunk_producer.py
│   └── v2criteo_cumulative_builder.py
└── custom_dockerfiles/        # Custom Docker images
    ├── README.md
    ├── build-all.sh
    ├── push-all.sh
    └── airflow/
        ├── Dockerfile
        ├── build.sh
        ├── push.sh
        └── README.md
```

## 🎓 Use Case: Criteo CTR Prediction

The pipeline processes the Criteo Click-Through Rate (CTR) dataset:

1. **Data Ingestion** - Download and chunk raw data
2. **Feature Processing** - Convert to Parquet format
3. **Cumulative Building** - Aggregate training data
4. **Model Training** - Train XGBoost models
5. **Model Registry** - Register in MLflow
6. **Model Serving** - Deploy with BentoML
7. **Inference** - Predict via Frontend API

## 🔧 Configuration

### Kubernetes Namespace
All services run in the `harshith` namespace.

### Storage
Services use `emptyDir` volumes (ephemeral). For production, configure persistent volumes.

### Credentials
- **PostgreSQL**: airflow/airflow, mlflow/mlflow
- **MinIO**: minio/minio123
- **Airflow Admin**: admin/admin

## 📚 Documentation

- [Custom Docker Images](custom_dockerfiles/README.md)
- [Airflow Image Details](custom_dockerfiles/airflow/README.md)
- [Project Notes](.mynotes.MD)

## 🤝 Contributing

This is a learning/demonstration project. Feel free to fork and adapt for your needs.

## 📝 License

MIT License

## 🔗 Links

- Docker Hub: https://hub.docker.com/u/harshith21
- Airflow Image: https://hub.docker.com/r/harshith21/ete-ml-pipeline-airflow

---

**ETE-ML-PIPELINE** - End-to-End Machine Learning Pipeline

