# ⚡ ETE-ML-PIPELINE - Quick Start Guide

**Get up and running in 5 minutes!**

## 🎯 Prerequisites

```bash
# Check you have:
kubectl version        # Kubernetes cluster access
docker --version      # Docker for building images (optional)
```

## 🚀 Deployment (60 seconds)

```bash
# 1. Deploy everything
./main.sh start all

# 2. Wait for pods to be ready (30-60 seconds)
watch kubectl get pods -n harshith

# 3. Done! All services running ✅
```

## 🌐 Access Services

```bash
# Terminal 1: Airflow UI
kubectl port-forward -n harshith svc/airflow-webserver 8080:8080

# Terminal 2: MinIO Console
kubectl port-forward -n harshith svc/minio 9090:9090

# Terminal 3: MLflow UI
kubectl port-forward -n harshith svc/mlflow 5000:5000

# Terminal 4: Frontend (Predictions!)
kubectl port-forward -n harshith svc/frontend 8081:8081
```

**Open in browser:**
- Airflow: http://localhost:8080 (admin/admin)
- MinIO: http://localhost:9090 (minio/minio123)
- MLflow: http://localhost:5000
- Frontend: http://localhost:8081 ⭐

## 🎯 Run Training Pipeline

1. Open **Airflow UI** → http://localhost:8080
2. Find **`criteo_training_pipeline`** DAG
3. Click **"Trigger DAG"** (▶️ icon)
4. Wait ~2-5 minutes for training
5. Model appears in **MLflow** automatically! ✅

## 🔮 Make Predictions

1. Open **Frontend** → http://localhost:8081
2. Click **"📝 Load Sample"** button
3. Click **"🚀 Predict CTR"**
4. See prediction with model provenance! 🎉

### Sample Input (paste if you want):
```
1, 2, 5, 0, 1382, 4, 15, 2, 181, 1, 2, 0, 3, 1, 0, 2, 1, 1, 1, 0, 1, 0, 1, 1, 0, 1, 0, 1, 1, 0, 1, 1, 1, 1, 1, 1, 0, 1, 0
```

## 🔍 Verify Model Provenance

After prediction, you'll see:

```
✅ Prediction: 2.45% CTR

🔍 Model Provenance:
├─ Run Name: glamorous-goose-948
├─ Run ID: 6820c410efef...
└─ Artifact URI: s3://mlflow-artifacts/1/6820c410efef.../artifacts/model
```

**Verify in MinIO:**
1. Open MinIO → http://localhost:9090
2. Go to `mlflow-artifacts` bucket
3. Navigate to `1/<run_id>/` folder
4. See your model files! 📦

## 🛠️ Common Commands

```bash
# Check pod status
kubectl get pods -n harshith

# View logs
kubectl logs -n harshith <pod-name>
kubectl logs -n harshith -l app=airflow-scheduler --tail=50

# Restart a service
./main.sh restart airflow
./main.sh restart bento

# Clean up everything
./main.sh cleanup all
```

## 📊 What You Just Built

```
User Input → Frontend → BentoML → Model (from MLflow) → Prediction
                            ↑
                        Trained by
                            ↑
                        Airflow DAG
                            ↑
                    Stored in MinIO
```

## 🎓 Next Steps

1. **Explore Airflow DAGs**: Check the training pipeline code in Airflow UI
2. **View MLflow Experiments**: See all training runs and metrics
3. **Try Different Inputs**: Use samples from `sample_input_frontend.txt`
4. **Retrain Model**: Trigger the DAG again, watch BentoML auto-update
5. **Customize**: Modify DAGs in `infra-k8s/2a.airflowconfigmaps.yaml`

## 🆘 Troubleshooting

### Pods stuck in `Pending`?
```bash
kubectl describe pod <pod-name> -n harshith
# Check: Node resources, image pull errors
```

### Can't access UI?
```bash
# Check port-forward is running
ps aux | grep port-forward

# Restart it
kubectl port-forward -n harshith svc/frontend 8081:8081
```

### Training fails?
```bash
# Check scheduler logs
kubectl logs -n harshith -l app=airflow-scheduler --tail=100

# Check MLflow is running
kubectl get pods -n harshith -l app=mlflow
```

### Image pull errors?
Images are hosted on Docker Hub and should pull automatically.
If issues persist, check: https://hub.docker.com/u/harshith21

## 📚 Full Documentation

See [README.md](README.md) for complete documentation.

---

**That's it!** You now have a full end-to-end ML pipeline running! 🎉

