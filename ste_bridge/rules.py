"""Deterministic rules for checking controlled-language (ASD-STE100) compliance."""
import json
import pathlib
import re


_VAGUE_PT = {
    "eventualmente", "célere", "tempestivo", "tempestividade", "adequado",
    "oportunamente", "breve", "razoável", "diligenciar", "conformidade",
}

_VAGUE_EN = {
    "eventually", "timely", "adequate", "reasonable", "soon",
    "appropriate", "promptly", "as needed",
}

_PASSIVE_PT = re.compile(
    r"\b(foi|foram|é|são|será|serão|seja|sejam)\s+\w+(ado|ada|ados|adas|ido|ida|idos|idas)\b",
    re.IGNORECASE,
)

_PASSIVE_EN = re.compile(
    r"\b(is|are|was|were|be|been|being)\s+\w+ed\b",
    re.IGNORECASE,
)

_MULTI_ACTION = re.compile(r"( e | and |;|, procedendo)", re.IGNORECASE)


def _split_sentences(text: str) -> list[str]:
    """Split text into sentences on . ! ? and newlines. Strip leading list numbers like '1.' first."""
    lines = text.split("\n")
    sents: list[str] = []
    for line in lines:
        # Strip leading list number BEFORE splitting on punctuation
        line = re.sub(r"^\s*\d+[.)]\s*", "", line).strip()
        if not line:
            continue
        parts = re.split(r"[.!?]+", line)
        for p in parts:
            p = p.strip()
            if p:
                sents.append(p)
    return sents


def check(text: str, lang: str) -> list[dict]:
    """Return a list of violation dicts for *text* in the given language.

    Each dict has keys: ``rule``, ``sentence_index``, ``detail``.
    """
    sentences = _split_sentences(text)
    violations: list[dict] = []
    vague = _VAGUE_PT if lang == "pt" else _VAGUE_EN

    for idx, sent in enumerate(sentences):
        words = sent.split()

        # R1_LENGTH
        if len(words) > 20:
            violations.append({
                "rule": "R1_LENGTH",
                "sentence_index": idx,
                "detail": f"sentence has {len(words)} words (max 20)",
            })

        # R2_VAGUE — match on word boundaries so "breve" doesn't match "breve\n"
        # inside "breve\n" or "abreviado"
        sent_lower = sent.lower()
        for word in vague:
            if re.search(r"\b" + re.escape(word) + r"\b", sent_lower):
                violations.append({
                    "rule": "R2_VAGUE",
                    "sentence_index": idx,
                    "detail": f"vague word found: {word}",
                })

        # R3_PASSIVE
        if lang == "pt":
            passive_re = _PASSIVE_PT
        else:
            passive_re = _PASSIVE_EN
        m = passive_re.search(sent)
        if m:
            violations.append({
                "rule": "R3_PASSIVE",
                "sentence_index": idx,
                "detail": f"passive construction: {m.group()}",
            })

        # R4_MULTI_ACTION
        if _MULTI_ACTION.search(sent) and len(words) > 8:
            violations.append({
                "rule": "R4_MULTI_ACTION",
                "sentence_index": idx,
                "detail": "multiple actions joined in one sentence",
            })

    return violations
