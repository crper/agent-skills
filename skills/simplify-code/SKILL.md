---
name: simplify-code
description: Simplify recently changed code while preserving behavior, public contracts, side effects, data shape, and project conventions. Use when the user asks to simplify code, clean up a patch, reduce duplication or nesting, improve naming or readability, remove dead code, tighten a small abstraction, or run a post-implementation cleanup and light hardening pass on touched files. Default to a strict auto-fix pass for low-risk issues within a small diff budget; if the user asks for a report only, no edits, or the work crosses into structural refactoring, switch to review-only output or stop for approval.
---

# Simplify Code

Simplify the requested code without changing what it does. Optimize for smaller, clearer, more maintainable code that still matches existing behavior, interfaces, platform assumptions, and repository conventions.

## Inputs Needed

Use the narrowest concrete artifact available:

- a pasted snippet
- one or more file paths
- a directory
- an explicit diff command
- the current git diff when the user asks for a cleanup pass without naming files

If no concrete scope exists, do not guess across the whole repo. Ask for scope or state the narrow assumption you are making.

## Scope Resolution

Resolve scope in this order:

1. explicit files, directories, snippets, or diff commands from the user
2. the current git diff when the user asks for a cleanup pass without naming files
3. tracked + untracked local changes when inside a git repo and step 2 is empty

Exclude generated or low-signal files unless the user explicitly includes them:

- lockfiles
- generated code
- minified bundles
- build outputs
- vendored code

If the task is not in a git repo and the user did not provide concrete files or snippets, stop and ask for scope instead of wandering.

## Operating Contract

- User intent overrides the default mode. If the user asks for a report only, no edits, or planning, do not modify files.
- Read the existing code and adjacent helpers before changing anything.
- Preserve behavior, public APIs, side effects, data shape, logs that may be operationally relevant, and established platform compatibility unless the user explicitly approves a change.
- Prefer local, reversible simplifications over architectural rewrites.
- Match the project's naming, error-handling, testing, and formatting conventions.
- Keep the cleanup diff small. When working from an existing diff, do not grow the patch by more than about 20 percent unless the user explicitly asks for deeper refactoring.
- Stay single-threaded by default. Only delegate when the active environment explicitly allows it and the scope is broad enough to justify the coordination cost.
- Reply in the user's language.

## Workflow

```text
[Scope] -> [Mode] -> [Local Context] -> [Risk Triage] -> [Safe Simplification] -> [Validation] -> [Report]
```

## 1. Choose the mode

Default to `strict auto-fix`.

Switch to `review-only` when any of these are true:

- the user asks for a report, findings, review, or recommendations only
- the requested change is obviously cross-cutting or high risk
- the resolved scope is broad enough that safe validation is unlikely, for example more than about 8-12 meaningful source files or roughly 400 changed lines
- validation is too weak to support direct edits confidently
- the repo state is too unclear to separate safe edits from risky ones

## 2. Build the smallest useful context

- Read the full touched file, not just a diff hunk, before editing.
- Inspect adjacent helpers, shared utilities, types, tests, and direct callers when they define the behavior boundary.
- Reuse existing utilities before inventing new helpers.
- Keep the review surface tight. The goal is to simplify the requested code, not to wander into unrelated cleanup.

## 3. Re-read with fresh eyes

Before editing, re-read the touched code as if you did not write it.

Ask:

- what reads as confusing or overbuilt now that the full solution is visible
- whether any debug scaffolding, temporary names, or iteration leftovers remain
- whether a clearer expression exists without changing contracts
- whether the touched code introduced obvious local hardening gaps such as unchecked external input, brittle assumptions, or swallowed errors

## 4. Triage before changing code

Read [references/safety-boundaries.md](references/safety-boundaries.md) and [references/simplification-checklist.md](references/simplification-checklist.md) before deciding what to auto-fix and what to defer.

Focus on these candidate improvements:

- duplicated or near-duplicated local logic
- dead branches, dead variables, redundant wrappers, and no-op abstractions
- unnecessarily deep nesting or repeated condition checks
- poor naming that obscures intent
- repeated work that can be removed without semantic change
- hand-rolled logic that should use an existing local utility
- obvious light hardening such as missing guard clauses or unchecked local assumptions

## 5. Apply only low-risk simplifications

Make the smallest change that improves clarity.

- Favor deleting code over introducing new abstractions.
- Favor existing helpers over new helpers.
- Favor file-local refactors over cross-package moves.
- Stop before changing signatures, lifetimes, ownership boundaries, persistence behavior, auth logic, permission logic, concurrency behavior, or externally visible error semantics.
- Treat structural edits as a stop hook: extracting shared helpers across call sites, changing visibility, changing sync/async boundaries, or removing logging/retries/guards requires explicit user approval.

If a promising cleanup crosses those boundaries, do not force it through. Keep it in the report as a deferred recommendation.

## 6. Validate the changed surface

Run the smallest useful validation for what changed:

- targeted tests for touched modules when available
- focused type checks, linting, or build checks when they cover the edited surface
- a narrow command or reproduction path when the change is behavior-sensitive

Do not default to unrelated full-repo checks when a smaller command gives enough confidence. If meaningful validation is not possible, say so explicitly.

If baseline checks for the touched surface are already failing before the cleanup pass, do not stack speculative simplifications on top. Report the baseline failure and keep edits minimal or switch to review-only.

## 7. Report clearly

Read [references/report-shape.md](references/report-shape.md) before writing the final answer.

At minimum, report:

- what scope was touched
- what was simplified
- what was intentionally deferred
- what validation ran
- what behavior assumptions were preserved
- what residual risk remains, if any

If nothing needed changing, say the code was already reasonably clean and explain what you checked.
