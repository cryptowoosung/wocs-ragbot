# WOCS RAG 지식봇

WOCS(우성어닝천막공사캠프시스템)의 카탈로그·FITI 성적서·제품 브로슈어를 AI로 검색·질의하는 지식봇.

해외 바이어 응대 속도 9배 단축을 목표로 함.

## 기술 스택
- Python 3.12
- RAG-Anything (LightRAG 기반)
- MinerU (PDF 파서)
- OpenAI GPT-4o-mini (LLM), GPT-4o (Vision), text-embedding-3-large
- Streamlit (UI)

## 설치

### 1. 저장소 클론
```bash
git clone https://github.com/cryptowoosung/wocs-ragbot.git
cd wocs-ragbot
```

### 2. 가상환경 + 의존성
```bash
py -3.12 -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### 3. API 키 설정
```bash
copy .env.example .env
# .env 열어서 OPENAI_API_KEY 값 입력
```

## 실행

### PDF 인덱싱 (최초 1회)
```bash
python ingest.py
```

### Streamlit 앱 실행
```bash
streamlit run app.py
```

## 폴더 구조
```
wocs-ragbot/
├── source_docs/        # PDF 원본 (gitignore, 로컬에만)
├── rag_storage/        # 인덱싱 결과 (gitignore)
├── utils/              # 유틸리티 모듈
├── logs/               # 로그
├── ingest.py           # 인덱싱 스크립트
├── app.py              # Streamlit UI
├── requirements.txt
└── README.md
```

## 라이선스
MIT

## 작성자
우성 (cryptowoosung)
