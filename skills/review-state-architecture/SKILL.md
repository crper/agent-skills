---
name: review-state-architecture
description: Use when reviewing a codebase's application-state ownership, source-of-truth boundaries, read/write paths, or store/context/hook/reducer/machine responsibilities, especially when state feels unclear, duplicated, or cyclic and the user wants evidence-backed refactoring guidance with Mermaid diagrams. Do not use for generic code review, backend-only architecture review, design critique, or performance audits unless state ownership or flow is the main problem.
---

# Review State Architecture

Diagnose where state lives, who owns it, who writes it, who reads it, and whether those boundaries match the product's real behavior. Favor the smallest viable refactor that reduces mental load, not a fashionable rewrite.

## Inputs Needed

Use whatever the user provides, then fill the smallest missing gaps from the repo.

Preferred inputs:

- repo or workspace to inspect
- modules, directories, or screens believed to contain the state bottleneck
- any named state subjects the user is already worried about
- expected review depth: quick pass or deep review

If some inputs are missing:

- infer the likely state surface from the repo
- keep the scope narrow
- state the assumption before giving strong conclusions

## Review Contract

- Read the existing code before making architectural claims.
- Prefer sharp diagnosis over vague best practices.
- Use actual module, store, hook, context, reducer, machine, and cache names from the repo.
- Distinguish source of truth from derived or mirrored state.
- Judge boundaries by ownership, lifetime, mutation paths, and coupling, not by library preference alone.
- Prefer KISS and YAGNI. Do not recommend a new state library unless the current tool is itself the root cause.
- Reply in the user's language. Default to Chinese when the user writes in Chinese.
- Every major finding must use this shape: `结论` / `证据` / `影响` / `处理`.
- `证据` must include at least 2 real `file:line` references when the codebase allows it, ideally 1 write path and 1 read path.
- If the path is only partially traced, mark it `推断`, not `证据`.
- When replying in Chinese, keep all prose, table headers, action labels, and risk statements in Chinese.
- Keep English only for code symbols, library names, real module/store/hook names, and Mermaid node ids.
- Use these Chinese action labels in Chinese output: `保留 / 拆分 / 合并 / 下沉 / 上提 / 迁移到 URL / 迁移到表单状态 / 迁移到服务端缓存 / 改为派生 / 隔离副作用 / 删除`.
- Trust outside opinions, then verify them. No subagent claim becomes `证据` until it is tied back to real `file:line`.
- If the scope of review exceeds what you can verify from the codebase, stop expanding the diagnosis and mark the gap as `待确认`.

## Boundary Handling Rules

- Work at the module or directory boundary first. Use file-level details to prove reads, writes, and leaks, not to replace the boundary model.
- Prefer one stable owner per business entity and lifetime. If two state subjects share the same owner, lifetime, and mutation cadence, merging is the default direction.
- If one state subject mixes multiple lifetimes, owners, or concern types, splitting is the default direction.
- Before proposing a new shared boundary, ask whether existing flows already solve the problem. Do not invent a parallel store for something the current architecture can already derive.
- Prefer capture over duplication: if an existing flow can expose the needed state, derive or project it instead of mirroring it.
- Prefer sequential diagnosis when all prioritized subjects cluster in the same primary module. Parallelism helps only when the questions are truly separable.

## First Pass: Build the State Inventory

Start by mapping the concrete state subjects in the codebase. Typical subjects include:

- component local state
- lifted screen/page state
- context providers
- global stores
- reducers
- state machines
- form state
- URL/search-param/router state
- server cache or query cache
- session/auth state
- optimistic state
- derived view models

For each state subject, capture only:

- name
- type
- owner module
- source of truth or derived
- writers
- readers
- lifetime
- primary responsibility
- obvious smells

Only for prioritized or problematic subjects, expand with:

- side effects attached to writes or transitions
- upstream dependencies
- downstream dependents
- one representative read path
- one representative write path

If the user gives placeholders like `[xxx]`, replace them with the real state subjects discovered from code and say that the original list was incomplete.

## Triage: Narrow the Review

After the inventory, rank state subjects by:

- user-facing risk
- write frequency
- cross-module coupling
- duplication or conflict potential

Deep-trace only the top 3-5 subjects unless the user explicitly asks for exhaustive coverage.

## Subagent Gate

Open subagents only if ALL of these are true:

- subagent tooling is available in the current environment
- triage produced at least 2 independent review questions, or 3+ prioritized state subjects
- the review can be split by concern or boundary without duplicating the same file-reading work
- the main agent is not blocked on one tightly integrated reading of the same files
- subagent findings can still be verified against the repo before the final answer

Stay single-threaded if ANY of these are true:

- the repo is small, or the main issues live in 1-2 tightly coupled modules
- all prioritized subjects share the same owner and need integrated reasoning
- the user asked for a quick pass instead of a deep review
- the evidence is sparse and parallel review would mostly produce speculation
- coordination cost is likely higher than insight gained

If the gate fails, continue locally without apology or fallback drama.

## How to Search

Prefer `rg` and scan for the smallest set of files that reveal ownership and mutation:

- framework state primitives
- store declarations
- context providers and consumers
- reducers and action creators
- state machine definitions
- query/cache setup
- form controllers
- URL/search-param helpers
- event buses or pub/sub utilities
- modules that import each other both ways

Do not stop at declarations. Trace at least one realistic read path and one realistic write path for each prioritized state subject.

## Parallel Review Mode

If the Subagent Gate passes and the user allows parallel work, launch up to 4 agents after triage, not before. Launch all selected agents in one round so they run in parallel. Give each one raw file context or precise search targets for the prioritized subjects, not your conclusions.

Default split for a larger or messier repo:

1. Ownership agent
   Audit where each state subject is defined and whether the owner is the right boundary.
2. Mutation-path agent
   Trace write paths, events, reducers, effects, and action fan-out.
3. State-type agent
   Separate UI state, form state, URL state, server/cache state, domain/app state, and workflow state.
4. Smell-and-target agent
   Identify the worst bad smells and sketch the cleanest target partitioning.

For a smaller review, use only 2-3 agents and collapse overlapping roles rather than forcing all 4.

Subagent prompt rules:

- give one bounded question per agent
- include only the prioritized modules or state subjects that agent needs
- do not pass your diagnosis, preferred answer, or intended fix
- ask for evidence and contradictions, not polished prose

After the agents return:

- keep partial results if some agents fail or time out
- merge overlaps and resolve contradictions in the main thread
- treat subagent output as additive, not authoritative
- promote a subagent claim to `证据` only after local verification against the repo

If subagents are unavailable, create and keep updating a Markdown plan in a writable temp location for the current environment, for example:

`<temp-dir>/state-architecture-review-plan.md`

Use this plan format:

```markdown
# State Architecture Review Plan

## Inventory
- [ ] Enumerate state subjects
- [ ] Mark owners, writers, readers, lifetime

## Flow Tracing
- [ ] Trace key read paths
- [ ] Trace key write paths

## Smell Detection
- [ ] Identify duplicated truth
- [ ] Identify circular dependencies
- [ ] Identify cross-layer leakage
- [ ] Identify over-centralization or over-fragmentation

## Refactor Model
- [ ] Define recommended state subjects
- [ ] Draft 3 Mermaid diagrams
- [ ] Summarize migration order
```

## Diagnosis Rubric

After triage, read [references/state-analysis.md](references/state-analysis.md) before writing the diagnosis.

That reference contains:

- the prioritized state-subject diagnosis questions
- the bad-smell catalog
- recommended target-state heuristics
- action mapping guidance for `保留 / 拆分 / 合并 / 下沉 / 上提 / 迁移到 URL / 迁移到表单状态 / 迁移到服务端缓存 / 改为派生 / 隔离副作用 / 删除`

## Output Format

Before drafting the final answer, read [references/report-and-diagrams.md](references/report-and-diagrams.md).

That reference defines:

- required section order
- brevity and evidence rules
- the exact responsibilities of 图1 / 图2 / 图3
- diagram size, labeling, and information-gain constraints

Before drawing the ASCII pre-map or Mermaid diagrams, also read [references/render-friendly-diagrams.md](references/render-friendly-diagrams.md).

That reference defines:

- terminal-safe ASCII fallback rules
- when to use ASCII Basic vs Unicode box drawing
- width, label, and alignment limits for agent-friendly output
- how to keep diagrams readable across terminals, markdown renderers, and agents

If you need concrete output patterns or feel the diagrams are getting too dense, read [references/examples.md](references/examples.md).

That reference contains:

- good vs bad ASCII pre-map examples
- good vs bad Mermaid examples
- subagent-gate examples for when to parallelize and when to stay local

## Recommendation Style

When concluding, make the decision actionable:

- say which state subjects are wrongly cut today
- say what the new ownership boundaries should be
- say what should stop depending on what
- say which duplication should disappear
- say the smallest migration order that reduces risk fastest

Prefer migration waves over big-bang rewrites:

1. stop new coupling
2. isolate side effects
3. consolidate or split state authorities
4. remove mirrored state
5. simplify reads and writes

For diagrams, prefer compatibility and clarity over decoration. The ASCII pre-map should optimize for terminal readability first, not visual flourish.

## Final Checks Before Responding

- Replace placeholders such as `[xxx]` with real state subjects from the repo, or say they could not be resolved.
- Make sure every major conclusion is backed by `证据` or explicitly downgraded to `推断` or `待确认`.
- Confirm that the recommended target model is the simplest viable boundary change, not a library-driven rewrite.
- Confirm that the diagrams remain readable even if Mermaid fails to render.
- Confirm that the 3 Mermaid diagrams add distinct information:
  - 图1 = current problematic paths
  - 图2 = target ownership map
  - 图3 = target end-to-end runtime flow
- Keep the report focused on the top issues. Do not expand into a whole-codebase architecture treatise unless the user explicitly asked for that depth.
- If the Subagent Gate did not clearly pass, do not force parallel review.

## Constraints

- Do not rewrite code unless the user explicitly asks for implementation.
- Do not hide uncertainty. If the repo is incomplete, state what is inferred.
- Do not fill the answer with generic state-management philosophy.
- Do not recommend XState, Redux, Zustand, Pinia, Context, or any other tool just because it is popular.
- Do not omit file references when the evidence is available.
- If you cannot verify the main recommendation from traced ownership and mutation paths, downgrade it to `推断`.
- If the review would require runtime-only knowledge, generated artifacts, hidden configs, or cross-repo context you cannot inspect, say so explicitly and stop short of overconfident architecture surgery.
- Tag uncertainty explicitly:
  - `证据`: directly supported by file:line references
  - `推断`: likely conclusion based on partial path tracing
  - `待确认`: blocked by missing code, runtime behavior, or hidden dependencies
- Never present `推断` or `待确认` as settled fact.
