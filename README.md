# WOCS 내부 지식봇 + 바이어 응대 도구

우성어닝천막공사캠프시스템(WOCS)의 제품 카탈로그, FITI 시험성적서, 제품 브로셔를 하나의 RAG(검색 증강 생성) 지식 그래프로 묶어, 한국어 질의·영문 응대 초안 작성·제품 스펙 비교를 한 화면에서 수행하는 내부용 Streamlit 도구.

해외 바이어 메일을 붙여넣으면 사실 기반의 영문 초안(Formal / Friendly / Concise)을 분 단위로 생성한다. 수치가 지식베이스에 없으면 자동으로 *"confirm with engineering team"* 으로 회피하여 허위 스펙 생성을 차단한다.

## 🛠️ 기술 스택

- **Python** 3.12
- **RAG-Anything 1.2.x** (LightRAG 기반 멀티모달 RAG 프레임워크)
- **MinerU 3.1.x** (PDF → Markdown + 이미지/표/수식, `pipeline` 백엔드 — CPU)
- **OpenAI**: `gpt-4o-mini`(LLM) / `gpt-4o`(Vision) / `text-embedding-3-large`(3072d)
- **Streamlit 1.56.x** (UI)

## 📦 설치 (3단계)

### 1. 가상환경 & 의존성
```powershell
py -3.12 -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### 2. API 키 설정
```powershell
copy .env.example .env
# .env 파일을 열어 OPENAI_API_KEY 값 입력
```

### 3. 원본 자료 배치 + 인덱싱 (최초 1회)
원본 PDF를 `source_docs/` 아래에 배치:
```
source_docs/
├── catalog/            # 통합 카탈로그 1부
├── brochure/           # 통합 브로셔 1부
├── product_brochure/   # 모델별 브로셔 16부 (KO Print 권장)
└── fiti/               # FITI 시험성적서
```

원본 자료는 레포에 포함되지 않는다(`.gitignore`). 인덱싱 실행:
```powershell
venv\Scripts\python.exe ingest.py
```
- CPU 기준 약 90분~2시간 (파일 27개 합계 약 40 MB 기준).
- 실패 없이 중단 시 재실행하면 이어 처리한다(`logs/ingest.log` 에서 success 엔트리 스킵).

## ▶️ 실행

```powershell
streamlit run app.py
```

브라우저가 열리고 3개 탭 UI가 뜬다:

| 탭 | 기능 |
|---|---|
| 💬 자유 질의 | 한국어 질문 → RAG hybrid/local/global/naive 모드로 답변 + 근거 문서 |
| ✉️ 바이어 응대 | 바이어 메일 + 스타일 선택 → 사실 기반 영문 초안 (250단어 이하, CTA 포함) |
| 📊 제품 비교 | 최대 3개 모델 × 선택 축(크기/무게/용도/가격대/특징) markdown 표 |

## 🗂️ 폴더 구조

```
wocs-ragbot/
├── app.py                  # Streamlit UI (3탭)
├── ingest.py               # PDF → RAG 인덱싱 파이프라인
├── utils/
│   ├── rag_client.py       # RAGAnything 싱글턴 (OpenAI + MinerU pipeline 백엔드)
│   ├── prompts.py          # 바이어 응대 프롬프트 템플릿
│   └── fiti_redactor.py    # (TODO, Step 5) FITI 성적서 모자이크 처리
├── scripts/
│   └── query_smoke.py      # 샘플 5개 질의 검증 스크립트
├── requirements.txt
├── .env.example
├── source_docs/            # (gitignore) 원본 PDF
├── rag_storage/            # (gitignore) LightRAG 인덱스 (약 330MB)
├── logs/                   # (gitignore) ingest/질의 로그
└── README.md
```

## 📈 운영 모니터링

GitHub public repo의 views / clones / popular paths / referrers를 CLI로 조회하여 이상 급증을 감지한다. LinkedIn 포스팅 직후 등 공개 구간에서 주기적으로 실행을 권장한다.

### 실행

PowerShell:
```powershell
powershell.exe -ExecutionPolicy Bypass -File scripts\monitor.ps1
```

Git Bash (jq 필요 — `winget install jqlang.jq` 로 설치):
```bash
bash scripts/monitor.sh
```

### 출력 예시
```
== WOCS RAG Bot GitHub 트래픽 모니터 ==
Repo      : cryptowoosung/wocs-ragbot
임계치    : 일 100회 이상 → HIGH  |  전일 대비 x5.0 이상 → SPIKE
----------------------------------------------------------------
-- views --
  총계 :      0    고유 :      0
  날짜            count  uniques   플래그
  2026-04-20          0        0
  2026-04-21          0        0

-- 인기 경로 (paths) --
  (데이터 없음 — 아직 방문이 적습니다)
----------------------------------------------------------------
완료 : 2026-04-21 20:00  |  히스토리 엔트리 1개 -> logs/monitor_history.json
```

실행 결과는 `logs/monitor_history.json` 에 누적 저장되며(gitignore 대상), 다음 실행 시 전일·전회 대비 변화를 바탕으로 HIGH / SPIKE 플래그를 색으로 표시한다.

## ⚠️ 주의사항 (필독)

- **외부 유출 금지**: `source_docs/` 안에는 FITI 시험성적서·영업 수치 등 영업 기밀이 포함된다. `.gitignore`로 차단되어 있으나 별도 매체로 반출 금지.
- **특허 문서 제외**: 이 프로젝트의 인덱싱 대상에는 출원 중인 특허 문서가 포함되지 않는다. `.gitignore` 끝에 `*특허*`, `*patent*`, `*출원*`, `*10-2026-*` 방어 패턴이 있어 이름만으로도 실수 커밋이 차단된다.
- **수치 허위 생성 방지**: 바이어 응대 탭의 프롬프트는 "지식베이스에 없는 수치는 `I will confirm this with our engineering team`으로 회피하라"는 규칙을 강제한다. 그럼에도 반드시 최종 송부 전 엔지니어링 팀 크로스체크 권장.
- **VLM 호출 비활성화**: 모든 쿼리는 `vlm_enhanced=False`. 이미지 첨부형 쿼리는 OpenAI gpt-4o TPM 30K 한도에 걸려 실패한다. 이미지 기반 비교가 필요할 경우 향후 별도 Tier 업그레이드 후 활성화 검토.

## 📜 라이선스

MIT (참고: 원본 자료 제외 — 코드만 대상)

## ✍️ 작성자

우성 (cryptowoosung)
