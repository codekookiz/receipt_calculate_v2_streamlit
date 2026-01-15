import streamlit as st
from datetime import datetime
from typing import List

from aws_utils import (
    upload_receipt_to_s3,
    save_monthly_total_to_dynamodb,
    list_receipts_from_s3,
    delete_receipt_from_s3,
    delete_monthly_total_from_dynamodb,
)
from ocr import extract_total_from_image


def render_calc_page():
    st.header("📄 영수증 합계 계산")

    st.caption(
        "여러 장의 영수증 이미지를 업로드하면 선택한 월의 총 합계를 계산하고 저장합니다."
    )
    st.warning("⚠️ 해당 연월의 **기존 영수증이 모두 삭제**되고 새로 저장됩니다.")

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

        # 기본값: 이전 달
        if today.month == 1:
            default_year = today.year - 1
            default_month = 12
        else:
            default_year = today.year
            default_month = today.month - 1

        year = st.selectbox(
            "📅 연도",
            options=list(range(today.year - 1, today.year + 2)),
            index=list(range(today.year - 1, today.year + 2)).index(default_year),
            key="calc_year_select"
        )
        month = st.selectbox(
            "📅 월",
            options=list(range(1, 13)),
            index=default_month - 1,
            key="calc_month_select"
        )

    st.divider()

    btn_col1, btn_col2, btn_col3 = st.columns([1, 2, 1])
    with btn_col2:
        run_button = st.button("▶️ 합계 계산 및 저장", use_container_width=True, type="primary")

    if not run_button:
        return

    if not uploaded_files:
        st.warning("⚠️ 영수증 이미지를 하나 이상 업로드하세요.")
        return

    # Process receipts
    with st.spinner("🔍 영수증을 분석하고 저장 중입니다..."):
        # Step 1: 기존 데이터 삭제 (덮어쓰기)
        existing_receipts = list_receipts_from_s3(year, month)
        if existing_receipts:
            for key in existing_receipts:
                delete_receipt_from_s3(key)
        delete_monthly_total_from_dynamodb(year, month)
        
        # Step 2: 새 영수증 처리
        results = []
        total_amount = 0
        
        # Extract amounts from each receipt
        for idx, file in enumerate(uploaded_files, 1):
            image_bytes = file.read()
            amount = extract_total_from_image(image_bytes)
            
            if amount > 0:
                # Upload to S3 with amount in filename
                key = upload_receipt_to_s3(
                    image_bytes=image_bytes,
                    year=year,
                    month=month,
                    amount=amount
                )
                results.append({
                    'filename': file.name,
                    'amount': amount,
                    'key': key,
                    'success': True
                })
                total_amount += amount
            else:
                results.append({
                    'filename': file.name,
                    'amount': 0,
                    'success': False
                })
        
        # Step 3: 새로운 합계 저장
        receipt_count = len([r for r in results if r['success']])
        
        if receipt_count > 0:
            save_monthly_total_to_dynamodb(
                year=year,
                month=month,
                total_amount=total_amount,
                receipt_count=receipt_count
            )

    # Display results
    st.success("✅ 저장이 완료되었습니다!")

    st.divider()

    # Final summary
    st.subheader(f"📅 {year}년 {month}월 최종 합계")
    
    # Show successful and failed extractions
    successful = [r for r in results if r['success']]
    failed = [r for r in results if not r['success']]
    
    # Build receipt list HTML
    receipt_list_html = ""
    if successful:
        for r in successful:
            receipt_list_html += f"<div style='margin-top: 0.3em;'>• {r['filename']}: <strong>{r['amount']:,}원</strong></div>"
    
    if failed:
        for r in failed:
            receipt_list_html += f"<div style='margin-top: 0.3em; color: #999;'>• {r['filename']}: <span style='color: #ff6b6b;'>추출 실패</span></div>"
    
    st.markdown(
        f"""
        <div style="padding: 1.5em; border-radius: 12px; background-color: #f0f8ff; border: 2px solid #4a90e2;">
            <p style="font-size: 2rem; margin: 0; color: #2c5aa0;">
                <strong>{total_amount:,} 원</strong>
            </p>
            <p style="margin-top: 0.5em; color: #666;">
                총 영수증 수: <strong>{receipt_count}장</strong>
            </p>
            {receipt_list_html}
        </div>
        """,
        unsafe_allow_html=True
    )
