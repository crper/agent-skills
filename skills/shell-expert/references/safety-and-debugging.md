# Safety And Debugging

Use this reference when the task is destructive, flaky, or explicitly about a broken shell command or script.

## Safety checklist

Before approving a command:

- quote parameter expansions unless splitting is intentional
- add `--` before path arguments when supported
- avoid `eval` unless there is no simpler structure
- avoid `rm "$dir"/*` when `$dir` might be empty or unset
- prefer preview-first output for delete, move, or rewrite commands
- verify whether filenames can contain spaces, newlines, or leading dashes
- separate trusted literals from untrusted user data

## Debugging flow

1. Reproduce the smallest failing command.
2. Confirm the target shell. `/bin/sh` often means Dash or BusyBox, not Bash.
3. Enable tracing as narrowly as possible:

```sh
set -x
```

4. Print the values that affect branching or quoting:

```sh
printf 'var=<%s>\n' "$var"
```

5. Check exit codes explicitly around pipelines or conditionals.
6. Run `sh -n`, `bash -n`, or `zsh -n` for syntax-only checks.
7. Run `shellcheck` if available, but do not assume it is installed.

## Common root causes

| Symptom | Common cause |
| --- | --- |
| `unexpected operator` | Bash syntax such as `[[` executed by POSIX `sh` |
| Missing files in loops | Word splitting from unquoted substitutions |
| Pipeline appears successful but output is wrong | Failure hidden inside a pipeline without `pipefail` support |
| Variables not preserved after `while read` | Loop ran in a subshell because of a pipeline |
| `sed -i` works on Linux but not macOS | GNU/BSD flag mismatch |

If the bug is shell mismatch, say that clearly before rewriting the whole script.
