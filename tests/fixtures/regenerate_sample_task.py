"""Re-render tests/fixtures/sample_task/click-00-manual-sample with harbor_writer.

Run from the repo root after any change to task_factory/templates/harbor/*:

    python tests/fixtures/regenerate_sample_task.py
    python tests/fixtures/regenerate_sample_task.py --from <dir>   # bootstrap from loose files

``<dir>`` (default: the existing package) must provide instruction.md, solution.patch (or
solution/solution.patch), the feature test module, fail_to_pass.json and pass_to_pass.json
(or their tests/ equivalents). Node IDs must come from the Stage 1 sandbox, never by hand.
"""

from __future__ import annotations

import argparse
import json
import shutil
import tempfile
from pathlib import Path

from task_factory.harbor_writer import write_task_package
from task_factory.schemas import FeatureBlueprint, SynthesizedTask

FIXTURE_ROOT = Path(__file__).resolve().parent / "sample_task"
TASK_ID = "click-00-manual-sample"
FEATURE_TEST = "tests/test_feature_result_lines.py"

BLUEPRINT = FeatureBlueprint(
    task_id=TASK_ID,
    axis="testing-completion",
    title="Line-oriented access to captured CLI output in click.testing.Result",
    summary="Add Result.output_lines / stdout_lines / stderr_lines read-only list properties.",
    target_files=["src/click/testing.py"],
    target_symbols=["click.testing.Result"],
    difficulty="easy",
    acceptance_criteria=[
        "Split only on '\\n'; a single trailing newline adds no empty item",
        "Empty text yields []; inner blank lines are kept",
        "Each access returns a new list",
    ],
    non_goals=["No CliRunner changes", "No custom separators"],
)


def _first(src: Path, *names: str) -> Path:
    for name in names:
        if (src / name).is_file():
            return src / name
    raise FileNotFoundError(f"none of {names} in {src}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--from", dest="src", type=Path, default=FIXTURE_ROOT / TASK_ID)
    args = parser.parse_args()
    feature_name = Path(FEATURE_TEST).name

    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / "src"
        shutil.copytree(args.src, src)  # read everything before the package is replaced
        task = SynthesizedTask(
            blueprint=BLUEPRINT,
            instruction_md=_first(src, "instruction.md").read_text(encoding="utf-8"),
            solution_patch=_first(src, "solution/solution.patch", "solution.patch").read_text(
                encoding="utf-8"
            ),
            feature_test_filename=FEATURE_TEST,
            feature_test_code=_first(src, FEATURE_TEST, feature_name).read_text(encoding="utf-8"),
            fail_to_pass=json.loads(
                _first(src, "tests/fail_to_pass.json", "fail_to_pass.json").read_text("utf-8")
            ),
            pass_to_pass=json.loads(
                _first(src, "tests/pass_to_pass.json", "pass_to_pass.json").read_text("utf-8")
            ),
        )
        path = write_task_package(task, FIXTURE_ROOT, overwrite=True)
    print(f"regenerated {path}")


if __name__ == "__main__":
    main()
