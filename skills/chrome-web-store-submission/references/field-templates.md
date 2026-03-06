# Chrome Web Store Field Templates

Use these as starting points. Always adapt them to the current repo.

## 1. Single Purpose

### Chinese
- This extension helps users [do one specific thing] inside a browser extension UI. It focuses on [core purpose only], and all permissions and features exist only to support that purpose.

### English
- This extension helps users [do one specific thing] through a browser extension interface. Its features and permissions are limited to supporting that single, clearly defined purpose.

## 2. Permission Rationale

### `storage`

**Chinese**
- Used to store user-entered settings and extension data locally in the browser so the extension can preserve state and continue working across sessions.

**English**
- Used to store user-entered settings and extension data locally in the browser so the extension can preserve state across sessions.

### `contextMenus`

**Chinese**
- Used to add a right-click browser menu item that opens the extension interface. This permission is only used to provide an entry point and is not used to read webpage content.

**English**
- Used to add a browser right-click menu entry for opening the extension interface. It is only used as an entry point and not to read page content.

### `sidePanel`

**Chinese**
- Used to open the extension in the browser side panel so users can use the extension interface without leaving the current page.

**English**
- Used to open the extension in the browser side panel so users can access the extension UI without leaving the current page.

## 3. Remote Code

### No remote code

**Chinese**
- No remote code is used. All JavaScript code is bundled inside the extension package. The extension does not load executable code from external servers and does not use eval-like runtime code execution.

**English**
- No remote code is used. All JavaScript is bundled inside the extension package. The extension does not load executable code from external servers and does not use eval-like runtime code execution.

## 4. Data Use

### Local-only extension

**Chinese**
- The extension does not collect or transmit user data to external servers. User-entered data is stored locally in the browser only and is used solely to power the extension’s core functionality.

**English**
- The extension does not collect or transmit user data to external servers. User-entered data is stored locally in the browser only and is used solely to power the extension’s core functionality.

## 5. Listing Copy Skeleton

### Short Description

**Chinese**
- [Target user] 的 [single purpose] 工具，帮助你 [core outcome].

**English**
- A [single purpose] tool for [target user], helping them [core outcome].

### Detailed Description

**Chinese**
- Start with who it is for
- Explain the main workflow in 2–3 sentences
- List 4–6 core features
- End with a short positioning sentence

**English**
- Start with who it is for
- Explain the main workflow in 2–3 sentences
- List 4–6 core features
- End with a short positioning sentence

## 6. Reviewer Note Skeleton

### Chinese
- This extension’s single purpose is [purpose].
- For each requested permission, explain its concrete reason briefly.
- No remote code is used.
- User-entered data stays local in the browser.

### English
- The extension’s single purpose is [purpose].
- For each requested permission, explain its concrete reason briefly.
- No remote code is used.
- User-entered data stays local in the browser.

## 7. Stable Output Structure

Keep the field order stable unless the user asks for a custom format. Recommended order:

1. 单一用途说明 / Single Purpose
2. 已实际申请权限的理由 / Requested permission rationale only
3. 远程代码 / Remote Code
4. 数据使用 / Data Use
5. 短描述 / Short Description
6. 详细介绍 / Detailed Description
7. Reviewer Note（optional）

Only include permission fields that are actually present in the extension config. If multiple permission blocks are needed, keep their order stable and omit any permission the extension does not request.

This makes the skill easier to reuse for direct copy-paste or light editing.
