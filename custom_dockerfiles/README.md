# Custom Docker Images for ETE-ML-PIPELINE

This directory contains custom Dockerfiles for the ETE-ML-PIPELINE infrastructure components.

## Available Images

### Airflow (`airflow/`)
Custom Apache Airflow image with ML dependencies.
- **Image**: `harshith21/ete-ml-pipeline-airflow:latest`
- **Base**: Apache Airflow 2.10.1 with Python 3.11
- **Includes**: MLflow, XGBoost, scikit-learn, pandas, pyarrow, boto3, and more

## Quick Start

### Build All Images

```bash
# Build all custom images
./build-all.sh
```

### Push All Images

```bash
# Login to Docker Hub
docker login

# Push all images
./push-all.sh
```

### Build Individual Images

```bash
# Airflow
cd airflow
./build.sh
./push.sh
```

## Directory Structure

```
custom_dockerfiles/
├── README.md           # This file
├── build-all.sh        # Build all images
├── push-all.sh         # Push all images
└── airflow/
    ├── Dockerfile      # Airflow image definition
    ├── README.md       # Airflow-specific docs
    ├── build.sh        # Build Airflow image
    ├── push.sh         # Push Airflow image
    └── .dockerignore   # Docker ignore rules
```

## Docker Hub Repository

All images are published to: https://hub.docker.com/u/harshith21

## Adding New Custom Images

To add a new custom image:

1. Create a new directory (e.g., `custom_dockerfiles/mlflow/`)
2. Add a `Dockerfile`
3. Create `build.sh` and `push.sh` scripts
4. Update `build-all.sh` and `push-all.sh`
5. Add documentation in a `README.md`

## Usage in Kubernetes

Update the `infra-k8s/` YAML files to use custom images:

```yaml
containers:
  - name: airflow-webserver
    image: harshith21/ete-ml-pipeline-airflow:latest
```

## Testing Images Locally

```bash
# Test Airflow image
docker run -it --rm harshith21/ete-ml-pipeline-airflow:latest bash
pip list | grep mlflow
```

