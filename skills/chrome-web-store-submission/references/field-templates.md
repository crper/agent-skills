# Chrome Web Store Field Templates

Use these as starting points. Always adapt them to the current repo.

## 1. Single Purpose

### Chinese
- 这个扩展只帮助用户完成一件明确的事情：[do one specific thing]。所有权限和功能都只服务于这个单一、清晰的用途。

### English
- This extension helps users [do one specific thing] through a browser extension interface. Its features and permissions are limited to supporting that single, clearly defined purpose.

## 2. Permission Rationale

### `storage`

**Chinese**
- 用于把用户输入的设置和扩展数据保存在浏览器本地，使扩展能够在不同会话之间保留状态并持续工作。

**English**
- Used to store user-entered settings and extension data locally in the browser so the extension can preserve state across sessions.

### `contextMenus`

**Chinese**
- 用于添加浏览器右键菜单入口，以便用户打开扩展界面。该权限只用于提供入口，不用于读取网页内容。

**English**
- Used to add a browser right-click menu entry for opening the extension interface. It is only used as an entry point and not to read page content.

### `sidePanel`

**Chinese**
- 用于在浏览器侧边栏中打开扩展，让用户无需离开当前页面即可使用扩展界面。

**English**
- Used to open the extension in the browser side panel so users can access the extension UI without leaving the current page.

### `host_permissions`

**Chinese**
- 用于访问 [specific sites or APIs]，以支持 [feature]。扩展只会在用户使用相关功能时访问这些站点，不会申请超出功能所需范围的网站访问权限。

**English**
- Used to access [specific sites or APIs] required for [feature]. The extension only accesses these hosts when the related feature is used and does not request broader site access than necessary.

## 3. Remote Code

### No remote code

**Chinese**
- 未使用远程代码。所有 JavaScript 代码都打包在扩展包内，扩展不会从外部服务器加载可执行代码，也不会使用 `eval` 一类的运行时动态执行方式。

**English**
- No remote code is used. All JavaScript is bundled inside the extension package. The extension does not load executable code from external servers and does not use eval-like runtime code execution.

## 4. Data Use

### Local-only extension

**Chinese**
- 扩展不会把用户数据收集或传输到外部服务器。用户输入的数据只保存在浏览器本地，仅用于支撑扩展的核心功能。

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
- 先说明适合谁使用
- 用 2 到 3 句话解释主要工作流
- 列出 4 到 6 个核心功能
- 用一句简短定位语收尾

**English**
- Start with who it is for
- Explain the main workflow in 2–3 sentences
- List 4–6 core features
- End with a short positioning sentence

## 6. Reviewer Note Skeleton

### Chinese
- 这个扩展的单一用途是 [purpose]。
- 对每个已申请权限，简要说明其对应的实际用途。
- 未使用远程代码。
- 用户输入的数据保存在浏览器本地。

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
