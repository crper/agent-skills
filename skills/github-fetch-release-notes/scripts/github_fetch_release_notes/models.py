from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


DEFAULT_TIMEOUT = 10
DEFAULT_DETAIL_LIMIT = 8
DEFAULT_MAX_WORKERS = 6
DEFAULT_MAX_REPOS = 10
DEFAULT_CHANGELOG_RELEASE_CONFIRMATION_LIMIT = 5
DEFAULT_RELEASE_LOOKBACK_LIMIT = 10
DEFAULT_MAX_CONCURRENT_GH_REQUESTS = 6
DEFAULT_MAX_RETRIES = 1


@dataclass(frozen=True)
class FetchConfig:
    release_limit: int
    timeout: int = DEFAULT_TIMEOUT
    detail_limit: int = DEFAULT_DETAIL_LIMIT
    include_details: bool = False
    max_workers: int = DEFAULT_MAX_WORKERS
    max_repos: int = DEFAULT_MAX_REPOS
    changelog_release_confirmation_limit: int = DEFAULT_CHANGELOG_RELEASE_CONFIRMATION_LIMIT
    release_lookback_limit: int = DEFAULT_RELEASE_LOOKBACK_LIMIT
    max_concurrent_gh_requests: int = DEFAULT_MAX_CONCURRENT_GH_REQUESTS
    max_retries: int = DEFAULT_MAX_RETRIES

    @property
    def release_fetch_limit(self) -> int:
        return max(
            self.release_limit,
            self.changelog_release_confirmation_limit,
            self.release_lookback_limit,
        )


@dataclass(frozen=True)
class ChangelogDocument:
    path: str
    text: str
    html_url: str


@dataclass(frozen=True)
class ResultWarning:
    code: str
    message: str

    def to_dict(self) -> Dict[str, str]:
        return {
            'code': self.code,
            'message': self.message,
        }


@dataclass(frozen=True)
class ChangelogCandidate:
    input_repo: str
    repo: str
    latest_version: Optional[str]
    previous_version: Optional[str]
    unreleased_present: bool
    unreleased_has_content: bool
    published_at: Optional[str]
    decision_code: str
    release_confirmed: bool
    warnings: List[ResultWarning] = field(default_factory=list)
    highlights: List[str] = field(default_factory=list)
    raw_url: Optional[str] = None
    notes: List[str] = field(default_factory=list)
    latest_details: List[str] = field(default_factory=list)
    previous_details: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class RepoUpdateResult:
    input_repo: str
    repo: Optional[str]
    source: str
    error_code: Optional[str] = None
    latest_version: Optional[str] = None
    previous_version: Optional[str] = None
    unreleased_present: bool = False
    published_at: Optional[str] = None
    highlights: List[str] = field(default_factory=list)
    raw_url: Optional[str] = None
    notes: List[str] = field(default_factory=list)
    latest_details: List[str] = field(default_factory=list)
    previous_details: List[str] = field(default_factory=list)
    decision_code: Optional[str] = None
    release_confirmed: Optional[bool] = None
    latest_is_prerelease: Optional[bool] = None
    previous_is_prerelease: Optional[bool] = None
    changelog_stale: bool = False
    stable_release_preferred: bool = False
    warnings: List[ResultWarning] = field(default_factory=list)

    @property
    def status(self) -> str:
        if self.source in {'changelog', 'releases'}:
            return 'ok'
        if self.source == 'none':
            return 'no_data'
        return 'error'

    def to_dict(self, include_details: bool = True) -> Dict[str, Any]:
        latest_item: Optional[Dict[str, Any]] = None
        if self.latest_version or self.published_at or self.highlights or self.latest_details:
            latest_item = {
                'version': self.latest_version,
                'published_at': self.published_at,
                'is_prerelease': self.latest_is_prerelease,
                'highlights': list(self.highlights),
            }
            if include_details:
                latest_item['details'] = list(self.latest_details)

        previous_item: Optional[Dict[str, Any]] = None
        if self.previous_version or self.previous_details:
            previous_item = {
                'version': self.previous_version,
                'is_prerelease': self.previous_is_prerelease,
            }
            if include_details:
                previous_item['details'] = list(self.previous_details)

        error_item = None
        if self.status == 'error':
            error_item = {
                'code': self.error_code,
                'message': self.notes[0] if self.notes else None,
            }

        return {
            'input': {
                'raw': self.input_repo,
                'normalized': self.repo,
                'repo_url': f'https://github.com/{self.repo}' if self.repo else None,
            },
            'status': self.status,
            'selection': {
                'source': self.source,
                'decision_code': self.decision_code,
                'selected_url': self.raw_url if self.source in {'changelog', 'releases'} else None,
                'release_confirmed': self.release_confirmed,
            },
            'versions': {
                'latest': latest_item,
                'previous': previous_item,
            },
            'signals': {
                'unreleased_present': self.unreleased_present,
                'changelog_stale': self.changelog_stale,
                'stable_release_preferred': self.stable_release_preferred,
            },
            'warnings': [item.to_dict() for item in self.warnings],
            'notes': list(self.notes),
            'error': error_item,
        }
