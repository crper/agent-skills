# agent-skills

[English](./README.md) | 简体中文

这是一个由 [@crper](https://github.com/crper) 维护的自用 / 可复用 agent skills 仓库。

每个技能都放在 `skills/<skill-name>/` 下，并带有自己的 `SKILL.md`、说明文档、参考资料、脚本和必要的评测文件。

## 安装方式

安装仓库里的某个指定技能：

```bash
npx skills add https://github.com/crper/agent-skills --skill github-fetch-release-notes
npx skills add https://github.com/crper/agent-skills --skill chrome-web-store-submission
npx skills add https://github.com/crper/agent-skills --skill shell-expert
npx skills add https://github.com/crper/agent-skills --skill review-state-architecture
```

查看当前仓库可安装的技能：

```bash
npx skills add https://github.com/crper/agent-skills --list
```

## 技能索引

| 分类 | 技能 | 作用 | 预览 |
| --- | --- | --- | --- |
| 仓库情报 | [`github-fetch-release-notes`](./skills/github-fetch-release-notes/README.zh.md) | 基于本机 `gh` 登录态抓取 GitHub Release / CHANGELOG 更新并输出稳定 JSON。 | <img src="./demos/github-fetch-release-notes/github-fetch-release-notes.png" alt="github-fetch-release-notes preview" width="220"> |
| 商店与发布 | [`chrome-web-store-submission`](./skills/chrome-web-store-submission/README.zh.md) | 生成可直接复制粘贴的 Chrome Web Store 提交文案，包括权限说明、数据使用说明和 Reviewer Note。 | <img src="./demos/chrome-web-store-submission/chrome-web-store-submission.png" alt="chrome-web-store-submission preview" width="220"> |
| Shell 与 CLI | [`shell-expert`](./skills/shell-expert/README.zh.md) | 在明确 POSIX/Bash/Zsh 假设的前提下，编写、审查、迁移和调试 shell 命令，强调引用安全与可移植性。 | POSIX + Bash |
| 架构评审 | [`review-state-architecture`](./skills/review-state-architecture/README.zh.md) | 审查应用状态所有权、真实真源边界和读写路径，并输出带证据的重构建议与 ASCII + Mermaid 图。 | ASCII + Mermaid |

## 贡献说明

仓库结构和新增技能的约定见 [`CONTRIBUTING.md`](./CONTRIBUTING.md)。

## 许可证

见 [`LICENSE`](./LICENSE)。
