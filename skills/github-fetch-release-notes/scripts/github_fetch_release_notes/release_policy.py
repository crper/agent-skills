import re
from typing import Any, Dict, List, Optional, Tuple

from .changelog import extract_version_label
from .models import ChangelogCandidate


PRERELEASE_TOKEN_SPLIT_RE = re.compile(r"[._-]+")


def normalize_version_for_match(value: Optional[str]) -> Optional[str]:
    if not value:
        return None

    normalized = (extract_version_label(value) or value).strip().lower()
    if normalized.startswith('v') and len(normalized) > 1 and normalized[1].isdigit():
        normalized = normalized[1:]
    return normalized or None


def parse_comparable_version(value: Optional[str]) -> Optional[Tuple[Tuple[int, ...], Tuple[Tuple[int, Any], ...]]]:
    normalized = normalize_version_for_match(value)
    if not normalized:
        return None

    version_text = normalized.split('+', 1)[0]
    core_text, separator, prerelease_text = version_text.partition('-')
    core_parts = core_text.split('.')
    if len(core_parts) < 2 or any(not part.isdigit() for part in core_parts):
        return None

    core = tuple(int(part) for part in core_parts)
    prerelease: List[Tuple[int, Any]] = []
    if separator:
        for part in PRERELEASE_TOKEN_SPLIT_RE.split(prerelease_text):
            if not part:
                continue
            if part.isdigit():
                prerelease.append((0, int(part)))
            else:
                prerelease.append((1, part.lower()))

    return core, tuple(prerelease)


def compare_versions(left: Optional[str], right: Optional[str]) -> Optional[int]:
    left_parsed = parse_comparable_version(left)
    right_parsed = parse_comparable_version(right)
    if not left_parsed or not right_parsed:
        return None

    left_core, left_prerelease = left_parsed
    right_core, right_prerelease = right_parsed
    max_core_len = max(len(left_core), len(right_core))
    padded_left = left_core + (0,) * (max_core_len - len(left_core))
    padded_right = right_core + (0,) * (max_core_len - len(right_core))

    if padded_left < padded_right:
        return -1
    if padded_left > padded_right:
        return 1

    if not left_prerelease and not right_prerelease:
        return 0
    if left_prerelease and not right_prerelease:
        return -1
    if not left_prerelease and right_prerelease:
        return 1

    for left_token, right_token in zip(left_prerelease, right_prerelease):
        if left_token == right_token:
            continue
        if left_token[0] != right_token[0]:
            return -1 if left_token[0] < right_token[0] else 1
        if left_token[1] < right_token[1]:
            return -1
        if left_token[1] > right_token[1]:
            return 1

    if len(left_prerelease) < len(right_prerelease):
        return -1
    if len(left_prerelease) > len(right_prerelease):
        return 1
    return 0


def latest_release_version(release: Optional[Dict[str, Any]]) -> Optional[str]:
    if not release:
        return None
    return release.get('tag_name') or release.get('name')


def is_prerelease(release: Optional[Dict[str, Any]]) -> bool:
    return bool(release and release.get('prerelease'))


def pick_release_for_staleness(releases: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    comparable_stable = [
        release
        for release in releases
        if not is_prerelease(release) and parse_comparable_version(latest_release_version(release)) is not None
    ]
    if comparable_stable:
        return comparable_stable[0]

    comparable_any = [
        release
        for release in releases
        if parse_comparable_version(latest_release_version(release)) is not None
    ]
    if comparable_any:
        return comparable_any[0]

    return None


def find_release_confirmation(releases: List[Dict[str, Any]], version: Optional[str]) -> Optional[Dict[str, Any]]:
    target = normalize_version_for_match(version)
    if not target:
        return None

    for release in releases:
        candidates = [release.get('tag_name'), release.get('name')]
        if any(normalize_version_for_match(candidate) == target for candidate in candidates):
            return release
    return None


def should_prefer_releases(changelog_candidate: ChangelogCandidate, releases: List[Dict[str, Any]]) -> bool:
    if not releases:
        return False

    latest_version = changelog_candidate.latest_version
    if not latest_version:
        return True

    release_for_staleness = pick_release_for_staleness(releases)
    if not release_for_staleness:
        return False

    comparison = compare_versions(latest_version, latest_release_version(release_for_staleness))
    return comparison is not None and comparison < 0


def build_release_notes_from_changelog_context(changelog_candidate: ChangelogCandidate) -> List[str]:
    notes: List[str] = []
    if changelog_candidate.latest_version:
        notes.append('CHANGELOG 最新正式版本落后于 GitHub Releases，已回退到 Releases')
    else:
        notes.append('已读取 changelog，但未稳定识别出最新版本标题，已回退到 Releases')

    if changelog_candidate.unreleased_has_content:
        notes.append('发现 Unreleased 分段')
        notes.append('CHANGELOG 中存在 Unreleased 内容，未并入本次正式版本摘要')
    return notes


def select_releases_for_summary(releases: List[Dict[str, Any]], limit: int) -> List[Dict[str, Any]]:
    if limit < 1 or not releases:
        return []

    stable_releases = [release for release in releases if not is_prerelease(release)]
    if not stable_releases:
        return releases[:limit]

    prioritized = stable_releases + [release for release in releases if is_prerelease(release)]
    return prioritized[:limit]


def build_release_selection_notes(releases: List[Dict[str, Any]], selected_releases: List[Dict[str, Any]]) -> List[str]:
    if not releases or not selected_releases:
        return []

    raw_versions = [latest_release_version(release) for release in releases[: len(selected_releases)]]
    selected_versions = [latest_release_version(release) for release in selected_releases]
    recent_releases = releases[: len(selected_releases) + 2]
    if raw_versions != selected_versions and any(is_prerelease(release) for release in recent_releases):
        return ['检测到预发布 Release，默认优先正式版轨道']
    return []
