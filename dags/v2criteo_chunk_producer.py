# criteo_chunk_producer.py
import os
import io
import time
import math
import gzip
import logging
from pathlib import Path

import boto3
from botocore.exceptions import ClientError
import pandas as pd

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.utils.dates import days_ago

log = logging.getLogger(__name__)

# ----------------------------------------------------------
# CONFIG
# ----------------------------------------------------------
S3_ENDPOINT = os.getenv("AWS_ENDPOINT_URL", "http://minio.harshith.svc.cluster.local:9000")
ACCESS_KEY = os.getenv("AWS_ACCESS_KEY_ID", "minio")
SECRET_KEY = os.getenv("AWS_SECRET_ACCESS_KEY", "minio123")
BUCKET = os.getenv("S3_BUCKET", "criteo-bucket")

CRITEO_URL = os.getenv(
    "CRITEO_URL",
    "https://huggingface.co/datasets/criteo/CriteoClickLogs/resolve/main/day_0.gz"
)

RAW_KEY = "raw/train.txt.gz"
LOCAL_RAW = "/tmp/train.txt.gz"

CHUNK_PERCENT = 0.02    # 2%
MIN_SIZE_BYTES = 1_000_000

STATE_NEXT_LINE = "state/next_line.txt"
STATE_TOTAL_LINES = "state/total_lines.txt"

CHUNK_PREFIX = "chunks/"

# ----------------------------------------------------------
def make_s3():
    return boto3.client(
        "s3",
        endpoint_url=S3_ENDPOINT,
        aws_access_key_id=ACCESS_KEY,
        aws_secret_access_key=SECRET_KEY,
        config=boto3.session.Config(signature_version="s3v4")
    )

# ----------------------------------------------------------
def wait_minio(s3):
    for _ in range(20):
        try:
            s3.list_buckets()
            return
        except Exception:
            time.sleep(1)
    raise Exception("MinIO unreachable")

# ----------------------------------------------------------
def ensure_minio_and_paths():
    s3 = make_s3()
    wait_minio(s3)

    # Ensure bucket
    try:
        s3.head_bucket(Bucket=BUCKET)
        log.info("Bucket exists: %s", BUCKET)
    except:
        log.info("Creating bucket %s", BUCKET)
        s3.create_bucket(Bucket=BUCKET)

    prefixes = ["raw/", "chunks/", "offline/", "cumulative/", "state/"]
    for p in prefixes:
        marker = p + ".keep"
        try:
            s3.head_object(Bucket=BUCKET, Key=marker)
        except:
            s3.put_object(Bucket=BUCKET, Key=marker, Body=b"")

# ----------------------------------------------------------
def object_exists_and_large(s3, key, min_bytes):
    try:
        meta = s3.head_object(Bucket=BUCKET, Key=key)
        return meta["ContentLength"] >= min_bytes
    except:
        return False

# ----------------------------------------------------------
def robust_download(url, local_path):
    import requests
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry

    session = requests.Session()
    retries = Retry(total=8, backoff_factor=1)
    session.mount("https://", HTTPAdapter(max_retries=retries))

    with session.get(url, stream=True) as r:
        r.raise_for_status()
        with open(local_path, "wb") as f:
            for chunk in r.iter_content(1024 * 1024):
                if chunk:
                    f.write(chunk)

    size = Path(local_path).stat().st_size
    if size < MIN_SIZE_BYTES:
        raise RuntimeError("Downloaded file too small")

# ----------------------------------------------------------
def read_state(s3, key, default=None, cast=int):
    try:
        raw = s3.get_object(Bucket=BUCKET, Key=key)["Body"].read().decode()
        return cast(raw)
    except:
        return default

def write_state(s3, key, val):
    s3.put_object(Bucket=BUCKET, Key=key, Body=str(val).encode())

# ----------------------------------------------------------
def download_raw():
    s3 = make_s3()
    wait_minio(s3)

    if object_exists_and_large(s3, RAW_KEY, MIN_SIZE_BYTES):
        log.info("Raw file already exists in MinIO — skipping download.")
        return

    log.info("Downloading raw file from %s", CRITEO_URL)
    robust_download(CRITEO_URL, LOCAL_RAW)

    s3.upload_file(LOCAL_RAW, BUCKET, RAW_KEY)
    log.info("Uploaded raw file to MinIO")

# ----------------------------------------------------------
def count_total_lines():
    s3 = make_s3()
    wait_minio(s3)

    total = read_state(s3, STATE_TOTAL_LINES, default=None)
    if total is not None:
        log.info("Total lines already known: %d", total)
        return

    log.info("Counting total lines in raw gzip file...")
    s3.download_file(BUCKET, RAW_KEY, LOCAL_RAW)

    cnt = 0
    with gzip.open(LOCAL_RAW, "rt", encoding="utf-8", errors="ignore") as f:
        for _ in f:
            cnt += 1

    write_state(s3, STATE_TOTAL_LINES, cnt)
    log.info("Total lines stored: %d", cnt)

# ----------------------------------------------------------
def produce_next_chunk():
    s3 = make_s3()
    wait_minio(s3)

    total = read_state(s3, STATE_TOTAL_LINES, default=None)
    if total is None:
        raise Exception("Total lines not computed")

    next_line = read_state(s3, STATE_NEXT_LINE, default=0)
    if next_line >= total:
        log.info("All lines already chunked. Nothing to do.")
        return

    # compute number of lines per chunk
    chunk_lines = max(1, math.ceil(total * CHUNK_PERCENT))
    start = next_line
    end = min(total, start + chunk_lines)

    log.info("Producing chunk for lines %d .. %d", start, end)

    # download whole raw file
    s3.download_file(BUCKET, RAW_KEY, LOCAL_RAW)

    collected = []
    with gzip.open(LOCAL_RAW, "rt", encoding="utf-8", errors="ignore") as f:
        for i, line in enumerate(f):
            if i < start:
                continue
            if i >= end:
                break
            collected.append(line)

    if not collected:
        log.info("No lines collected.")
        return

    # Next chunk index
    objs = s3.list_objects_v2(Bucket=BUCKET, Prefix=CHUNK_PREFIX).get("Contents", [])
    real_chunks = [o for o in objs if not o["Key"].endswith(".keep")]
    next_idx = len(real_chunks)

    chunk_key = f"{CHUNK_PREFIX}chunk_{next_idx:06d}.txt"
    body = "".join(collected).encode()

    s3.put_object(Bucket=BUCKET, Key=chunk_key, Body=body)
    log.info("Uploaded chunk %s (%d lines)", chunk_key, len(collected))

    write_state(s3, STATE_NEXT_LINE, end)
    log.info("Updated next_line → %d", end)

# ----------------------------------------------------------
default_args = {"owner": "airflow", "retries": 1}

with DAG(
    "criteo_chunk_producer",
    start_date=days_ago(1),
    schedule_interval=None,   # MANUAL ONLY
    catchup=False,
    default_args=default_args,
) as dag:

    ensure = PythonOperator(task_id="ensure_minio", python_callable=ensure_minio_and_paths)
    download = PythonOperator(task_id="download_raw", python_callable=download_raw)
    count = PythonOperator(task_id="count_total_lines", python_callable=count_total_lines)
    produce = PythonOperator(task_id="produce_next_chunk", python_callable=produce_next_chunk)

    ensure >> download >> count >> produce