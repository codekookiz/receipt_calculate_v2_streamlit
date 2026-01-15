import streamlit as st
from datetime import datetime

from aws_utils import (
    get_monthly_total_from_dynamodb,
    list_receipts_from_s3,
    get_receipt_bytes_from_s3,
    parse_amount_from_filename,
)


def render_history_page():
    st.header("📊 과거 월별 기록 조회")

    st.caption(
        "연도와 월을 선택하면 저장된 영수증 합계 기록을 확인할 수 있습니다."
    )

    st.divider()

    tabs = st.tabs(["📅 월별 조회", "📆 연간 조회"])

    today = datetime.today()

    # 기본값: 직전 월
    if today.month == 1:
        default_year = today.year - 1
        default_month = 12
    else:
        default_year = today.year
        default_month = today.month - 1

    with tabs[0]:
        col1, col2 = st.columns(2)
        with col1:
            year_options = list(range(today.year - 2, today.year + 2))
            year = st.selectbox(
                "📅 연도",
                options=year_options,
                index=year_options.index(default_year) if default_year in year_options else 2,
                key="monthly_year_select"
            )
        with col2:
            month = st.selectbox(
                "📅 월",
                options=list(range(1, 13)),
                index=default_month - 1,
                key="monthly_month_select"
            )

        st.divider()

        btn_col1, btn_col2, btn_col3 = st.columns([1, 2, 1])
        with btn_col2:
            search_button = st.button("🔍 기록 조회", use_container_width=True, key="monthly_search_btn")

        if not search_button:
            st.info("💡 연도와 월을 선택한 뒤 '기록 조회'를 눌러주세요.")
        else:
            record = get_monthly_total_from_dynamodb(year=year, month=month)

            if record is None:
                st.info("ℹ️ 해당 월에 저장된 기록이 없습니다.")
            else:
                updated_at = record["updated_at"].replace("T", " ").split(".")[0].replace("Z", "")

                st.subheader(f"📅 {year}년 {month}월 요약")
                st.markdown(
                    f"""
                    <div style="padding: 1.5em; border-radius: 12px; background-color: #f0f8ff; border: 2px solid #4a90e2;">
                        <p style="font-size: 2rem; margin: 0; color: #2c5aa0;">
                            <strong>{record['total_amount']:,} 원</strong>
                        </p>
                        <p style="margin-top: 0.5em; color: #666;">
                            영수증 수: <strong>{record['receipt_count']}장</strong><br>
                            <small>마지막 업데이트: {updated_at}</small>
                        </p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

                st.divider()

                st.subheader("🧾 영수증 이미지")

                receipt_keys = list_receipts_from_s3(year=year, month=month)

                if not receipt_keys:
                    st.info("해당 월에 저장된 영수증 이미지가 없습니다.")
                else:
                    cols = st.columns(3, gap="medium")
                    for idx, key in enumerate(receipt_keys):
                        with cols[idx % 3]:
                            # Parse amount from filename
                            amount = parse_amount_from_filename(key)
                            amount_text = f"{amount:,}원" if amount else "금액 불명"
                            
                            image_bytes = get_receipt_bytes_from_s3(key)
                            
                            st.markdown(
                                f"<div style='margin-bottom: 1rem; text-align: center; font-size: 0.9rem; color: #666;'>"
                                f"<strong>{amount_text}</strong></div>",
                                unsafe_allow_html=True
                            )
                            st.image(image_bytes, use_column_width=True)

    with tabs[1]:
        st.subheader("📆 연간 지출 요약")

        year = st.selectbox(
            "📅 연도 선택",
            options=[today.year - 2, today.year - 1, today.year, today.year + 1],
            index=2,
            key="yearly_year_select"
        )

        st.divider()

        # 연간 집계
        monthly_records = []
        total_year_amount = 0
        total_receipt_count = 0

        for m in range(1, 13):
            record = get_monthly_total_from_dynamodb(year=year, month=m)
            if record:
                monthly_records.append((m, record))
                total_year_amount += record["total_amount"]
                total_receipt_count += record["receipt_count"]

        if not monthly_records:
            st.info("선택한 연도에 저장된 기록이 없습니다.")
            return

        # 연간 요약 카드
        st.markdown(
            f"""
<div style="
    padding: 1.5rem;
    border-radius: 12px;
    background-color: #f0fdf4;
    border: 2px solid #10b981;
    margin-bottom: 1.5rem;
">
    <div style="font-size: 2rem; font-weight: 600; margin-bottom: 0.5rem; color: #047857;">
        {year}년 총 지출 {total_year_amount:,} 원
    </div>
    <div style="font-size: 1rem; color: #666;">
        기록된 영수증 <strong>{total_receipt_count}장</strong>
    </div>
</div>
""",
            unsafe_allow_html=True
        )

        st.subheader("📊 월별 내역")

        for m, record in monthly_records:
            updated_at = record["updated_at"].replace("T", " ").split(".")[0].replace("Z", "")
            st.markdown(
                f"""
<div style="
    padding: 1rem 1.2rem;
    border-radius: 10px;
    border: 1px solid #e5e7eb;
    margin-bottom: 0.8rem;
    background-color: #fafafa;
">
    <strong style="font-size: 1.1rem;">{m}월</strong> · 
    <span style="font-size: 1.2rem; color: #2563eb;">{record['total_amount']:,} 원</span>  
    <br>
    <span style="color:#6b7280; font-size:0.85rem;">
        영수증 {record['receipt_count']}장 · {updated_at}
    </span>
</div>
""",
                unsafe_allow_html=True
            )
