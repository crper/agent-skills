# GitHub Fetch Release Notes

[English](./README.md) | 简体中文

基于本机 `gh auth login` 登录态抓取 GitHub Release / CHANGELOG 更新，并输出稳定的 JSON 结果。

## 适用范围

- 适合**小批量查询**
- 建议一次最多 **10 个仓库**
- 超过 10 个请拆分执行

## 项目结构

- `scripts/fetch_updates.py`：入口
- `scripts/github_fetch_release_notes/cli.py`：主流程与参数解析
- `scripts/github_fetch_release_notes/gh_client.py`：环境校验与 `gh api` 调用
- `scripts/github_fetch_release_notes/changelog.py`：CHANGELOG 解析
- `scripts/github_fetch_release_notes/output.py`：稳定输出与错误语义
- `evals/evals.json`：后续回归检查可复用的最小评测提示集

## 依赖

- `Python 3.8+`
- `GitHub CLI (gh)`

安装指南：<https://github.com/cli/cli#installation>

```bash
gh auth login
```

## 用法

```bash
python3 ./skills/github-fetch-release-notes/scripts/fetch_updates.py owner/repo
python3 ./skills/github-fetch-release-notes/scripts/fetch_updates.py owner/repo --details
python3 ./skills/github-fetch-release-notes/scripts/fetch_updates.py owner/repo --json
```

## 输出

顶层字段固定包含：

- `schema_version`
- `generated_at`
- `query`
- `stats`
- `results`

每个 `results[]` 固定包含：

- `input_repo`
- `repo`
- `status`
- `source`
- `error_code`
- `latest_version`
- `previous_version`
- `unreleased_present`
- `published_at`
- `highlights`
- `raw_url`
- `notes`

开启 `--details` 时，额外包含：

- `latest_details`
- `previous_details`

字段语义补充：

- `published_at` 仅在找到可匹配的 GitHub Release 时填充
- 如果结果来自 `CHANGELOG`，但最近的 `Releases` 里还没确认该版本，则 `published_at` 会保持为 `null`，并在 `notes` 里提示这可能是预写或待发布条目
- 如果 `CHANGELOG` 可读，但其最新正式版本明显落后于更新的已发布 Release，技能会自动回退到 `Releases`，避免把陈旧 changelog 当成最新结果；stale 判断会优先参考可比较的稳定版，再回退到预发布版本
- `Unreleased` 只作为补充信号，不会单独阻止回退到更新的已发布 Release

## 常见认证相关错误码

- `gh_auth_unavailable`：当前环境没有可用的 gh 登录态，常见于 cron 或隔离运行环境
- `gh_not_logged_in`：交互式本地环境里没有完成 gh 登录
- `gh_auth_invalid`：当前环境能读取 gh 登录态，但 token 无效或已过期

## Schema 说明

如果要按字段严格消费结果，请看 [`references/output-schema.md`](./references/output-schema.md)。
