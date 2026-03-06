import base64
import json
import re
import shutil
import subprocess
import threading
import time
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import quote, urlparse


DEFAULT_TIMEOUT = 15
REQUEST_INTERVAL_SECONDS = 0.35
MAX_RETRIES = 1
DEFAULT_CHANGELOG_PATHS = (
    "CHANGELOG.md",
    "changelog.md",
    "Changelog.md",
    "CHANGELOG",
    "changelog",
    "docs/CHANGELOG.md",
    "docs/changelog.md",
)
REPO_PART_RE = re.compile(r"^[A-Za-z0-9._-]+$")
HTTP_STATUS_RE = re.compile(r"\(HTTP\s+(\d{3})\)")
GH_READY: Optional[bool] = None
QUEUE_LOCK = threading.Lock()
NEXT_REQUEST_AT = 0.0

AUTH_MISSING_MARKERS = (
    "gh auth login",
    "not logged into any hosts",
    "authentication required",
    "try authenticating with",
)
AUTH_ENV_MARKERS = (
    "keyring",
    "keychain",
    "secretservice",
    "dbus",
    "credential",
    "password store",
    "could not read token",
    "failed to get oauth token",
    "failed to load token",
)
AUTH_INVALID_MARKERS = (
    "bad credentials",
    "invalid token",
    "token expired",
    "authorization token has expired",
    "unauthorized",
)


class GitHubApiError(RuntimeError):
    def __init__(self, status: int, message: str) -> None:
        super().__init__(message)
        self.status = status
        self.message = message


def github_repo_url(repo: str) -> str:
    return f"https://github.com/{repo}"


def github_blob_url(repo: str, branch: str, path: str) -> str:
    quoted_branch = quote(branch, safe="")
    quoted_path = quote(path, safe="/")
    return f"https://github.com/{repo}/blob/{quoted_branch}/{quoted_path}"


def repo_api_base(repo: str) -> str:
    owner, name = repo.split("/", 1)
    return f"repos/{quote(owner, safe='')}/{quote(name, safe='')}"


def normalize_repo_input(raw_repo: str) -> Tuple[Optional[str], Optional[str]]:
    candidate = raw_repo.strip()
    if not candidate:
        return None, "仓库名不能为空"

    if candidate.startswith("github.com/"):
        candidate = f"https://{candidate}"

    if candidate.startswith("git@github.com:"):
        candidate = candidate.split(":", 1)[1]
    elif candidate.lower().startswith(("http://", "https://")):
        parsed = urlparse(candidate)
        host = parsed.netloc.lower()
        if host not in {"github.com", "www.github.com"}:
            return None, "当前只支持 github.com 仓库地址"
        parts = [part for part in parsed.path.split("/") if part]
        if len(parts) < 2:
            return None, "仓库 URL 缺少 owner/repo"
        candidate = "/".join(parts[:2])

    candidate = candidate.rstrip("/")
    if candidate.endswith(".git"):
        candidate = candidate[:-4]

    if candidate.count("/") != 1:
        return None, "格式应为 owner/repo，或完整 GitHub 仓库 URL"

    owner, repo = candidate.split("/", 1)
    if not owner or not repo:
        return None, "owner 和 repo 不能为空"
    if not REPO_PART_RE.fullmatch(owner) or not REPO_PART_RE.fullmatch(repo):
        return None, "owner/repo 仅允许字母、数字、点、下划线和连字符"

    return f"{owner}/{repo}", None


def ensure_gh_ready() -> None:
    global GH_READY
    if GH_READY:
        return

    if shutil.which("gh") is None:
        raise RuntimeError("未检测到 GitHub CLI（gh），请先安装 gh，再执行 gh auth login")

    GH_READY = True


def extract_gh_error(stderr: str, stdout: str) -> Tuple[int, str]:
    text = (stderr or stdout or "").strip()
    if not text:
        return 0, "gh api 调用失败"

    status_match = HTTP_STATUS_RE.search(text)
    status = int(status_match.group(1)) if status_match else 0
    message = text[4:] if text.startswith("gh: ") else text
    if status_match:
        message = text[:status_match.start()].strip()
    return status, message.rstrip(": ") or "gh api 调用失败"


def wait_for_queue_slot() -> None:
    global NEXT_REQUEST_AT
    sleep_seconds = 0.0

    with QUEUE_LOCK:
        now = time.monotonic()
        if now < NEXT_REQUEST_AT:
            sleep_seconds = NEXT_REQUEST_AT - now
            now = NEXT_REQUEST_AT
        NEXT_REQUEST_AT = now + REQUEST_INTERVAL_SECONDS

    if sleep_seconds > 0:
        time.sleep(sleep_seconds)


def should_retry(status: int, message: str) -> bool:
    low = message.lower()
    return status in {502, 503, 504} or any(
        token in low
        for token in (
            "eof",
            "timeout",
            "connection reset",
            "broken pipe",
            "bad gateway",
            "service unavailable",
            "gateway timeout",
        )
    )


def run_gh_api(path: str, timeout: int) -> str:
    last_error: Optional[Exception] = None

    for attempt in range(MAX_RETRIES + 1):
        wait_for_queue_slot()

        try:
            result = subprocess.run(
                ["gh", "api", path],
                capture_output=True,
                text=True,
                timeout=timeout,
            )
        except subprocess.TimeoutExpired:
            last_error = RuntimeError(f"gh api 请求超时（>{timeout} 秒）")
        except Exception as exc:
            last_error = RuntimeError(f"gh api 调用失败：{exc}")
        else:
            if result.returncode == 0:
                return result.stdout
            status, message = extract_gh_error(result.stderr, result.stdout)
            last_error = GitHubApiError(status=status, message=message)
            if not should_retry(status, message):
                raise last_error

        if attempt < MAX_RETRIES:
            time.sleep(0.8 * (attempt + 1))
            continue

        if last_error is not None:
            raise last_error

    raise RuntimeError("gh api 调用失败：未知错误")


def api_get_json(path: str, timeout: int) -> Any:
    ensure_gh_ready()
    output = run_gh_api(path, timeout)
    try:
        return json.loads(output)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"gh api 返回了无法解析的 JSON：{exc}")


def is_auth_error(status: int, message: str) -> bool:
    low = message.lower()
    return status == 401 or any(token in low for token in AUTH_MISSING_MARKERS + AUTH_ENV_MARKERS + AUTH_INVALID_MARKERS)


def diagnose_auth_state() -> Tuple[str, str]:
    if shutil.which("gh") is None:
        return "gh_not_installed", "当前环境没有安装 gh，无法使用 GitHub CLI 登录态"

    try:
        result = subprocess.run(
            ["gh", "auth", "status"],
            capture_output=True,
            text=True,
            timeout=10,
        )
    except Exception:
        return "gh_auth_unavailable", "当前环境无法读取 gh 登录态，常见于 cron 或隔离环境；请显式注入 GH_TOKEN，或确保该环境共享 gh 配置目录"

    text = f"{result.stdout}\n{result.stderr}".strip().lower()

    if result.returncode == 0:
        return "gh_auth_invalid", "当前环境能读取 gh 登录态，但请求仍被 GitHub 拒绝；请检查 token 是否过期，或执行 gh auth refresh"

    if any(marker in text for marker in AUTH_ENV_MARKERS):
        return "gh_auth_unavailable", "当前环境无法读取 gh 登录态，常见于 cron 或隔离环境；请显式注入 GH_TOKEN，或确保该环境共享 gh 配置目录"

    if any(marker in text for marker in AUTH_MISSING_MARKERS):
        return "gh_auth_unavailable", "当前环境没有可用的 gh 登录态，常见于 cron 或隔离环境没有复用到同一个 HOME / gh 配置目录；如果这是交互式环境，请执行 gh auth login"

    if any(marker in text for marker in AUTH_INVALID_MARKERS):
        return "gh_auth_invalid", "当前环境能读取 gh 登录态，但 token 无效或已过期；请重新执行 gh auth login 或 gh auth refresh"

    return "gh_auth_unavailable", "当前环境无法确认 gh 登录状态；请检查 cron / 隔离环境是否共享 gh 配置，或显式注入 GH_TOKEN"


def fetch_repo_metadata(repo: str, timeout: int) -> Dict[str, Any]:
    data = api_get_json(repo_api_base(repo), timeout)
    if not isinstance(data, dict):
        raise RuntimeError("仓库元信息格式异常")
    return data


def fetch_contents(repo: str, path: str, timeout: int) -> Optional[str]:
    endpoint = f"{repo_api_base(repo)}/contents/{quote(path, safe='/')}"
    try:
        data = api_get_json(endpoint, timeout)
    except GitHubApiError as exc:
        if exc.status == 404:
            return None
        raise

    if not isinstance(data, dict) or data.get("type") != "file":
        return None

    content = data.get("content")
    if not isinstance(content, str) or not content.strip():
        return None

    try:
        return base64.b64decode(content).decode("utf-8", errors="replace")
    except Exception:
        return None


def get_latest_releases(repo: str, limit: int, timeout: int) -> List[Dict[str, Any]]:
    endpoint = f"{repo_api_base(repo)}/releases?per_page={limit}"
    data = api_get_json(endpoint, timeout)
    if not isinstance(data, list):
        return []
    return [item for item in data if isinstance(item, dict)]
