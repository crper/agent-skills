# Shell Expert

[English](./README.md) | 简体中文

用于编写、审查、迁移和排查 shell 命令或脚本，并在 POSIX `sh`、Bash、Zsh 之间选择合适的可移植性级别。

## 适用范围

- 适合 **shell 单行命令、脚本、CI 片段**
- 处理 **可移植性、引用安全、危险操作防护、调试**
- 会先判断该用 **POSIX `sh`**、**Bash** 还是 **Zsh**，而不是默认把所有 shell 都当成 Bash

## 目录结构

- `SKILL.md`：工作流和输出约定
- `references/portability-levels.md`：shell 选择与 bashism 可移植性对照
- `references/execution-contexts.md`：Docker、Make、CI、cron 等嵌入式 shell 场景注意点
- `references/command-patterns.md`：稳健命令和脚本模式
- `references/safety-and-debugging.md`：安全加固与调试检查清单
- `agents/openai.yaml`：Agent UI 预设提示
- `evals/evals.json`：最小回归提示集

## 适合处理的任务

- 为 CI、Docker、BusyBox、Alpine 写可移植的 `sh` 脚本
- 修复嵌在 Dockerfile `RUN`、Make recipe、GitHub Actions `run:` 里的 shell 代码
- 审查命令里的 quoting、globbing、注入风险
- 替换脆弱的 `find | xargs` 或 `for f in $(...)` 用法
- 把 Bash 脚本迁移到更接近 POSIX `sh`
- 排查 `unexpected operator`、引用错误、管道静默失败等 shell 问题
- 生成更安全的批量重命名、删除、移动、文本替换命令

## 输出风格

这个技能应当：

- 先给完整可执行的命令或脚本
- 说明目标 shell 和关键假设
- 对危险操作做显式提醒，并尽量提供 dry-run 版本
- 在涉及 GNU/BSD/BusyBox 差异时明确说明

## 说明

- 优先给出明确的 shell 契约，而不是笼统的“shell 脚本”
- 默认选择满足需求的最小可移植方案
- 只有在环境明确、或者收益足够明显时，才使用 Bash / Zsh 特性
