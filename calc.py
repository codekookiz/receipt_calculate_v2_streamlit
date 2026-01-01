import streamlit as st
from datetime import datetime
from typing import List

from aws_utils import (
    upload_receipt_to_s3,
    save_monthly_total_to_dynamodb,
)
from ocr import extract_total_from_image


def render_calc_page():
    st.header("📄 영수증 합계 계산")

    st.caption(
        "여러 장의 영수증 이미지를 업로드하면 선택한 월의 총 합계를 계산하고 저장합니다."
    )

    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        uploaded_files = st.file_uploader(
            "📤 영수증 이미지 업로드",
            type=["jpg", "jpeg", "png"],
            accept_multiple_files=True,
            help="여러 장의 영수증을 한 번에 업로드할 수 있습니다."
        )

    with col2:
        today = datetime.today()

        if today.month == 1:
            year = today.year
            month = 12
        else:
            year = today.year - 1
            month = today.month - 1

        year = st.selectbox(
            "📅 연도",
            options=list(range(today.year - 1, today.year + 2)),
            index=today.year - year,
            key="history_year_select"
        )
        month = st.selectbox(
            "📅 월",
            options=list(range(1, 13)),
            index=month - 1,
            key="history_month_select"
        )

    st.divider()

    btn_col1, btn_col2, btn_col3 = st.columns([1, 2, 1])
    with btn_col2:
        run_button = st.button("▶️ 합계 계산 및 저장", use_container_width=True)

    if not run_button:
        return

    if not uploaded_files:
        st.warning("영수증 이미지를 하나 이상 업로드하세요.")
        return

    image_bytes_list: List[bytes] = [file.read() for file in uploaded_files]

    with st.spinner("영수증을 분석하고 저장 중입니다..."):
        totals = []
        for img in image_bytes_list:
            amount = extract_total_from_image(img)
            totals.append(amount)

        total_amount = sum(totals)

        for idx, img in enumerate(image_bytes_list, start=1):
            upload_receipt_to_s3(
                image_bytes=img,
                year=year,
                month=month,
                index=idx
            )

        save_monthly_total_to_dynamodb(
            year=year,
            month=month,
            total_amount=total_amount,
            receipt_count=len(image_bytes_list)
        )

    st.success("저장이 완료되었습니다.")

    st.subheader("📊 계산 결과")
    st.markdown(
        f"""
        <div style="padding: 1.2em; border-radius: 12px; background-color: #f6f6f6;">
            <p><strong>대상 월</strong><br>{year}년 {month}월</p>
            <p style="font-size: 1.8rem; margin-top: 0.8em;">
                <strong>총 합계</strong><br>
                {total_amount:,} 원
            </p>
            <p>영수증 수: {len(image_bytes_list)}장</p>
        </div>
        """,
        unsafe_allow_html=True
    )
