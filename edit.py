import streamlit as st
from datetime import datetime

from aws_utils import (
    get_monthly_total_from_dynamodb,
    list_receipts_from_s3,
    get_receipt_bytes_from_s3,
    parse_amount_from_filename,
    delete_receipt_from_s3,
    recalculate_monthly_total,
    save_monthly_total_to_dynamodb,
    delete_monthly_total_from_dynamodb,
    upload_receipt_to_s3,
)
from ocr import extract_total_from_image


def render_edit_page():
    st.header("✏️ 영수증 수정 및 삭제")

    st.caption(
        "기존 월별 영수증을 관리하고, 개별 영수증을 추가하거나 삭제할 수 있습니다."
    )

    st.divider()

    tabs = st.tabs(["🗑️ 삭제하기", "➕ 추가하기"])

    today = datetime.today()

    # 기본값: 직전 월
    if today.month == 1:
        default_year = today.year - 1
        default_month = 12
    else:
        default_year = today.year
        default_month = today.month - 1

    # ========== 삭제 탭 ==========
    with tabs[0]:
        st.subheader("🗑️ 영수증 삭제")
        
        col1, col2 = st.columns(2)
        with col1:
            year_options = list(range(today.year - 2, today.year + 2))
            del_year = st.selectbox(
                "📅 연도",
                options=year_options,
                index=year_options.index(default_year) if default_year in year_options else 2,
                key="delete_year_select"
            )
        with col2:
            del_month = st.selectbox(
                "📅 월",
                options=list(range(1, 13)),
                index=default_month - 1,
                key="delete_month_select"
            )

        st.divider()

        if st.button("🔍 영수증 불러오기", key="load_receipts_btn", use_container_width=True):
            with st.spinner("영수증 로딩 중..."):
                record = get_monthly_total_from_dynamodb(year=del_year, month=del_month)
                receipt_keys = list_receipts_from_s3(year=del_year, month=del_month)
                
                st.session_state['delete_record'] = record
                st.session_state['delete_receipts'] = receipt_keys
                st.session_state['delete_year'] = del_year
                st.session_state['delete_month'] = del_month

        if 'delete_receipts' in st.session_state and st.session_state['delete_receipts']:
            record = st.session_state.get('delete_record')
            receipt_keys = st.session_state['delete_receipts']
            stored_year = st.session_state.get('delete_year')
            stored_month = st.session_state.get('delete_month')
            
            # Display current summary
            if record:
                st.info(f"📊 현재: {record['total_amount']:,}원 ({record['receipt_count']}장)")
            
            st.divider()
            st.subheader("영수증 목록")
            st.caption("각 영수증 아래의 삭제 버튼을 클릭하세요")
            
            # Display receipts with individual delete buttons
            cols = st.columns(3, gap="medium")
            for idx, key in enumerate(receipt_keys):
                with cols[idx % 3]:
                    amount = parse_amount_from_filename(key)
                    amount_text = f"{amount:,}원" if amount else "금액 불명"
                    
                    # Show image
                    image_bytes = get_receipt_bytes_from_s3(key)
                    st.image(image_bytes, use_column_width=True)
                    
                    # Show amount
                    st.markdown(
                        f"<div style='text-align: center; margin: 0.5em 0;'><strong>{amount_text}</strong></div>",
                        unsafe_allow_html=True
                    )
                    
                    # Individual delete button
                    if st.button(
                        "🗑️ 삭제",
                        key=f"del_btn_{idx}_{key}",
                        use_container_width=True,
                        type="secondary"
                    ):
                        with st.spinner(f"삭제 중... ({amount_text})"):
                            # Delete from S3
                            success = delete_receipt_from_s3(key)
                            
                            if success:
                                # Recalculate total
                                new_total, new_count = recalculate_monthly_total(stored_year, stored_month)
                                
                                if new_count > 0:
                                    # Update DynamoDB
                                    save_monthly_total_to_dynamodb(
                                        stored_year, stored_month, new_total, new_count
                                    )
                                    st.success(f"✅ 삭제 완료! 새로운 합계: {new_total:,}원 ({new_count}장)")
                                else:
                                    # Delete from DynamoDB if no receipts left
                                    delete_monthly_total_from_dynamodb(stored_year, stored_month)
                                    st.success("✅ 모든 영수증이 삭제되었습니다.")
                                
                                # Clear session state
                                if 'delete_receipts' in st.session_state:
                                    del st.session_state['delete_receipts']
                                if 'delete_record' in st.session_state:
                                    del st.session_state['delete_record']
                                if 'delete_year' in st.session_state:
                                    del st.session_state['delete_year']
                                if 'delete_month' in st.session_state:
                                    del st.session_state['delete_month']
                                
                                # Wait a moment for user to see the message
                                import time
                                time.sleep(1)
                                
                                # Rerun to refresh
                                st.rerun()
                            else:
                                st.error("❌ 삭제 실패")
        
        elif 'delete_receipts' in st.session_state:
            st.info("ℹ️ 해당 월에 영수증이 없습니다.")

    # ========== 추가 탭 ==========
    with tabs[1]:
        st.subheader("➕ 영수증 추가")
        
        col1, col2 = st.columns(2)
        with col1:
            add_year = st.selectbox(
                "📅 연도",
                options=year_options,
                index=year_options.index(default_year) if default_year in year_options else 2,
                key="add_year_select"
            )
        with col2:
            add_month = st.selectbox(
                "📅 월",
                options=list(range(1, 13)),
                index=default_month - 1,
                key="add_month_select"
            )

        st.divider()
        
        # File uploader
        uploaded_files = st.file_uploader(
            "📤 추가할 영수증 이미지",
            type=["jpg", "jpeg", "png"],
            accept_multiple_files=True,
            key="add_receipt_uploader",
            help="기존 월에 영수증을 추가합니다."
        )

        if uploaded_files and st.button("➕ 영수증 추가", type="primary", use_container_width=True, key="add_receipts_btn"):
            with st.spinner("영수증 추가 중..."):
                results = []
                
                # Process each file
                for idx, file in enumerate(uploaded_files, 1):
                    image_bytes = file.read()
                    amount = extract_total_from_image(image_bytes)
                    
                    if amount > 0:
                        # Upload to S3
                        key = upload_receipt_to_s3(
                            image_bytes=image_bytes,
                            year=add_year,
                            month=add_month,
                            amount=amount
                        )
                        results.append({
                            'filename': file.name,
                            'amount': amount,
                            'success': True
                        })
                    else:
                        results.append({
                            'filename': file.name,
                            'success': False
                        })
                
                # Recalculate total
                new_total, new_count = recalculate_monthly_total(add_year, add_month)
                
                # Update DynamoDB
                save_monthly_total_to_dynamodb(
                    add_year, add_month, new_total, new_count
                )
                
                # Show summary
                successful = [r for r in results if r['success']]
                
                st.success(f"✅ {len(successful)}개 영수증 추가 완료!")
                st.info(f"📊 {add_year}년 {add_month}월 최종 합계: **{new_total:,}원** ({new_count}장)")
