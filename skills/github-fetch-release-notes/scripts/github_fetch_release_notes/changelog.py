import re
from typing import Any, Dict, List, Optional


HEADER_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
VERSION_RE = re.compile(r"v?\d+(?:\.\d+){1,3}(?:[-+][A-Za-z0-9._-]+)?")
MARKDOWN_LINK_RE = re.compile(r"\[([^\]]+)\]\([^)]+\)")
CODE_SPAN_RE = re.compile(r"`([^`]+)`")
BOLD_RE = re.compile(r"\*\*([^*]+)\*\*")
EM_RE = re.compile(r"\*([^*]+)\*")
GENERIC_RELEASE_TITLE_RE = re.compile(r"^(release|version)\s+v?\d", re.IGNORECASE)
STATS_LINE_RE = re.compile(r"^stats\*?:", re.IGNORECASE)
GENERIC_HEADING_VALUES = {
    "what's changed",
    "whats changed",
    "changelog",
    "new features",
    "bug fixes",
    "documentation",
    "chores",
}


def parse_changelog(text: str) -> Dict[str, Any]:
    unreleased = None
    version_sections = []
    current = None

    for line in text.splitlines():
        match = HEADER_RE.match(line)
        if match:
            title = match.group(2).strip()
            low_title = title.lower()
            if "unreleased" in low_title or "unrelease" in low_title:
                current = {"title": title, "lines": []}
                unreleased = current
                continue
            if VERSION_RE.search(title):
                current = {"title": title, "lines": []}
                version_sections.append(current)
                continue
        if current is not None:
            current["lines"].append(line)

    return {
        "unreleased": unreleased,
        "latest": version_sections[0] if version_sections else None,
        "previous": version_sections[1] if len(version_sections) > 1 else None,
    }


def extract_version_label(title: Optional[str]) -> Optional[str]:
    if not title:
        return None
    match = VERSION_RE.search(title)
    if match:
        return match.group(0)
    return title.strip() or None


def normalize_item_text(line: str) -> str:
    raw_text = line.strip()
    if not raw_text or raw_text.startswith("#"):
        return ""

    text = re.sub(r"\s+", " ", raw_text).strip()
    text = re.sub(r"^[-*+]\s*\[[ xX]\]\s*", "", text)
    text = re.sub(r"^[-*+]\s*", "", text)
    text = re.sub(r"^\d+[.)]\s*", "", text)
    text = MARKDOWN_LINK_RE.sub(r"\1", text)
    text = CODE_SPAN_RE.sub(r"\1", text)
    text = BOLD_RE.sub(r"\1", text)
    text = EM_RE.sub(r"\1", text)
    text = text.strip(" -*_#`\t")

    lower = text.lower()
    if not text:
        return ""
    if re.fullmatch(r"[-–—_=#.`\s]+", text):
        return ""
    if lower.startswith("full changelog:") or lower.startswith("full list of changes:") or lower.startswith("compare/"):
        return ""
    if STATS_LINE_RE.match(text):
        return ""
    if GENERIC_RELEASE_TITLE_RE.match(text):
        return ""
    if lower in GENERIC_HEADING_VALUES:
        return ""
    return text


def collect_items(lines: List[str], limit: Optional[int] = None) -> List[str]:
    items: List[str] = []
    seen = set()

    for line in lines:
        item = normalize_item_text(line)
        if not item:
            continue
        key = item.lower()
        if key in seen:
            continue
        seen.add(key)
        items.append(item)
        if limit is not None and len(items) >= limit:
            break

    return items


def summarize_lines(lines: List[str], limit: int = 3) -> List[str]:
    return collect_items(lines, limit)
