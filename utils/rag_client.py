"""RAG-Anything 싱글턴 초기화

OpenAI gpt-4o-mini (LLM) + gpt-4o (Vision) + text-embedding-3-large (3072d)
+ MinerU PDF 파서. 한글 파일명/콘텐츠 UTF-8 안전 처리.
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# UTF-8 강제 (한글 파일명 안전 처리)
os.environ.setdefault("PYTHONIOENCODING", "utf-8")
os.environ.setdefault("PYTHONUTF8", "1")

# venv 활성화 없이도 mineru.exe 등 venv 스크립트를 찾을 수 있도록 PATH 보강
_venv_scripts = Path(sys.executable).parent
_current_path = os.environ.get("PATH", "")
if str(_venv_scripts) not in _current_path:
    os.environ["PATH"] = str(_venv_scripts) + os.pathsep + _current_path

from raganything import RAGAnything, RAGAnythingConfig
from lightrag.llm.openai import openai_complete_if_cache, openai_embed
from lightrag.utils import EmbeddingFunc

_API_KEY = os.getenv("OPENAI_API_KEY")
_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
_LLM_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
_VISION_MODEL = os.getenv("OPENAI_VISION_MODEL", "gpt-4o")
_EMBED_MODEL = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-large")

WORKING_DIR = str(Path("rag_storage").resolve())

_rag_instance = None


def _llm_model_func(prompt, system_prompt=None, history_messages=None, **kwargs):
    return openai_complete_if_cache(
        _LLM_MODEL,
        prompt,
        system_prompt=system_prompt,
        history_messages=history_messages or [],
        api_key=_API_KEY,
        base_url=_BASE_URL,
        **kwargs,
    )


def _vision_model_func(prompt, system_prompt=None, history_messages=None,
                       image_data=None, messages=None, **kwargs):
    if messages:
        return openai_complete_if_cache(
            _VISION_MODEL, "", messages=messages,
            api_key=_API_KEY, base_url=_BASE_URL, **kwargs,
        )
    if image_data:
        return openai_complete_if_cache(
            _VISION_MODEL, "",
            messages=[
                {"role": "user", "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url",
                     "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}},
                ]},
            ],
            api_key=_API_KEY, base_url=_BASE_URL, **kwargs,
        )
    return _llm_model_func(prompt, system_prompt, history_messages or [], **kwargs)


def _embed_call(texts):
    fn = getattr(openai_embed, "func", openai_embed)
    return fn(texts, model=_EMBED_MODEL, api_key=_API_KEY, base_url=_BASE_URL)


_embedding_func = EmbeddingFunc(
    embedding_dim=3072,
    max_token_size=8192,
    func=_embed_call,
)


def get_rag() -> RAGAnything:
    """프로세스당 1회 초기화되는 RAGAnything 싱글턴."""
    global _rag_instance
    if _rag_instance is None:
        if not _API_KEY:
            raise RuntimeError("OPENAI_API_KEY not set. .env 파일 확인.")
        config = RAGAnythingConfig(
            working_dir=WORKING_DIR,
            parser="mineru",
            parse_method="auto",
            enable_image_processing=True,
            enable_table_processing=True,
            enable_equation_processing=True,
        )
        _rag_instance = RAGAnything(
            config=config,
            llm_model_func=_llm_model_func,
            vision_model_func=_vision_model_func,
            embedding_func=_embedding_func,
        )
    return _rag_instance
