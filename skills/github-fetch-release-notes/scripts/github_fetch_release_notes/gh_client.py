import base64
from datetime import datetime
import json
import re
import shutil
import subprocess
import threading
import time
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import quote, urlparse

from .models import (
    ChangelogDocument,
    FetchConfig,
    DEFAULT_MAX_CONCURRENT_GH_REQUESTS as MODEL_DEFAULT_MAX_CONCURRENT_GH_REQUESTS,
    DEFAULT_MAX_RETRIES as MODEL_DEFAULT_MAX_RETRIES,
    DEFAULT_TIMEOUT as MODEL_DEFAULT_TIMEOUT,
)


DEFAULT_TIMEOUT = MODEL_DEFAULT_TIMEOUT
MAX_CONCURRENT_GH_REQUESTS = MODEL_DEFAULT_MAX_CONCURRENT_GH_REQUESTS
MAX_RETRIES = MODEL_DEFAULT_MAX_RETRIES
CHANGELOG_FILENAMES = (
    'CHANGELOG.md',
    'changelog.md',
    'Changelog.md',
    'CHANGELOG',
    'changelog',
)
REPO_PART_RE = re.compile(r'^[A-Za-z0-9._-]+$')
HTTP_STATUS_RE = re.compile(r'\(HTTP\s+(\d{3})\)')

AUTH_MISSING_MARKERS = (
    'gh auth login',
    'not logged into any hosts',
    'authentication required',
    'try authenticating with',
)
AUTH_ENV_MARKERS = (
    'keyring',
    'keychain',
    'secretservice',
    'dbus',
    'credential',
    'password store',
    'could not read token',
    'failed to get oauth token',
    'failed to load token',
)
AUTH_INVALID_MARKERS = (
    'bad credentials',
    'invalid token',
    'token expired',
    'authorization token has expired',
    'unauthorized',
    'token is invalid',
    'failed to log in to github.com using token',
)


class GitHubApiError(RuntimeError):
    def __init__(self, status: int, message: str) -> None:
        super().__init__(message)
        self.status = status
        self.message = message


def github_repo_url(repo: str) -> str:
    return f'https://github.com/{repo}'


def github_blob_url(repo: str, branch: str, path: str) -> str:
    quoted_branch = quote(branch, safe='')
    quoted_path = quote(path, safe='/')
    return f'https://github.com/{repo}/blob/{quoted_branch}/{quoted_path}'


def repo_api_base(repo: str) -> str:
    owner, name = repo.split('/', 1)
    return f"repos/{quote(owner, safe='')}/{quote(name, safe='')}"


def contents_api_path(repo: str, path: Optional[str] = None) -> str:
    base = f'{repo_api_base(repo)}/contents'
    if not path:
        return base
    return f"{base}/{quote(path, safe='/')}"


def normalize_repo_input(raw_repo: str) -> Tuple[Optional[str], Optional[str]]:
    candidate = raw_repo.strip()
    if not candidate:
        return None, '仓库名不能为空'

    if candidate.startswith('github.com/'):
        candidate = f'https://{candidate}'

    if candidate.startswith('git@github.com:'):
        candidate = candidate.split(':', 1)[1]
    elif candidate.lower().startswith(('http://', 'https://')):
        parsed = urlparse(candidate)
        host = parsed.netloc.lower()
        if host not in {'github.com', 'www.github.com'}:
            return None, '当前只支持 github.com 仓库地址'
        parts = [part for part in parsed.path.split('/') if part]
        if len(parts) < 2:
            return None, '仓库 URL 缺少 owner/repo'
        candidate = '/'.join(parts[:2])

    candidate = candidate.rstrip('/')
    if candidate.endswith('.git'):
        candidate = candidate[:-4]

    if candidate.count('/') != 1:
        return None, '格式应为 owner/repo，或完整 GitHub 仓库 URL'

    owner, repo = candidate.split('/', 1)
    if not owner or not repo:
        return None, 'owner 和 repo 不能为空'
    if not REPO_PART_RE.fullmatch(owner) or not REPO_PART_RE.fullmatch(repo):
        return None, 'owner/repo 仅允许字母、数字、点、下划线和连字符'

    return f'{owner}/{repo}', None


def extract_gh_error(stderr: str, stdout: str) -> Tuple[int, str]:
    text = (stderr or stdout or '').strip()
    if not text:
        return 0, 'gh api 调用失败'

    status_match = HTTP_STATUS_RE.search(text)
    status = int(status_match.group(1)) if status_match else 0
    message = text[4:] if text.startswith('gh: ') else text
    if status_match:
        message = text[:status_match.start()].strip()
    return status, message.rstrip(': ') or 'gh api 调用失败'


def is_auth_error(status: int, message: str) -> bool:
    low = message.lower()
    return status == 401 or any(token in low for token in AUTH_MISSING_MARKERS + AUTH_ENV_MARKERS + AUTH_INVALID_MARKERS)


def diagnose_auth_state() -> Tuple[str, str]:
    if shutil.which('gh') is None:
        return 'gh_not_installed', '当前环境没有安装 gh，无法使用 GitHub CLI 登录态'

    try:
        result = subprocess.run(
            ['gh', 'auth', 'status'],
            capture_output=True,
            text=True,
            timeout=10,
        )
    except Exception:
        return 'gh_auth_unavailable', '当前环境无法读取 gh 登录态，常见于 cron 或隔离环境；请显式注入 GH_TOKEN，或确保该环境共享 gh 配置目录'

    text = f'{result.stdout}\n{result.stderr}'.strip().lower()


    if result.returncode == 0:
        return 'gh_auth_invalid', '当前环境能读取 gh 登录态，但请求仍被 GitHub 拒绝；请检查 token 是否过期，或执行 gh auth refresh'

    if any(marker in text for marker in AUTH_ENV_MARKERS):
        return 'gh_auth_unavailable', '当前环境无法读取 gh 登录态，常见于 cron 或隔离环境；请显式注入 GH_TOKEN，或确保该环境共享 gh 配置目录'

    if any(marker in text for marker in AUTH_MISSING_MARKERS):
        return 'gh_not_logged_in', '当前环境没有可用的 gh 登录态；如果这是交互式环境，请执行 gh auth login；如果这是 cron 或隔离环境，请确保共享 gh 配置目录或显式注入 GH_TOKEN'

    if any(marker in text for marker in AUTH_INVALID_MARKERS):
        return 'gh_auth_invalid', '当前环境能读取 gh 登录态，但 token 无效或已过期；请重新执行 gh auth login 或 gh auth refresh'

    return 'gh_auth_unavailable', '当前环境无法确认 gh 登录状态；请检查 cron / 隔离环境是否共享 gh 配置，或显式注入 GH_TOKEN'


class GhApiClient:
    def __init__(self, config: FetchConfig) -> None:
        self.config = config
        self._gh_ready = False
        self._ready_lock = threading.Lock()
        self._request_semaphore = threading.BoundedSemaphore(config.max_concurrent_gh_requests)
        self._backoff_lock = threading.Lock()
        self._global_backoff_until = 0.0

    def ensure_gh_ready(self) -> None:
        if self._gh_ready:
            return

        with self._ready_lock:
            if self._gh_ready:
                return
            if shutil.which('gh') is None:
                raise RuntimeError('未检测到 GitHub CLI（gh），请先安装 gh，再执行 gh auth login')
            self._gh_ready = True

    def wait_for_backoff_window(self) -> None:
        while True:
            with self._backoff_lock:
                sleep_seconds = self._global_backoff_until - time.monotonic()
            if sleep_seconds <= 0:
                return
            time.sleep(sleep_seconds)

    def apply_global_backoff(self, seconds: float) -> None:
        if seconds <= 0:
            return
        with self._backoff_lock:
            self._global_backoff_until = max(self._global_backoff_until, time.monotonic() + seconds)

    @staticmethod
    def should_retry(status: int, message: str) -> bool:
        low = message.lower()
        if status in {403, 429} and 'rate limit' in low:
            return True

        return status in {502, 503, 504} or any(
            token in low
            for token in (
                'eof',
                'timeout',
                'connection reset',
                'broken pipe',
                'bad gateway',
                'service unavailable',
                'gateway timeout',
            )
        )

    @staticmethod
    def retry_backoff_seconds(status: int, message: str, attempt: int) -> float:
        low = message.lower()
        factor = attempt + 1
        if status in {403, 429} and 'rate limit' in low:
            return 2.5 * factor
        if status in {502, 503, 504}:
            return 1.2 * factor
        if any(token in low for token in ('timeout', 'eof', 'connection reset', 'broken pipe')):
            return 0.8 * factor
        return 0.0

    def run_api(self, path: str, timeout: Optional[int] = None) -> str:
        last_error: Optional[Exception] = None
        request_timeout = timeout or self.config.timeout

        self.ensure_gh_ready()
        for attempt in range(self.config.max_retries + 1):
            self.wait_for_backoff_window()
            try:
                with self._request_semaphore:
                    result = subprocess.run(
                        ['gh', 'api', path],
                        capture_output=True,
                        text=True,
                        timeout=request_timeout,
                    )
            except subprocess.TimeoutExpired:
                last_error = RuntimeError(f'gh api 请求超时（>{request_timeout} 秒）')
                backoff_seconds = 0.8 * (attempt + 1)
            except Exception as exc:
                last_error = RuntimeError(f'gh api 调用失败：{exc}')
                backoff_seconds = 0.0
            else:
                if result.returncode == 0:
                    return result.stdout
                status, message = extract_gh_error(result.stderr, result.stdout)
                last_error = GitHubApiError(status=status, message=message)
                if not self.should_retry(status, message):
                    raise last_error
                backoff_seconds = self.retry_backoff_seconds(status, message, attempt)

            if attempt < self.config.max_retries:
                self.apply_global_backoff(backoff_seconds)
                continue

            if last_error is not None:
                raise last_error

        raise RuntimeError('gh api 调用失败：未知错误')

    def api_get_json(self, path: str, timeout: Optional[int] = None) -> Any:
        output = self.run_api(path, timeout=timeout)
        try:
            return json.loads(output)
        except json.JSONDecodeError as exc:
            raise RuntimeError(f'gh api 返回了无法解析的 JSON：{exc}')

    @staticmethod
    def sort_releases(releases: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        def sort_key(item: Dict[str, Any]) -> Tuple[int, str]:
            for field in ('published_at', 'created_at'):
                value = item.get(field)
                if isinstance(value, str) and value:
                    try:
                        dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
                        return 1, dt.isoformat()
                    except ValueError:
                        continue
            return 0, ''

        releases.sort(key=sort_key, reverse=True)
        return releases

    def normalize_release_items(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        releases = [item for item in items if isinstance(item, dict) and not item.get('draft')]
        return self.sort_releases(releases)

    def graphql_query_json(self, query: str, timeout: Optional[int] = None) -> Any:
        last_error: Optional[Exception] = None
        request_timeout = timeout or self.config.timeout

        self.ensure_gh_ready()
        for attempt in range(self.config.max_retries + 1):
            self.wait_for_backoff_window()
            try:
                with self._request_semaphore:
                    result = subprocess.run(
                        ['gh', 'api', 'graphql', '-f', f'query={query}'],
                        capture_output=True,
                        text=True,
                        timeout=request_timeout,
                    )
            except subprocess.TimeoutExpired:
                last_error = RuntimeError(f'gh api 请求超时（>{request_timeout} 秒）')
                backoff_seconds = 0.8 * (attempt + 1)
            except Exception as exc:
                last_error = RuntimeError(f'gh api 调用失败：{exc}')
                backoff_seconds = 0.0
            else:
                payload = None
                if result.stdout.strip():
                    try:
                        payload = json.loads(result.stdout)
                    except json.JSONDecodeError:
                        payload = None
                if isinstance(payload, dict) and payload.get('data') is not None:
                    return payload
                if result.returncode == 0 and payload is not None:
                    return payload

                status, message = extract_gh_error(result.stderr, result.stdout)
                last_error = GitHubApiError(status=status, message=message)
                if not self.should_retry(status, message):
                    raise last_error
                backoff_seconds = self.retry_backoff_seconds(status, message, attempt)

            if attempt < self.config.max_retries:
                self.apply_global_backoff(backoff_seconds)
                continue

            if last_error is not None:
                raise last_error

        raise RuntimeError('gh api 调用失败：未知错误')

    @staticmethod
    def graphql_release_to_rest_item(item: Dict[str, Any]) -> Dict[str, Any]:
        return {
            'tag_name': item.get('tagName'),
            'name': item.get('name'),
            'prerelease': item.get('isPrerelease'),
            'draft': item.get('isDraft'),
            'published_at': item.get('publishedAt'),
            'created_at': item.get('createdAt'),
            'html_url': item.get('url'),
            'body': item.get('description') or '',
        }

    @staticmethod
    def build_batch_releases_query(repos: List[str], limit: int) -> str:
        parts = ['query {']
        for index, repo in enumerate(repos):
            owner, name = repo.split('/', 1)
            parts.append(
                f"  repo{index}: repository(owner: \"{owner}\", name: \"{name}\") {{\n"
                f"    releases(first: {limit}, orderBy: {{field: CREATED_AT, direction: DESC}}) {{\n"
                f"      nodes {{\n"
                f"        tagName\n"
                f"        name\n"
                f"        isPrerelease\n"
                f"        isDraft\n"
                f"        publishedAt\n"
                f"        createdAt\n"
                f"        url\n"
                f"        description\n"
                f"      }}\n"
                f"    }}\n"
                f"  }}"
            )
        parts.append('}')
        return '\n'.join(parts)

    def batch_get_latest_releases(self, repos: List[str], limit: int, timeout: Optional[int] = None) -> Dict[str, List[Dict[str, Any]]]:
        unique_repos = list(dict.fromkeys(repos))
        if not unique_repos:
            return {}

        payload = self.graphql_query_json(self.build_batch_releases_query(unique_repos, limit), timeout=timeout)
        if not isinstance(payload, dict):
            return {}

        data = payload.get('data')
        if not isinstance(data, dict):
            return {}

        release_map: Dict[str, List[Dict[str, Any]]] = {}
        for index, repo in enumerate(unique_repos):
            repo_data = data.get(f'repo{index}')
            if not isinstance(repo_data, dict):
                continue

            releases_data = repo_data.get('releases')
            if not isinstance(releases_data, dict):
                continue

            nodes = releases_data.get('nodes')
            if not isinstance(nodes, list):
                continue

            mapped = [
                self.graphql_release_to_rest_item(item)
                for item in nodes
                if isinstance(item, dict)
            ]
            release_map[repo] = self.normalize_release_items(mapped)

        return release_map

    def fetch_contents(self, repo: str, path: str, timeout: Optional[int] = None) -> Optional[str]:
        endpoint = contents_api_path(repo, path)
        try:
            data = self.api_get_json(endpoint, timeout=timeout)
        except GitHubApiError as exc:
            if exc.status == 404:
                return None
            raise

        if not isinstance(data, dict) or data.get('type') != 'file':
            return None

        content = data.get('content')
        if not isinstance(content, str) or not content.strip():
            return None

        try:
            return base64.b64decode(content).decode('utf-8', errors='replace')
        except Exception:
            return None

    def fetch_directory_entries(self, repo: str, path: Optional[str], timeout: Optional[int] = None) -> Optional[List[Dict[str, Any]]]:
        endpoint = contents_api_path(repo, path)
        try:
            data = self.api_get_json(endpoint, timeout=timeout)
        except GitHubApiError as exc:
            if exc.status == 404:
                return None
            raise

        if not isinstance(data, list):
            return None
        return [item for item in data if isinstance(item, dict)]

    @staticmethod
    def changelog_name_rank(name: str) -> Optional[int]:
        for index, candidate in enumerate(CHANGELOG_FILENAMES):
            if name == candidate:
                return index

        low = name.lower()
        for index, candidate in enumerate(CHANGELOG_FILENAMES):
            if low == candidate.lower():
                return len(CHANGELOG_FILENAMES) + index
        return None

    def pick_changelog_entry(self, entries: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        best_entry: Optional[Dict[str, Any]] = None
        best_rank: Optional[int] = None

        for entry in entries:
            if entry.get('type') != 'file':
                continue

            name = entry.get('name')
            if not isinstance(name, str):
                continue

            rank = self.changelog_name_rank(name)
            if rank is None:
                continue

            if best_rank is None or rank < best_rank:
                best_entry = entry
                best_rank = rank
        return best_entry

    @staticmethod
    def find_directory_entry(entries: List[Dict[str, Any]], name: str) -> Optional[Dict[str, Any]]:
        target = name.lower()
        for entry in entries:
            if entry.get('type') != 'dir':
                continue
            entry_name = entry.get('name')
            if isinstance(entry_name, str) and entry_name.lower() == target:
                return entry
        return None

    def fetch_changelog_document(self, repo: str, timeout: Optional[int] = None) -> Optional[ChangelogDocument]:
        root_entries = self.fetch_directory_entries(repo, None, timeout=timeout)
        if not root_entries:
            return None

        root_match = self.pick_changelog_entry(root_entries)
        if root_match:
            root_path = root_match.get('path') or root_match.get('name')
            if isinstance(root_path, str):
                text = self.fetch_contents(repo, root_path, timeout=timeout)
                if text:
                    return ChangelogDocument(
                        path=root_path,
                        text=text,
                        html_url=root_match.get('html_url') or github_blob_url(repo, 'HEAD', root_path),
                    )

        docs_entry = self.find_directory_entry(root_entries, 'docs')
        docs_path = docs_entry.get('path') if docs_entry else None
        if not isinstance(docs_path, str):
            return None

        docs_entries = self.fetch_directory_entries(repo, docs_path, timeout=timeout)
        if not docs_entries:
            return None

        docs_match = self.pick_changelog_entry(docs_entries)
        if not docs_match:
            return None

        changelog_path = docs_match.get('path') or docs_match.get('name')
        if not isinstance(changelog_path, str):
            return None

        text = self.fetch_contents(repo, changelog_path, timeout=timeout)
        if not text:
            return None

        return ChangelogDocument(
            path=changelog_path,
            text=text,
            html_url=docs_match.get('html_url') or github_blob_url(repo, 'HEAD', changelog_path),
        )

    def get_latest_releases(self, repo: str, limit: int, timeout: Optional[int] = None) -> List[Dict[str, Any]]:
        endpoint = f'{repo_api_base(repo)}/releases?per_page={limit}'
        data = self.api_get_json(endpoint, timeout=timeout)
        if not isinstance(data, list):
            return []
        return self.normalize_release_items([item for item in data if isinstance(item, dict)])
