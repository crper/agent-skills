import argparse
import json
import re
from typing import Any, Dict, List, Optional, Tuple

from .changelog import collect_items, extract_version_label, parse_changelog, summarize_lines
from .gh_client import (
    DEFAULT_CHANGELOG_PATHS,
    DEFAULT_TIMEOUT,
    GitHubApiError,
    fetch_contents,
    fetch_repo_metadata,
    get_latest_releases,
    github_blob_url,
    github_repo_url,
    normalize_repo_input,
)
from .output import (
    ERROR_INVALID_REPO,
    build_payload,
    error_code_from_runtime,
    make_result,
    notes_and_code_from_api_error,
)


DEFAULT_DETAIL_LIMIT = 8
MAX_REPOS = 10
CHANGELOG_RELEASE_CONFIRMATION_LIMIT = 5
PRERELEASE_TOKEN_SPLIT_RE = re.compile(r"[._-]+")


def normalize_version_for_match(value: Optional[str]) -> Optional[str]:
    if not value:
        return None

    normalized = (extract_version_label(value) or value).strip().lower()
    if normalized.startswith("v") and len(normalized) > 1 and normalized[1].isdigit():
        normalized = normalized[1:]
    return normalized or None


def parse_comparable_version(value: Optional[str]) -> Optional[Tuple[Tuple[int, ...], Tuple[Tuple[int, Any], ...]]]:
    normalized = normalize_version_for_match(value)
    if not normalized:
        return None

    version_text = normalized.split("+", 1)[0]
    core_text, separator, prerelease_text = version_text.partition("-")
    core_parts = core_text.split(".")
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
    return release.get("tag_name") or release.get("name")


def is_prerelease(release: Optional[Dict[str, Any]]) -> bool:
    return bool(release and release.get("prerelease"))


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
        candidates = [release.get("tag_name"), release.get("name")]
        if any(normalize_version_for_match(candidate) == target for candidate in candidates):
            return release
    return None


def build_changelog_candidate(
    repo: str,
    default_branch: str,
    detail_limit: int,
    timeout: int,
    releases: List[Dict[str, Any]],
    input_repo: str,
) -> Optional[Dict[str, Any]]:
    for path in DEFAULT_CHANGELOG_PATHS:
        text = fetch_contents(repo, path, timeout)
        if not text:
            continue

        parsed = parse_changelog(text)
        latest = parsed.get("latest") or {}
        previous = parsed.get("previous") or {}
        unreleased = parsed.get("unreleased") or {}

        latest_version = extract_version_label(latest.get("title"))
        previous_version = extract_version_label(previous.get("title"))
        latest_lines = latest.get("lines", [])
        previous_lines = previous.get("lines", [])
        unreleased_lines = unreleased.get("lines", [])

        latest_details = collect_items(latest_lines, detail_limit)
        previous_details = collect_items(previous_lines, detail_limit)
        unreleased_has_content = bool(collect_items(unreleased_lines, 1))
        highlights = summarize_lines(latest_lines or unreleased_lines, 3)

        if not latest_version and not latest_details and not highlights:
            continue

        notes: List[str] = []
        published_at = None
        if unreleased_has_content:
            notes.append("发现 Unreleased 分段")
        if not latest_version:
            notes.append("已读取 changelog，但未稳定识别出最新版本标题")
        else:
            matched_release = find_release_confirmation(releases, latest_version)
            if matched_release:
                published_at = matched_release.get("published_at")
                notes.append("已用 GitHub Release 确认该版本发布时间")
            elif releases:
                notes.append("CHANGELOG 最新版本尚未在最近的 GitHub Releases 中确认，可能是预写或待发布")
            else:
                notes.append("仓库没有可用于确认发布时间的 GitHub Releases")

        return {
            "input_repo": input_repo,
            "repo": repo,
            "latest_version": latest_version,
            "previous_version": previous_version,
            "unreleased_present": bool(unreleased_lines),
            "unreleased_has_content": unreleased_has_content,
            "published_at": published_at,
            "highlights": highlights,
            "raw_url": github_blob_url(repo, default_branch, path),
            "notes": notes,
            "latest_details": latest_details,
            "previous_details": previous_details,
        }

    return None


def build_changelog_result(candidate: Dict[str, Any]) -> Dict[str, Any]:
    return make_result(
        input_repo=candidate["input_repo"],
        repo=candidate["repo"],
        source="changelog",
        latest_version=candidate.get("latest_version"),
        previous_version=candidate.get("previous_version"),
        unreleased_present=bool(candidate.get("unreleased_present")),
        published_at=candidate.get("published_at"),
        highlights=candidate.get("highlights"),
        raw_url=candidate.get("raw_url"),
        notes=candidate.get("notes"),
        latest_details=candidate.get("latest_details"),
        previous_details=candidate.get("previous_details"),
    )


def build_release_result(
    input_repo: str,
    repo: str,
    releases: List[Dict[str, Any]],
    detail_limit: int,
    unreleased_present: bool = False,
    prepend_notes: Optional[List[str]] = None,
) -> Optional[Dict[str, Any]]:
    if not releases:
        return None

    latest = releases[0]
    previous = releases[1] if len(releases) > 1 else {}
    latest_body = latest.get("body") or ""
    previous_body = previous.get("body") or ""
    latest_details = collect_items(latest_body.splitlines(), detail_limit)
    previous_details = collect_items(previous_body.splitlines(), detail_limit)
    notes = list(prepend_notes or [])
    if not latest_body.strip():
        notes.append("最新 Release 没有正文内容")
    elif not latest_details:
        notes.append("最新 Release 的正文过于简略，未提取到可用摘要")

    return make_result(
        input_repo=input_repo,
        repo=repo,
        source="releases",
        latest_version=latest_release_version(latest),
        previous_version=latest_release_version(previous),
        unreleased_present=unreleased_present,
        published_at=latest.get("published_at"),
        highlights=summarize_lines(latest_body.splitlines(), 3),
        raw_url=latest.get("html_url") or github_repo_url(repo),
        notes=notes,
        latest_details=latest_details,
        previous_details=previous_details,
    )


def should_prefer_releases(changelog_candidate: Dict[str, Any], releases: List[Dict[str, Any]]) -> bool:
    if not changelog_candidate or not releases:
        return False

    latest_version = changelog_candidate.get("latest_version")
    if not latest_version:
        return True

    release_for_staleness = pick_release_for_staleness(releases)
    if not release_for_staleness:
        return False

    comparison = compare_versions(latest_version, latest_release_version(release_for_staleness))
    return comparison is not None and comparison < 0


def build_release_notes_from_changelog_context(changelog_candidate: Dict[str, Any]) -> List[str]:
    notes: List[str] = []
    latest_version = changelog_candidate.get("latest_version")
    if latest_version:
        notes.append("CHANGELOG 最新正式版本落后于 GitHub Releases，已回退到 Releases")
    else:
        notes.append("已读取 changelog，但未稳定识别出最新版本标题，已回退到 Releases")

    if changelog_candidate.get("unreleased_has_content"):
        notes.append("发现 Unreleased 分段")
        notes.append("CHANGELOG 中存在 Unreleased 内容，未并入本次正式版本摘要")
    return notes


def repo_update(raw_repo: str, release_limit: int, timeout: int, detail_limit: int) -> Dict[str, Any]:
    repo, validation_error = normalize_repo_input(raw_repo)
    if validation_error or not repo:
        return make_result(
            input_repo=raw_repo,
            repo=None,
            source="error",
            error_code=ERROR_INVALID_REPO,
            notes=[f"仓库名不合法：{validation_error}"],
        )

    try:
        metadata = fetch_repo_metadata(repo, timeout)
    except GitHubApiError as exc:
        notes, error_code = notes_and_code_from_api_error(repo, exc)
        return make_result(
            input_repo=raw_repo,
            repo=repo,
            source="error",
            error_code=error_code,
            raw_url=github_repo_url(repo),
            notes=notes,
        )
    except RuntimeError as exc:
        message = str(exc)
        return make_result(
            input_repo=raw_repo,
            repo=repo,
            source="error",
            error_code=error_code_from_runtime(message),
            raw_url=github_repo_url(repo),
            notes=[message],
        )

    default_branch = metadata.get("default_branch") or "HEAD"

    try:
        release_fetch_limit = max(release_limit, CHANGELOG_RELEASE_CONFIRMATION_LIMIT)
        releases = get_latest_releases(repo, release_fetch_limit, timeout)
        changelog_candidate = build_changelog_candidate(repo, default_branch, detail_limit, timeout, releases, raw_repo)
        if changelog_candidate:
            if should_prefer_releases(changelog_candidate, releases):
                release_result = build_release_result(
                    raw_repo,
                    repo,
                    releases[:release_limit],
                    detail_limit,
                    unreleased_present=bool(changelog_candidate.get("unreleased_present")),
                    prepend_notes=build_release_notes_from_changelog_context(changelog_candidate),
                )
                if release_result:
                    return release_result
            return build_changelog_result(changelog_candidate)

        release_result = build_release_result(raw_repo, repo, releases[:release_limit], detail_limit)
        if release_result:
            return release_result
    except GitHubApiError as exc:
        notes, error_code = notes_and_code_from_api_error(repo, exc)
        return make_result(
            input_repo=raw_repo,
            repo=repo,
            source="error",
            error_code=error_code,
            raw_url=github_repo_url(repo),
            notes=notes,
        )
    except RuntimeError as exc:
        message = str(exc)
        return make_result(
            input_repo=raw_repo,
            repo=repo,
            source="error",
            error_code=error_code_from_runtime(message),
            raw_url=github_repo_url(repo),
            notes=[message],
        )

    notes = ["未找到可用的 CHANGELOG 或 Releases"]
    if metadata.get("archived"):
        notes.append("仓库已归档")
    return make_result(
        input_repo=raw_repo,
        repo=repo,
        source="none",
        raw_url=github_repo_url(repo),
        notes=notes,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="抓取 GitHub 仓库的产品更新信息")
    parser.add_argument("repos", nargs="+", help="仓库名，格式 owner/repo，也支持 GitHub 仓库 URL")
    parser.add_argument("--limit-releases", type=int, default=2, help="获取的 Release 数量上限，至少为 1")
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT, help="单次 GitHub API 请求超时时间（秒）")
    parser.add_argument("--details", action="store_true", help="在结构化输出中附带最近两个版本的详细条目")
    parser.add_argument("--detail-limit", type=int, default=DEFAULT_DETAIL_LIMIT, help="每个版本最多保留多少条详细更新，默认 8")
    parser.add_argument("--json", action="store_true", help="输出紧凑 JSON")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.limit_releases < 1:
        parser.error("--limit-releases 必须大于等于 1")
    if args.timeout < 1:
        parser.error("--timeout 必须大于等于 1")
    if args.detail_limit < 1:
        parser.error("--detail-limit 必须大于等于 1")
    if len(args.repos) > MAX_REPOS:
        parser.error("当前技能定位为小批量查询，建议一次最多 10 个仓库，请分批执行")

    results = [repo_update(repo, args.limit_releases, args.timeout, args.detail_limit) for repo in args.repos]
    payload = build_payload(args.repos, results, args.limit_releases, args.detail_limit, args.details)

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, separators=(",", ":")))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
