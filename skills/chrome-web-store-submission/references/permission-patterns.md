# Chrome Permission Patterns

Use these only after inspecting the repo. Prefer concrete evidence over generic copy.

## How to use

- Start from the actual requested permissions in the manifest or inspector JSON.
- Reuse these patterns as scaffolding, then replace placeholders with real features.
- If code evidence is weak, say that the current repo inspection suggests a use case and needs confirmation.

## `activeTab`

**Chinese**
- 用于在用户主动触发扩展操作时，临时访问当前活动标签页，以完成 [feature]。该权限不会在后台持续读取所有页面内容。

**English**
- Used to temporarily access the active tab when the user explicitly triggers [feature]. It is not used for persistent background access to all page content.

## `tabs`

**Chinese**
- 用于读取当前标签页的基本信息，或在 [feature] 中打开、切换、更新标签页。该权限只用于扩展的具体交互流程，不用于无关的数据收集。

**English**
- Used to read basic tab metadata or to open, switch, or update tabs for [feature]. It is used only for the extension workflow and not for unrelated data collection.

## `scripting`

**Chinese**
- 用于在用户触发 [feature] 时向页面注入扩展自带脚本，以完成页面交互、内容提取或界面增强。注入的代码随扩展一起打包，不是远程加载的。

**English**
- Used to inject packaged extension scripts into the page when the user triggers [feature], such as page interaction, content extraction, or UI enhancement. The injected code is bundled with the extension and is not remotely hosted.

## `storage`

**Chinese**
- 用于把用户设置、历史记录或扩展状态保存在浏览器本地，使扩展在不同会话间保持连续体验。

**English**
- Used to store user settings, history, or extension state locally in the browser so the extension can preserve continuity across sessions.

## `contextMenus`

**Chinese**
- 用于在浏览器右键菜单中提供 [feature] 的快捷入口，方便用户从当前页面直接打开扩展操作。

**English**
- Used to provide a right-click shortcut for [feature], letting users launch the extension action directly from the current page.

## `sidePanel`

**Chinese**
- 用于在浏览器侧边栏中展示扩展界面，让用户在保留当前页面上下文的同时使用 [feature]。

**English**
- Used to show the extension UI in the browser side panel so users can use [feature] without leaving the current page context.

## `host_permissions`

**Chinese**
- 用于访问 [specific sites or APIs]，以完成 [feature]。访问范围只覆盖该功能所必需的站点，不会扩展到无关域名。

**English**
- Used to access [specific sites or APIs] required for [feature]. The requested scope is limited to the hosts needed for that feature.

## `downloads`

**Chinese**
- 用于把 [generated/exported content] 保存到用户设备，或触发浏览器下载流程完成 [feature]。

**English**
- Used to save [generated/exported content] to the user’s device or trigger the browser download flow for [feature].

## `alarms`

**Chinese**
- 用于按计划触发扩展内部任务，例如 [scheduled feature]。该权限只负责定时唤起扩展逻辑，不用于后台数据收集。

**English**
- Used to trigger scheduled internal extension tasks such as [scheduled feature]. It is only for timed execution of extension logic.

## `notifications`

**Chinese**
- 用于在 [feature] 完成、失败或需要用户关注时显示浏览器通知，帮助用户及时看到扩展结果。

**English**
- Used to show browser notifications when [feature] completes, fails, or needs user attention.

## `identity`

**Chinese**
- 用于支持 [sign-in flow/provider] 登录流程，帮助用户在扩展内完成身份验证。

**English**
- Used to support [sign-in flow/provider] authentication so users can sign in within the extension.

## `cookies`

**Chinese**
- 用于在 [feature] 中读取或写入与目标站点相关的 cookie，以维持用户会话或完成授权流程。

**English**
- Used to read or write site cookies needed for [feature], such as maintaining a session or completing an authorization flow.

## `declarativeNetRequest`

**Chinese**
- 用于按扩展规则拦截、重定向或修改网络请求，以实现 [feature]。规则由扩展本地定义，不依赖远程下发代码。

**English**
- Used to block, redirect, or modify network requests according to packaged extension rules for [feature]. The rules are defined locally in the extension.

## `webRequest`

**Chinese**
- 用于观察或处理与 [feature] 直接相关的网络请求。该权限只用于支持该功能所需的请求级能力。

**English**
- Used to observe or handle network requests directly related to [feature]. It is requested only for the request-level capability needed by that feature.
