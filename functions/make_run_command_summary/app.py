import boto3
import csv
import os
import re

S3_CLIENT = boto3.client("s3")
LOG_BUCKET = os.environ["LOG_BUCKET"]
LOG_BUCKET_REGION = os.environ["LOG_BUCKET_REGION"]

SUMMARY_FILE = "/tmp/summary.csv"


def __get_pages(execution_uuid):
    paginator = S3_CLIENT.get_paginator("list_objects_v2")
    pages = paginator.paginate(
        Bucket=LOG_BUCKET,
        Prefix=f"{execution_uuid}/logs"
    )
    return pages


def __download_object(object_key, file):
    with open(file, 'wb') as f:
        S3_CLIENT.download_fileobj(LOG_BUCKET, object_key, f)
    return file


def __upload_object(file, object_key):
    S3_CLIENT.upload_file(file, LOG_BUCKET, object_key)
    return object_key


def __download_run_command_logs(execution_uuid):
    INSTANCE_ID_REGEX = r"i-[0-9a-z]+"
    files = []
    for page in __get_pages(execution_uuid):
        try:
            for obj in page["Contents"]:
                object_key = obj["Key"]
                if "stdout" in object_key:
                    instance_id = re.search(INSTANCE_ID_REGEX, object_key).group()
                    file = __download_object(object_key, f"/tmp/{instance_id}.log")
                    files.append({
                        "path": file,
                        "instance_id": instance_id
                    })
        except KeyError:
            print("No files exist")
    return files


def make_run_command_summary(execution_uuid):
    files = __download_run_command_logs(execution_uuid)
    with open(SUMMARY_FILE, "w") as wf:
        writer = csv.writer(wf)
        for file in files:
            with open(file["path"], "r") as rf:
                writer.writerow([file["instance_id"], rf.read()])
    summary_object_key = __upload_object(SUMMARY_FILE, f"{execution_uuid}/_output/summary.csv")
    return summary_object_key


def lambda_handler(event, context):
    print(event)
    execution_uuid = event["execution_id"].split(":")[-1]
    summary_object_key = make_run_command_summary(execution_uuid)
    return {
        "console_url": f"https://{LOG_BUCKET_REGION}.console.aws.amazon.com/s3/object/{LOG_BUCKET}?region={LOG_BUCKET_REGION}&bucketType=general&prefix={summary_object_key}",
        "s3_url": f"https://{LOG_BUCKET}.s3.{LOG_BUCKET_REGION}.amazonaws.com/{summary_object_key}"
    }
