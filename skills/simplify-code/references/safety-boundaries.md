# Safety Boundaries

Use this checklist before changing code. `simplify-code` defaults to strict auto-fix, but only inside low-risk boundaries.

## Scope lock and budget

- Stay inside the user-provided files, snippet, or resolved git scope.
- Exclude generated, minified, vendored, and other low-signal files unless the user explicitly includes them.
- When working from an existing patch, keep cleanup additions small. A good default is no more than about 20 percent extra diff beyond the original requested change.
- If a useful cleanup would exceed that budget, list it as deferred instead of silently broadening the patch.

## Safe to auto-fix

These are usually safe when the behavior boundary is already clear from code, types, tests, or direct callers:

- remove dead locals, dead branches, unreachable returns, and redundant temporary variables
- collapse duplicated local logic when both paths are semantically identical
- replace a hand-rolled local helper with an existing project utility after verifying the semantics match
- tighten guard clauses or early returns without changing externally visible behavior
- simplify repeated conditionals, repeated property lookups, or repeated pure computations
- rename private locals or private helper functions when all direct references are updated together
- delete wrappers that only forward arguments and add no meaningful boundary
- replace broad reads or repeated scans with a narrower local equivalent when the output is unchanged
- add light local hardening such as null checks, length checks, or clearer fallbacks when they preserve current behavior

## Safe only with stronger evidence

Apply only when the intent is well proven by tests, callers, or highly local context:

- extract a new helper inside the same file
- merge two nearby functions into one simpler implementation
- reduce visibility of a symbol that is clearly private
- simplify condition ordering in code that has side effects
- remove caching or memoization that appears redundant
- change iteration structure for performance or clarity
- tighten error handling while keeping the same contract

If you cannot prove the change is safe quickly, defer it.

## Stop and report instead of auto-fixing

Do not auto-fix these without explicit user approval:

- public function signatures, exported types, CLI flags, API payloads, or storage formats
- auth, permissions, secrets handling, encryption, rate limits, or tenancy boundaries
- concurrency, locking, retries, background jobs, cache invalidation, or resource lifetimes
- persistence, migrations, SQL semantics, transaction behavior, or filesystem layout
- telemetry, audit logging, billing logic, feature flags, or compliance-sensitive paths
- framework wiring, build config, CI, deployment config, or cross-platform compatibility code
- sync-to-async or async-to-sync changes
- removing or collapsing domain-specific steps that currently make intent explicit
- changing error propagation, error messages, or user-facing messages that callers may rely on
- removing logging, guards, retries, or compatibility branches that may encode operational intent
- large cross-directory refactors or introducing a new abstraction layer
- removing tests or weakening assertions to make the cleanup pass

## Verification gate

- Prefer a clean baseline. If targeted tests or checks for the touched surface are already failing before the cleanup pass, do not stack broad simplifications on top.
- If the only possible verification is weak and the proposed edits are more than cosmetic, switch to review-only or ask before proceeding.
- If checks cannot run, say exactly what was skipped and why.

## Review-only triggers

Switch to review-only output when:

- the user says `report only`, `review only`, `no edits`, `just findings`, or equivalent
- the requested cleanup is really a redesign, rewrite, or ownership change
- the resolved scope is broad enough that safe validation is unlikely, for example more than about 8-12 meaningful source files or roughly 400 changed lines
- multiple plausible simplifications exist and the choice changes architecture
- the changed surface is too broad to validate confidently
- the repo has conflicting local edits that make safe automated cleanup unclear
- the useful next step is writing characterization tests before any cleanup

## Escalation rule

When in doubt, preserve behavior and stop early. A shorter report is better than a clever refactor that quietly changes semantics.
