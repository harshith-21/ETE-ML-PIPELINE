# Building the Custom Airflow Image

## Problem: Platform Mismatch

When you build a Docker image on **macOS** (ARM64/M1/M2), it creates an ARM image by default. 
However, most Kubernetes clusters run on **Linux AMD64** servers, causing the error:

```
no match for platform in manifest: not found
```

## Solution: Multi-Platform Builds

We use Docker Buildx to build images for both platforms simultaneously.

## Build Scripts

### 1. `build.sh` - Multi-Platform Build (RECOMMENDED for Production)

Builds for **both** `linux/amd64` and `linux/arm64` and pushes to Docker Hub automatically.

```bash
# Make sure you're logged in to Docker Hub first
docker login

# Build and push multi-platform image
./build.sh
```

**What it does:**
- ✅ Builds for linux/amd64 (Intel/AMD servers)
- ✅ Builds for linux/arm64 (ARM servers)
- ✅ Automatically pushes to Docker Hub
- ✅ Works on Kubernetes clusters running on any platform

**Requirements:**
- Docker Buildx (comes with Docker Desktop)
- Internet connection
- Docker Hub account

### 2. `build-local.sh` - Local Build Only

Builds ONLY for your current platform (faster, but not for production).

```bash
./build-local.sh
```

**What it does:**
- 📦 Builds for your current platform only
- ⚠️ Image may not work on different platforms
- 🚫 Does NOT push to Docker Hub automatically

**Use when:**
- Testing locally with `docker run`
- Developing/debugging the Dockerfile
- Quick iterations

## Step-by-Step Guide

### For Kubernetes Deployment

1. **Login to Docker Hub**
   ```bash
   docker login
   ```

2. **Build multi-platform image**
   ```bash
   cd /path/to/custom_dockerfiles/airflow
   ./build.sh
   ```

3. **Verify on Docker Hub**
   Visit: https://hub.docker.com/r/harshith21/ete-ml-pipeline-airflow
   
   Check that both platforms are listed:
   - linux/amd64
   - linux/arm64

4. **Deploy to Kubernetes**
   ```bash
   cd ../../
   ./main.sh start airflow
   ```

### For Local Testing

```bash
# Quick local build
./build-local.sh

# Test the image
docker run -it --rm harshith21/ete-ml-pipeline-airflow:latest bash

# Verify packages
pip list | grep -E "mlflow|xgboost|scikit-learn"
```

## Troubleshooting

### Error: "buildx: command not found"

**Solution:** Update Docker Desktop or enable buildx:
```bash
docker buildx create --use
```

### Error: "permission denied"

**Solution:** Make scripts executable:
```bash
chmod +x build.sh build-local.sh push.sh
```

### Error: "denied: requested access to the resource is denied"

**Solution:** Login to Docker Hub:
```bash
docker login
```

### Image still not working on Kubernetes?

1. Check what platforms were built:
   ```bash
   docker buildx imagetools inspect harshith21/ete-ml-pipeline-airflow:latest
   ```

2. Force pull the image on Kubernetes:
   ```bash
   kubectl delete pod -n harshith -l app=airflow-scheduler
   kubectl delete pod -n harshith -l app=airflow-web
   ```

## Platform Details

| Platform | Use Case | Works On |
|----------|----------|----------|
| `linux/amd64` | Most cloud VMs, servers | AWS EC2, GCP, Azure, DigitalOcean |
| `linux/arm64` | ARM servers, some cloud | AWS Graviton, Oracle ARM |
| `darwin/arm64` | macOS M1/M2/M3 | Local Mac development |
| `darwin/amd64` | macOS Intel | Local Mac development |

## Best Practices

1. **Always use multi-platform builds** for production deployments
2. **Test locally first** with `build-local.sh`
3. **Verify the manifest** on Docker Hub after pushing
4. **Use specific tags** (like `2.10.1`) in production, not just `latest`
5. **Keep the Dockerfile optimized** to reduce build time

## Quick Reference

```bash
# Production deployment (multi-platform)
docker login
./build.sh

# Local testing (single platform)
./build-local.sh
docker run -it --rm harshith21/ete-ml-pipeline-airflow:latest bash

# Check what platforms are available
docker buildx imagetools inspect harshith21/ete-ml-pipeline-airflow:latest

# Rebuild and deploy
./build.sh
cd ../../
./main.sh cleanup airflow
./main.sh start airflow
```

