#!/usr/bin/env python3

import json
import subprocess
import sys
import tempfile
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
INSPECTOR = SCRIPT_DIR / "inspect_extension_facts.py"


def run_raw_inspector(project_root: Path) -> dict:
    result = subprocess.run(
        [sys.executable, str(INSPECTOR), str(project_root), "--compact"],
        capture_output=True,
        text=True,
        check=False,
    )
    if not result.stdout.strip():
        raise AssertionError(f"inspector produced no stdout: {result.stderr}")
    return json.loads(result.stdout)


def run_inspector(project_root: Path) -> dict:
    payload = run_raw_inspector(project_root)
    if payload.get("status") != "ok":
        raise AssertionError(f"inspector returned error payload: {payload}")
    return payload


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


def expect(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def case_local_only_extension() -> None:
    with tempfile.TemporaryDirectory(prefix="cws-local-") as tempdir:
        root = Path(tempdir)
        write(
            root / "manifest.json",
            """{
  "manifest_version": 3,
  "name": "Local Notes",
  "version": "0.1.0",
  "permissions": ["storage", "contextMenus", "sidePanel"],
  "background": {"service_worker": "background.js"},
  "side_panel": {"default_path": "sidepanel.html"}
}
""",
        )
        write(
            root / "background.js",
            """chrome.contextMenus.create({ title: "Open", contexts: ["all"] })
chrome.storage.local.set({ theme: "light" })
chrome.sidePanel.open({ windowId: 1 })
""",
        )

        payload = run_inspector(root)
        expect(payload["permissions"]["requested"] == ["storage", "contextMenus", "sidePanel"], f"unexpected permissions: {payload['permissions']}")
        expect(payload["assessments"]["remote_code"]["status"] == "no", f"unexpected remote_code: {payload['assessments']}")
        expect(payload["assessments"]["data_transmission"]["status"] == "no", f"unexpected data_transmission: {payload['assessments']}")
        expect(payload["assessments"]["local_storage_only"]["status"] == "yes", f"unexpected local_storage_only: {payload['assessments']}")
        expect("storage" in payload["permission_evidence"], f"missing storage evidence: {payload['permission_evidence']}")


def case_network_extension() -> None:
    with tempfile.TemporaryDirectory(prefix="cws-network-") as tempdir:
        root = Path(tempdir)
        write(
            root / "manifest.json",
            """{
  "manifest_version": 3,
  "name": "API Client",
  "version": "0.2.0",
  "permissions": ["storage"],
  "host_permissions": ["https://api.example.com/*"]
}
""",
        )
        write(root / "src" / "worker.ts", """await fetch("https://api.example.com/data")\n""")

        payload = run_inspector(root)
        expect(payload["assessments"]["data_transmission"]["status"] == "possible", f"unexpected data_transmission: {payload['assessments']}")
        expect(payload["assessments"]["local_storage_only"]["status"] == "no", f"unexpected local_storage_only: {payload['assessments']}")


def case_remote_code_pattern() -> None:
    with tempfile.TemporaryDirectory(prefix="cws-remote-") as tempdir:
        root = Path(tempdir)
        write(
            root / "manifest.json",
            """{
  "manifest_version": 3,
  "name": "Risky Extension",
  "version": "0.3.0"
}
""",
        )
        write(root / "content.js", """const fn = new Function("return 1")\n""")

        payload = run_inspector(root)
        expect(payload["assessments"]["remote_code"]["status"] == "possible", f"unexpected remote_code: {payload['assessments']}")
        expect(payload["ambiguities"], f"expected ambiguities: {payload}")


def case_wxt_fallback() -> None:
    with tempfile.TemporaryDirectory(prefix="cws-wxt-") as tempdir:
        root = Path(tempdir)
        write(root / "package.json", """{"name":"wxt-demo","version":"1.0.0"}\n""")
        write(
            root / "wxt.config.ts",
            """export default defineConfig({
  manifest: {
    name: "WXT Demo",
    version: "1.0.1",
    permissions: ["storage", "activeTab"],
    host_permissions: ["https://example.com/*"]
  }
})
""",
        )
        write(root / "entry.ts", """chrome.storage.local.get("foo")\n""")

        payload = run_inspector(root)
        expect(payload["sources"]["wxt_config"] == "wxt.config.ts", f"unexpected sources: {payload['sources']}")
        expect(payload["extension"]["name"] == "WXT Demo", f"unexpected extension: {payload['extension']}")
        expect(payload["permissions"]["requested"] == ["storage", "activeTab"], f"unexpected permissions: {payload['permissions']}")


def case_vue_files_are_scanned_for_network_activity() -> None:
    with tempfile.TemporaryDirectory(prefix="cws-vue-") as tempdir:
        root = Path(tempdir)
        write(
            root / "manifest.json",
            """{
  "manifest_version": 3,
  "name": "Vue Popup",
  "version": "0.1.0",
  "permissions": ["storage"]
}
""",
        )
        write(
            root / "src" / "popup.vue",
            """<script setup>
await fetch("https://api.example.com/data")
</script>
""",
        )

        payload = run_inspector(root)
        expect(payload["signals"]["network_calls_present"] is True, f"expected network signal: {payload['signals']}")
        expect(payload["assessments"]["data_transmission"]["status"] == "possible", f"unexpected data_transmission: {payload['assessments']}")


def case_wxt_config_beats_stale_build_manifest() -> None:
    with tempfile.TemporaryDirectory(prefix="cws-stale-build-") as tempdir:
        root = Path(tempdir)
        write(
            root / "dist" / "manifest.json",
            """{
  "manifest_version": 3,
  "name": "Old Build",
  "version": "0.9.0",
  "permissions": ["storage"]
}
""",
        )
        write(
            root / "wxt.config.ts",
            """export default defineConfig({
  manifest: {
    name: "New Source",
    version: "1.0.0",
    permissions: ["storage", "sidePanel"]
  }
})
""",
        )

        payload = run_inspector(root)
        expect(payload["extension"]["name"] == "New Source", f"unexpected extension: {payload['extension']}")
        expect(payload["extension"]["version"] == "1.0.0", f"unexpected extension: {payload['extension']}")
        expect(payload["permissions"]["requested"] == ["storage", "sidePanel"], f"unexpected permissions: {payload['permissions']}")


def case_missing_extension_config_returns_error() -> None:
    with tempfile.TemporaryDirectory(prefix="cws-no-manifest-") as tempdir:
        root = Path(tempdir)
        write(root / "package.json", """{"name":"not-an-extension","version":"1.2.3"}\n""")

        payload = run_raw_inspector(root)
        expect(payload["status"] == "error", f"expected error payload: {payload}")
        expect(payload["errors"], f"expected explanation for error payload: {payload}")


def case_dev_output_is_ignored_when_source_exists() -> None:
    with tempfile.TemporaryDirectory(prefix="cws-dev-output-") as tempdir:
        root = Path(tempdir)
        write(
            root / "wxt.config.ts",
            """export default defineConfig({
  manifest: {
    name: "Source First",
    version: "1.0.0",
    permissions: ["storage"]
  }
})
""",
        )
        write(
            root / "src" / "store.ts",
            """import { storage } from "#imports";
const settings = storage.defineItem("local:settings", { fallback: null });
await settings.getValue();
""",
        )
        write(
            root / ".output" / "chrome-mv3-dev" / "popup.html",
            """<script src="http://localhost:3000/@vite/client" type="module"></script>
""",
        )
        write(
            root / ".output" / "chrome-mv3-dev" / "background.js",
            """const ws = new WebSocket("ws://localhost:3000", "vite-hmr");
""",
        )

        payload = run_inspector(root)
        expect(payload["signals"]["network_calls_present"] is False, f"unexpected network signal: {payload['signals']}")
        expect(payload["signals"]["remote_code_patterns_present"] is False, f"unexpected remote-code signal: {payload['signals']}")
        expect(payload["assessments"]["data_transmission"]["status"] == "no", f"unexpected data_transmission: {payload['assessments']}")
        expect(payload["assessments"]["remote_code"]["status"] == "no", f"unexpected remote_code: {payload['assessments']}")


def case_declared_permissions_filter_false_positive_matches() -> None:
    with tempfile.TemporaryDirectory(prefix="cws-permission-filter-") as tempdir:
        root = Path(tempdir)
        write(
            root / "manifest.json",
            """{
  "manifest_version": 3,
  "name": "Filtered Evidence",
  "version": "0.1.0",
  "permissions": ["storage"]
}
""",
        )
        write(
            root / "src" / "app.tsx",
            """const [activeTab, setActiveTab] = useState("general");
const downloads = ["report.xlsx"];
setActiveTab("data");
""",
        )

        payload = run_inspector(root)
        evidence = payload["permission_evidence"]
        expect("activeTab" not in evidence, f"unexpected activeTab evidence: {evidence}")
        expect("downloads" not in evidence, f"unexpected downloads evidence: {evidence}")


def case_wxt_local_storage_is_recognized() -> None:
    with tempfile.TemporaryDirectory(prefix="cws-wxt-storage-") as tempdir:
        root = Path(tempdir)
        write(
            root / "wxt.config.ts",
            """export default defineConfig({
  manifest: {
    name: "WXT Storage",
    version: "1.0.0",
    permissions: ["storage"]
  }
})
""",
        )
        write(
            root / "src" / "storage.ts",
            """import { storage } from "#imports";
const item = storage.defineItem("local:settings", { fallback: null });
await item.setValue({ theme: "light" });
""",
        )

        payload = run_inspector(root)
        expect(payload["signals"]["local_storage_present"] is True, f"expected local storage signal: {payload['signals']}")
        expect(payload["assessments"]["local_storage_only"]["status"] == "yes", f"unexpected local_storage_only: {payload['assessments']}")


def case_wxt_features_are_inferred_without_manifest() -> None:
    with tempfile.TemporaryDirectory(prefix="cws-wxt-features-") as tempdir:
        root = Path(tempdir)
        write(
            root / "wxt.config.ts",
            """export default defineConfig({
  manifest: {
    name: "WXT Features",
    version: "1.0.0",
    permissions: ["storage"],
    action: {
      default_title: "WXT Features"
    },
    side_panel: {
      default_path: "sidepanel.html"
    }
  }
})
""",
        )
        write(root / "src" / "entrypoints" / "background.ts", """export default defineBackground(() => {})\n""")

        payload = run_inspector(root)
        expect(payload["extension"]["manifest_version"] == 3, f"unexpected extension: {payload['extension']}")
        expect(payload["features"]["background_present"] is True, f"unexpected features: {payload['features']}")
        expect(payload["features"]["side_panel_present"] is True, f"unexpected features: {payload['features']}")


def main() -> int:
    cases = [
        ("local-only", case_local_only_extension),
        ("network", case_network_extension),
        ("remote-code", case_remote_code_pattern),
        ("wxt-fallback", case_wxt_fallback),
        ("vue-network", case_vue_files_are_scanned_for_network_activity),
        ("stale-build", case_wxt_config_beats_stale_build_manifest),
        ("missing-config", case_missing_extension_config_returns_error),
        ("dev-output-ignored", case_dev_output_is_ignored_when_source_exists),
        ("permission-filter", case_declared_permissions_filter_false_positive_matches),
        ("wxt-local-storage", case_wxt_local_storage_is_recognized),
        ("wxt-feature-inference", case_wxt_features_are_inferred_without_manifest),
    ]
    failures = []
    for name, runner in cases:
        try:
            runner()
        except Exception as exc:
            failures.append((name, str(exc)))
            print(f"FAIL {name}: {exc}")
        else:
            print(f"PASS {name}")

    if failures:
        print(f"\n{len(failures)} cases failed")
        return 1

    print(f"\nAll {len(cases)} cases passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
