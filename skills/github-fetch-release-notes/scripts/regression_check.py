#!/usr/bin/env python3

import argparse
import json
import os
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence


SCRIPT_DIR = Path(__file__).resolve().parent
ENTRYPOINT = SCRIPT_DIR / 'fetch_updates.py'
PYTHON = sys.executable
MAX_OUTPUT_PREVIEW = 400


@dataclass
class CommandResult:
    argv: List[str]
    returncode: int
    stdout: str
    stderr: str
    payload: Optional[Dict[str, Any]]


@dataclass
class Case:
    name: str
    description: str
    runner: Callable[[], None]


def build_env(*, path_override: Optional[str] = None, gh_config_dir: Optional[str] = None, gh_token: Optional[str] = None) -> Dict[str, str]:
    env = os.environ.copy()
    env.pop('GH_TOKEN', None)
    env.pop('GITHUB_TOKEN', None)
    if path_override is not None:
        env['PATH'] = path_override
    if gh_config_dir is not None:
        env['GH_CONFIG_DIR'] = gh_config_dir
    if gh_token is not None:
        env['GH_TOKEN'] = gh_token
    return env


def run_command(argv: Sequence[str], *, env: Optional[Dict[str, str]] = None) -> CommandResult:
    result = subprocess.run(list(argv), capture_output=True, text=True, env=env)
    payload = None
    if result.stdout.strip():
        try:
            payload = json.loads(result.stdout)
        except json.JSONDecodeError:
            payload = None
    return CommandResult(
        argv=list(argv),
        returncode=result.returncode,
        stdout=result.stdout,
        stderr=result.stderr,
        payload=payload,
    )


def run_fetch(args: Sequence[str], *, env: Optional[Dict[str, str]] = None, expect_json: bool = True) -> CommandResult:
    argv = [PYTHON, str(ENTRYPOINT), *args]
    if expect_json and '--json' not in argv:
        argv.append('--json')
    return run_command(argv, env=env)


def preview(text: str) -> str:
    text = text.strip()
    if len(text) <= MAX_OUTPUT_PREVIEW:
        return text
    return text[:MAX_OUTPUT_PREVIEW] + '...'


def expect(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def first_result(command: CommandResult) -> Dict[str, Any]:
    expect(command.payload is not None, f'预期拿到 JSON，实际 stdout={preview(command.stdout)!r} stderr={preview(command.stderr)!r}')
    results = command.payload.get('results')
    expect(isinstance(results, list) and results, 'JSON payload 缺少非空 results')
    return results[0]


def assert_error_code(command: CommandResult, code: str) -> None:
    result = first_result(command)
    error = result.get('error')
    expect(isinstance(error, dict), f'预期 error 对象存在，实际 result={result}')
    expect(error.get('code') == code, f'预期 error.code={code!r}，实际={error.get("code")!r}')
    expect(result.get('status') == 'error', f'预期 status=error，实际={result.get("status")!r}')


def case_public_release_success() -> None:
    command = run_fetch(['openai/codex'])
    result = first_result(command)
    expect(command.returncode == 0, f'命令应成功，实际 rc={command.returncode} stderr={preview(command.stderr)!r}')
    expect(command.payload.get('schema_version') == 'github-fetch-release-notes/v3', 'schema_version 不是 v3')
    expect(result.get('status') == 'ok', f'预期 status=ok，实际={result.get("status")!r}')
    selection = result.get('selection') or {}
    expect(selection.get('source') == 'releases', f'预期 selection.source=releases，实际={selection.get("source")!r}')
    latest = ((result.get('versions') or {}).get('latest') or {})
    expect(bool(latest.get('version')), '预期 latest.version 非空')


def case_public_changelog_success() -> None:
    command = run_fetch(['openclaw/openclaw'])
    result = first_result(command)
    expect(command.returncode == 0, f'命令应成功，实际 rc={command.returncode} stderr={preview(command.stderr)!r}')
    expect(result.get('status') == 'ok', f'预期 status=ok，实际={result.get("status")!r}')
    selection = result.get('selection') or {}
    expect(selection.get('source') == 'changelog', f'预期 selection.source=changelog，实际={selection.get("source")!r}')
    expect((result.get('input') or {}).get('normalized') == 'openclaw/openclaw', 'normalized 仓库名不正确')


def case_invalid_repo_input() -> None:
    command = run_fetch(['bad repo'])
    assert_error_code(command, 'invalid_repo')


def case_missing_gh_binary() -> None:
    env = build_env(path_override='/usr/bin:/bin')
    command = run_fetch(['openai/codex'], env=env)
    assert_error_code(command, 'gh_not_installed')


def case_gh_not_logged_in() -> None:
    with tempfile.TemporaryDirectory(prefix='gh-no-auth-') as tempdir:
        env = build_env(gh_config_dir=tempdir)
        command = run_fetch(['openai/codex'], env=env)
        assert_error_code(command, 'gh_not_logged_in')


def case_invalid_gh_token() -> None:
    with tempfile.TemporaryDirectory(prefix='gh-invalid-token-') as tempdir:
        env = build_env(gh_config_dir=tempdir, gh_token='ghp_invalid_token_for_regression_test')
        command = run_fetch(['openai/codex'], env=env)
        assert_error_code(command, 'gh_auth_invalid')


def case_graphql_partial_fallback() -> None:
    command = run_fetch(['openai/codex', 'definitely-not-exist-owner/definitely-not-exist-repo'])
    expect(command.returncode == 0, f'命令应返回结构化 JSON，实际 rc={command.returncode} stderr={preview(command.stderr)!r}')
    payload = command.payload or {}
    stats = payload.get('stats') or {}
    expect(stats.get('ok') == 1 and stats.get('error') == 1, f'预期 ok=1 error=1，实际 stats={stats}')
    results = payload.get('results') or []
    expect(len(results) == 2, f'预期两条结果，实际={len(results)}')
    expect(((results[0].get('selection') or {}).get('source')) in {'releases', 'changelog'}, f'第一条结果应成功，实际={results[0]}')
    error = results[1].get('error') or {}
    expect(error.get('code') == 'repo_not_found_or_no_access', f'第二条错误码不正确，实际={error}')


def case_oversized_batch_rejected() -> None:
    repos = [f'owner{i}/repo{i}' for i in range(11)]
    command = run_fetch(repos, expect_json=False)
    expect(command.returncode != 0, '预期 oversized batch 返回非零退出码')
    text = f'{command.stdout}\n{command.stderr}'
    expect('建议一次最多 10 个仓库' in text, f'预期错误消息提示拆分执行，实际={preview(text)!r}')


CASES = [
    Case('public-release', '公开仓库 release 路径成功', case_public_release_success),
    Case('public-changelog', '公开仓库 changelog 路径成功', case_public_changelog_success),
    Case('invalid-input', '非法仓库输入返回 invalid_repo', case_invalid_repo_input),
    Case('missing-gh', '未安装 gh 时返回 gh_not_installed', case_missing_gh_binary),
    Case('not-logged-in', 'gh 未登录时返回 gh_not_logged_in', case_gh_not_logged_in),
    Case('invalid-token', '无效 token 返回 gh_auth_invalid', case_invalid_gh_token),
    Case('graphql-partial-fallback', 'GraphQL 部分成功时其余仓库仍能回退并返回结构化错误', case_graphql_partial_fallback),
    Case('oversized-batch', '超过 10 个仓库时提前拒绝执行', case_oversized_batch_rejected),
]
CASE_BY_NAME = {case.name: case for case in CASES}


def main() -> int:
    parser = argparse.ArgumentParser(description='运行 github-fetch-release-notes 的关键回归场景')
    parser.add_argument('--case', action='append', dest='cases', help='只运行指定场景，可重复传入')
    parser.add_argument('--list', action='store_true', help='列出所有可运行场景')
    args = parser.parse_args()

    if args.list:
        for case in CASES:
            print(f'{case.name}\t{case.description}')
        return 0

    selected = CASES
    if args.cases:
        selected = []
        for name in args.cases:
            case = CASE_BY_NAME.get(name)
            if case is None:
                parser.error(f'未知场景: {name}')
            selected.append(case)

    failures: List[str] = []
    for case in selected:
        try:
            case.runner()
        except Exception as exc:
            failures.append(f'{case.name}: {exc}')
            print(f'FAIL {case.name} - {case.description}')
            print(f'  {exc}')
        else:
            print(f'PASS {case.name} - {case.description}')

    if failures:
        print(f'\n{len(failures)} 个场景失败')
        return 1

    print(f'\n全部通过：{len(selected)} 个场景')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
