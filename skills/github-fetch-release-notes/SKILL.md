---
name: github-fetch-release-notes
description: 📦 获取 GitHub 仓库更新摘要。优先读取 CHANGELOG，读取不到时回退到 Releases。只要用户提到 GitHub 仓库更新、Release Notes、CHANGELOG、版本对比、日报周报、订阅多个项目动态、直接贴 GitHub 仓库 URL，或者想把 GitHub 更新接进 cron / 自动化，都应该使用这个技能。默认输出稳定的结构化 JSON，适合脚本和大模型消费，并优先复用本机 `gh auth login` 的登录态。这个技能面向小批量查询，建议一次最多 10 个仓库。
compatibility: Python 3.8+；需要安装 GitHub CLI（gh）并先执行一次 gh auth login；需要能访问 github.com。
---

# 📦 GitHub Fetch Release Notes

> 这个技能只负责稳定取数，不负责替用户决定最终排版。

## 适用场景

- 看某个 GitHub 仓库最近更新了什么
- 比较最新版本和上一版的差异
- 给多个仓库做更新订阅、日报或周报
- 把 GitHub 更新接进 cron、workflow、bot 或其他自动化流程

## 定位

- 只面向**小批量查询**
- 建议一次最多 **10 个仓库**
- 超过 10 个仓库请分批执行
- 不在这个技能里继续叠加缓存、批处理编排、临时文件恢复之类的复杂机制

## 这个技能会做什么

- 优先读取 `CHANGELOG`
- 从 `CHANGELOG` 取到内容后，会用最近的 `Releases` 轻量确认发布时间
- 如果 `CHANGELOG` 可读，但其最新正式版本明显落后于更新的已发布 Release（优先参考可比较的稳定版），会自动回退到 `Releases`
- 如果 `CHANGELOG` 不可用，就回退到 `Releases`
- 自动处理 `owner/repo`、GitHub URL、SSH 仓库地址
- 默认输出固定 schema 的 JSON
- 复用用户本机 `gh auth login` 的登录态
- 用 `error_code` 明确标记错误类型，方便脚本分支处理

## 运行前提

```bash
gh auth login
```

## 调用方式

```bash
python3 ./skills/github-fetch-release-notes/scripts/fetch_updates.py owner/repo
python3 ./skills/github-fetch-release-notes/scripts/fetch_updates.py owner/repo --details
python3 ./skills/github-fetch-release-notes/scripts/fetch_updates.py owner/repo --json
```

## 输出约定

默认输出顶层固定包含：

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

其中：

- `published_at` 仅表示**已被 GitHub Release 确认的发布时间**
- 如果只在 `CHANGELOG` 中看到版本，但最近的 `Releases` 里还未确认，会保留 `published_at = null`，并在 `notes` 说明
- `Unreleased` 只作为补充信号，不会阻止对“陈旧 changelog”的回退判断

如果带 `--details`，还会额外返回：

- `latest_details`
- `previous_details`

如果需要按字段严格消费结果，请查看 `references/output-schema.md`。

## 常见 `error_code`

- `invalid_repo`
- `gh_not_installed`
- `gh_auth_unavailable`：当前环境没有可用的 gh 登录态，常见于 cron 或隔离环境
- `gh_not_logged_in`：交互式本地环境里没有完成 gh 登录
- `gh_auth_invalid`：能读取 gh 登录态，但 token 无效或已过期
- `repo_not_found_or_no_access`
- `rate_limited`
- `permission_denied`
- `request_timeout`
- `gh_api_failed`
- `runtime_error`

## 交互原则

- 默认先拿结构化 JSON，再由上层决定翻译、总结和排版
- 用户明确要自动化接入、脚本消费，或者要把结果喂给别的模型时，直接使用默认 JSON
- 用户要更多上下文时，再加 `--details`
- 不要把 `CHANGELOG` 标题里的日期或版本号直接当成正式发布时间；正式发布时间以 GitHub Release 确认为准
- 如果最新 release note 过于简短，就明确返回空亮点或提示说明，不要为了“看起来完整”而脑补内容
- 技能内部保留轻量串行和一次重试，但不把复杂参数暴露给用户
