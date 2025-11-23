# Custom Airflow Docker Image

Custom Apache Airflow image with ML dependencies for the ETE-ML-PIPELINE project.

## Base Image
- **Apache Airflow**: 2.10.1
- **Python**: 3.11

## Additional Packages

### ML & Data Processing
- mlflow==2.9.2
- pandas==2.1.3
- pyarrow==14.0.2
- scikit-learn==1.4.2
- xgboost==2.0.3

### Infrastructure
- docker==6.1.3
- boto3
- psycopg2-binary

### Security & Compatibility
- protobuf==4.25.3
- cryptography==43.0.1
- cffi==1.16.0

## Building the Image

```bash
# Make scripts executable
chmod +x build.sh push.sh

# Build the image locally
./build.sh

# Or manually
docker build -t harshith21/ete-ml-pipeline-airflow:2.10.1 -t harshith21/ete-ml-pipeline-airflow:latest .
```

## Pushing to Docker Hub

```bash
# Login to Docker Hub
docker login

# Push using script
./push.sh

# Or manually
docker push harshith21/ete-ml-pipeline-airflow:2.10.1
docker push harshith21/ete-ml-pipeline-airflow:latest
```

## Using in Kubernetes

Update your Airflow deployment YAML to use this image:

```yaml
containers:
  - name: airflow-webserver
    image: harshith21/ete-ml-pipeline-airflow:latest
    # ... rest of config
```

## Docker Hub

Image repository: https://hub.docker.com/r/harshith21/ete-ml-pipeline-airflow

## Testing Locally

```bash
# Run a test container
docker run -it --rm harshith21/ete-ml-pipeline-airflow:latest bash

# Verify packages
pip list | grep -E "mlflow|xgboost|scikit-learn|pandas"
```

## Version History

- **2.10.1**: Initial release with Airflow 2.10.1-python3.11 base

