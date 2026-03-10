import argparse
import json

from .models import (
    FetchConfig,
    DEFAULT_DETAIL_LIMIT,
    DEFAULT_MAX_REPOS,
    DEFAULT_TIMEOUT,
)
from .output import build_payload
from .service import RepoUpdateService


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description='抓取 GitHub 仓库的产品更新信息')
    parser.add_argument('repos', nargs='+', help='仓库名，格式 owner/repo，也支持 GitHub 仓库 URL')
    parser.add_argument('--limit-releases', type=int, default=2, help='获取的 Release 数量上限，至少为 1')
    parser.add_argument('--timeout', type=int, default=DEFAULT_TIMEOUT, help='单次 GitHub API 请求超时时间（秒）')
    parser.add_argument('--details', action='store_true', help='在结构化输出中附带最近两个版本的详细条目')
    parser.add_argument('--detail-limit', type=int, default=DEFAULT_DETAIL_LIMIT, help='每个版本最多保留多少条详细更新，默认 8')
    parser.add_argument('--json', action='store_true', help='输出紧凑 JSON')
    return parser


def build_config(args: argparse.Namespace) -> FetchConfig:
    return FetchConfig(
        release_limit=args.limit_releases,
        timeout=args.timeout,
        detail_limit=args.detail_limit,
        include_details=args.details,
        max_repos=DEFAULT_MAX_REPOS,
    )


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.limit_releases < 1:
        parser.error('--limit-releases 必须大于等于 1')
    if args.timeout < 1:
        parser.error('--timeout 必须大于等于 1')
    if args.detail_limit < 1:
        parser.error('--detail-limit 必须大于等于 1')

    config = build_config(args)
    if len(args.repos) > config.max_repos:
        parser.error('当前技能定位为小批量查询，建议一次最多 10 个仓库，请分批执行')

    service = RepoUpdateService(config)
    results = service.run_repo_updates(args.repos)
    payload = build_payload(args.repos, results, config.release_limit, config.detail_limit, config.include_details)

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, separators=(',', ':')))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
