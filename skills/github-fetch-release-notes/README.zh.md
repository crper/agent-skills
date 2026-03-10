# GitHub Fetch Release Notes

[English](./README.md) | 简体中文

基于本机 `gh auth login` 登录态抓取 GitHub Release / CHANGELOG 更新，并输出稳定的 JSON 结果。

## 适用范围

- 适合**小批量查询**
- 建议一次最多 **10 个仓库**
- 超过 10 个请拆分执行
- 默认使用轻量有界并发与错误退避；release 查询会优先通过 `gh api graphql` 批量预取，更适合 cron / bot 场景下的小批量抓取

## 项目结构

- `scripts/fetch_updates.py`：入口
- `scripts/regression_check.py`：关键错误路径与回归场景检查脚本
- `scripts/github_fetch_release_notes/cli.py`：CLI 入口与参数解析
- `scripts/github_fetch_release_notes/models.py`：配置对象与结果模型
- `scripts/github_fetch_release_notes/service.py`：主流程编排与多仓并发调度
- `scripts/github_fetch_release_notes/release_policy.py`：版本比较、预发布过滤与回退策略
- `scripts/github_fetch_release_notes/gh_client.py`：环境校验、`gh api` 调用与并发退避
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

每个 `results[]` 采用嵌套结构，固定包含：

- `input`
- `status`
- `selection`
- `versions`
- `signals`
- `warnings`
- `notes`
- `error`

开启 `--details` 时，详细条目会出现在：

- `versions.latest.details`
- `versions.previous.details`

字段语义补充：

- `selection.decision_code` 提供稳定的机器可读决策原因
- `selection.release_confirmed` 表示最终选中的最新版本是否已被 GitHub Release 确认
- `versions.latest` / `versions.previous` 统一承载版本、发布时间、是否预发布、亮点和详情
- `signals` 存放补充判断信号，例如 `unreleased_present`、`changelog_stale`、`stable_release_preferred`
- `warnings[].code` 提供稳定的结构化告警标签
- 如果最近 Releases 同时混有预发布和正式版，默认优先正式版；只有最近没有正式版时，才返回预发布

## 常见认证相关错误码

- `gh_auth_unavailable`：当前环境没有可用的 gh 登录态，常见于 cron 或隔离运行环境
- `gh_not_logged_in`：交互式本地环境里没有完成 gh 登录
- `gh_auth_invalid`：当前环境能读取 gh 登录态，但 token 无效或已过期

## Schema 说明

如果要按字段严格消费结果，请看 [`references/output-schema.md`](./references/output-schema.md)。
