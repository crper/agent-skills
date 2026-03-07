# GitHub Fetch Release Notes

English | [简体中文](./README.zh.md)

Fetch GitHub Release / CHANGELOG updates through the local `gh auth login` session and return a stable JSON payload.

## Scope

- Designed for **small-batch queries**
- Recommended limit: **up to 10 repositories per run**
- Split larger workloads into multiple runs

## Project Structure

- `scripts/fetch_updates.py` — entry point
- `scripts/github_fetch_release_notes/cli.py` — main flow and argument parsing
- `scripts/github_fetch_release_notes/gh_client.py` — environment checks and `gh api` calls
- `scripts/github_fetch_release_notes/changelog.py` — CHANGELOG parsing
- `scripts/github_fetch_release_notes/output.py` — stable output schema and error semantics
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

Each `results[]` item includes:

- `input_repo`
- `repo`
- `status`
- `source`
- `error_code`
- `latest_version`
- `previous_version`
- `unreleased_present`
- `published_at`
- `highlights`
- `raw_url`
- `notes`

When `--details` is enabled, these fields are added:

- `latest_details`
- `previous_details`

Field semantics:

- `published_at` is only populated when a matching GitHub Release confirms the version
- If the result comes from `CHANGELOG` but the latest version is not confirmed by recent `Releases`, `published_at` stays `null` and `notes` explains that the changelog entry may be prewritten or pending release
- If a readable `CHANGELOG` is clearly behind a newer published GitHub Release, the skill falls back to `Releases` instead of reporting the stale changelog version as latest; this stale check prefers comparable stable releases before prereleases
- `Unreleased` is treated as a supplemental signal and does not, by itself, block fallback to fresher published Releases

## Common auth-related error codes

- `gh_auth_unavailable` — the current environment has no usable gh login state, common in cron or isolated runtimes
- `gh_not_logged_in` — explicit local login is missing in an interactive environment
- `gh_auth_invalid` — a gh login exists, but the token is invalid or expired

## Schema Reference

For strict field-level consumption, see [`references/output-schema.md`](./references/output-schema.md).
