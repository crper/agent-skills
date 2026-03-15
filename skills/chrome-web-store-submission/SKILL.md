---
name: chrome-web-store-submission
description: Use when the user needs copy-and-paste Chrome Web Store submission materials for a browser extension, including 单一用途说明、权限理由、远程代码回答、数据使用/隐私披露、Reviewer Note、短描述或详细介绍。Trigger on Chrome 发布、Chrome 商店、Chrome Web Store、上架文案、审核表单、单一用途、权限理由、远程代码、数据使用、隐私披露, or store listing requests.
---

# Chrome Web Store Submission

Generate accurate, copy-and-paste Chrome Web Store submission content for a browser extension. Inspect the current project first, then draft answers in the exact language the user asks for while keeping the field structure stable and easy to paste into the Chrome dashboard.

## What this skill covers

This skill is for submission-writing and compliance-copy tasks such as:

- single-purpose statements
- permission justifications
- remote-code answers
- data-use and privacy disclosures
- short description and detailed description
- reviewer notes
- screenshot captions or listing copy

This skill does **not** publish the extension or interact with Chrome Web Store APIs directly.

## Workflow

### 1. Extract extension facts before writing

Run this first:

```bash
python3 ./skills/chrome-web-store-submission/scripts/inspect_extension_facts.py [project-root]
```

Use the JSON output as the primary source of truth. If the script returns `status = error` or leaves key fields ambiguous, then inspect these sources manually in this order:

- `manifest.json` or build output manifest
- `package.json`
- `wxt.config.ts`
- relevant entrypoints such as `src/entrypoints/background.ts`
- content scripts, popup pages, options pages, and HTML entrypoints when needed

Verify at least:

- extension name
- version
- requested permissions
- whether content scripts exist
- whether remote code is used
- whether user data is collected, transmitted, sold, or shared

### 2. Treat assessment states as hard gates

When `inspect_extension_facts.py` reports:

- `assessments.remote_code.status = no`: you may say no remote code is used
- `assessments.remote_code.status = possible`: do not claim “No remote code is used”; say the repo contains patterns that need manual confirmation
- `assessments.data_transmission.status = no`: you may say data is not transmitted to external servers
- `assessments.data_transmission.status = possible`: do not claim data stays local only
- `assessments.data_sale_or_sharing.status = unknown`: do not claim data is not sold or shared unless the repo or user explicitly provides evidence

### 3. Write from code, not from assumptions

When drafting any Chrome Web Store field:

- tie each permission to a concrete feature in the codebase
- prefer `permission_evidence` from the inspector output over generic template text
- do not justify permissions with “future use”
- distinguish local browser storage from server-side collection
- explicitly state when data stays local and is not transmitted
- only write permission sections for permissions that are actually requested by the extension, unless the user explicitly asks for a full template
- keep `host_permissions` separate from API permissions when they matter for the form
- flag ambiguity instead of guessing

### 4. Keep the output structure stable

Unless the user asks for a custom format, output in this order:

1. `单一用途说明` / `Single Purpose`
2. requested permission rationale blocks in a stable order
3. `远程代码` / `Remote Code`
4. `数据使用` / `Data Use`
5. `短描述` / `Short Description`
6. `详细介绍` / `Detailed Description`
7. `Reviewer Note` (optional)

For permission rationale blocks:

- include only permissions that are actually present in the extension config
- keep their order stable when multiple are needed
- do not invent `storage`, `contextMenus`, or `sidePanel` sections when the extension does not request them

### 5. Honor the requested language

- If the user asks for **Chinese**, output only Chinese
- If the user asks for **English**, output only English
- If the user asks for **bilingual**, output Chinese first and English second
- If the user does not specify, match the conversation language

### 6. Use reviewer-friendly wording

Prefer concrete wording like:

- “Used to store user-entered configuration locally in the browser”
- “Used to add a right-click shortcut for opening the extension UI”
- “Used to open the extension in the browser side panel”

Avoid vague wording like:

- “Improves user experience”
- “Used for various features”
- “May be needed in some scenarios”

## Ambiguity handling

If evidence is incomplete, write conservative copy:

- say what the code clearly shows
- say what still needs confirmation
- avoid absolute privacy or compliance claims without repo evidence
- prefer “The current repo inspection shows ...” over “The extension guarantees ...”

## Output modes

### Chrome form answers

Produce short, field-specific answers that can be pasted directly into the Chrome dashboard.

### Listing copy

Produce:

- short description
- detailed description
- optional bilingual version

### Reviewer note

When useful, produce a short reviewer note summarizing:

- the extension’s single purpose
- what each permission is used for
- whether remote code is used
- whether user data stays local

## Accuracy checklist

Before finalizing, verify:

- the extension name matches current config
- the version matches current config
- permission explanations match the actual permission list
- permission explanations match concrete code usage when evidence is available
- remote-code answers match the actual code
- data-use answers match storage/network behavior
- no unsupported claims about privacy policy, encryption, or compliance are added without evidence

## References

- Read `references/field-templates.md` for reusable answer patterns and stable field order.
- Read `references/permission-patterns.md` for permission-specific wording beyond the basic examples.
