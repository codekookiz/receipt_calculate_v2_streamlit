# 🧾 영수증 계산기 V2

영수증 이미지를 업로드하면 AI가 자동으로 합계 금액을 추출하여 월별로 관리하는 웹 애플리케이션입니다.

## ✨ 주요 기능

### 📤 1. 영수증 계산 및 저장
- 여러 장의 영수증 이미지를 한 번에 업로드
- AI OCR로 자동 합계 금액 추출
- 월별 자동 집계 및 저장
- **파일명에 금액 포함** → 재계산 가능

### 📊 2. 히스토리 조회
- 월별 영수증 합계 및 이미지 확인
- 연간 총 지출 통계
- 모든 영수증 이미지 갤러리 형태로 표시

### ✏️ 3. 수정 및 삭제 (NEW!)
- **개별 영수증 삭제** 기능
- 삭제 후 **자동 합계 재계산**
- **영수증 추가** 기능
- 실시간 DB 업데이트

## 🛠️ 기술 스택

- **Frontend**: Streamlit
- **OCR**: Huggingface Router API (Nebius/Gemma-3-27b)
- **Storage**: AWS S3 (이미지)
- **Database**: AWS DynamoDB (합계 데이터)

## 📦 설치 방법

### 1. 패키지 설치
```bash
pip install -r requirements.txt
```

### 2. 환경 변수 설정
`.env` 파일을 프로젝트 루트에 생성:

```env
HF_TOKEN=your_huggingface_token
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_REGION=ap-northeast-2
S3_BUCKET_NAME=receipt-codekookiz-bucket
DYNAMODB_TABLE_NAME=receipt_total
```

### 3. AWS 리소스 설정

#### S3 버킷 생성
```bash
aws s3 mb s3://receipt-codekookiz-bucket --region ap-northeast-2
```

#### DynamoDB 테이블 생성
```bash
aws dynamodb create-table \
    --table-name receipt_total \
    --attribute-definitions \
        AttributeName=year,AttributeType=N \
        AttributeName=month,AttributeType=N \
    --key-schema \
        AttributeName=year,KeyType=HASH \
        AttributeName=month,KeyType=RANGE \
    --billing-mode PAY_PER_REQUEST \
    --region ap-northeast-2
```

## 🚀 실행 방법

```bash
streamlit run main.py
```

브라우저에서 `http://localhost:8501`로 접속

## 📁 프로젝트 구조

```
receipt_calculate_v2/
├── main.py              # Streamlit 메인 앱
├── calc.py              # 영수증 계산 페이지
├── history.py           # 히스토리 조회 페이지
├── edit.py              # 수정/삭제 페이지 (NEW!)
├── ocr.py               # OCR 서비스
├── aws_utils.py         # AWS 유틸리티 (개선됨!)
├── requirements.txt     # 패키지 의존성
└── .env                 # 환경 변수
```

## 🔑 핵심 개선사항 (V1 → V2)

### 1. 파일명 구조 변경
**V1 (문제)**:
```
receipts/2024/01/1월_영수증_1.jpg  ← 금액 정보 없음
```

**V2 (해결)**:
```
receipts/2024/01/2024_01_50000_20240115_120000.jpg  ← 금액 포함!
                          ^^^^^ 
```

### 2. 재계산 기능 추가
- 파일명에서 금액을 추출하여 자동 합계 재계산
- 영수증 삭제/추가 시 즉시 반영

### 3. 수정/삭제 기능
- 개별 영수증 삭제
- 영수증 추가
- 실시간 DB 업데이트

## 💡 사용 팁

1. **영수증 촬영 팁**:
   - 합계 부분이 명확하게 보이도록 촬영
   - 충분한 조명 확보
   - 흔들리지 않게 촬영

2. **삭제 시 주의사항**:
   - 삭제는 즉시 반영되며 되돌릴 수 없습니다
   - 삭제 전 확인하세요

3. **재계산 자동화**:
   - 영수증 추가/삭제 시 자동으로 합계 재계산
   - DynamoDB도 자동 업데이트

## 🐛 문제 해결

### OCR 추출 실패 시
- 이미지 품질을 확인하세요
- 영수증의 "합계" 부분이 명확한지 확인
- 다른 각도로 촬영해보세요

### AWS 연결 오류 시
- `.env` 파일의 AWS 자격 증명 확인
- S3 버킷과 DynamoDB 테이블 생성 확인
- AWS 리전 확인

## 📝 라이선스

MIT License

## 👨‍💻 개발자

KOOKIZ

---

**V1 대비 주요 개선점**: 파일명에 금액 포함 → 재계산 가능 + 수정/삭제 기능 추가 🎉
