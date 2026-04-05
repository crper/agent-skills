# Contributing

Thanks for contributing to `agent-skills`.

## Repository Structure

Each skill lives in its own directory under `skills/`:

```text
skills/
└── my-skill/
    ├── SKILL.md
    ├── README.md
    ├── README.zh.md
    ├── agents/
    │   └── openai.yaml
    ├── evals/
    │   └── evals.json
    ├── references/
    │   └── output-schema.md
    └── scripts/
```

## Minimum Requirements for a Skill

Every skill should include:

- `SKILL.md` — required
- `README.md` — recommended
- `README.zh.md` — recommended when Chinese users are expected
- `agents/openai.yaml` — optional, but useful for preset integration in agent UIs
- `evals/evals.json` — recommended for regression coverage
- `references/` — optional, but useful for output schema or operational notes

If `SKILL.md` links to local files under `references/`, `scripts/`, or `agents/`, those files must exist in the repository and stay in sync with the skill text.

## SKILL.md Guidelines

Your `SKILL.md` should clearly answer these questions:

1. What does the skill do?
2. When should the skill trigger?
3. What does the output look like?
4. What are the limits or assumptions?

Keep the description specific enough that an agent knows when to activate the skill.

Prefer keeping `SKILL.md` focused on discovery, trigger rules, and core workflow. Move heavier examples, report schemas, or diagram rules into `references/` when that improves long-term maintainability.

## Coding Guidelines

- Prefer deterministic scripts over prompt-only behavior
- Keep the implementation small and easy to maintain
- Use stable output contracts for anything intended for automation
- Avoid adding complexity for large-scale orchestration unless the skill truly needs it
- Keep code comments and technical documentation in English

## Testing

Before opening a pull request, make sure:

- The skill runs with its documented command
- `evals/evals.json` still reflects realistic user prompts
- Output shape remains stable for success and error cases
- New behavior is documented in the skill README or references if needed

## Documentation

For public-facing repositories:

- Use `README.md` as the default English document
- Use `README.zh.md` for Chinese documentation when helpful
- Put machine-facing details such as output schema into `references/`

## Adding a New Skill

1. Create `skills/<skill-name>/`
2. Add `SKILL.md`
3. Add README files as needed
4. Add scripts only when deterministic logic is required
5. Add minimal eval cases in `evals/evals.json`
6. Link to related skills when useful

## Pull Requests

Keep pull requests focused. If you change both behavior and documentation, make sure they stay consistent.

For security-sensitive issues, please follow [`SECURITY.md`](./SECURITY.md) instead of opening a detailed public issue.
