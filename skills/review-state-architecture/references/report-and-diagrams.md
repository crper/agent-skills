# Report And Diagram Reference

Use this reference immediately before drafting the final answer.

## Contents

- Output structure
- Output brevity rules
- Diagram responsibilities
- Diagram quality bar

## Output Structure

Return Markdown. Keep the answer structured, evidence-based, and brief.

Recommended section order:

0. `结论先行`
1. `架构诊断`
2. `状态主体评估`
3. `坏味道`
4. `图1：当前认知模型图（Current State Model）`
5. `图2：推荐状态模型图（Refactored State Model）`
6. `图3：目标架构组织图（Target Architecture）`
7. `重构建议`
8. `迁移顺序`
9. `风险与待确认项`

## Output Brevity Rules

- `结论先行`: at most 3 bullets, sorted by severity. Each bullet must include `结论` + `影响` + `证据`.
- `架构诊断`: 3-5 bullets max.
- `状态主体评估`: use a table with columns `主体 | 类型 | 所有者 | 真源/派生 | 写入点 | 读取点 | 生命周期 | 建议动作`.
- `坏味道`: include only the top 3-5 smells that materially increase bug risk or change cost.
- `迁移顺序`: 5 steps max.
- Do not restate the same problem in multiple sections.

## Diagram Responsibilities

Always output the 3 diagrams in Markdown + Mermaid syntax. Use real repo names, prefer `flowchart LR`, and keep each diagram to roughly 6-12 nodes. If a full graph would exceed that, collapse secondary modules into one named group and keep only the path or paths tied to the main finding.

### 图1：当前认知模型图（Current State Model）

Show only the 1-2 current paths that best explain today's main state problems. This diagram is evidence of the current mess, not a full app map.

Include:

- real modules, state subjects, and external IO
- labeled edges for `calls`, `reads`, `writes`, or `effects`
- duplicated truth, cycles, and leaked side effects where they actually occur

Do not try to draw every module in the repo.

### 图2：推荐状态模型图（Refactored State Model）

Show the target ownership map only. This diagram is structural, not runtime flow.

Include:

- `subgraph` boundaries for each owner
- the state subjects that remain after refactor
- action labels for each changed subject using the chosen output language
- any boundary that becomes read-only to others

If a subject is merged or split, show the mapping from old subject name to new subject name with a dashed edge.

### 图3：目标架构组织图（Target Architecture）

Show one representative end-to-end flow after refactor, using the ownership boundaries from 图2. This diagram is behavioral, not a second ownership map.

Include:

- `subgraph` layers for `UI`, `Interaction/Application`, `State Owners`, `Services`, and `External IO`
- one concrete scenario, preferably the highest-value write path from 图1
- labeled edges for event, read, write, fetch, effect, and response

Do not re-list every state subject here unless it is required to explain the end-to-end flow.

## Diagram Quality Bar

Do not draw toy diagrams. Use the real concepts from the repo.

If helpful, add a tiny ASCII pre-map before the Mermaid diagrams, for example:

```text
UI -> Page Model -> Domain Store -> Service -> API
 \-> Form State     \-> Query Cache
```

Do not let the ASCII sketch replace the Mermaid diagrams.

- Each diagram must add new information; do not redraw the same graph three times with renamed nodes.
- Use Chinese labels for layers, roles, and actions when replying in Chinese. Keep English only for real code, module, store names and Mermaid node ids.
