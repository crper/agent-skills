# AGENTS

Repository instructions for contributors and coding agents working in `agent-skills`.

## Working Model

- Read the existing skill package before editing it.
- Prefer small, additive updates over rewrites.
- Keep solutions KISS and YAGNI.
- When a change is large enough to affect repository conventions, update this file together with the change.

## Skill Package Contract

Each public skill should live in `skills/<skill-name>/` and should keep related assets together:

```text
skills/<skill-name>/
├── SKILL.md
├── README.md
├── README.zh.md
├── agents/
│   └── openai.yaml
├── evals/
│   └── evals.json
├── references/
└── scripts/
```

Minimum bar:

- `SKILL.md` is required.
- Add bilingual README files when the skill is meant for public reuse.
- Add `evals/evals.json` for reusable prompts and regression intent.
- Add `agents/openai.yaml` when the skill benefits from a preset entry point.
- If `SKILL.md` references local files, those files must be committed in the same package.

## Documentation Rules

- Update the root `README.md` and `README.zh.md` when adding or removing a public skill.
- Keep `SKILL.md` focused on trigger rules, workflow, and behavior.
- Move bulky examples, schemas, or formatting rules into `references/` when that improves maintainability.
- Keep technical documentation in English unless a file is explicitly Chinese-facing.

## Validation

- Run the smallest useful validation for the changed surface only.
- For doc-only or metadata-only skill changes, validate file presence and JSON/YAML parsing instead of running unrelated full-repo checks.
- Prefer filtered checks that finish fast.
