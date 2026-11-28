import click
from click.testing import CliRunner


def _invoke(*messages):
    """Invoke a command that echoes each (text, err) pair without extra newlines."""

    @click.command()
    def cli():
        for text, err in messages:
            click.echo(text, err=err, nl=False)

    return CliRunner().invoke(cli)


def test_output_lines_split_on_newline():
    result = _invoke(("hello\nworld\n", False))
    assert result.output_lines == ["hello", "world"]


def test_lines_are_empty_list_for_empty_output():
    result = _invoke()
    assert result.output_lines == []
    assert result.stdout_lines == []
    assert result.stderr_lines == []


def test_single_newline_is_one_empty_line():
    result = _invoke(("\n", False))
    assert result.output_lines == [""]


def test_inner_blank_lines_preserved_without_trailing_newline():
    result = _invoke(("a\n\nb", False))
    assert result.stdout_lines == ["a", "", "b"]


def test_only_newline_separates_lines():
    result = _invoke(("a\x0cb\n", False))
    assert result.output_lines == ["a\x0cb"]


def test_stdout_stderr_and_mixed_output_lines():
    result = _invoke(("out\n", False), ("err\n", True))
    assert result.stdout_lines == ["out"]
    assert result.stderr_lines == ["err"]
    assert result.output_lines == ["out", "err"]


def test_lines_property_returns_a_new_list_each_time():
    result = _invoke(("x\n", False))
    first = result.output_lines
    first.append("mutated")
    assert result.output_lines == ["x"]
