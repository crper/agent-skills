# GitHub Fetch Release Notes

English | [简体中文](./README.zh.md)

Fetch GitHub Release / CHANGELOG updates through the local `gh auth login` session and return a stable JSON payload.

## Scope

- Designed for **small-batch queries**
- Recommended limit: **up to 10 repositories per run**
- Split larger workloads into multiple runs
- Uses light bounded concurrency with error-driven backoff by default; release lookups prefer batched `gh api graphql` prefetch and fall back to REST when needed, which fits cron / bot style small-batch polling better

## Project Structure

- `scripts/fetch_updates.py` — entry point
- `scripts/regression_check.py` — regression script for critical error paths and behavior checks
- `scripts/github_fetch_release_notes/cli.py` — CLI entry and argument parsing
- `scripts/github_fetch_release_notes/models.py` — config objects and result models
- `scripts/github_fetch_release_notes/service.py` — orchestration and multi-repo scheduling
- `scripts/github_fetch_release_notes/release_policy.py` — version comparison, prerelease filtering, and fallback policy
- `scripts/github_fetch_release_notes/gh_client.py` — environment checks, `gh api` execution, and concurrency backoff
- `scripts/github_fetch_release_notes/changelog.py` — CHANGELOG parsing
- `scripts/github_fetch_release_notes/output.py` — stable output schema and error semantics
- `references/output-schema.md` — strict field-level schema reference
- `agents/openai.yaml` — prompt preset for agent UIs
- `evals/evals.json` — minimal evaluation prompts for future regression checks

## Requirements

- `Python 3.8+`
- `GitHub CLI (gh)`

Installation guide: <https://github.com/cli/cli#installation>

```bash
gh auth login
```

## Usage

```bash
python3 ./skills/github-fetch-release-notes/scripts/fetch_updates.py owner/repo
python3 ./skills/github-fetch-release-notes/scripts/fetch_updates.py owner/repo --details
python3 ./skills/github-fetch-release-notes/scripts/fetch_updates.py owner/repo --json
```

## Output

Top-level fields:

- `schema_version`
- `generated_at`
- `query`
- `stats`
- `results`

Each `results[]` item now uses a nested structure:

- `input`
- `status`
- `selection`
- `versions`
- `signals`
- `warnings`
- `notes`
- `error`

When `--details` is enabled, detailed items appear in:

- `versions.latest.details`
- `versions.previous.details`

Field semantics:

- `selection.decision_code` provides a stable machine-friendly explanation for the final choice
- `selection.release_confirmed` indicates whether the selected latest version is confirmed by GitHub Releases
- `versions.latest` / `versions.previous` group version, publish time, prerelease state, summary quality (`summary_state`), highlights, and details
- `signals` carries supplemental reasoning signals such as `unreleased_present`, `changelog_stale`, and `stable_release_preferred`
- `warnings[].code` provides stable structured warning labels
- When recent Releases mix prereleases and stable releases, the skill prefers stable releases by default and only falls back to prereleases when no recent stable release is available

## Common `error.code` values

- `gh_auth_unavailable` — the current environment has no usable gh login state, common in cron or isolated runtimes
- `gh_not_logged_in` — explicit local login is missing in an interactive environment
- `gh_auth_invalid` — a gh login exists, but the token is invalid or expired

## Schema Reference

For strict field-level consumption, see [`references/output-schema.md`](./references/output-schema.md).
