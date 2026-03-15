from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Sequence, Tuple

from .gh_client import GitHubApiError, diagnose_auth_state, is_auth_error
from .models import RepoUpdateResult, ResultWarning


SCHEMA_VERSION = 'github-fetch-release-notes/v3'
ERROR_INVALID_REPO = 'invalid_repo'
ERROR_GH_NOT_INSTALLED = 'gh_not_installed'
ERROR_GH_NOT_LOGGED_IN = 'gh_not_logged_in'
ERROR_GH_AUTH_UNAVAILABLE = 'gh_auth_unavailable'
ERROR_GH_AUTH_INVALID = 'gh_auth_invalid'
ERROR_RATE_LIMITED = 'rate_limited'
ERROR_REPO_NOT_FOUND = 'repo_not_found_or_no_access'
ERROR_PERMISSION_DENIED = 'permission_denied'
ERROR_REQUEST_TIMEOUT = 'request_timeout'
ERROR_GH_API_FAILED = 'gh_api_failed'
ERROR_RUNTIME = 'runtime_error'


def utc_now_iso() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace('+00:00', 'Z')
    )


def make_warning(code: str, message: str) -> ResultWarning:
    return ResultWarning(code=code, message=message)


def make_result(
    *,
    input_repo: str,
    repo: Optional[str] = None,
    source: str,
    error_code: Optional[str] = None,
    latest_version: Optional[str] = None,
    previous_version: Optional[str] = None,
    unreleased_present: bool = False,
    published_at: Optional[str] = None,
    highlights: Optional[List[str]] = None,
    raw_url: Optional[str] = None,
    notes: Optional[List[str]] = None,
    latest_details: Optional[List[str]] = None,
    previous_details: Optional[List[str]] = None,
    decision_code: Optional[str] = None,
    release_confirmed: Optional[bool] = None,
    latest_is_prerelease: Optional[bool] = None,
    previous_is_prerelease: Optional[bool] = None,
    latest_summary_state: Optional[str] = None,
    previous_summary_state: Optional[str] = None,
    changelog_stale: bool = False,
    stable_release_preferred: bool = False,
    warnings: Optional[List[ResultWarning]] = None,
) -> RepoUpdateResult:
    return RepoUpdateResult(
        input_repo=input_repo,
        repo=repo,
        source=source,
        error_code=error_code,
        latest_version=latest_version,
        previous_version=previous_version,
        unreleased_present=unreleased_present,
        published_at=published_at,
        highlights=highlights or [],
        raw_url=raw_url,
        notes=notes or [],
        latest_details=latest_details or [],
        previous_details=previous_details or [],
        decision_code=decision_code,
        release_confirmed=release_confirmed,
        latest_is_prerelease=latest_is_prerelease,
        previous_is_prerelease=previous_is_prerelease,
        latest_summary_state=latest_summary_state,
        previous_summary_state=previous_summary_state,
        changelog_stale=changelog_stale,
        stable_release_preferred=stable_release_preferred,
        warnings=warnings or [],
    )


def build_stats(results: Sequence[RepoUpdateResult]) -> Dict[str, int]:
    return {
        'total': len(results),
        'ok': sum(1 for result in results if result.source in {'changelog', 'releases'}),
        'no_data': sum(1 for result in results if result.source == 'none'),
        'error': sum(1 for result in results if result.source == 'error'),
    }


def build_payload(
    input_repos: List[str],
    results: Sequence[RepoUpdateResult],
    release_limit: int,
    detail_limit: int,
    include_details: bool,
) -> Dict[str, Any]:
    normalized_results = [result.to_dict(include_details=include_details) for result in results]
    return {
        'schema_version': SCHEMA_VERSION,
        'generated_at': utc_now_iso(),
        'query': {
            'input_repos': input_repos,
            'release_limit': release_limit,
            'detail_limit': detail_limit,
            'details_included': include_details,
            'output_mode': 'stable_json',
        },
        'stats': build_stats(results),
        'results': normalized_results,
    }


def build_rate_limit_note() -> str:
    return 'GitHub API 触发限流，请稍后重试，或检查 gh 登录账号的请求配额'


def error_code_from_runtime(message: str) -> str:
    if '未检测到 GitHub CLI' in message:
        return ERROR_GH_NOT_INSTALLED
    if 'GitHub CLI 未登录' in message:
        return ERROR_GH_NOT_LOGGED_IN
    if '请求超时' in message:
        return ERROR_REQUEST_TIMEOUT
    if 'gh api 调用失败' in message:
        return ERROR_GH_API_FAILED
    return ERROR_RUNTIME


def notes_and_code_from_api_error(repo: str, exc: GitHubApiError) -> Tuple[List[str], str]:
    message = exc.message.lower()

    if exc.status == 404:
        return [f'仓库不存在，或当前账号无权访问私有仓库：{repo}'], ERROR_REPO_NOT_FOUND

    if exc.status in {403, 429} and 'rate limit' in message:
        return [build_rate_limit_note()], ERROR_RATE_LIMITED

    if is_auth_error(exc.status, exc.message):
        error_code, note = diagnose_auth_state()
        return [note], error_code

    if exc.status == 403:
        return ['当前请求被 GitHub 拒绝，请检查账号权限或仓库访问范围'], ERROR_PERMISSION_DENIED

    return [f'GitHub API 返回 {exc.status}：{exc.message}'], ERROR_GH_API_FAILED
