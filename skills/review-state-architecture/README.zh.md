# Review State Architecture

[English](./README.md) | 简体中文

审查应用状态放在哪里、谁拥有、谁写、谁读，以及这些边界是否真的符合产品行为。这个技能重点解决重复真源、所有权不清、跨边界写入、状态流转泄漏等问题，并输出带证据的诊断结果和 ASCII + Mermaid 图。

## 适用范围

```text
[状态盘点] -> [收窄范围] -> [读写路径追踪] -> [坏味道诊断] -> [目标模型]
```

适合：

- React / Vue / SPA 的状态边界审查
- store / context / reducer / query cache 的所有权问题
- 判断状态应该落在本地 UI、URL、表单状态、服务端缓存还是共享领域状态
- 需要基于代码证据而不是库偏好的重构讨论

不适合：

- 泛化代码审查
- 纯后端架构审查
- 视觉设计点评
- 与状态所有权无关的纯性能排查

## 目录结构

- `SKILL.md`：触发条件、评审契约与工作流
- `README.md` / `README.zh.md`：对外说明文档
- `references/state-analysis.md`：诊断问题清单、坏味道目录、动作映射
- `references/report-and-diagrams.md`：报告结构与图1/图2/图3职责
- `references/render-friendly-diagrams.md`：ASCII 优先的出图规则
- `references/examples.md`：好坏示例
- `evals/evals.json`：后续回归检查提示集
- `agents/openai.yaml`：Agent UI 预设提示

## 评审契约

- 先读真实代码，再下架构结论。
- 只要仓库允许，就尽量给出真实 `file:line` 证据。
- 明确区分 `证据`、`推断`、`待确认`。
- 优先 KISS 和 YAGNI，不默认引入新状态库。
- 优先给出分波次迁移方案，而不是大爆炸重写。

## 输出形态

这个技能会稳定产出：

1. 使用 `结论 / 证据 / 影响 / 处理` 的核心发现
2. 一张覆盖所有者、生命周期、写入点、读取点、建议动作的状态主体表
3. 一张终端友好的 ASCII 预图
4. 三张职责明确、互不重复的 Mermaid 图
5. 一个先降风险、再清边界的最小迁移顺序

## 典型问题

- 这个功能的真实 source of truth 到底在哪？
- 这个 store 是太大了，还是拆得太碎了？
- 这个值应该迁到 URL、表单状态还是服务端缓存？
- 两个模块是不是在互相写状态？
- 哪些读是派生的，哪些写造成了耦合？

## 说明

- 这个技能只做状态架构审查；除非用户明确要求，否则不直接实现重构。
- 大块规则沉到 `references/`，这样 `SKILL.md` 更聚焦，也更适合公开维护。
