---
name: shell-expert
description: Write, review, port, and debug shell commands or shell scripts with the right portability level across POSIX sh, Bash, and Zsh. Use when the user asks for shell one-liners, `.sh` scripts, `.bashrc` or `.zshrc` edits, Dockerfile `RUN` snippets, Makefile recipes, GitHub Actions `run:` blocks, command pipelines, quoting fixes, shell portability, shell debugging, or safer replacements for brittle find/xargs/sed/awk/jq usage.
---

# Shell Expert

Write shell that is copy-pasteable, explicit about assumptions, and safe for the requested execution environment. Start by deciding whether the task needs strict POSIX portability or can rely on Bash or Zsh features, then optimize for predictable behavior, readable quoting, and debuggable failure modes.

## Workflow Map

```text
[Task Shape] -> [Shell Contract] -> [Runtime Constraints] -> [Draft or Review] -> [Safety Pass] -> [Validation]
```

## 1. Classify the task first

Work from the user artifact before inventing a replacement:

- one-off command
- reusable script
- portability upgrade or bashism removal
- debugging or root-cause analysis
- safety hardening for destructive or bulk-edit commands

If the user already provided a command, script, error message, or failing CI step, inspect that first and preserve the original intent.

## 2. Choose the shell contract early

Do not assume Bash just because the request says "shell."

Default decision rules:

- Use **POSIX sh** when the user mentions `sh`, `/bin/sh`, POSIX, BusyBox, Alpine, Dash, init scripts, Docker `RUN`, Make recipes, or broad portability.
- Use **Bash** when the file already targets Bash, the user explicitly asks for Bash, or Bash-only features materially simplify the solution.
- Use **Zsh** only when the user explicitly targets `zsh`, shell startup files like `.zshrc`, or interactive Zsh workflows.
- If the shell is unspecified and shell-specific features are unnecessary, produce a portable command and state that assumption.

Read [references/portability-levels.md](references/portability-levels.md) when shell choice, bashism removal, or GNU/BSD/BusyBox differences matter.

Read [references/execution-contexts.md](references/execution-contexts.md) when the shell is embedded in Dockerfiles, Makefiles, CI steps, cron, or package-manager scripts.

## 3. Recover the runtime constraints

Before writing or approving a command, identify the smallest reliable set of constraints:

- target shell and known shell version
- embedding context such as a standalone script, Docker `RUN`, Make recipe, `cron`, or CI `run:` step
- operating system or image family such as GNU/Linux, macOS, BusyBox, Alpine
- required external tools such as `jq`, `rg`, `fd`, `awk`, `sed`
- whether the task is one-off or should live as a reusable script
- whether the command can delete, overwrite, rename, or execute arbitrary input
- whether filenames may contain spaces, tabs, newlines, or leading dashes

If some constraints are unknown, infer the minimum needed and state the assumption before relying on shell-specific behavior.

## 4. Drafting rules

### Always

- Prefer complete, copy-pasteable commands over pseudo-shell.
- Quote expansions unless intentional splitting or globbing is required.
- Prefer `printf` over non-trivial `echo`.
- Prefer `command -v` for tool detection.
- Use `IFS=` with `read -r` for line reads.
- Use `--` before path arguments when the command supports it.
- Use NUL-delimited pipelines or `find ... -exec ... +` when paths may contain whitespace or newlines.
- Do not call a newline-delimited list "safe for arbitrary filenames". If round-trippable output matters, use NUL-delimited output or explicitly label the result human-readable only.
- Separate trusted literals from user input instead of building commands through string concatenation.
- Explain required tools and assumptions right next to the command.
- Match the user's language for prose explanations unless they requested a specific output language.

### In POSIX sh mode

- Avoid arrays, `[[ ... ]]`, `(( ... ))`, brace expansion, process substitution, here-strings, `mapfile`, `readarray`, `shopt`, and `set -o pipefail`.
- Prefer `case`, `test` or `[`, `getopts`, `find ... -exec`, portable `awk`, and conservative `sed`.
- Treat GNU-specific flags as opt-in assumptions, not defaults.

### In Bash or Zsh mode

- Use arrays, `[[ ... ]]`, `set -o pipefail`, process substitution, and shell-specific parameter expansion only when the target shell is explicit and the gain is real.
- Prefer readable features over clever golf. A longer command is acceptable when it is materially safer or easier to debug.

Read [references/command-patterns.md](references/command-patterns.md) when writing loops, file walkers, temporary-file flows, or bulk-processing pipelines.

## 5. Review and hardening pass

Before finalizing, check:

- Does the command preserve filenames with spaces, tabs, newlines, and leading `-`?
- Are there hidden word-splitting or globbing hazards?
- Does it rely on GNU utilities that will break on macOS or BusyBox?
- Does it need a dry-run form before deletion or overwrite?
- Does it fail with a useful non-zero exit status?
- Does the script need cleanup via `trap` for temp files or directories?
- Is there any use of `eval`, command injection, or unchecked interpolation that can be removed?

Read [references/safety-and-debugging.md](references/safety-and-debugging.md) when the task is destructive, flaky, or explicitly about shell debugging.

## 6. Validation rules

Run the smallest useful validation for the requested surface:

- `sh -n` for POSIX shell syntax checks
- `dash -n` or BusyBox `sh -n` when `/bin/sh` portability is the actual target and those shells are available
- `bash -n` or `zsh -n` for shell-specific scripts
- a dry-run invocation for destructive commands
- a reduced reproducer when debugging pipeline or quoting issues
- `shellcheck` when available and relevant, but do not assume it is installed

If validation is not possible in the current environment, say that plainly and explain what was still checked.

## Output contract

When responding with this skill:

- Lead with the finished command or script.
- Immediately state the target shell and key environment assumptions.
- Call out required tools or shell features.
- Flag destructive steps and provide a dry-run variant when practical.
- If the user asked why something broke, explain the root cause before or alongside the fix.
- If one fully portable solution is unrealistic, say so explicitly and offer the clean POSIX-safe and Bash-specific versions separately.
