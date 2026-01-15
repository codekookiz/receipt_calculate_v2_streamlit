import os
import re
import base64

import streamlit as st
from huggingface_hub import InferenceClient


# ---------- Environment Validation ----------
if not os.environ.get("HF_TOKEN"):
    st.error("HF_TOKEN 환경변수가 설정되어 있지 않습니다.")
    st.stop()


# ---------- Hugging Face Client ----------
client = InferenceClient(
    api_key=os.environ["HF_TOKEN"],
    base_url="https://router.huggingface.co",
)


# ---------- OCR Logic ----------
def extract_total_from_image(image_bytes: bytes) -> int:
    """
    Extracts the final total amount from a receipt image.
    Returns 0 if no numeric total is detected.
    """

    encoded_image = base64.b64encode(image_bytes).decode("utf-8")

    response = client.chat.completions.create(
        model="google/gemma-3-27b-it:nebius",
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": (
                            "다음 영수증 이미지에서 최종 결제 금액(합계, TOTAL)에 해당하는 "
                            "숫자 하나만 출력해. 통화 기호, 쉼표, 설명 문장은 제외하고 "
                            "숫자만 출력해."
                        )
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{encoded_image}"
                        }
                    }
                ]
            }
        ],
    )

    content = response.choices[0].message.content

    match = re.search(r"\d+", content)
    if not match:
        return 0

    return int(match.group())
