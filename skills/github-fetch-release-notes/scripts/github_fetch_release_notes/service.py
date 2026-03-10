from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List, Optional

from .changelog import collect_items, extract_version_label, parse_changelog, summarize_lines
from .gh_client import GitHubApiError, GhApiClient, github_repo_url, normalize_repo_input
from .models import ChangelogCandidate, FetchConfig, RepoUpdateResult, ResultWarning
from .output import (
    ERROR_INVALID_REPO,
    ERROR_RUNTIME,
    error_code_from_runtime,
    make_result,
    make_warning,
    notes_and_code_from_api_error,
)
from .release_policy import (
    build_release_notes_from_changelog_context,
    build_release_selection_notes,
    find_release_confirmation,
    is_prerelease,
    latest_release_version,
    select_releases_for_summary,
    should_prefer_releases,
)


class RepoUpdateService:
    def __init__(self, config: FetchConfig, client: Optional[GhApiClient] = None) -> None:
        self.config = config
        self.client = client or GhApiClient(config)

    def build_changelog_candidate(
        self,
        repo: str,
        releases: List[Dict[str, Any]],
        input_repo: str,
        release_probe_succeeded: bool,
    ) -> Optional[ChangelogCandidate]:
        changelog_document = self.client.fetch_changelog_document(repo)
        if not changelog_document:
            return None

        parsed = parse_changelog(changelog_document.text)
        latest = parsed.get('latest') or {}
        previous = parsed.get('previous') or {}
        unreleased = parsed.get('unreleased') or {}

        latest_version = extract_version_label(latest.get('title'))
        previous_version = extract_version_label(previous.get('title'))
        latest_lines = latest.get('lines', [])
        previous_lines = previous.get('lines', [])
        unreleased_lines = unreleased.get('lines', [])

        latest_details = collect_items(latest_lines, self.config.detail_limit)
        previous_details = collect_items(previous_lines, self.config.detail_limit)
        unreleased_has_content = bool(collect_items(unreleased_lines, 1))
        highlights = summarize_lines(latest_lines or unreleased_lines, 3)

        if not latest_version and not latest_details and not highlights:
            return None

        warnings: List[ResultWarning] = []
        notes: List[str] = []
        published_at = None
        release_confirmed = False

        if unreleased_has_content:
            message = '发现 Unreleased 分段'
            notes.append(message)
            warnings.append(make_warning('unreleased_present', message))

        if not latest_version:
            message = '已读取 changelog，但未稳定识别出最新版本标题'
            notes.append(message)
            warnings.append(make_warning('version_title_unparsed', message))
            decision_code = 'changelog_selected_version_unparsed'
        else:
            matched_release = find_release_confirmation(releases, latest_version)
            if matched_release:
                published_at = matched_release.get('published_at')
                release_confirmed = True
                message = '已用 GitHub Release 确认该版本发布时间'
                notes.append(message)
                decision_code = 'changelog_selected_release_confirmed'
            elif release_probe_succeeded and releases:
                message = 'CHANGELOG 最新版本尚未在最近的 GitHub Releases 中确认，可能是预写或待发布'
                notes.append(message)
                warnings.append(make_warning('release_confirmation_missing', message))
                decision_code = 'changelog_selected_release_unconfirmed'
            elif release_probe_succeeded:
                message = '仓库没有可用于确认发布时间的 GitHub Releases'
                notes.append(message)
                warnings.append(make_warning('no_releases_for_confirmation', message))
                decision_code = 'changelog_selected_without_releases'
            else:
                message = '未能读取 GitHub Releases，暂未确认发布时间'
                notes.append(message)
                warnings.append(make_warning('release_probe_failed', message))
                decision_code = 'changelog_selected_release_probe_failed'

        return ChangelogCandidate(
            input_repo=input_repo,
            repo=repo,
            latest_version=latest_version,
            previous_version=previous_version,
            unreleased_present=bool(unreleased_lines),
            unreleased_has_content=unreleased_has_content,
            published_at=published_at,
            decision_code=decision_code,
            release_confirmed=release_confirmed,
            warnings=warnings,
            highlights=highlights,
            raw_url=changelog_document.html_url or github_repo_url(repo),
            notes=notes,
            latest_details=latest_details,
            previous_details=previous_details,
        )

    @staticmethod
    def build_changelog_result(candidate: ChangelogCandidate) -> RepoUpdateResult:
        return make_result(
            input_repo=candidate.input_repo,
            repo=candidate.repo,
            source='changelog',
            latest_version=candidate.latest_version,
            previous_version=candidate.previous_version,
            unreleased_present=candidate.unreleased_present,
            published_at=candidate.published_at,
            highlights=candidate.highlights,
            raw_url=candidate.raw_url,
            notes=candidate.notes,
            latest_details=candidate.latest_details,
            previous_details=candidate.previous_details,
            decision_code=candidate.decision_code,
            release_confirmed=candidate.release_confirmed,
            warnings=candidate.warnings,
        )

    @staticmethod
    def build_release_result(
        input_repo: str,
        repo: str,
        releases: List[Dict[str, Any]],
        detail_limit: int,
        decision_code: str,
        unreleased_present: bool = False,
        changelog_stale: bool = False,
        stable_release_preferred: bool = False,
        notes: Optional[List[str]] = None,
        warnings: Optional[List[ResultWarning]] = None,
    ) -> Optional[RepoUpdateResult]:
        if not releases:
            return None

        latest = releases[0]
        previous = releases[1] if len(releases) > 1 else {}
        latest_body = latest.get('body') or ''
        previous_body = previous.get('body') or ''
        latest_details = collect_items(latest_body.splitlines(), detail_limit)
        previous_details = collect_items(previous_body.splitlines(), detail_limit)
        note_list = list(notes or [])
        warning_list = list(warnings or [])

        if not latest_body.strip():
            message = '最新 Release 没有正文内容'
            note_list.append(message)
            warning_list.append(make_warning('release_body_empty', message))
        elif not latest_details:
            message = '最新 Release 的正文过于简略，未提取到可用摘要'
            note_list.append(message)
            warning_list.append(make_warning('release_body_sparse', message))

        return make_result(
            input_repo=input_repo,
            repo=repo,
            source='releases',
            latest_version=latest_release_version(latest),
            previous_version=latest_release_version(previous),
            unreleased_present=unreleased_present,
            published_at=latest.get('published_at'),
            highlights=summarize_lines(latest_body.splitlines(), 3),
            raw_url=latest.get('html_url') or github_repo_url(repo),
            notes=note_list,
            latest_details=latest_details,
            previous_details=previous_details,
            decision_code=decision_code,
            release_confirmed=True,
            latest_is_prerelease=is_prerelease(latest),
            previous_is_prerelease=is_prerelease(previous),
            changelog_stale=changelog_stale,
            stable_release_preferred=stable_release_preferred,
            warnings=warning_list,
        )

    @staticmethod
    def build_probe_warning(subject: str, exc: Exception) -> ResultWarning:
        if isinstance(exc, GitHubApiError):
            message = exc.message.lower()
            if exc.status in {403, 429} and 'rate limit' in message:
                return make_warning(f'{subject.lower()}_rate_limited', f'{subject} 读取受限：触发 GitHub API 限流')
            return make_warning(f'{subject.lower()}_fetch_failed', f'{subject} 读取失败：GitHub API 返回 {exc.status}')

        message = str(exc)
        if '超时' in message:
            return make_warning(f'{subject.lower()}_timeout', f'{subject} 读取超时')
        return make_warning(f'{subject.lower()}_fetch_failed', f'{subject} 读取失败：{message}')

    @staticmethod
    def build_error_result_from_exception(input_repo: str, repo: str, exc: Exception) -> RepoUpdateResult:
        if isinstance(exc, GitHubApiError):
            notes, error_code = notes_and_code_from_api_error(repo, exc)
            return make_result(
                input_repo=input_repo,
                repo=repo,
                source='error',
                error_code=error_code,
                raw_url=github_repo_url(repo),
                notes=notes,
                decision_code='fetch_failed',
            )

        message = str(exc)
        return make_result(
            input_repo=input_repo,
            repo=repo,
            source='error',
            error_code=error_code_from_runtime(message),
            raw_url=github_repo_url(repo),
            notes=[message],
            decision_code='fetch_failed',
        )

    def prefetch_releases(self, repos: List[str]) -> Dict[str, List[Dict[str, Any]]]:
        normalized_repos: List[str] = []
        seen = set()
        for raw_repo in repos:
            repo, validation_error = normalize_repo_input(raw_repo)
            if validation_error or not repo or repo in seen:
                continue
            seen.add(repo)
            normalized_repos.append(repo)

        if len(normalized_repos) <= 1:
            return {}

        try:
            return self.client.batch_get_latest_releases(normalized_repos, self.config.release_fetch_limit)
        except (GitHubApiError, RuntimeError):
            return {}

    def repo_update(self, raw_repo: str, prefetched_releases: Optional[Dict[str, List[Dict[str, Any]]]] = None) -> RepoUpdateResult:
        repo, validation_error = normalize_repo_input(raw_repo)
        if validation_error or not repo:
            return make_result(
                input_repo=raw_repo,
                repo=None,
                source='error',
                error_code=ERROR_INVALID_REPO,
                notes=[f'仓库名不合法：{validation_error}'],
                decision_code='invalid_input',
            )

        releases: List[Dict[str, Any]] = []
        release_probe_succeeded = False
        release_error: Optional[Exception] = None
        changelog_error: Optional[Exception] = None

        if prefetched_releases is not None and repo in prefetched_releases:
            releases = prefetched_releases[repo]
            release_probe_succeeded = True
        else:
            try:
                releases = self.client.get_latest_releases(repo, self.config.release_fetch_limit)
                release_probe_succeeded = True
            except (GitHubApiError, RuntimeError) as exc:
                release_error = exc

        changelog_candidate: Optional[ChangelogCandidate] = None
        try:
            changelog_candidate = self.build_changelog_candidate(
                repo,
                releases,
                raw_repo,
                release_probe_succeeded,
            )
        except (GitHubApiError, RuntimeError) as exc:
            changelog_error = exc

        if changelog_candidate:
            if releases and should_prefer_releases(changelog_candidate, releases):
                selected_releases = select_releases_for_summary(releases, self.config.release_limit)
                note_list = build_release_notes_from_changelog_context(changelog_candidate)
                warning_list = list(changelog_candidate.warnings)
                selection_notes = build_release_selection_notes(releases, selected_releases)
                stable_release_preferred = bool(selection_notes)
                if stable_release_preferred:
                    note_list.extend(selection_notes)
                    warning_list.extend(make_warning('stable_release_preferred', item) for item in selection_notes)
                release_result = self.build_release_result(
                    raw_repo,
                    repo,
                    selected_releases,
                    self.config.detail_limit,
                    decision_code='releases_selected_stale_changelog',
                    unreleased_present=changelog_candidate.unreleased_present,
                    changelog_stale=True,
                    stable_release_preferred=stable_release_preferred,
                    notes=note_list,
                    warnings=warning_list,
                )
                if release_result:
                    return release_result
            return self.build_changelog_result(changelog_candidate)

        if releases:
            selected_releases = select_releases_for_summary(releases, self.config.release_limit)
            note_list: List[str] = []
            warning_list: List[ResultWarning] = []
            selection_notes = build_release_selection_notes(releases, selected_releases)
            stable_release_preferred = bool(selection_notes)
            if stable_release_preferred:
                note_list.extend(selection_notes)
                warning_list.extend(make_warning('stable_release_preferred', item) for item in selection_notes)

            decision_code = 'releases_selected'
            if changelog_error:
                changelog_warning = self.build_probe_warning('CHANGELOG', changelog_error)
                warning_list.append(changelog_warning)
                note_list.append(changelog_warning.message)
                decision_code = 'releases_selected_changelog_unavailable'

            release_result = self.build_release_result(
                raw_repo,
                repo,
                selected_releases,
                self.config.detail_limit,
                decision_code=decision_code,
                stable_release_preferred=stable_release_preferred,
                notes=note_list,
                warnings=warning_list,
            )
            if release_result:
                return release_result

        if release_error is not None:
            return self.build_error_result_from_exception(raw_repo, repo, release_error)
        if changelog_error is not None:
            return self.build_error_result_from_exception(raw_repo, repo, changelog_error)

        return make_result(
            input_repo=raw_repo,
            repo=repo,
            source='none',
            raw_url=github_repo_url(repo),
            notes=['未找到可用的 CHANGELOG 或 Releases'],
            decision_code='no_changelog_or_releases',
        )

    def repo_update_safe(
        self,
        raw_repo: str,
        prefetched_releases: Optional[Dict[str, List[Dict[str, Any]]]] = None,
    ) -> RepoUpdateResult:
        try:
            return self.repo_update(raw_repo, prefetched_releases=prefetched_releases)
        except Exception as exc:
            repo, _ = normalize_repo_input(raw_repo)
            return make_result(
                input_repo=raw_repo,
                repo=repo,
                source='error',
                error_code=ERROR_RUNTIME,
                raw_url=github_repo_url(repo) if repo else None,
                notes=[f'未处理异常：{exc}'],
                decision_code='unexpected_exception',
            )

    def run_repo_updates(self, repos: List[str]) -> List[RepoUpdateResult]:
        prefetched_releases = self.prefetch_releases(repos)

        if len(repos) <= 1:
            return [self.repo_update_safe(repo, prefetched_releases=prefetched_releases) for repo in repos]

        results: List[Optional[RepoUpdateResult]] = [None] * len(repos)
        max_workers = min(self.config.max_workers, len(repos))
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_index = {
                executor.submit(self.repo_update_safe, repo, prefetched_releases): index
                for index, repo in enumerate(repos)
            }
            for future in as_completed(future_to_index):
                results[future_to_index[future]] = future.result()

        return [result for result in results if result is not None]
