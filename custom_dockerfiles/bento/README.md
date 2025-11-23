# BentoML Service for Criteo CTR Model

This directory contains the BentoML service that serves the Criteo CTR model from MLflow.

## Features

- **MLflow Integration**: Automatically loads the Production model from MLflow Model Registry
- **S3/MinIO Support**: Configured to work with MinIO for artifact storage
- **REST API**: Provides prediction, health check, and model info endpoints
- **Multi-platform**: Supports both linux/amd64 and linux/arm64

## Files

- `service.py`: BentoML service definition with prediction endpoints
- `Dockerfile`: Multi-stage Docker build
- `requirements.txt`: Python dependencies
- `build.sh`: Build and push script for multi-platform images

## Building the Image

```bash
cd custom_dockerfiles/bento
./build.sh
```

This will:
1. Build the Docker image for both linux/amd64 and linux/arm64
2. Push to Docker Hub as `harshith21/ete-ml-pipeline-bento:latest`

## API Endpoints

### 1. `/predict` - Make Predictions

**Request**:
```json
{
  "features": [
    [1, 2, 3, ..., 39],  // 39 features per sample
    [4, 5, 6, ..., 42]   // Multiple samples supported
  ]
}
```

**Response**:
```json
{
  "predictions": [0.123, 0.456],
  "model_name": "criteo_ctr_model",
  "model_stage": "Production",
  "num_samples": 2
}
```

### 2. `/health` - Health Check

**Response**:
```json
{
  "status": "healthy",
  "model_name": "criteo_ctr_model",
  "model_stage": "Production",
  "mlflow_uri": "http://mlflow.harshith.svc.cluster.local:5000"
}
```

### 3. `/model_info` - Model Information

**Response**:
```json
{
  "model_name": "criteo_ctr_model",
  "model_stage": "Production",
  "mlflow_uri": "http://mlflow.harshith.svc.cluster.local:5000",
  "versions": [
    {
      "version": "1",
      "stage": "Production",
      "run_id": "abc123...",
      "creation_timestamp": "2025-11-23 09:00:00"
    }
  ]
}
```

## Environment Variables

- `MLFLOW_TRACKING_URI`: MLflow server URL (default: `http://mlflow.harshith.svc.cluster.local:5000`)
- `MODEL_NAME`: Model name in MLflow registry (default: `criteo_ctr_model`)
- `MODEL_STAGE`: Model stage to serve (default: `Production`)
- `AWS_ACCESS_KEY_ID`: MinIO access key (default: `minio`)
- `AWS_SECRET_ACCESS_KEY`: MinIO secret key (default: `minio123`)
- `MLFLOW_S3_ENDPOINT_URL`: MinIO endpoint (default: `http://minio.harshith.svc.cluster.local:9000`)

## Testing Locally

```bash
# Build locally
docker build -t ete-ml-pipeline-bento .

# Run locally (requires MLflow and MinIO to be accessible)
docker run -p 3000:3000 \
  -e MLFLOW_TRACKING_URI=http://mlflow.harshith.svc.cluster.local:5000 \
  ete-ml-pipeline-bento

# Test prediction
curl -X POST http://localhost:3000/predict \
  -H "Content-Type: application/json" \
  -d '{"features": [[1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39]]}'
```

## Deployment

The service is deployed via `infra-k8s/4.bento.yaml` with:
- Service exposed on port 3000
- Automatic model loading from MLflow
- S3/MinIO configuration for artifact access

