# Portability Levels

Use this reference when the task depends on shell choice or on cross-platform utility behavior.

## Shell selection guide

Choose the narrowest shell contract that still fits the task:

| Target | Prefer when | Avoid assuming |
| --- | --- | --- |
| POSIX `sh` | `/bin/sh`, BusyBox, Alpine, Dash, Make recipes, Docker `RUN`, wide portability | Arrays, `[[ ]]`, `(( ))`, process substitution, `pipefail` |
| Bash | Existing Bash scripts, `#!/usr/bin/env bash`, explicit Bash request, Linux-focused automation | That `/bin/sh` is Bash on every host |
| Zsh | `.zshrc`, interactive shell helpers, explicit Zsh request | That CI or scripts will run under Zsh |

If the user only needs a normal terminal command and no shell-specific feature is required, prefer a portable command shape and state the assumption.

## Common bashisms and portable replacements

| Bash/Zsh feature | Portable direction |
| --- | --- |
| `[[ "$x" == y* ]]` | `case $x in y*) ... ;; esac` |
| `source ./env.sh` | `. ./env.sh` |
| `local var=value` | Use ordinary variables with careful naming and function boundaries |
| Arrays like `files=(...)` | Positional params via `set -- ...` or line/NUL streams |
| `(( i += 1 ))` | `i=$((i + 1))` |
| `{1..10}` | Explicit loop counter |
| `function name { ...; }` | `name() { ...; }` |
| `readarray` / `mapfile` | `while IFS= read -r line; do ...; done` |
| `< <(cmd)` | Temporary file, named pipe, or pipeline redesign |
| `<<< "$x"` | `printf '%s\n' "$x" | ...` |
| `set -o pipefail` | Only use when the shell explicitly supports it |

## GNU/BSD/BusyBox gotchas

Call these out instead of silently assuming one platform:

| Command | Portability risk |
| --- | --- |
| `sed -i` | Flag shape differs between GNU and BSD `sed` |
| `date -d` | GNU-specific; macOS uses `-j -f` patterns instead |
| `readlink -f` | Missing on macOS by default |
| `grep -P` | Often unavailable outside GNU `grep` |
| `find -printf` | GNU-specific |
| `find -delete` | Common but not portable enough to treat as a POSIX default |
| `find -print0` / `xargs -0` | Standardized in POSIX Issue 8 and common on modern GNU/BSD/macOS, but still worth verifying on older or very small environments |
| `mktemp -d` | Widely available but not specified by POSIX |
| `xargs -r` | GNU-specific; BSD behavior differs |

If a command depends on GNU behavior, either say so explicitly or provide a split solution.
