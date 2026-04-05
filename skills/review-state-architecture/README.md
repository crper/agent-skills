# Review State Architecture

English | [简体中文](./README.zh.md)

Review where application state lives, who owns it, who writes it, and who reads it. This skill focuses on evidence-backed diagnosis of duplicated truth, unclear ownership, cross-boundary writes, and leaky mutation paths, then proposes the smallest viable target model with ASCII + Mermaid diagrams.

## Scope

```text
[Inventory] -> [Triage] -> [Read/Write Tracing] -> [Bad Smells] -> [Target Model]
```

Best for:

- React / Vue / SPA state-boundary reviews
- store / context / reducer / query-cache ownership questions
- deciding whether state belongs in local UI, URL, form state, server cache, or shared domain state
- refactoring discussions that need concrete evidence instead of library opinions

Not for:

- generic code review
- backend-only architecture review
- visual design critique
- pure performance audits where state ownership is not the main problem

## Project Structure

- `SKILL.md` — trigger rules, review contract, and workflow
- `README.md` / `README.zh.md` — public-facing documentation
- `references/state-analysis.md` — diagnosis rubric, smell catalog, and action mapping
- `references/report-and-diagrams.md` — report shape and responsibilities for Diagram 1/2/3
- `references/render-friendly-diagrams.md` — ASCII-first rendering rules
- `references/examples.md` — good and bad diagram examples
- `evals/evals.json` — regression-style prompts for future checks
- `agents/openai.yaml` — prompt preset for agent UIs

## Review Contract

- Read real code before making architectural claims.
- Use real `file:line` references when the repo allows it.
- Separate `证据`, `推断`, and `待确认`.
- Prefer KISS and YAGNI over introducing a new state library.
- Recommend migration waves, not big-bang rewrites.

## Output Shape

The skill is designed to produce:

1. conclusion-first findings with `结论 / 证据 / 影响 / 处理`
2. a state-subject table covering owner, lifetime, writers, readers, and suggested action
3. a compact ASCII pre-map for terminal readability
4. three Mermaid diagrams with distinct roles
5. a small migration order that reduces risk first

## Typical Questions

- Where is the real source of truth for this feature?
- Is this store too large, or did we split it too far?
- Should this value move to URL state, form state, or server cache?
- Are two modules writing into each other?
- Which reads are derived, and which writes are causing coupling?

## Notes

- The skill reviews architecture and state boundaries only; it does not implement the refactor unless the user explicitly asks.
- Heavy guidance lives in `references/` so `SKILL.md` can stay focused on triggering and behavior.
