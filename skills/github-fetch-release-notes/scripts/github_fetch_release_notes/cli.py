import argparse
import json
from typing import Any, Dict, List, Optional

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


def normalize_version_for_match(value: Optional[str]) -> Optional[str]:
    if not value:
        return None

    normalized = (extract_version_label(value) or value).strip().lower()
    if normalized.startswith("v") and len(normalized) > 1 and normalized[1].isdigit():
        normalized = normalized[1:]
    return normalized or None


def find_release_confirmation(releases: List[Dict[str, Any]], version: Optional[str]) -> Optional[Dict[str, Any]]:
    target = normalize_version_for_match(version)
    if not target:
        return None

    for release in releases:
        candidates = [release.get("tag_name"), release.get("name")]
        if any(normalize_version_for_match(candidate) == target for candidate in candidates):
            return release
    return None


def resolve_from_changelog(
    input_repo: str,
    repo: str,
    default_branch: str,
    release_limit: int,
    timeout: int,
    detail_limit: int,
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
        highlights = summarize_lines(latest_lines or unreleased_lines, 3)

        if not latest_version and not latest_details and not highlights:
            continue

        notes: List[str] = []
        published_at = None
        if collect_items(unreleased_lines, 1):
            notes.append("发现 Unreleased 分段")
        if not latest_version:
            notes.append("已读取 changelog，但未稳定识别出最新版本标题")
        else:
            confirmation_limit = max(release_limit, CHANGELOG_RELEASE_CONFIRMATION_LIMIT)
            releases = get_latest_releases(repo, confirmation_limit, timeout)
            matched_release = find_release_confirmation(releases, latest_version)
            if matched_release:
                published_at = matched_release.get("published_at")
                notes.append("已用 GitHub Release 确认该版本发布时间")
            elif releases:
                notes.append("CHANGELOG 最新版本尚未在最近的 GitHub Releases 中确认，可能是预写或待发布")
            else:
                notes.append("仓库没有可用于确认发布时间的 GitHub Releases")

        return make_result(
            input_repo=input_repo,
            repo=repo,
            source="changelog",
            latest_version=latest_version,
            previous_version=previous_version,
            unreleased_present=bool(unreleased_lines),
            published_at=published_at,
            highlights=highlights,
            raw_url=github_blob_url(repo, default_branch, path),
            notes=notes,
            latest_details=latest_details,
            previous_details=previous_details,
        )

    return None


def resolve_from_releases(
    input_repo: str,
    repo: str,
    release_limit: int,
    timeout: int,
    detail_limit: int,
) -> Optional[Dict[str, Any]]:
    releases = get_latest_releases(repo, release_limit, timeout)
    if not releases:
        return None

    latest = releases[0]
    previous = releases[1] if len(releases) > 1 else {}
    latest_body = latest.get("body") or ""
    previous_body = previous.get("body") or ""
    latest_details = collect_items(latest_body.splitlines(), detail_limit)
    previous_details = collect_items(previous_body.splitlines(), detail_limit)
    notes = []
    if not latest_body.strip():
        notes.append("最新 Release 没有正文内容")
    elif not latest_details:
        notes.append("最新 Release 的正文过于简略，未提取到可用摘要")

    return make_result(
        input_repo=input_repo,
        repo=repo,
        source="releases",
        latest_version=latest.get("tag_name") or latest.get("name"),
        previous_version=previous.get("tag_name") or previous.get("name"),
        unreleased_present=False,
        published_at=latest.get("published_at"),
        highlights=summarize_lines(latest_body.splitlines(), 3),
        raw_url=latest.get("html_url") or github_repo_url(repo),
        notes=notes,
        latest_details=latest_details,
        previous_details=previous_details,
    )


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
        changelog_result = resolve_from_changelog(raw_repo, repo, default_branch, release_limit, timeout, detail_limit)
        if changelog_result:
            return changelog_result
        release_result = resolve_from_releases(raw_repo, repo, release_limit, timeout, detail_limit)
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
