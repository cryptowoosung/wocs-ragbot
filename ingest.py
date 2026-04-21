"""source_docs/ 전체 PDF → RAG 인덱싱

- 한글 파일명 그대로 유지 (pathlib 재귀 스캔)
- .pdf + .PDF 모두 대상
- 실패해도 다음 파일 계속
- logs/ingest.log에 JSON 라인으로 기록 (재실행 시 중복 스킵)
"""
import asyncio
import json
import os
import sys
from pathlib import Path
from datetime import datetime

os.environ.setdefault("PYTHONIOENCODING", "utf-8")
os.environ.setdefault("PYTHONUTF8", "1")

from tqdm import tqdm
from utils.rag_client import get_rag

SOURCE_DIR = Path("source_docs")
LOG_FILE = Path("logs/ingest.log")


def find_pdfs():
    """한글 파일명 포함 모든 PDF (대소문자 확장자 모두)."""
    files = set()
    for pattern in ("**/*.pdf", "**/*.PDF"):
        files.update(SOURCE_DIR.glob(pattern))
    return sorted(files)


def load_already_indexed():
    """logs/ingest.log에서 status=success인 파일 경로."""
    done = set()
    if not LOG_FILE.exists():
        return done
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        for line in f:
            try:
                entry = json.loads(line.strip())
                if entry.get("status") == "success":
                    done.add(entry.get("path"))
            except json.JSONDecodeError:
                continue
    return done


async def run():
    pdfs = find_pdfs()
    print(f"[scan] 총 {len(pdfs)}개 PDF 발견")
    already = load_already_indexed()
    print(f"[scan] 이미 인덱싱: {len(already)}개")
    to_process = [p for p in pdfs if str(p) not in already]
    print(f"[scan] 처리 예정: {len(to_process)}개")

    if not to_process:
        print("[done] 처리할 파일 없음.")
        return

    print("[init] RAGAnything 싱글턴 초기화...")
    rag = get_rag()
    print(f"[init] working_dir = {rag.config.working_dir}")

    LOG_FILE.parent.mkdir(exist_ok=True)
    success, error = 0, 0

    with open(LOG_FILE, "a", encoding="utf-8") as f:
        for pdf in tqdm(to_process, desc="Indexing", ncols=100):
            start = datetime.now()
            try:
                await rag.process_document_complete(
                    file_path=str(pdf),
                    parse_method="auto",
                    backend="pipeline",   # CPU 환경 — VLM/hybrid 대신 경량 파이프라인
                    lang="korean",        # 한글 OCR 힌트 (영문/숫자 혼재 문서에도 안전)
                )
                status, err = "success", None
                success += 1
            except Exception as e:
                status = "error"
                err = f"{type(e).__name__}: {str(e)[:500]}"
                error += 1
                print(f"\n[error] {pdf.name}: {err[:200]}", file=sys.stderr)

            elapsed = (datetime.now() - start).total_seconds()
            entry = {
                "timestamp": datetime.now().isoformat(),
                "file": pdf.name,
                "path": str(pdf),
                "status": status,
                "error": err,
                "elapsed_sec": round(elapsed, 2),
            }
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
            f.flush()

    print(f"\n[summary] success={success}, error={error}, total={len(to_process)}")


def main():
    asyncio.run(run())


if __name__ == "__main__":
    main()
