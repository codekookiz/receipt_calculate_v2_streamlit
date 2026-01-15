from dotenv import load_dotenv
load_dotenv()

import os
import re
from datetime import datetime
from typing import List, Optional, Tuple

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
S3_BUCKET_NAME = os.environ.get("S3_BUCKET_NAME", "receipt-codekookiz-bucket")
DYNAMODB_TABLE_NAME = os.environ.get("DYNAMODB_TABLE_NAME", "receipt_total")


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


# ---------- S3 Utilities (개선: 파일명에 금액 포함) ----------
def upload_receipt_to_s3(
    image_bytes: bytes,
    year: int,
    month: int,
    amount: int,
) -> str:
    """
    Upload receipt to S3 with amount in filename for easy recalculation.
    Filename format: {year}_{month}_{amount}_{timestamp}.jpg
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    filename = f"{year}_{month:02d}_{amount}_{timestamp}.jpg"
    key = f"receipts/{year}/{month:02d}/{filename}"

    s3_client.put_object(
        Bucket=S3_BUCKET_NAME,
        Key=key,
        Body=image_bytes,
        ContentType="image/jpeg",
    )

    return key


def list_receipts_from_s3(year: int, month: int) -> List[str]:
    """List all receipt keys for a specific year/month."""
    prefix = f"receipts/{year}/{month:02d}/"

    response = s3_client.list_objects_v2(
        Bucket=S3_BUCKET_NAME,
        Prefix=prefix,
    )

    contents = response.get("Contents", [])
    return [obj["Key"] for obj in contents]


def delete_receipt_from_s3(key: str) -> bool:
    """Delete a specific receipt from S3."""
    try:
        s3_client.delete_object(
            Bucket=S3_BUCKET_NAME,
            Key=key,
        )
        return True
    except Exception as e:
        st.error(f"S3 삭제 실패: {e}")
        return False


def parse_amount_from_filename(key: str) -> Optional[int]:
    """
    Extract amount from filename.
    Filename format: {year}_{month}_{amount}_{timestamp}.jpg
    Example: 2024_01_50000_20240115_120000_123456.jpg → 50000
    """
    filename = key.split("/")[-1]  # Get filename from full path
    
    # Pattern: year_month_amount_timestamp.jpg
    match = re.match(r'\d{4}_\d{2}_(\d+)_', filename)
    if match:
        return int(match.group(1))
    
    return None


def recalculate_monthly_total(year: int, month: int) -> Tuple[int, int]:
    """
    Recalculate monthly total by reading all receipt filenames.
    Returns: (total_amount, receipt_count)
    """
    receipt_keys = list_receipts_from_s3(year, month)
    
    total_amount = 0
    receipt_count = 0
    
    for key in receipt_keys:
        amount = parse_amount_from_filename(key)
        if amount is not None:
            total_amount += amount
            receipt_count += 1
    
    return total_amount, receipt_count


def get_receipt_bytes_from_s3(key: str) -> bytes:
    """Download receipt image bytes from S3."""
    response = s3_client.get_object(
        Bucket=S3_BUCKET_NAME,
        Key=key,
    )
    return response["Body"].read()


# ---------- DynamoDB Utilities ----------
def save_monthly_total_to_dynamodb(
    year: int,
    month: int,
    total_amount: int,
    receipt_count: int,
):
    """Save or update monthly total in DynamoDB."""
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
    """Get monthly total from DynamoDB."""
    response = receipt_table.get_item(
        Key={
            "year": year,
            "month": month,
        }
    )

    return response.get("Item")


def delete_monthly_total_from_dynamodb(year: int, month: int) -> bool:
    """Delete monthly total from DynamoDB."""
    try:
        receipt_table.delete_item(
            Key={
                "year": year,
                "month": month,
            }
        )
        return True
    except Exception as e:
        st.error(f"DynamoDB 삭제 실패: {e}")
        return False
