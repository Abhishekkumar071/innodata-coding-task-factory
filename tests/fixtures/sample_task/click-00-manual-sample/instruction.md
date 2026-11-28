# Line-oriented access to captured CLI output in `click.testing.Result`

## Goal

Tests written with `click.testing.CliRunner` very often need to inspect output one line at a
time, so they repeat the same `result.output.split(...)` boilerplate and frequently get the
trailing-newline edge case wrong. Add first-class, line-oriented views of captured output to
`click.testing.Result`.

## Required behaviour

1. `Result` gains three new **read-only properties**: `output_lines`, `stdout_lines`, and
   `stderr_lines`.
2. Each property returns a new `list[str]` derived from the corresponding existing text
   property: `output_lines` from `Result.output`, `stdout_lines` from `Result.stdout`, and
   `stderr_lines` from `Result.stderr`. Line-ending normalization already performed by those
   properties (`"\r\n"` becomes `"\n"`) therefore applies.
3. Lines are separated **only** by the newline character `"\n"`. Other characters that
   `str.splitlines()` would treat as boundaries (for example form feed `"\x0c"`) must stay
   inside the line.
4. The returned items never contain the `"\n"` separator itself.
5. A single trailing `"\n"` at the very end of the text does **not** produce an extra empty
   item. Empty lines elsewhere (including an output consisting only of `"\n"`) are kept as `""`
   items.
6. If the underlying text is empty, the property returns an empty list.

## Public API

```python
class Result:
    @property
    def output_lines(self) -> list[str]: ...

    @property
    def stdout_lines(self) -> list[str]: ...

    @property
    def stderr_lines(self) -> list[str]: ...
```

No other public names are added or changed.

## Errors and messages

The properties never raise for any captured output and introduce no new exceptions or
messages.

## Examples

```python
import click
from click.testing import CliRunner

@click.command()
def cli():
    click.echo("out")
    click.echo("err", err=True)

result = CliRunner().invoke(cli)
result.stdout_lines   # ["out"]
result.stderr_lines   # ["err"]
result.output_lines   # ["out", "err"]  (mixed, in the order written)
```

| Captured text      | Lines                |
| :----------------- | :------------------- |
| `""`               | `[]`                 |
| `"\n"`             | `[""]`               |
| `"a\nb\n"`         | `["a", "b"]`         |
| `"a\n\nb"`         | `["a", "", "b"]`     |
| `"a\x0cb\n"`       | `["a\x0cb"]`         |

## Non-goals

- No changes to `CliRunner`, `CliRunner.invoke()`, or how output is captured.
- No new parameters for custom separators and no handling of a bare `"\r"` separator.

## Compatibility

`Result.output`, `Result.stdout`, `Result.stderr`, the `*_bytes` attributes, and every other
existing behaviour of `click.testing` must remain unchanged.
