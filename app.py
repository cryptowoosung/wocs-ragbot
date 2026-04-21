"""WOCS 내부 지식봇 + 바이어 응대 도구 (Streamlit UI).

실행: `streamlit run app.py` (venv 활성화된 상태에서, 또는 venv/Scripts/python 으로)
- 탭1: 자유 질의 (RAG hybrid/local/global/naive)
- 탭2: 바이어 문의 → 영문 응대 초안
- 탭3: 제품 스펙 비교 (최대 3개 × 선택 축)
"""
import os
import sys
import re
import time
import asyncio
from pathlib import Path

os.environ.setdefault("PYTHONIOENCODING", "utf-8")
os.environ.setdefault("PYTHONUTF8", "1")

# streamlit run 실행 시 cwd가 프로젝트 루트가 아닐 수 있어 sys.path 보강
sys.path.insert(0, str(Path(__file__).resolve().parent))

import streamlit as st

from utils.rag_client import get_rag
from utils.prompts import build_buyer_reply_prompt


# ---------------- 페이지 설정 ----------------

st.set_page_config(
    page_title="WOCS 지식봇",
    page_icon="🏕️",
    layout="wide",
)


# ---------------- RAG 초기화 (프로세스당 1회) ----------------

@st.cache_resource(show_spinner=False)
def _get_event_loop():
    """Streamlit rerun 간 공유할 asyncio 이벤트 루프."""
    return asyncio.new_event_loop()


@st.cache_resource(show_spinner="RAG 초기화 중... (최초 1회만 수 초 소요)")
def _init_rag(_loop):
    """RAGAnything 싱글턴 + LightRAG 스토리지 로드. `_loop` 언더스코어 prefix 는
    st.cache_resource 가 해시 대상에서 제외하도록 하는 관례."""
    rag = get_rag()
    _loop.run_until_complete(rag._ensure_lightrag_initialized())
    return rag


loop = _get_event_loop()
rag = _init_rag(loop)


def run_sync(coro):
    """Streamlit main thread에서 async 메서드 동기 실행."""
    return loop.run_until_complete(coro)


# ---------------- 상수 ----------------

PRODUCT_MODELS = [
    "D-Dome", "D-Pro", "D600", "D800", "EX",
    "Lodge", "LodgeLX", "S-Classic",
    "SigA", "SigH", "SigM", "SigO", "SigP", "SigQ", "SigT", "Suite",
]

COMPARE_AXES = ["크기", "무게", "추천 용도", "가격대", "주요 특징"]

QUERY_MODES = ["hybrid", "local", "global", "naive"]


# ---------------- 유틸 ----------------

def query_rag(question: str, mode: str = "hybrid") -> tuple[str, float]:
    """RAG hybrid 질의. vlm_enhanced=False 강제 (gpt-4o TPM 30K 초과 방지)."""
    start = time.time()
    answer = run_sync(rag.aquery(question, mode=mode, vlm_enhanced=False))
    elapsed = time.time() - start
    return answer, elapsed


def extract_references(answer: str) -> list[str]:
    """답변 markdown의 'References' 섹션에서 파일명 추출.
    RAG-Anything 기본 포맷: `- [1] filename.pdf` 또는 `* [1] filename.pdf`."""
    if "References" not in answer:
        return []
    tail = answer.split("References", 1)[1]
    # [숫자] 뒤에 오는 파일명 (.pdf / .PDF / .md)
    found = re.findall(r"\[\d+\]\s*([^\n]+?\.(?:pdf|PDF|md))", tail)
    # dedup 유지 순서
    seen, result = set(), []
    for f in found:
        f = f.strip()
        if f not in seen:
            seen.add(f)
            result.append(f)
    return result


def split_answer_and_refs(answer: str) -> tuple[str, list[str]]:
    """답변 본문과 References 섹션 분리."""
    refs = extract_references(answer)
    body = re.split(r"###?\s*References", answer, maxsplit=1)[0].rstrip()
    return body, refs


# ---------------- 사이드바 ----------------

st.sidebar.title("📚 WOCS 지식봇")

with st.sidebar.expander("📁 현재 인덱싱된 자료 (27개)", expanded=False):
    st.markdown(
        """
- 📘 **통합 카탈로그** (1)
  - `catalog_v10_8.pdf`
- 📗 **통합 브로셔** (1)
  - `wocs_brochure_v3.pdf`
- 📙 **제품별 브로셔** (16)
  - D-Dome / D-Pro / D600 / D800 / EX
  - Lodge / LodgeLX / S-Classic
  - SigA / SigH / SigM / SigO / SigP / SigQ / SigT / Suite
  - _(모두 한국어 Print 버전)_
- 🧪 **FITI 시험성적서** (9)
  - STP5052 내수도 · FR 방염성 · 기본물성
  - STP1054XCL FR 방염 · 아이보리(졸)
  - STP1054X 오렌지(졸)
  - STP1060PVDF 인장·인열·접착
  - STP1055 PCF FR 중금속·프탈레이트
  - pvc글램핑원단 종합
"""
    )

st.sidebar.markdown("---")
st.sidebar.warning("⚠️ 내부 참조용. 외부 공개 금지 자료 포함")


# ---------------- 메인 헤더 ----------------

st.title("🏕️ WOCS 내부 지식봇 + 바이어 응대 도구")
st.caption("우성어닝천막공사캠프시스템 · 카탈로그 / FITI 성적서 / 제품 브로셔 통합 검색")


# ---------------- 탭 ----------------

tab1, tab2, tab3 = st.tabs([
    "💬 자유 질의",
    "✉️ 바이어 응대 (영문)",
    "📊 제품 비교",
])


# ============ 탭 1: 자유 질의 ============
with tab1:
    st.subheader("자유롭게 질문하세요")

    # 예시 질문 — 버튼 클릭 시 session_state에 저장되어 아래 text_area가 다음 렌더에서 채움
    example_qs = [
        "S-Classic 모델의 구조강재 스펙과 풍하중 기준",
        "STP5052 원단의 내수도 수치와 시험기준",
        "가장 큰 글램핑 텐트 모델과 그 면적",
    ]
    ex_cols = st.columns(3)
    for i, eq in enumerate(example_qs):
        if ex_cols[i].button(f"예시 {i+1}", help=eq, use_container_width=True, key=f"ex_{i}"):
            st.session_state["q_text"] = eq

    q = st.text_area(
        "질문",
        height=100,
        placeholder="예: D-Pro 모델의 치수와 무게는?",
        key="q_text",
    )
    mode = st.selectbox(
        "검색 모드",
        QUERY_MODES,
        index=0,
        help="hybrid=로컬+글로벌 혼합(기본 권장) · local=엔티티 근처 · global=관계 요약 · naive=단순 청크 검색",
    )
    ask = st.button("질문하기", type="primary", disabled=not (q or "").strip())

    if ask:
        with st.spinner(f"RAG 질의 중 (mode={mode})..."):
            ans, elapsed = query_rag(q, mode=mode)
        body, refs = split_answer_and_refs(ans)

        meta_cols = st.columns(3)
        meta_cols[0].metric("응답 시간", f"{elapsed:.1f}s")
        meta_cols[1].metric("사용 모드", mode)
        meta_cols[2].metric("참조 문서", len(refs))

        st.markdown(body)

        if refs:
            with st.expander("📎 근거 문서 보기", expanded=False):
                for r in refs:
                    st.markdown(f"- `{r}`")


# ============ 탭 2: 바이어 응대 ============
with tab2:
    st.subheader("✉️ 바이어 문의 → 영문 응대 초안")
    st.caption(
        "지식베이스 기반. 수치는 인덱싱된 자료에 있을 때만 사용하고 "
        "없으면 자동으로 *'confirm with engineering team'* 으로 회피합니다."
    )

    left, right = st.columns([1, 1])

    with left:
        buyer_email = st.text_area(
            "바이어 원문 메일",
            height=250,
            placeholder=(
                "Hi, I'm interested in your D-Pro model for our resort "
                "project in Thailand. Could you send specs and pricing for 20 units?"
            ),
            key="buyer_email",
        )
        style = st.radio(
            "응대 스타일",
            ["Formal", "Friendly", "Concise"],
            horizontal=True,
        )
        extra_notes = st.text_input(
            "추가 요청사항 (선택)",
            placeholder="예: 포트폴리오 링크 언급, 납기 60일 이내 가능",
        )
        generate = st.button(
            "영문 초안 생성",
            type="primary",
            disabled=not (buyer_email or "").strip(),
            use_container_width=True,
        )

    with right:
        if generate:
            prompt = build_buyer_reply_prompt(buyer_email, style, extra_notes)
            with st.spinner("영문 초안 생성 중... (약 10초)"):
                ans, elapsed = query_rag(prompt, mode="hybrid")
            body, refs = split_answer_and_refs(ans)

            st.markdown("**📝 생성된 영문 초안**")
            # st.code(language=None): 우측 상단에 복사 아이콘 자동 표시
            st.code(body, language=None)

            meta_cols = st.columns(2)
            meta_cols[0].metric("응답 시간", f"{elapsed:.1f}s")
            meta_cols[1].metric("스타일", style)

            if refs:
                with st.expander("📎 근거 제품/스펙 출처"):
                    for r in refs:
                        st.markdown(f"- `{r}`")

            st.info("💡 위 코드 블록 우측 상단의 복사 아이콘으로 클립보드에 복사할 수 있습니다.")
        else:
            st.markdown(
                "_좌측에 바이어 메일을 붙여넣고 **영문 초안 생성** 버튼을 눌러주세요._"
            )


# ============ 탭 3: 제품 비교 ============
with tab3:
    st.subheader("📊 제품 스펙 비교")
    st.caption("최대 3개 제품 × 원하는 비교 축. 카탈로그/브로셔 수치 기반.")

    sel_products = st.multiselect(
        "제품 선택 (최대 3개)",
        PRODUCT_MODELS,
        default=["D-Dome", "D-Pro", "D800"],
        max_selections=3,
    )
    sel_axes = st.multiselect(
        "비교 축",
        COMPARE_AXES,
        default=COMPARE_AXES,
    )
    compare_btn = st.button(
        "비교하기",
        type="primary",
        disabled=not (sel_products and sel_axes),
        use_container_width=True,
    )

    if compare_btn:
        q = (
            f"{', '.join(sel_products)} 모델의 {', '.join(sel_axes)}을(를) "
            "한국어 markdown 표(table) 형식으로 정리해줘. "
            "행=제품, 열=비교 축. 카탈로그와 브로셔의 수치를 우선 사용하고, "
            "수치가 없는 항목은 '자료 없음'이라고 명시해줘."
        )
        with st.spinner("비교 표 생성 중..."):
            ans, elapsed = query_rag(q, mode="hybrid")
        body, refs = split_answer_and_refs(ans)

        st.markdown(body)
        st.caption(
            f"응답 {elapsed:.1f}s · 제품 {len(sel_products)}개 × 축 {len(sel_axes)}개"
        )

        if refs:
            with st.expander("📎 근거 문서"):
                for r in refs:
                    st.markdown(f"- `{r}`")
