# Output Schema

This skill returns a stable JSON payload optimized for both script consumption and LLM parsing.

## Top-Level Fields

- `schema_version`
- `generated_at`
- `query`
- `stats`
- `results`

## `query`

- `input_repos`: original repository inputs
- `release_limit`: maximum number of releases fetched
- `detail_limit`: maximum number of detail items kept per version
- `details_included`: whether detailed items are included
- `output_mode`: currently `stable_json`

## `stats`

- `total`: total repositories requested
- `ok`: repositories resolved through changelog or releases
- `no_data`: repositories that exist but expose no usable changelog or releases
- `error`: repositories that failed validation or fetching

## `results[]`

Each result item now has a nested structure:

- `input`
- `status`
- `selection`
- `versions`
- `signals`
- `warnings`
- `notes`
- `error`

### `input`

- `raw`: original repository input
- `normalized`: normalized `owner/repo` when available, otherwise `null`
- `repo_url`: canonical repository URL when normalization succeeds

### `status`

- `ok`
- `no_data`
- `error`

### `selection`

- `source`: `changelog` / `releases` / `none` / `error`
- `decision_code`: stable machine-friendly reason for the final selection
- `selected_url`: selected changelog URL or release URL when `source` is `changelog` or `releases`; otherwise `null`
- `release_confirmed`: whether the selected latest version has GitHub Release confirmation

Common `decision_code` values include:

- `changelog_selected_release_confirmed`
- `changelog_selected_release_unconfirmed`
- `changelog_selected_without_releases`
- `changelog_selected_release_probe_failed`
- `changelog_selected_version_unparsed`
- `releases_selected`
- `releases_selected_stale_changelog`
- `releases_selected_changelog_unavailable`
- `no_changelog_or_releases`
- `invalid_input`
- `fetch_failed`
- `unexpected_exception`

### `versions`

- `latest`
- `previous`

Each version object may include:

- `version`
- `published_at` (latest only)
- `is_prerelease`
- `highlights` (latest only)
- `details` (only when `details_included = true`)

### `signals`

- `unreleased_present`: whether changelog still contains an `Unreleased` section
- `changelog_stale`: whether changelog existed but was rejected in favor of newer releases
- `stable_release_preferred`: whether prereleases were present but the final selection preferred the stable track

### `warnings`

Structured warning objects:

- `code`
- `message`

Common warning codes include:

- `unreleased_present`
- `version_title_unparsed`
- `release_confirmation_missing`
- `no_releases_for_confirmation`
- `release_probe_failed`
- `stable_release_preferred`
- `release_body_empty`
- `release_body_sparse`
- `changelog_fetch_failed`
- `changelog_timeout`
- `changelog_rate_limited`

### `notes`

- Human-readable supplemental notes
- Useful for direct display or prompt context
- Not intended to be the primary machine decision surface; prefer `selection.decision_code` and `warnings[].code`

### `error`

- `null` when `status != error`
- otherwise includes:
  - `code`
  - `message`

## Minimal Success Example

```json
{
  "schema_version": "github-fetch-release-notes/v3",
  "generated_at": "2026-03-10T10:20:30Z",
  "query": {
    "input_repos": ["openclaw/openclaw"],
    "release_limit": 2,
    "detail_limit": 8,
    "details_included": false,
    "output_mode": "stable_json"
  },
  "stats": {
    "total": 1,
    "ok": 1,
    "no_data": 0,
    "error": 0
  },
  "results": [
    {
      "input": {
        "raw": "openclaw/openclaw",
        "normalized": "openclaw/openclaw"
      },
      "status": "ok",
      "selection": {
        "source": "changelog",
        "decision_code": "changelog_selected_release_confirmed",
        "selected_url": "https://github.com/openclaw/openclaw/blob/main/CHANGELOG.md",
        "release_confirmed": true
      },
      "versions": {
        "latest": {
          "version": "2026.3.8",
          "published_at": "2026-03-09T07:49:27Z",
          "is_prerelease": null,
          "highlights": ["..."]
        },
        "previous": {
          "version": "2026.3.7",
          "is_prerelease": null
        }
      },
      "signals": {
        "unreleased_present": true,
        "changelog_stale": false,
        "stable_release_preferred": false
      },
      "warnings": [
        {
          "code": "unreleased_present",
          "message": "发现 Unreleased 分段"
        }
      ],
      "notes": [
        "发现 Unreleased 分段",
        "已用 GitHub Release 确认该版本发布时间"
      ],
      "error": null
    }
  ]
}
```

## Minimal Error Example

```json
{
  "results": [
    {
      "input": {
        "raw": "badrepo",
        "normalized": null
      },
      "status": "error",
      "selection": {
        "source": "error",
        "decision_code": "invalid_input",
        "selected_url": null,
        "release_confirmed": null
      },
      "versions": {
        "latest": null,
        "previous": null
      },
      "signals": {
        "unreleased_present": false,
        "changelog_stale": false,
        "stable_release_preferred": false
      },
      "warnings": [],
      "notes": [
        "仓库名不合法：格式应为 owner/repo，或完整 GitHub 仓库 URL"
      ],
      "error": {
        "code": "invalid_repo",
        "message": "仓库名不合法：格式应为 owner/repo，或完整 GitHub 仓库 URL"
      }
    }
  ]
}
```
