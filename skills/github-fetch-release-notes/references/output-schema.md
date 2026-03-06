# Output Schema

This skill returns a stable JSON payload.

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

Each result item includes:

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

Field notes:

- `published_at`: official publish time confirmed by a matching GitHub Release; otherwise `null`
- `notes`: may include hints such as `发现 Unreleased 分段`, `已用 GitHub Release 确认该版本发布时间`, or `CHANGELOG 最新版本尚未在最近的 GitHub Releases 中确认，可能是预写或待发布`

When `--details` is enabled, each item also includes:

- `latest_details`
- `previous_details`

## Status Values

- `ok`
- `no_data`
- `error`

## Source Values

- `changelog`
- `releases`
- `none`
- `error`

## Common `error_code` Values

- `invalid_repo`
- `gh_not_installed`
- `gh_auth_unavailable`
- `gh_not_logged_in`
- `gh_auth_invalid`
- `repo_not_found_or_no_access`
- `rate_limited`
- `permission_denied`
- `request_timeout`
- `gh_api_failed`
- `runtime_error`

## Minimal Success Example

```json
{
  "schema_version": "github-fetch-release-notes/v2",
  "generated_at": "2026-03-06T17:42:48Z",
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
      "input_repo": "openclaw/openclaw",
      "repo": "openclaw/openclaw",
      "status": "ok",
      "source": "changelog",
      "error_code": null,
      "latest_version": "2026.3.3",
      "previous_version": "2026.3.2",
      "unreleased_present": true,
      "published_at": null,
      "highlights": ["..."],
      "raw_url": "https://github.com/openclaw/openclaw/blob/main/CHANGELOG.md",
      "notes": [
        "发现 Unreleased 分段",
        "CHANGELOG 最新版本尚未在最近的 GitHub Releases 中确认，可能是预写或待发布"
      ]
    }
  ]
}
```

## Minimal Error Example

```json
{
  "results": [
    {
      "input_repo": "badrepo",
      "repo": null,
      "status": "error",
      "source": "error",
      "error_code": "invalid_repo",
      "latest_version": null,
      "previous_version": null,
      "unreleased_present": false,
      "published_at": null,
      "highlights": [],
      "raw_url": null,
      "notes": [
        "Repository input is invalid."
      ]
    }
  ]
}
```
