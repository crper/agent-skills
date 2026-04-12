# Simplify Code

[English](./README.md) | 简体中文

在不改变行为的前提下，精简最近改动过的代码。`simplify-code` 适合做实现后的收尾清理、补丁打磨，以及保持当前契约不变的小型重构，同时顺手做一层轻量 hardening，并把额外清理控制在一个很小的 diff 预算内。

## 适用范围

```text
[确定范围] -> [选择模式] -> [补齐上下文] -> [风险分级] -> [安全简化] -> [最小验证] -> [汇报结果]
```

适合：

- 清理刚写完的一组改动
- 缩减触达文件里的重复逻辑、深层嵌套和死代码
- 在不重做设计的前提下提升命名和可读性
- 用仓库里已有 helper 替换手搓的局部逻辑
- 增加不改变现有行为的小型防御性判断

不适合：

- 大范围架构重写
- 在 auth、存储、并发、计费等敏感边界上盲改
- 改 schema、API 契约或持久化格式
- 在缺少验证的情况下做“顺手提速”并改变语义

## 默认行为

- 默认执行“严谨的自动修”，只处理低风险清理项。
- 如果用户明确说“只要报告 / 不要改 / 只提建议”，立刻切到 review-only。
- 编辑前先用“fresh eyes”重读一遍触达代码。
- 一旦碰到公共契约、敏感逻辑、结构性边界或平台兼容边界，就停手并升级汇报。
- 额外清理应当保持很小，不应悄悄把补丁越改越大。
- 如果范围大到无法安全验证，就优先降级成 review-only，而不是做一轮扫射式自动修。

## 安全模型

- 编辑前先读完整文件，不只看 diff 片段。
- 先检查相邻 helper、类型、测试和直接调用方。
- 保持行为、数据形状、副作用和项目约定不变。
- 优先做局部删除和合并，不轻易引入新抽象层。
- 结构性 refactor 不是默认动作，需要先征求确认。
- 只跑与改动面匹配的最小必要验证。

## 目录结构

- `SKILL.md`：触发条件、工作流、执行契约
- `README.md` / `README.zh.md`：对外说明文档
- `references/safety-boundaries.md`：哪些可以自动修，哪些必须停手
- `references/simplification-checklist.md`：评审顺序与简化启发式清单
- `references/report-shape.md`：自动修 / review-only 的输出格式
- `evals/evals.json`：真实风格的回归提示集
- `agents/openai.yaml`：Agent UI 预设提示

## 典型提问

- `Use $simplify-code to clean up the files I just changed without changing behavior.`
- `用 $simplify-code 帮我瘦身这几个文件，先直接改低风险项。`
- `Use $simplify-code in review-only mode and give me a report for this diff.`
- `用 $simplify-code 看看这里有没有重复逻辑、坏味道或者可以复用现有 helper 的地方。`

## 说明

- 重规则沉到 `references/`，让主 skill 保持短、小、好触发。
- 这个技能天生偏保守：守住行为边界，比盲目追求“更少行数”更重要。
- 如果最安全的下一步其实是先补 characterization tests，这个技能应该直接说出来，而不是硬改。
- 如果既没有 git 上下文，也没有明确文件或代码片段范围，这个技能应该先要 scope，而不是在仓库里乱逛。
