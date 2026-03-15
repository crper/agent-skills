#!/usr/bin/env python3

import argparse
import json
import re
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple


SCHEMA_VERSION = "chrome-web-store-submission/extension-facts/v1"
MAX_FILE_BYTES = 512_000
MAX_EVIDENCE_PER_KEY = 3
IGNORED_DIRS = {
    ".git",
    "node_modules",
    ".turbo",
    ".next",
    "coverage",
    "dist-assets",
}
BUILD_ARTIFACT_DIRS = {
    ".output",
    ".plasmo",
    "dist",
    "build",
}
CODE_SUFFIXES = {
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
    ".vue",
    ".svelte",
    ".mjs",
    ".cjs",
    ".mts",
    ".cts",
    ".html",
}
SOURCE_MANIFEST_CANDIDATES = (
    "manifest.json",
    "src/manifest.json",
    "public/manifest.json",
)
BUILD_MANIFEST_CANDIDATES = (
    "dist/manifest.json",
    "build/manifest.json",
    ".output/chrome-mv3/manifest.json",
    ".output/chrome-mv3-dev/manifest.json",
    ".plasmo/chrome-mv3-dev/manifest.json",
    ".plasmo/build/chrome-mv3-prod/manifest.json",
)
MANIFEST_CANDIDATES = SOURCE_MANIFEST_CANDIDATES + BUILD_MANIFEST_CANDIDATES
WXT_CANDIDATES = (
    "wxt.config.ts",
    "wxt.config.js",
    "wxt.config.mjs",
    "wxt.config.mts",
)

PERMISSION_PATTERNS: Dict[str, Sequence[str]] = {
    "storage": (r"\b(?:chrome|browser)\.storage\b", r"\blocalStorage\b", r"\bindexedDB\b"),
    "contextMenus": (r"\b(?:chrome|browser)\.contextMenus\b",),
    "sidePanel": (r"\b(?:chrome|browser)\.sidePanel\b",),
    "activeTab": (r"\bactiveTab\b",),
    "tabs": (r"\b(?:chrome|browser)\.tabs\b",),
    "scripting": (r"\b(?:chrome|browser)\.scripting\b",),
    "downloads": (r"\b(?:chrome|browser)\.downloads\b",),
    "alarms": (r"\b(?:chrome|browser)\.alarms\b",),
    "notifications": (r"\b(?:chrome|browser)\.notifications\b",),
    "identity": (r"\b(?:chrome|browser)\.identity\b",),
    "cookies": (r"\b(?:chrome|browser)\.cookies\b",),
    "declarativeNetRequest": (r"\b(?:chrome|browser)\.declarativeNetRequest\b",),
    "webRequest": (r"\b(?:chrome|browser)\.webRequest\b",),
}
NETWORK_PATTERNS = (
    r"\bfetch\s*\(",
    r"\bXMLHttpRequest\b",
    r"\bWebSocket\b",
    r"\bnavigator\.sendBeacon\b",
    r"\bEventSource\b",
)
LOCAL_STORAGE_PATTERNS = (
    r"\b(?:chrome|browser)\.storage\b",
    r"\blocalStorage\b",
    r"\bsessionStorage\b",
    r"\bindexedDB\b",
    r"\bstorage\.defineItem(?:<[^>]+>)?\s*\(\s*['\"`]local:",
)
REMOTE_CODE_PATTERNS = {
    "eval_like": (
        r"\beval\s*\(",
        r"\bnew\s+Function\s*\(",
    ),
    "remote_script": (
        r"importScripts\s*\(\s*['\"]https?://",
        r"<script[^>]+src=['\"]https?://",
        r"import\s*\(\s*['\"]https?://",
    ),
}
STRING_RE = re.compile(r"['\"]([^'\"]+)['\"]")


def read_text(path: Path) -> Optional[str]:
    try:
        if path.stat().st_size > MAX_FILE_BYTES:
            return None
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None


def read_json(path: Path) -> Optional[Dict[str, object]]:
    text = read_text(path)
    if text is None:
        return None
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return None
    return payload if isinstance(payload, dict) else None


def relative_to(root: Path, path: Optional[Path]) -> Optional[str]:
    if path is None:
        return None
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def find_first_existing(root: Path, candidates: Sequence[str]) -> Optional[Path]:
    for candidate in candidates:
        path = root / candidate
        if path.exists() and path.is_file():
            return path
    return None


def discover_manifest(root: Path) -> Optional[Path]:
    manifest_path = find_first_existing(root, MANIFEST_CANDIDATES)
    if manifest_path is not None:
        return manifest_path

    fallback: List[Path] = []
    for path in root.rglob("manifest.json"):
        if is_ignored(path):
            continue
        fallback.append(path)
    if not fallback:
        return None
    fallback.sort(key=lambda item: (len(item.parts), str(item)))
    return fallback[0]


def is_build_manifest_path(root: Path, path: Optional[Path]) -> bool:
    relative_path = relative_to(root, path)
    return bool(relative_path and relative_path in BUILD_MANIFEST_CANDIDATES)


def is_ignored(path: Path) -> bool:
    return any(part in IGNORED_DIRS for part in path.parts)


def is_build_artifact_code_path(path: Path) -> bool:
    return any(part in BUILD_ARTIFACT_DIRS for part in path.parts)


def iter_code_files(root: Path) -> Iterable[Path]:
    source_files: List[Path] = []
    build_files: List[Path] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if is_ignored(path):
            continue
        if path.suffix.lower() not in CODE_SUFFIXES:
            continue
        if is_build_artifact_code_path(path):
            build_files.append(path)
        else:
            source_files.append(path)

    for path in source_files or build_files:
        yield path


def parse_string_array_from_text(text: str, key: str) -> List[str]:
    match = re.search(rf"{re.escape(key)}\s*:\s*\[(.*?)\]", text, re.DOTALL)
    if not match:
        return []
    values: List[str] = []
    seen = set()
    for candidate in STRING_RE.findall(match.group(1)):
        if candidate not in seen:
            seen.add(candidate)
            values.append(candidate)
    return values


def parse_string_from_text(text: str, key: str) -> Optional[str]:
    match = re.search(rf"{re.escape(key)}\s*:\s*['\"]([^'\"]+)['\"]", text)
    if not match:
        return None
    return match.group(1)


def parse_wxt_config(path: Optional[Path]) -> Dict[str, object]:
    if path is None:
        return {}
    text = read_text(path)
    if text is None:
        return {}
    return {
        "name": parse_string_from_text(text, "name"),
        "version": parse_string_from_text(text, "version"),
        "permissions": parse_string_array_from_text(text, "permissions"),
        "host_permissions": parse_string_array_from_text(text, "host_permissions"),
        "optional_permissions": parse_string_array_from_text(text, "optional_permissions"),
        "optional_host_permissions": parse_string_array_from_text(text, "optional_host_permissions"),
        "manifest_version": 3,
        "action_present": bool(re.search(r"\baction\s*:", text)),
        "side_panel_present": bool(re.search(r"\bside_panel\s*:", text)),
    }


def ensure_string_list(value: object) -> List[str]:
    if not isinstance(value, list):
        return []
    result: List[str] = []
    seen = set()
    for item in value:
        if isinstance(item, str) and item not in seen:
            seen.add(item)
            result.append(item)
    return result


def manifest_permissions(manifest: Dict[str, object], fallback: Dict[str, object], key: str, *, prefer_fallback: bool = False) -> List[str]:
    if prefer_fallback:
        raw = fallback.get(key)
        if isinstance(raw, list) and raw:
            return raw
    values = ensure_string_list(manifest.get(key))
    if values:
        return values
    raw = fallback.get(key)
    return raw if isinstance(raw, list) else []


def primary_string_value(
    manifest: Dict[str, object],
    fallback: Dict[str, object],
    key: str,
    *,
    prefer_fallback: bool = False,
) -> Optional[str]:
    fallback_value = fallback.get(key)
    manifest_value = manifest.get(key)
    if prefer_fallback and isinstance(fallback_value, str) and fallback_value:
        return fallback_value
    if isinstance(manifest_value, str) and manifest_value:
        return manifest_value
    if isinstance(fallback_value, str) and fallback_value:
        return fallback_value
    return None


def build_snippet(lines: Sequence[str], line_index: int) -> str:
    return lines[line_index].strip()[:160]


def find_matches(path: Path, patterns: Sequence[str], root: Path, limit: int = MAX_EVIDENCE_PER_KEY) -> List[Dict[str, object]]:
    text = read_text(path)
    if text is None:
        return []
    lines = text.splitlines()
    results: List[Dict[str, object]] = []
    for pattern in patterns:
        regex = re.compile(pattern)
        for line_index, line in enumerate(lines):
            if regex.search(line):
                results.append(
                    {
                        "file": relative_to(root, path),
                        "line": line_index + 1,
                        "snippet": build_snippet(lines, line_index),
                    }
                )
                if len(results) >= limit:
                    return results
    return results


def collect_evidence(
    root: Path,
    permissions_to_scan: Sequence[str],
) -> Tuple[Dict[str, List[Dict[str, object]]], List[Dict[str, object]], List[Dict[str, object]], List[Dict[str, object]]]:
    tracked_permissions = [permission for permission in permissions_to_scan if permission in PERMISSION_PATTERNS]
    permission_evidence: Dict[str, List[Dict[str, object]]] = {key: [] for key in tracked_permissions}
    network_evidence: List[Dict[str, object]] = []
    local_storage_evidence: List[Dict[str, object]] = []
    remote_code_evidence: List[Dict[str, object]] = []

    for path in iter_code_files(root):
        text = read_text(path)
        if text is None:
            continue
        for permission in tracked_permissions:
            patterns = PERMISSION_PATTERNS[permission]
            if len(permission_evidence[permission]) >= MAX_EVIDENCE_PER_KEY:
                continue
            matches = find_matches(path, patterns, root, MAX_EVIDENCE_PER_KEY - len(permission_evidence[permission]))
            if matches:
                permission_evidence[permission].extend(matches)

        if len(network_evidence) < MAX_EVIDENCE_PER_KEY:
            network_evidence.extend(find_matches(path, NETWORK_PATTERNS, root, MAX_EVIDENCE_PER_KEY - len(network_evidence)))
        if len(local_storage_evidence) < MAX_EVIDENCE_PER_KEY:
            local_storage_evidence.extend(find_matches(path, LOCAL_STORAGE_PATTERNS, root, MAX_EVIDENCE_PER_KEY - len(local_storage_evidence)))
        for patterns in REMOTE_CODE_PATTERNS.values():
            if len(remote_code_evidence) >= MAX_EVIDENCE_PER_KEY:
                break
            remote_code_evidence.extend(find_matches(path, patterns, root, MAX_EVIDENCE_PER_KEY - len(remote_code_evidence)))

    permission_evidence = {key: value for key, value in permission_evidence.items() if value}
    return permission_evidence, network_evidence, local_storage_evidence, remote_code_evidence


def entrypoint_exists(root: Path, name: str) -> bool:
    entrypoints_root = root / "src" / "entrypoints"
    if not entrypoints_root.exists():
        return False

    direct_candidates = [
        entrypoints_root / f"{name}{suffix}"
        for suffix in (".ts", ".tsx", ".js", ".jsx", ".mjs", ".mts", ".cts", ".cjs")
    ]
    if any(candidate.is_file() for candidate in direct_candidates):
        return True

    directory_candidate = entrypoints_root / name
    return directory_candidate.exists()


def build_assessments(
    host_permissions: List[str],
    network_evidence: List[Dict[str, object]],
    local_storage_evidence: List[Dict[str, object]],
    remote_code_evidence: List[Dict[str, object]],
) -> Dict[str, Dict[str, object]]:
    remote_code_status = "possible" if remote_code_evidence else "no"
    data_transmission_possible = bool(host_permissions or network_evidence)
    local_only_status = "unknown"
    if local_storage_evidence and not data_transmission_possible:
        local_only_status = "yes"
    elif data_transmission_possible:
        local_only_status = "no"

    return {
        "remote_code": {
            "status": remote_code_status,
            "reason": "Found eval-like or remote script loading patterns." if remote_code_evidence else "No eval-like or remote script loading patterns were found in the inspected files.",
            "evidence": remote_code_evidence,
        },
        "data_transmission": {
            "status": "possible" if data_transmission_possible else "no",
            "reason": "Found host permissions or network call patterns." if data_transmission_possible else "No host permissions or network call patterns were found in the inspected files.",
            "evidence": network_evidence,
        },
        "data_sale_or_sharing": {
            "status": "unknown",
            "reason": "Selling or sharing data usually cannot be proven from repo inspection alone.",
            "evidence": [],
        },
        "local_storage_only": {
            "status": local_only_status,
            "reason": "Local storage patterns were found without network activity." if local_only_status == "yes" else "Local-only storage cannot be guaranteed from the current evidence." if local_only_status == "unknown" else "Network-related behavior was found, so local-only claims are unsafe.",
            "evidence": local_storage_evidence,
        },
    }


def build_payload(root: Path) -> Dict[str, object]:
    manifest_path = discover_manifest(root)
    package_json_path = find_first_existing(root, ("package.json",))
    wxt_config_path = find_first_existing(root, WXT_CANDIDATES)

    manifest = read_json(manifest_path) if manifest_path else {}
    package_json = read_json(package_json_path) if package_json_path else {}
    wxt_config = parse_wxt_config(wxt_config_path)
    prefer_wxt_config = bool(wxt_config and is_build_manifest_path(root, manifest_path))

    if not manifest and not wxt_config:
        return {
            "schema_version": SCHEMA_VERSION,
            "status": "error",
            "project_root": str(root.resolve()),
            "sources": {
                "manifest": None,
                "package_json": None,
                "wxt_config": None,
            },
            "errors": ["No extension manifest.json or wxt.config.* was found in the inspected project root."],
        }

    requested_permissions = manifest_permissions(manifest, wxt_config, "permissions", prefer_fallback=prefer_wxt_config)
    host_permissions = manifest_permissions(manifest, wxt_config, "host_permissions", prefer_fallback=prefer_wxt_config)
    optional_permissions = manifest_permissions(manifest, wxt_config, "optional_permissions", prefer_fallback=prefer_wxt_config)
    optional_host_permissions = manifest_permissions(manifest, wxt_config, "optional_host_permissions", prefer_fallback=prefer_wxt_config)

    permissions_to_scan = requested_permissions + [permission for permission in optional_permissions if permission not in requested_permissions]
    permission_evidence, network_evidence, local_storage_evidence, remote_code_evidence = collect_evidence(root, permissions_to_scan)
    assessments = build_assessments(host_permissions, network_evidence, local_storage_evidence, remote_code_evidence)
    background_present = bool(isinstance(manifest.get("background"), dict) and manifest.get("background")) or entrypoint_exists(root, "background")
    content_scripts_present = bool(isinstance(manifest.get("content_scripts"), list) and manifest.get("content_scripts"))
    side_panel_present = (
        bool(isinstance(manifest.get("side_panel"), dict) and manifest.get("side_panel"))
        or bool(wxt_config.get("side_panel_present"))
        or entrypoint_exists(root, "sidepanel")
    )
    manifest_version = manifest.get("manifest_version")
    if manifest_version is None and wxt_config:
        manifest_version = wxt_config.get("manifest_version")

    ambiguities: List[str] = []
    if assessments["remote_code"]["status"] == "possible":
        ambiguities.append("Remote-code safety needs manual confirmation because eval-like or remote script patterns were found.")
    if assessments["data_transmission"]["status"] == "possible":
        ambiguities.append("Data may be transmitted because host permissions or network call patterns were found.")
    if assessments["data_sale_or_sharing"]["status"] == "unknown":
        ambiguities.append("Selling or sharing data cannot be confirmed from repo inspection alone.")

    return {
        "schema_version": SCHEMA_VERSION,
        "status": "ok",
        "project_root": str(root.resolve()),
        "sources": {
            "manifest": relative_to(root, manifest_path),
            "package_json": relative_to(root, package_json_path),
            "wxt_config": relative_to(root, wxt_config_path),
        },
        "extension": {
            "name": primary_string_value(manifest, wxt_config, "name", prefer_fallback=prefer_wxt_config) or package_json.get("name"),
            "version": primary_string_value(manifest, wxt_config, "version", prefer_fallback=prefer_wxt_config) or package_json.get("version"),
            "manifest_version": manifest_version,
        },
        "permissions": {
            "requested": requested_permissions,
            "host_permissions": host_permissions,
            "optional_permissions": optional_permissions,
            "optional_host_permissions": optional_host_permissions,
        },
        "features": {
            "background_present": background_present,
            "content_scripts_present": content_scripts_present,
            "side_panel_present": side_panel_present,
        },
        "permission_evidence": permission_evidence,
        "signals": {
            "network_calls_present": bool(network_evidence),
            "local_storage_present": bool(local_storage_evidence),
            "remote_code_patterns_present": bool(remote_code_evidence),
        },
        "assessments": assessments,
        "ambiguities": ambiguities,
        "errors": [],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect a browser extension project and emit submission-relevant facts as JSON.")
    parser.add_argument("project_root", nargs="?", default=".", help="Path to the extension project root")
    parser.add_argument("--compact", action="store_true", help="Emit compact JSON")
    args = parser.parse_args()

    root = Path(args.project_root).resolve()
    payload = build_payload(root)
    if args.compact:
        print(json.dumps(payload, ensure_ascii=False, separators=(",", ":")))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload.get("status") == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
