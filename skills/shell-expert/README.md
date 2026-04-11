# Shell Expert

English | [简体中文](./README.zh.md)

Write, review, port, and debug shell commands or shell scripts with the right portability level across POSIX `sh`, Bash, and Zsh.

## Scope

- Best for **shell one-liners, scripts, and CI snippets**
- Handles **portability, quoting, safety, and debugging**
- Helps choose between **POSIX `sh`**, **Bash**, and **Zsh** instead of assuming Bash by default

## Project Structure

- `SKILL.md` — workflow and response contract
- `references/portability-levels.md` — shell selection and bashism portability map
- `references/execution-contexts.md` — Docker, Make, CI, cron, and script-host gotchas
- `references/command-patterns.md` — robust command and script patterns
- `references/safety-and-debugging.md` — hardening and debugging checklist
- `agents/openai.yaml` — prompt preset for agent UIs
- `evals/evals.json` — minimal regression prompts

## Best Use Cases

- Writing a portable `sh` script for CI, Docker, BusyBox, or Alpine
- Fixing shell that is embedded in a Dockerfile `RUN`, Make recipe, or GitHub Actions `run:` block
- Reviewing a shell command for quoting, globbing, or injection hazards
- Replacing brittle `find | xargs` or `for f in $(...)` pipelines
- Porting a Bash script toward POSIX `sh`
- Debugging shell errors such as `unexpected operator`, broken quoting, or silent pipeline failures
- Producing safer bulk-rename, delete, move, or text-rewrite commands

## Output Style

The skill should:

- lead with a finished command or script
- state the target shell and assumptions
- flag destructive behavior and offer a dry-run form when practical
- call out GNU/BSD/BusyBox differences when they matter

## Notes

- Prefer explicit shell contracts over vague "shell script" answers
- Default to the smallest portable solution that still fits the user's environment
- Only use Bash or Zsh features when the environment is explicit or the gain is worth the coupling
