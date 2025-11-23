# 📋 ETE-ML-PIPELINE - Project Summary

## 🎯 What We Built

A complete **End-to-End Machine Learning Pipeline** for **Criteo Click-Through Rate (CTR) prediction** with:
- ✅ Automated training pipeline (Airflow)
- ✅ Model versioning and registry (MLflow)
- ✅ Model serving with full provenance tracking (BentoML)
- ✅ User-friendly prediction interface (FastAPI)
- ✅ All running on Kubernetes with proper logging and storage

## 🏗️ Architecture Stack

### Core Services
| Service | Purpose | Image | Port |
|---------|---------|-------|------|
| **PostgreSQL** | Backend for Airflow & MLflow | `postgres:13` | 5432 |
| **MinIO** | S3-compatible object storage | `minio/minio:latest` | 9000/9090 |
| **Airflow** | Workflow orchestration | `harshith21/ete-ml-pipeline-airflow:latest` | 8080 |
| **MLflow** | Model registry & tracking | `ghcr.io/mlflow/mlflow:v2.9.2` | 5000 |
| **BentoML** | Model serving | `harshith21/ete-ml-pipeline-bento:latest` | 3000 |
| **Frontend** | User interface | `harshith21/ete-ml-pipeline-frontend:latest` | 8081 |

### Custom Docker Images

All images are **multi-platform** (linux/amd64, linux/arm64) and hosted on Docker Hub:

1. **harshith21/ete-ml-pipeline-airflow:latest**
   - Base: Apache Airflow 2.10.1 with Python 3.11
   - Added: MLflow, XGBoost, scikit-learn, pandas, boto3
   - Purpose: Run training DAGs with ML dependencies

2. **harshith21/ete-ml-pipeline-bento:latest**
   - Base: Python 3.11-slim
   - Added: BentoML, MLflow, XGBoost, numpy, pandas
   - Purpose: Serve models with provenance tracking

3. **harshith21/ete-ml-pipeline-frontend:latest**
   - Base: Python 3.11-slim
   - Added: FastAPI, uvicorn, httpx, jinja2
   - Purpose: Web UI for predictions

## 🔄 Complete Workflow

```
1. User triggers training in Airflow UI
   ↓
2. Airflow DAG: criteo_training_pipeline
   ├─ Download Criteo dataset
   ├─ Process features (39 features)
   ├─ Train XGBoost model
   ├─ Log to MLflow (metrics, params, artifacts)
   ├─ Register model in MLflow registry
   └─ Promote to Production stage
   ↓
3. BentoML automatically loads Production model
   ├─ Captures: version, run_id, run_name, artifact_uri
   └─ Exposes /predict, /health, /model_info APIs
   ↓
4. Frontend calls BentoML for predictions
   ├─ User inputs 39 feature values
   ├─ Returns CTR prediction (%)
   └─ Displays full model provenance
```

## 🎯 Key Features Implemented

### ✅ Model Provenance Tracking
Every prediction shows:
- **Model Name**: criteo_ctr_model
- **Version**: e.g., "2"
- **Stage**: Production/Staging
- **Run Name**: MLflow's auto-generated nickname (e.g., "glamorous-goose-948")
- **Run ID**: Hash matching MinIO artifact path (e.g., "6820c410efef...")
- **Artifact URI**: Full S3 path in MinIO

### ✅ Automated Training Pipeline
- Scheduled or manual training via Airflow
- Automatic feature engineering (categorical → numeric)
- Error handling and comprehensive logging
- Model validation before registration

### ✅ Model Registry
- All models tracked in MLflow
- Version management (v1, v2, v3...)
- Stage promotion (None → Staging → Production)
- Lineage tracking (which data, which parameters)

### ✅ Model Serving
- BentoML automatically loads latest Production model
- REST API endpoints (/predict, /health, /model_info)
- Model metadata in every response
- Graceful error handling

### ✅ User Interface
- Beautiful web UI with gradient design
- Load sample data with one click
- Real-time model information display
- Shows all registered model versions
- Full provenance for every prediction

## 📁 Project Structure

```
ete-ml-pipeline/
├── README.md                    # Complete documentation
├── QUICKSTART.md                # 5-minute setup guide
├── PROJECT_SUMMARY.md           # This file
├── sample_input_frontend.txt    # 20 test samples
├── main.sh                      # Service management script
│
├── infra-k8s/                   # Kubernetes manifests
│   ├── 0.namespace.yaml         # namespace: harshith
│   ├── 1.postgres.yaml          # 2 PostgreSQL instances
│   ├── 2.airflow.yaml           # Airflow webserver + scheduler
│   ├── 2a.airflowconfigmaps.yaml # DAG: criteo_training_pipeline
│   ├── 2b.Minio.yaml            # MinIO with auto-bucket creation
│   ├── 3.mlflow.yaml            # MLflow with S3 artifact storage
│   ├── 4.bento.yaml             # BentoML with service ConfigMap
│   └── 5.frontend.yaml          # FastAPI frontend
│
└── custom_dockerfiles/          # Custom Docker images
    ├── README.md
    ├── build-all.sh
    ├── push-all.sh
    │
    ├── airflow/                 # Custom Airflow image
    │   ├── Dockerfile
    │   ├── build.sh             # Multi-platform build
    │   ├── push.sh
    │   └── README.md
    │
    ├── bento/                   # Custom BentoML image
    │   ├── Dockerfile
    │   ├── service.py           # BentoML service code
    │   ├── requirements.txt
    │   ├── build.sh
    │   └── README.md
    │
    └── frontend/                # Custom Frontend image
        ├── Dockerfile
        ├── app.py               # FastAPI app
        ├── requirements.txt
        ├── build.sh
        └── templates/
            └── index.html       # Prediction UI
```

## 🎓 ML Pipeline Details

### Dataset: Criteo CTR
- **Features**: 39 (13 integer + 26 categorical)
- **Task**: Binary classification (click vs. no-click)
- **Model**: XGBoost classifier
- **Training Time**: ~2-5 minutes

### Training Pipeline (Airflow DAG)
```python
criteo_training_pipeline:
  ├─ download_data      # Download Criteo dataset
  ├─ process_features   # Convert categorical to numeric
  ├─ train_model        # Train XGBoost
  ├─ log_to_mlflow      # Log metrics/params/artifacts
  ├─ register_model     # Register in MLflow registry
  └─ promote_model      # Set to Production stage
```

### Storage Layout (MinIO)
```
MinIO Buckets:
├── criteo-data/          # Training data
├── criteo-logs/          # Airflow task logs
└── mlflow-artifacts/     # Model artifacts
    └── 1/
        └── <run_id>/     # e.g., 6820c410efef...
            └── artifacts/
                └── model/
```

## 🚀 Deployment Commands

### Quick Deploy
```bash
./main.sh start all
```

### Individual Services
```bash
./main.sh start postgres    # First
./main.sh start minio        # Second
./main.sh start airflow      # Third
./main.sh start mlflow       # Fourth
./main.sh start bento        # Fifth
./main.sh start frontend     # Sixth
```

### Management
```bash
./main.sh status all         # Check all services
./main.sh restart airflow    # Restart a service
./main.sh cleanup bento      # Remove a service
./main.sh cleanup all        # Remove everything
```

## 🌐 Access URLs (after port-forwarding)

```bash
# Terminal 1
kubectl port-forward -n harshith svc/airflow-webserver 8080:8080

# Terminal 2
kubectl port-forward -n harshith svc/minio 9090:9090

# Terminal 3
kubectl port-forward -n harshith svc/mlflow 5000:5000

# Terminal 4
kubectl port-forward -n harshith svc/frontend 8081:8081
```

- Airflow UI: http://localhost:8080 (admin/admin)
- MinIO Console: http://localhost:9090 (minio/minio123)
- MLflow UI: http://localhost:5000
- Frontend: http://localhost:8081

## 🔍 Model Provenance Example

**What you see in Frontend after prediction:**

```
✅ Prediction: 2.45% CTR
Raw Probability: 0.024567

🔍 Model Provenance:
├─ Model: criteo_ctr_model
├─ Version: 2
├─ Stage: Production
├─ Run Name: glamorous-goose-948
├─ Run ID: 6820c410efef45449fbb6ab1044f340c
└─ Artifact URI: s3://mlflow-artifacts/1/6820c410efef.../artifacts/model
```

**Verification:**
1. Copy the Run ID: `6820c410efef45449fbb6ab1044f340c`
2. Open MinIO: http://localhost:9090
3. Navigate to: `mlflow-artifacts/1/6820c410efef45449fbb6ab1044f340c/`
4. See your model files! ✅

## 🎉 What Makes This Special

1. **Full Traceability**: Every prediction traces back to exact model artifact in storage
2. **Production-Ready**: Proper logging, error handling, multi-platform images
3. **Automated**: Training → Registration → Deployment all automated
4. **User-Friendly**: Beautiful UI with clear provenance display
5. **Educational**: Clean code, well-documented, easy to understand
6. **Extensible**: Easy to add monitoring, A/B testing, canary deployments

## 📊 Technologies Used

- **Orchestration**: Apache Airflow 2.10.1
- **ML Framework**: XGBoost 2.0.3, scikit-learn 1.4.2
- **Model Registry**: MLflow 2.9.2
- **Model Serving**: BentoML 1.3.8
- **Web Framework**: FastAPI 0.104.1
- **Container Platform**: Kubernetes
- **Object Storage**: MinIO (S3-compatible)
- **Databases**: PostgreSQL 13
- **Languages**: Python 3.11

## 🏆 Achievement Summary

✅ **Architecture**: Designed complete end-to-end ML pipeline
✅ **Custom Images**: Created 3 multi-platform Docker images
✅ **Kubernetes**: Deployed 6 services with proper configs
✅ **Model Tracking**: Implemented full provenance tracking
✅ **Automation**: Automated training → deployment flow
✅ **UI/UX**: Built beautiful, functional frontend
✅ **Documentation**: Created comprehensive docs + quick start
✅ **Cleanup**: Removed all unnecessary files, added .dockerignore, .gitignore

## 📚 Documentation Files

- `README.md` - Complete project documentation
- `QUICKSTART.md` - 5-minute setup guide
- `PROJECT_SUMMARY.md` - This file
- `sample_input_frontend.txt` - 20 test samples
- `custom_dockerfiles/*/README.md` - Image-specific docs

## 🔗 Resources

- **Docker Hub**: https://hub.docker.com/u/harshith21
- **Airflow Image**: https://hub.docker.com/r/harshith21/ete-ml-pipeline-airflow
- **BentoML Image**: https://hub.docker.com/r/harshith21/ete-ml-pipeline-bento
- **Frontend Image**: https://hub.docker.com/r/harshith21/ete-ml-pipeline-frontend

---

## 🎯 Next Steps / Future Enhancements

Potential improvements:
- [ ] Add model performance monitoring (Evidently, whylogs)
- [ ] Implement A/B testing for model versions
- [ ] Add canary deployments with gradual rollout
- [ ] Integrate Prometheus + Grafana for metrics
- [ ] Add data validation (Great Expectations)
- [ ] Implement feature store (Feast)
- [ ] Add model explainability (SHAP, LIME)
- [ ] Set up CI/CD pipeline (GitHub Actions)
- [ ] Add unit tests and integration tests
- [ ] Implement model drift detection

---

**ETE-ML-PIPELINE** - A complete, production-ready MLOps pipeline! 🚀

Built with ❤️ for learning and demonstration.

