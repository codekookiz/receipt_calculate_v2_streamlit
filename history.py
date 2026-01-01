import streamlit as st
from datetime import datetime

from aws_utils import (
    get_monthly_total_from_dynamodb,
    list_receipts_from_s3,
    get_receipt_bytes_from_s3,
)


def render_history_page():
    st.header("📊 과거 월별 기록 조회")

    st.caption(
        "연도와 월을 선택하면 저장된 영수증 합계 기록을 확인할 수 있습니다."
    )

    st.divider()

    tabs = st.tabs(["📅 월별 조회", "📆 연간 조회"])

    today = datetime.today()

    with tabs[0]:
        col1, col2 = st.columns(2)
        with col1:
            year = st.selectbox(
                "📅 연도",
                options=[today.year - 1, today.year, today.year + 1],
                index=1,
                key="monthly_year_select"
            )
        with col2:
            month = st.selectbox(
                "📅 월",
                options=list(range(1, 13)),
                index=today.month - 1,
                key="monthly_month_select"
            )

        st.divider()

        btn_col1, btn_col2, btn_col3 = st.columns([1, 2, 1])
        with btn_col2:
            search_button = st.button("🔍 기록 조회", use_container_width=True, key="monthly_search_btn")

        if not search_button:
            st.info("연도와 월을 선택한 뒤 ‘기록 조회’를 눌러주세요.")
        else:
            record = get_monthly_total_from_dynamodb(year=year, month=month)

            if record is None:
                st.info("해당 월에 저장된 기록이 없습니다.")
            else:
                updated_at = record["updated_at"].replace("T", " ").split(".")[0].replace("Z", "")

                st.subheader(f"📅 {year}년 {month}월 요약")
                st.markdown(
                    f"""
                    <div style="padding: 1.2em; border-radius: 12px; background-color: #f6f6f6;">
                        <p style="font-size: 1.6rem;">
                            <strong>총 합계</strong><br>
                            {record['total_amount']:,} 원
                        </p>
                        <p>영수증 수: {record['receipt_count']}장</p>
                        <p style="color: #666;">마지막 업데이트: {updated_at}</p>
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
                    cols = st.columns(3)
                    for idx, key in enumerate(receipt_keys):
                        with cols[idx % 3]:
                            image_bytes = get_receipt_bytes_from_s3(key)
                            st.image(image_bytes, use_column_width=True)

    with tabs[1]:
        st.subheader("📆 연간 지출 요약")

        year = st.selectbox(
            "📅 연도 선택",
            options=[today.year - 1, today.year, today.year + 1],
            index=1,
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
    padding: 1.2rem;
    border-radius: 12px;
    background-color: #f7f7f7;
    border: 1px solid #e5e5e5;
    margin-bottom: 1rem;
">
    <div style="font-size: 1.6rem; font-weight: 600; margin-bottom: 0.6rem;">
        {year}년 총 지출 {total_year_amount:,} 원
    </div>
    <div style="font-size: 0.95rem; color: #666;">
        기록된 영수증 {total_receipt_count}장
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
    padding: 0.8rem 1rem;
    border-radius: 10px;
    border: 1px solid #eee;
    margin-bottom: 0.6rem;
">
    <strong>{m}월</strong> · {record['total_amount']:,} 원  
    <span style="color:#666; font-size:0.85rem;">
        (영수증 {record['receipt_count']}장 · 업데이트 {updated_at})
    </span>
</div>
""",
                unsafe_allow_html=True
            )
