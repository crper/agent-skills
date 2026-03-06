---
name: chrome-web-store-submission
description: Prepare copy-and-paste Chrome Web Store submission materials for browser extensions, including single-purpose statements, permission justifications, remote-code answers, privacy/data-use disclosures, reviewer notes, and store descriptions. Use this whenever the user mentions Chrome 发布、Chrome 商店、Chrome Web Store、上架文案、审核表单、单一用途、权限理由、远程代码、数据使用、隐私披露，or asks for listing copy they can directly paste into the Chrome dashboard.
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

### 1. Inspect the extension before writing

Read the current extension source of truth first:

- `package.json`
- `wxt.config.ts`
- relevant entrypoints such as `src/entrypoints/background.ts`
- manifest/build output only when helpful as confirmation

Verify at least:

- extension name
- version
- requested permissions
- whether content scripts exist
- whether remote code is used
- whether user data is collected, transmitted, sold, or shared

### 2. Write from code, not from assumptions

When drafting any Chrome Web Store field:

- tie each permission to a concrete feature in the codebase
- do not justify permissions with “future use”
- distinguish local browser storage from server-side collection
- explicitly state when data stays local and is not transmitted
- only write permission sections for permissions that are actually requested by the extension, unless the user explicitly asks for a full template
- flag ambiguity instead of guessing

### 3. Keep the output structure stable

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

### 4. Honor the requested language

- If the user asks for **Chinese**, output only Chinese
- If the user asks for **English**, output only English
- If the user asks for **bilingual**, output Chinese first and English second
- If the user does not specify, match the conversation language

### 5. Use reviewer-friendly wording

Prefer concrete wording like:

- “Used to store user-entered configuration locally in the browser”
- “Used to add a right-click shortcut for opening the extension UI”
- “Used to open the extension in the browser side panel”

Avoid vague wording like:

- “Improves user experience”
- “Used for various features”
- “May be needed in some scenarios”

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
- remote-code answers match the actual code
- data-use answers match storage/network behavior
- no unsupported claims about privacy policy, encryption, or compliance are added without evidence

## References

- Read `references/field-templates.md` for reusable answer patterns and stable field order.
