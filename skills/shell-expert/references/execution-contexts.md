# Execution Contexts

Use this reference when the shell is not a standalone script but is embedded in another tool or file format.

## Dockerfile `RUN`

- For shell-form `RUN` on Linux, the default shell is `/bin/sh -c` unless a later `SHELL` instruction changes it.
- Avoid `source`, `[[ ]]`, arrays, and `pipefail` unless the Dockerfile explicitly switches the shell.
- If Bash is required, say so explicitly and show the `SHELL` change or a Bash invocation.

## Make recipes

- By default, each recipe line runs in a separate shell.
- For portable makefiles, combine related commands with `&&` or a single logical recipe line when state must persist across lines.
- Use `.ONESHELL:` only when the project is already targeting GNU make.
- Keep POSIX `sh` assumptions unless the Makefile explicitly sets a different shell.

## GitHub Actions `run:`

- The default shell depends on runner OS and workflow configuration.
- On Linux and macOS, an unspecified `run:` shell is not exactly the same as explicit `shell: bash`; GitHub documents different internal commands for those cases.
- Say when the answer depends on workflow-level `shell:` configuration.

## `cron`

- Cron runs with a minimal environment and a reduced `PATH`.
- Use absolute paths for non-trivial jobs and avoid relying on interactive shell startup files.
- Prefer standalone scripts over long one-liners when quoting or logging gets complex.

## `package.json` or task-runner scripts

- On Unix-like hosts these often execute through `/bin/sh`.
- Do not assume Bash features unless the command explicitly invokes Bash.
- If cross-platform npm scripts are required, say when a shell-only approach is insufficient.
