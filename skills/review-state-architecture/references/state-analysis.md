# State Analysis Reference

Use this reference after triage and before writing the diagnosis.

## Contents

- Diagnosis rubric
- Bad-smell catalog
- Target-model heuristics
- Action mapping

## Diagnosis Rubric

Evaluate every prioritized state subject against these questions:

1. Is the responsibility singular and easy to name?
2. Is the owner the nearest stable boundary that actually needs to own it?
3. Is this a true source of truth, or just cached, derived, or mirrored data?
4. Are reads simple while writes are scattered everywhere?
5. Does this state mix UI concerns, domain rules, async lifecycle, and IO details in one place?
6. Does it create hidden temporal coupling, where update order matters too much?
7. Is the same business entity stored in multiple places?
8. Are peer modules writing into each other, directly or indirectly?
9. Are there circular imports or circular event dependencies?
10. Would a new engineer know where to change this behavior without reading half the app?

## Bad-Smell Catalog

Common smells:

- unclear ownership
- duplicated source of truth
- mirrored state used as convenience
- god store or god context
- over-sharded tiny stores with unclear boundaries
- bidirectional dependencies
- cross-layer writes
- domain state mixed with ephemeral UI state
- server state copied into client state without need
- selectors or getters hiding business side effects
- effects deciding business rules
- transition chains that require remembering update order
- actions or events with wide fan-out and unpredictable impact
- naming that reflects implementation instead of business meaning

For each major smell, explain:

- why it is a problem
- what symptom it creates for developers
- which modules participate
- whether the fix is split, merge, move, derive, isolate, or delete

## Target-Model Heuristics

Use these heuristics when proposing the refactor:

- Keep state local when only one component or screen owns it.
- Use URL state for shareable, bookmarkable, navigation-relevant values.
- Use form state for dirty values, validation, and submission lifecycle.
- Use server or cache state for backend-owned data and async fetch lifecycle.
- Use shared domain or app state only for truly client-owned, cross-screen business state.
- Use workflow or state-machine style modeling only when transitions are explicit, finite, and important.
- Prefer derivation over storing redundant computed data.
- Move side effects to explicit boundaries instead of hiding them inside selectors or state containers.

## Action Mapping

When reviewing the current split, classify each subject with one action:

- `保留`
- `拆分`
- `合并`
- `下沉`
- `上提`
- `迁移到 URL`
- `迁移到表单状态`
- `迁移到服务端缓存`
- `改为派生`
- `隔离副作用`
- `删除`

Choose the smallest action that removes the main smell without widening the architecture more than necessary.
