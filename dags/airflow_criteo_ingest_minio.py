# criteo_ingestion_minio_v3.py
import os
import io
import math
import time
import gzip
import logging
from pathlib import Path

import boto3
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.utils.dates import days_ago
from botocore.exceptions import ClientError
from requests.adapters import HTTPAdapter
from requests import Session
from urllib3.util.retry import Retry

log = logging.getLogger(__name__)

# ---------- CONFIG / ENV ----------
S3_ENDPOINT = os.getenv("AWS_ENDPOINT_URL", "http://minio.harshith.svc.cluster.local:9000")
ACCESS_KEY = os.getenv("AWS_ACCESS_KEY_ID", "minio")
SECRET_KEY = os.getenv("AWS_SECRET_ACCESS_KEY", "minio123")
BUCKET = os.getenv("S3_BUCKET", "criteo-bucket")
CRITEO_URL = os.getenv(
    "CRITEO_URL",
    "https://huggingface.co/datasets/criteo/CriteoClickLogs/resolve/main/day_0.gz"
)
# fraction of total lines to put in each chunk (0.02 => 2%)
CHUNK_PERCENT = float(os.getenv("CHUNK_PERCENT", "0.02"))
# default schedule - change to desired "every X minutes" via CRON
SCHEDULE_CRON = os.getenv("SCHEDULE_CRON", "*/10 * * * *")          # producer: every 10 minutes by default
AGG_SCHEDULE_CRON = os.getenv("AGG_SCHEDULE_CRON", "*/5 * * * *")   # aggregator: every 5 minutes by default

LOCAL_RAW = os.getenv("LOCAL_RAW_PATH", "/tmp/train.txt.gz")
STATE_NEXT_LINE = os.getenv("STATE_NEXT_LINE", "state/next_line.txt")
STATE_TOTAL_LINES = os.getenv("STATE_TOTAL_LINES", "state/total_lines.txt")
STATE_LAST_AGG = os.getenv("STATE_LAST_AGG", "state/last_agg_idx.txt")

CHUNK_PREFIX = "chunks/"
CUMULATIVE_PREFIX = "cumulative/"
RAW_KEY = "raw/train.txt.gz"
MIN_SIZE_BYTES = int(os.getenv("MIN_SIZE_BYTES", "100000"))  # sanity size

# boto3 client factory (create inside functions so it fresh-checks env)
def make_s3_client():
    return boto3.client(
        "s3",
        endpoint_url=S3_ENDPOINT,
        aws_access_key_id=ACCESS_KEY,
        aws_secret_access_key=SECRET_KEY,
        config=boto3.session.Config(signature_version="s3v4"),
    )

# ---------- HELPERS ----------
def wait_minio_ready(s3, attempts=10, sleep=2):
    for i in range(attempts):
        try:
            s3.list_buckets()
            return True
        except Exception as e:
            log.info("MinIO not ready (%s). retry %d/%d", e, i + 1, attempts)
            time.sleep(sleep)
    raise RuntimeError("MinIO unreachable after retries")

def ensure_bucket_and_prefixes():
    s3 = make_s3_client()
    wait_minio_ready(s3)
    try:
        s3.head_bucket(Bucket=BUCKET)
        log.info("Bucket exists: %s", BUCKET)
    except Exception:
        log.info("Creating bucket: %s", BUCKET)
        s3.create_bucket(Bucket=BUCKET)

    # create prefix markers (.keep) so we can show empty folders
    for p in ("raw/", CHUNK_PREFIX, "offline/", CUMULATIVE_PREFIX, "state/"):
        marker = p + ".keep"
        try:
            s3.head_object(Bucket=BUCKET, Key=marker)
        except Exception:
            s3.put_object(Bucket=BUCKET, Key=marker, Body=b"")
            log.info("Created prefix marker: %s", marker)

def robust_http_stream_download(url: str, local_path: str, min_size_bytes: int = MIN_SIZE_BYTES):
    session = Session()
    retries = Retry(total=8, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
    session.mount("https://", HTTPAdapter(max_retries=retries))
    session.mount("http://", HTTPAdapter(max_retries=retries))
    with session.get(url, stream=True, timeout=None) as r:
        r.raise_for_status()
        with open(local_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=4 * 1024 * 1024):
                if chunk:
                    f.write(chunk)
    size = Path(local_path).stat().st_size
    log.info("Downloaded %s size=%d", local_path, size)
    if size < min_size_bytes:
        raise RuntimeError("Downloaded file appears too small")

def object_exists_and_large(s3, key, min_bytes=MIN_SIZE_BYTES):
    try:
        meta = s3.head_object(Bucket=BUCKET, Key=key)
        size = meta.get("ContentLength", 0)
        return size >= min_bytes
    except ClientError:
        return False

def write_state(s3, key, value):
    s3.put_object(Bucket=BUCKET, Key=key, Body=str(value).encode("utf-8"))

def read_state(s3, key, default=None, cast=int):
    try:
        b = s3.get_object(Bucket=BUCKET, Key=key)["Body"].read().decode()
        return cast(b)
    except Exception:
        return default

def list_real_chunks(s3):
    objs = s3.list_objects_v2(Bucket=BUCKET, Prefix=CHUNK_PREFIX).get("Contents", [])
    # ignore .keep
    real = [o for o in objs if not o["Key"].endswith(".keep")]
    return sorted(real, key=lambda o: o["Key"])

# ---------- PRODUCER TASK ----------
def produce_next_chunk(**_ctx):
    """
    On each run, produce the next chunk consisting of CHUNK_PERCENT of the total lines.
    Maintains state in state/next_line.txt (0-based line index).
    """
    s3 = make_s3_client()
    wait_minio_ready(s3)
    ensure_bucket_and_prefixes()

    # ensure raw exists, otherwise download
    if not object_exists_and_large(s3, RAW_KEY):
        log.info("raw not found or too small. Downloading from %s", CRITEO_URL)
        robust_http_stream_download(CRITEO_URL, LOCAL_RAW)
        s3.upload_file(LOCAL_RAW, BUCKET, RAW_KEY)
        log.info("Uploaded raw -> %s/%s", BUCKET, RAW_KEY)
    else:
        log.info("raw already present; skipping download")

    # compute total lines if not present or recalc
    total_lines = read_state(s3, STATE_TOTAL_LINES, default=None, cast=int)
    if total_lines is None:
        # count lines by streaming gzip locally (cheapish but safe)
        log.info("Counting total lines in raw file")
        s3.download_file(BUCKET, RAW_KEY, LOCAL_RAW)
        cnt = 0
        with gzip.open(LOCAL_RAW, "rt", encoding="utf-8", errors="ignore") as fh:
            for _ in fh:
                cnt += 1
        total_lines = cnt
        write_state(s3, STATE_TOTAL_LINES, total_lines)
        log.info("Total lines = %d", total_lines)
    else:
        log.info("Total lines (cached) = %d", total_lines)

    if total_lines <= 0:
        raise RuntimeError("No lines in raw file")

    # compute chunk size in lines
    chunk_lines = max(1, math.ceil(total_lines * CHUNK_PERCENT))
    log.info("ChunkLines (2%% default) = %d lines per chunk", chunk_lines)

    # read current next_line
    next_line = read_state(s3, STATE_NEXT_LINE, default=0, cast=int)
    if next_line >= total_lines:
        log.info("All lines already chunked (next_line >= total_lines). Nothing to do.")
        return

    # produce one chunk: read file locally but skip until next_line then collect chunk_lines
    s3.download_file(BUCKET, RAW_KEY, LOCAL_RAW)
    start = next_line
    end = min(total_lines, start + chunk_lines)
    collected = []
    log.info("Producing chunk for lines %d .. %d (exclusive)", start, end)

    with gzip.open(LOCAL_RAW, "rt", encoding="utf-8", errors="ignore") as fh:
        for i, line in enumerate(fh):
            if i < start:
                continue
            if i >= end:
                break
            collected.append(line)

    if not collected:
        log.info("No lines collected (maybe concurrent). Exiting.")
        return

    # upload chunk
    # compute chunk index by counting existing real chunk objects
    real_chunks = list_real_chunks(s3)
    next_idx = len(real_chunks)
    chunk_key = f"{CHUNK_PREFIX}chunk_{next_idx:06d}.txt"
    body = "".join(collected).encode("utf-8")
    s3.put_object(Bucket=BUCKET, Key=chunk_key, Body=body)
    log.info("Uploaded chunk %s rows=%d bytes=%d", chunk_key, len(collected), len(body))

    # update next_line
    write_state(s3, STATE_NEXT_LINE, end)
    log.info("Updated next_line -> %d", end)

# ---------- AGGREGATOR TASK ----------
def aggregate_new_chunks(**_ctx):
    """
    Read any new chunk files (created by producer), convert to parquet and
    write cumulative/cumulative_{idx:06d}.parquet. State in state/last_agg_idx.txt
    """
    s3 = make_s3_client()
    wait_minio_ready(s3)
    ensure_bucket_and_prefixes()

    real_chunks = list_real_chunks(s3)
    if not real_chunks:
        log.info("No real chunks found")
        return

    # read last aggregated index
    last_agg = read_state(s3, STATE_LAST_AGG, default=-1, cast=int)

    # iterate new chunks
    for obj in real_chunks:
        key = obj["Key"]
        idx_str = Path(key).stem.split("_")[-1]  # chunk_000001 -> 000001
        try:
            idx = int(idx_str)
        except Exception:
            log.warning("Unexpected chunk name %s; skipping", key)
            continue
        if idx <= last_agg:
            log.debug("Already aggregated idx=%d; skipping", idx)
            continue

        # fetch chunk content
        body = s3.get_object(Bucket=BUCKET, Key=key)["Body"].read()
        if not body:
            log.warning("Chunk %s empty, skipping and marking processed", key)
            last_agg = idx
            write_state(s3, STATE_LAST_AGG, last_agg)
            continue

        try:
            df = pd.read_csv(io.StringIO(body.decode("utf-8")), sep="\t", header=None)
        except Exception as e:
            log.exception("Failed to parse chunk %s: %s", key, e)
            # mark as processed to avoid infinite loop; optionally move to bad/
            last_agg = idx
            write_state(s3, STATE_LAST_AGG, last_agg)
            continue

        # convert to parquet
        table = pa.Table.from_pandas(df)
        out = pa.BufferOutputStream()
        pq.write_table(table, out)
        parquet_bytes = out.getvalue()

        cum_key = f"{CUMULATIVE_PREFIX}cumulative_{idx:06d}.parquet"
        s3.put_object(Bucket=BUCKET, Key=cum_key, Body=parquet_bytes)
        log.info("Wrote cumulative parquet %s (rows=%d)", cum_key, len(df))

        # update last_agg state
        last_agg = idx
        write_state(s3, STATE_LAST_AGG, last_agg)

# ---------- DAGs ----------
default_args = {
    "owner": "airflow",
    "retries": 1,
    "retry_delay": 300,
}

# Producer DAG: creates one chunk (2% lines) per run
with DAG(
    dag_id="criteo_chunk_producer",
    start_date=days_ago(1),
    schedule_interval=SCHEDULE_CRON,
    catchup=False,
    default_args=default_args,
) as dag_producer:
    t_ensure = PythonOperator(
        task_id="ensure_minio_ready",
        python_callable=ensure_bucket_and_prefixes,
    )
    t_produce = PythonOperator(
        task_id="produce_next_chunk",
        python_callable=produce_next_chunk,
    )
    t_ensure >> t_produce

# Aggregator DAG: consumes new chunks and writes cumulative parquet
with DAG(
    dag_id="criteo_chunk_aggregator",
    start_date=days_ago(1),
    schedule_interval=AGG_SCHEDULE_CRON,
    catchup=False,
    default_args=default_args,
) as dag_agg:
    t_ensure2 = PythonOperator(
        task_id="ensure_minio_ready_agg",
        python_callable=ensure_bucket_and_prefixes,
    )
    t_agg = PythonOperator(task_id="aggregate_new_chunks", python_callable=aggregate_new_chunks)
    t_ensure2 >> t_agg