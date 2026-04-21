"""Step 3 샘플 질의 5개 — RAG 동작 검증."""
import asyncio
import json
import os
import sys
import time
from pathlib import Path

os.environ.setdefault("PYTHONIOENCODING", "utf-8")
os.environ.setdefault("PYTHONUTF8", "1")

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from utils.rag_client import get_rag  # noqa

QUERIES = [
    "WOCS의 방염 인증 등급은 무엇이고 어느 시험기관에서 받았나?",
    "STP5052 원단의 내수도 시험 결과 수치를 알려줘.",
    "우리 제품 중 가장 큰 글램핑 텐트 모델과 치수는?",
    "철골 프레임은 어떤 강재를 사용하는가?",
    "영문으로 제품 소개를 하려고 한다. D-Pro 모델의 핵심 특징 3가지를 영어로 정리해줘.",
]

OUT_MD = Path("logs/query_results.md")
OUT_JSON = Path("logs/query_results.json")


async def main():
    rag = get_rag()
    # 새 프로세스에서 rag_storage 로드 - aquery는 내부 호출 안 함
    await rag._ensure_lightrag_initialized()
    results = []
    print(f"Running {len(QUERIES)} queries in hybrid mode...")
    for i, q in enumerate(QUERIES, 1):
        print(f"\n=== Q{i} ===\n{q}")
        t0 = time.time()
        try:
            # vlm_enhanced=False: 이미지를 base64로 gpt-4o에 보내는 경로 비활성화
            # (gpt-4o TPM 30K 제한으로 rate-limit 걸림)
            ans = await rag.aquery(q, mode="hybrid", vlm_enhanced=False)
            status = "ok"
            err = None
        except Exception as e:
            ans = ""
            status = "error"
            err = f"{type(e).__name__}: {str(e)[:300]}"
        elapsed = round(time.time() - t0, 2)
        print(f"--- Answer ({elapsed}s, {status}) ---")
        print(ans if ans else f"[ERROR] {err}")
        results.append({
            "id": i,
            "question": q,
            "answer": ans,
            "elapsed_sec": elapsed,
            "status": status,
            "error": err,
        })

    OUT_MD.parent.mkdir(exist_ok=True)
    with open(OUT_MD, "w", encoding="utf-8") as f:
        f.write("# WOCS RAG 샘플 질의 결과 (Step 3)\n\n")
        for r in results:
            f.write(f"## Q{r['id']} — {r['elapsed_sec']}s ({r['status']})\n\n")
            f.write(f"**질문**: {r['question']}\n\n")
            f.write(f"**답변**:\n\n{r['answer'] or '_(no answer)_'}\n\n")
            if r['error']:
                f.write(f"**에러**: `{r['error']}`\n\n")
            f.write("---\n\n")
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\nSaved → {OUT_MD}")
    print(f"Saved → {OUT_JSON}")


if __name__ == "__main__":
    asyncio.run(main())
