from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Literal

Op = Literal[
    "key",
    "compare",
    "swap",
    "shift",
    "set",
    "pivot",
    "merge_mark",
    "merge_compare",
    "confirm",
]


@dataclass(frozen=True)
class Step:
    """Immutable step emitted by algorithms and consumed by the UI."""

    op: Op
    indices: tuple[int, ...]
    payload: Any = None

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["indices"] = list(self.indices)
        return data

    @staticmethod
    def from_dict(data: dict[str, Any]) -> Step:
        return Step(op=data["op"], indices=tuple(data["indices"]), payload=data.get("payload"))
