# criteo_cumulative_builder.py
import os
import io
import time
import logging
from pathlib import Path

import boto3
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from airflow import DAG
from airflow.utils.dates import days_ago
from airflow.operators.python import PythonOperator

log = logging.getLogger(__name__)

S3_ENDPOINT = os.getenv("AWS_ENDPOINT_URL", "http://minio.harshith.svc.cluster.local:9000")
ACCESS_KEY = os.getenv("AWS_ACCESS_KEY_ID", "minio")
SECRET_KEY = os.getenv("AWS_SECRET_ACCESS_KEY", "minio123")
BUCKET = os.getenv("S3_BUCKET", "criteo-bucket")

CHUNK_PREFIX = "chunks/"
CUM_PREFIX = "cumulative/"
STATE_LAST_AGG = "state/last_agg_idx.txt"

def s3():
    return boto3.client(
        "s3",
        endpoint_url=S3_ENDPOINT,
        aws_access_key_id=ACCESS_KEY,
        aws_secret_access_key=SECRET_KEY,
        config=boto3.session.Config(signature_version="s3v4")
    )

def wait_minio(c):
    for _ in range(20):
        try:
            c.list_buckets()
            return
        except:
            time.sleep(1)
    raise Exception("MinIO unreachable")

def read_state(c, key, default=-1):
    try:
        v = c.get_object(Bucket=BUCKET, Key=key)["Body"].read().decode()
        return int(v)
    except:
        return default

def write_state(c, key, val):
    c.put_object(Bucket=BUCKET, Key=key, Body=str(val).encode())

def aggregate():
    c = s3()
    wait_minio(c)

    objs = c.list_objects_v2(Bucket=BUCKET, Prefix=CHUNK_PREFIX).get("Contents", [])
    chunks = [o for o in objs if not o["Key"].endswith(".keep")]
    chunks = sorted(chunks, key=lambda o: o["Key"])

    last = read_state(c, STATE_LAST_AGG, -1)
    for o in chunks:
        key = o["Key"]
        idx = int(Path(key).stem.split("_")[-1])
        if idx <= last:
            continue

        body = c.get_object(Bucket=BUCKET, Key=key)["Body"].read()
        df = pd.read_csv(io.StringIO(body.decode()), sep="\t", header=None)

        table = pa.Table.from_pandas(df)
        out = pa.BufferOutputStream()
        pq.write_table(table, out)
        pb = out.getvalue()

        out_key = f"{CUM_PREFIX}cumulative_{idx:06d}.parquet"
        c.put_object(Bucket=BUCKET, Key=out_key, Body=pb)
        log.info("Created %s", out_key)

        write_state(c, STATE_LAST_AGG, idx)

default_args = {"owner": "airflow"}

with DAG(
    "criteo_cumulative_builder",
    start_date=days_ago(1),
    schedule_interval=None,  # MANUAL ONLY
    catchup=False,
    default_args=default_args,
) as dag:

    run = PythonOperator(task_id="aggregate_chunks", python_callable=aggregate)