"""바이어 응대 프롬프트 템플릿.

Step 4 탭2(바이어 응대)에서 사용. RAG `aquery`에 전달될 최종 프롬프트를 조립한다.
"""

# 스타일별 세부 지침 — 모델에게 톤/분량/포맷을 명시
STYLE_DETAILS = {
    "Formal": "Professional, polite, use 'we'. Include company introduction in 1 sentence.",
    "Friendly": "Warm but professional, use 'we'. Start with acknowledgment of their interest.",
    "Concise": "Direct, bullet-point style, no filler. Max 120 words.",
}


BUYER_REPLY_PROMPT = """You are a B2B sales assistant for WOCS (우성어닝천막공사캠프시스템), a Korean glamping tent and steel-frame structure manufacturer.
Task: Draft a {style} English reply to the following buyer inquiry, using ONLY factual information retrievable from the WOCS product catalog, brochures, and FITI fire-resistance test certifications indexed in the knowledge base.

Rules:
- If a specific number (size, weight, fire rating, tensile strength) is requested and not in the knowledge base, say "I will confirm this with our engineering team" — DO NOT fabricate numbers.
- Mention patented welding-free joint system where relevant.
- Keep reply under 250 words.
- End with a call-to-action (request for technical drawing / quantity / delivery timeline).
- Style: {style_detail}

Buyer inquiry:
{buyer_email}

Additional requirements from the sales rep:
{extra_notes}

Output ONLY the reply body (no subject line, no "Dear..." preamble if style is Concise)."""


def build_buyer_reply_prompt(buyer_email: str, style: str, extra_notes: str = "") -> str:
    """바이어 메일 + 스타일 + 추가 메모 → RAG에 보낼 최종 프롬프트."""
    style_detail = STYLE_DETAILS.get(style, STYLE_DETAILS["Formal"])
    return BUYER_REPLY_PROMPT.format(
        style=style,
        style_detail=style_detail,
        buyer_email=buyer_email.strip(),
        extra_notes=(extra_notes.strip() or "(none)"),
    )
