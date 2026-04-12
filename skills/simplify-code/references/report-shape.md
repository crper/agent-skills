# Report Shape

Keep the final answer concise, evidence-based, and easy to scan.

## Auto-fix mode

Use this order:

1. `Scope` — exact files or functions touched
2. `Outcome` — one short sentence describing the cleanup pass
3. `Applied` — flat bullets for the real changes made
4. `Deferred` — only include items that were intentionally left alone
5. `Validation` — exactly what was run
6. `Behavior preserved` — the key contracts or assumptions that were intentionally kept stable
7. `Risk` — residual uncertainty, or say `none worth calling out`

Example:

```text
Scope
- src/parser.ts

Outcome
Simplified the touched parser code without changing its public behavior.

Applied
- Removed a redundant temporary object in `parseEntry`.
- Reused the existing `normalizePath` helper instead of a local duplicate.
- Flattened two nested guards into one early-return path.

Deferred
- Left the exported `parseAll` signature unchanged; collapsing it would change a public API.

Validation
- Ran `pnpm vitest src/parser.test.ts`
- Ran `pnpm eslint src/parser.ts`

Behavior preserved
- Kept the exported `parseAll` API and current error messages unchanged.

Risk
- None worth calling out beyond the skipped full-repo test suite.
```

## Review-only mode

Lead with findings ordered by risk. Keep each finding short and use this shape:

- `Severity`
- `Finding`
- `Evidence`
- `Impact`
- `Recommendation`

Do not pad the report with generic best practices. Tie recommendations to the actual code surface under review.

## Tone rules

- Match the user's language.
- Prefer concrete code nouns over abstractions.
- Distinguish applied fixes from deferred ideas.
- If validation was partial, say exactly what was and was not checked.
- If nothing changed, say the code was already clean enough and mention the checks performed.
