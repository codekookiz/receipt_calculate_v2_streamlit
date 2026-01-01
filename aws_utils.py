from dotenv import load_dotenv
load_dotenv()

import os
from datetime import datetime
from typing import List, Optional

import boto3
import streamlit as st


# ---------- Environment Validation ----------
REQUIRED_ENV_VARS = [
    "AWS_ACCESS_KEY_ID",
    "AWS_SECRET_ACCESS_KEY",
    "AWS_REGION",
]

for var in REQUIRED_ENV_VARS:
    if not os.environ.get(var):
        st.error(f"AWS 환경변수 {var} 가 설정되어 있지 않습니다.")
        st.stop()

AWS_REGION = os.environ["AWS_REGION"]
S3_BUCKET_NAME = "receipt-codekookiz-bucket"
DYNAMODB_TABLE_NAME = "receipt_total"


# ---------- AWS Clients ----------
s3_client = boto3.client(
    "s3",
    region_name=AWS_REGION,
)

dynamodb = boto3.resource(
    "dynamodb",
    region_name=AWS_REGION,
)

receipt_table = dynamodb.Table(DYNAMODB_TABLE_NAME)


# ---------- S3 Utilities ----------
def upload_receipt_to_s3(
    image_bytes: bytes,
    year: int,
    month: int,
    index: int,
) -> str:
    key = f"receipts/{year}/{str(month).zfill(2)}/{month}월_영수증_{index}.jpg"

    s3_client.put_object(
        Bucket=S3_BUCKET_NAME,
        Key=key,
        Body=image_bytes,
        ContentType="image/jpeg",
    )

    return key


def list_receipts_from_s3(year: int, month: int) -> List[str]:
    prefix = f"receipts/{year}/{str(month).zfill(2)}/"

    response = s3_client.list_objects_v2(
        Bucket=S3_BUCKET_NAME,
        Prefix=prefix,
    )

    contents = response.get("Contents", [])
    return [obj["Key"] for obj in contents]


def generate_presigned_url(key: str, expires_in: int = 300) -> str:
    return s3_client.generate_presigned_url(
        "get_object",
        Params={
            "Bucket": S3_BUCKET_NAME,
            "Key": key,
        },
        ExpiresIn=expires_in,
    )


# ---------- DynamoDB Utilities ----------
def save_monthly_total_to_dynamodb(
    year: int,
    month: int,
    total_amount: int,
    receipt_count: int,
):
    receipt_table.put_item(
        Item={
            "year": year,
            "month": month,
            "total_amount": total_amount,
            "receipt_count": receipt_count,
            "updated_at": datetime.utcnow().isoformat() + "Z",
        }
    )


def get_monthly_total_from_dynamodb(
    year: int,
    month: int,
) -> Optional[dict]:
    response = receipt_table.get_item(
        Key={
            "year": year,
            "month": month,
        }
    )

    return response.get("Item")

def get_receipt_bytes_from_s3(key: str) -> bytes:
    response = s3_client.get_object(
        Bucket=S3_BUCKET_NAME,
        Key=key,
    )
    return response["Body"].read()