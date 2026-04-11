# Command Patterns

Use this reference when writing or reviewing shell commands that touch many files or transform arbitrary input.

## Safer file iteration

Prefer these patterns over word-splitting loops:

### Human-readable inspection with `find`

```sh
find . -type f -exec sh -c '
  for path do
    printf "%s\n" "$path"
  done
' sh {} +
```

Use this for human inspection only. If a filename contains a literal newline, no portable line-oriented display will be perfectly reversible.

### Lossless machine-readable stream

```sh
find . -type f -exec printf '%s\0' {} +
```

Use NUL-delimited flows when filenames may contain whitespace or newlines and the output must be round-trippable.

When you need to pipe that stream into another tool, `find -print0 | xargs -0 ...` is now standardized in POSIX Issue 8 and is widely available on modern GNU, BSD, and macOS systems, but older hosts may still lack one side of the pair.

## Reading lines reliably

```sh
while IFS= read -r line; do
  printf '%s\n' "$line"
done < input.txt
```

Avoid:

- `for line in $(cat file)`
- `cat file | while read line`

Those forms lose data or hide subshell behavior.

## Temporary directories

```sh
tmpdir=$(mktemp -d)
trap 'rm -rf "$tmpdir"' EXIT HUP INT TERM
```

Always clean up temp resources in reusable scripts.

`mktemp` is common but not POSIX-specified. If the target is a very stripped environment, check availability or provide a fallback.

## Separate dry-run and apply modes

For destructive or bulk-edit tasks, show a preview first:

```sh
find . -type f -name '*.tmp' -exec printf '%s\n' {} +
find . -type f -name '*.tmp' -exec rm -f -- {} +
```

If a command can delete or overwrite data, prefer preview-first output unless the user explicitly asked for the final destructive form only.
