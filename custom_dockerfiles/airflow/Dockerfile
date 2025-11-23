# =============================================================================
# Custom Airflow Image with ML Dependencies
# Base: Apache Airflow 2.10.1 with Python 3.11
# Target: harshith21/ete-ml-pipeline-airflow:latest
# =============================================================================

FROM apache/airflow:2.10.1-python3.11

# Switch to root to install system dependencies if needed
USER root

# Install any system-level dependencies (if required)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Switch back to airflow user
USER airflow

# Uninstall conflicting package
RUN pip uninstall apache-airflow-providers-docker -y

# Install ML and data processing dependencies
RUN pip install --no-cache-dir \
    mlflow==2.9.2 \
    docker==6.1.3 \
    pyarrow==14.0.2 \
    protobuf==4.25.3 \
    cryptography==43.0.1 \
    cffi==1.16.0 \
    pandas==2.1.3 \
    scikit-learn==1.4.2 \
    xgboost==2.0.3 \
    boto3 \
    psycopg2-binary \
    requests

# Set working directory
WORKDIR /opt/airflow

# Expose Airflow webserver port
EXPOSE 8080

# Default command (can be overridden in k8s)
CMD ["webserver"]

