"""Pure-Python text helpers shared by the backend, the formatters and the UI."""
import re
from typing import List, Tuple

_REPLACEMENTS = {
    "\u2018": "'", "\u2019": "'", "\u201a": "'", "\u201b": "'",
    "\u201c": '"', "\u201d": '"', "\u201e": '"',
    "\u2013": "-", "\u2014": " - ", "\u2212": "-",
    "\u2026": "...", "\u00a0": " ", "\u2022": "-", "\u25cf": "-",
    "\u200b": "", "\u200c": "", "\u200d": "", "\ufeff": "",
}


def sanitize_text(text: str) -> str:
    """Remove typographic quotes, zero-width characters and markdown emphasis."""
    if not text:
        return ""
    for src, dst in _REPLACEMENTS.items():
        text = text.replace(src, dst)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"```[a-zA-Z]*", "", text)      # code fences
    text = text.replace("**", "").replace("`", "")
    text = re.sub(r"(?<=\S) {2,}(?=\S)", " ", text)  # doubled spaces (e.g. after dash swap)
    text = re.sub(r"[ \t]+\n", "\n", text)        # trailing spaces
    text = re.sub(r"\n{3,}", "\n\n", text)        # collapse blank lines
    return text.strip()


def split_terms(terms: str) -> List[str]:
    """Split semicolon- or newline-separated terms into a clean list."""
    if not terms:
        return []
    parts = re.split(r"[;\n]+", terms)
    return [re.sub(r"^\s*[-*\u2022]\s*", "", p).strip() for p in parts if p.strip()]


# Block kinds returned by parse_blocks
TITLE, HEADING, PARA, SUB, BULLET = "title", "heading", "para", "sub", "bullet"

_NUM_HEADING = re.compile(r"^(\d+(\.\d+)*\.?|[IVX]+\.)\s+\S")
_SUBCLAUSE = re.compile(r"^\(?[a-z]{1,2}\)\s+\S|^\(?[ivx]+\)\s+\S")


def _looks_like_heading(line: str) -> bool:
    if len(line) > 80:
        return False
    if _NUM_HEADING.match(line) and not line.rstrip().endswith("."):
        return True
    letters = [c for c in line if c.isalpha()]
    if letters and len(line) <= 60 and all(c.isupper() for c in letters):
        return True                                   # e.g. WITNESSETH:
    return bool(re.match(r"^(ARTICLE|SECTION|SCHEDULE|ANNEXURE)\b", line, re.I))


def parse_blocks(text: str) -> List[Tuple[str, str]]:
    """Turn the model's lightly-marked text into [(kind, content), ...]."""
    blocks: List[Tuple[str, str]] = []
    for raw in sanitize_text(text).split("\n"):
        line = raw.strip()
        if not line:
            continue
        if line.startswith("### ") or line.startswith("## "):
            blocks.append((HEADING, line.lstrip("#").strip()))
        elif line.startswith("# "):
            blocks.append((TITLE, line[2:].strip()))
        elif re.match(r"^[-*]\s+\S", line):
            blocks.append((BULLET, line[1:].strip()))
        elif _SUBCLAUSE.match(line):
            blocks.append((SUB, line))
        elif _looks_like_heading(line):
            blocks.append((HEADING, line))
        else:
            blocks.append((PARA, line))
    return blocks


def slugify(value: str, default: str = "legal_document") -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", value or "").strip("_").lower()
    return slug or default
