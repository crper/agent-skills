# Simplify Code

English | [简体中文](./README.zh.md)

Simplify recently changed code without changing its behavior. `simplify-code` is a strict cleanup and light-hardening skill for post-implementation passes, patch polishing, and small refactors that should stay inside the current contract and a small diff budget.

## Scope

```text
[Scope] -> [Mode] -> [Local Context] -> [Risk Triage] -> [Safe Simplification] -> [Validation] -> [Report]
```

Best for:

- cleaning up a recent patch
- reducing duplication, nesting, or dead weight in touched files
- improving naming and readability without redesigning the module
- replacing hand-rolled local logic with an existing helper
- adding small defensive checks that preserve current behavior

Not for:

- broad architectural rewrites
- blind refactors across auth, storage, concurrency, or billing boundaries
- schema or API contract changes
- "make it faster" work where semantics might shift and no validation exists

## Default Behavior

- Default to strict auto-fix for low-risk cleanup.
- If the user asks for a report only, findings only, or no edits, switch to review-only mode.
- Re-read the touched code with fresh eyes before editing.
- Stop and escalate before changing public contracts, sensitive logic, structural boundaries, or platform compatibility assumptions.
- Keep cleanup additions small relative to the original requested patch.
- If the scope is too broad to validate safely, prefer review-only over a sweeping auto-fix pass.

## Safety Model

- Read the full touched file before editing.
- Check adjacent helpers, types, tests, and direct callers first.
- Preserve behavior, data shape, side effects, and project conventions.
- Prefer local deletions and consolidations over new abstraction layers.
- Treat structural refactors as approval-required, not default cleanup.
- Run the smallest useful validation for the edited surface.

## Project Structure

- `SKILL.md` — trigger rules, workflow, and operating contract
- `README.md` / `README.zh.md` — public-facing documentation
- `references/safety-boundaries.md` — what can be auto-fixed vs deferred
- `references/simplification-checklist.md` — review order and simplification heuristics
- `references/report-shape.md` — final answer format for auto-fix and review-only modes
- `evals/evals.json` — realistic prompts for regression-style checks
- `agents/openai.yaml` — prompt preset for agent UIs

## Typical Prompts

- `Use $simplify-code to clean up the files I just changed without changing behavior.`
- `用 $simplify-code 帮我瘦身这几个文件，先直接改低风险项。`
- `Use $simplify-code in review-only mode and give me a report for this diff.`
- `用 $simplify-code 看看这里有没有重复逻辑、坏味道或者可以复用现有 helper 的地方。`

## Notes

- Heavy guidance stays in `references/` so the main skill stays short and trigger-friendly.
- The skill is intentionally conservative: preserving behavior is more important than maximizing line-count reduction.
- When the safest next step is writing characterization tests first, the skill should say so instead of guessing.
- If there is no git context and no concrete file or snippet scope, the skill should ask for scope instead of roaming the repo.
