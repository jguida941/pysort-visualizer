from __future__ import annotations

from pathlib import Path

import pytest

FORBIDDEN_SNIPPETS = (
    "._on_",
    "._timer",
    "._step_idx",
    "._show_hud",
)

TEST_ROOT = Path(__file__).resolve().parent
GUARD_NAME = Path(__file__).name


@pytest.mark.parametrize(
    "path",
    [p for p in TEST_ROOT.glob("**/*.py") if p.name not in {"__init__.py", GUARD_NAME}],
)
def test_tests_do_not_touch_privates(path: Path) -> None:
    text = path.read_text()
    offenders = [needle for needle in FORBIDDEN_SNIPPETS if needle in text]
    if offenders:
        pytest.fail(
            f"test file {path.relative_to(TEST_ROOT)} references privates: {', '.join(offenders)}"
        )
