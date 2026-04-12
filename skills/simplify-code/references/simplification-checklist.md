# Simplification Checklist

Use this as the main review checklist after scope is locked and the touched files have been re-read with fresh eyes.

## Priority order

Work in this order and stop as soon as the next step would require structural refactoring:

1. context and conventions
2. behavior boundaries
3. control flow
4. naming and intent
5. duplication and helper reuse
6. dead code and comments
7. light hardening

## 1. Context and conventions

- Read project guidance files when present, especially `CLAUDE.md`, `AGENTS.md`, lint rules, formatter config, and adjacent tests.
- Match the surrounding file before applying generic style preferences.
- Reuse existing utilities and established patterns before introducing anything new.

## 2. Behavior boundaries

Preserve these unless the user explicitly approves a change:

- exported signatures and public types
- return values, data shape, and error semantics
- side effects such as logging, telemetry, persistence, retries, and state writes
- platform assumptions, environment branching, and compatibility shims

## 3. Control flow

Good candidates:

- flatten deep nesting with guard clauses or early returns
- replace nested ternaries with clearer branches
- split dense pipelines into named intermediate steps when readability improves
- simplify repeated boolean checks and repeated property access

Avoid:

- rearranging side-effect order without strong evidence
- turning explicit domain steps into dense one-liners

## 4. Naming and intent

- Rename only when the new name is clearly better and the symbol is safely scoped.
- Prefer intention-revealing names over abbreviations.
- Keep nouns for data and verbs for actions when the language and codebase follow that style.
- Do not rename exported symbols unless the user asked for it.

## 5. Duplication and helper reuse

- Prefer using an existing helper over creating a new one.
- Apply the rule of three: do not introduce a shared abstraction for a one-off duplication.
- Extract a helper only when it reduces cognitive load and does not hide domain intent.
- If the cleanup would require consolidating logic across multiple files or call sites, treat it as a structural refactor and stop for approval.

## 6. Dead code and comments

- Delete unused locals, imports, branches, and scaffolding.
- Delete commented-out code instead of preserving it in place.
- Remove comments that merely restate obvious code.
- Keep comments that explain why, invariants, or non-obvious constraints.

## 7. Light hardening

Only patch issues that stay local and preserve behavior:

- missing null or bounds checks
- unchecked parsing assumptions
- swallowed local exceptions
- path, shell, SQL, or template string building that obviously trusts external input in the touched surface
- accidental secret exposure in logs or literals

If hardening requires redesigning control flow, auth, permissions, data access, or public behavior, stop and report it instead.
