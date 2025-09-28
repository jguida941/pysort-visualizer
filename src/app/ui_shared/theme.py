from __future__ import annotations

from typing import cast

from PyQt6.QtWidgets import QApplication


def apply_global_tooltip_theme(theme: str) -> None:
    app = QApplication.instance()
    if app is None:
        return
    qapp = cast(QApplication, app)
    if theme == "high-contrast":
        qapp.setStyleSheet(
            "QToolTip { color: #111111; background: #f7f7f7; border: 1px solid #0f6fff; }"
        )
    else:
        qapp.setStyleSheet(
            "QToolTip { color: #e6e6e6; background: #1e2530; border: 1px solid #6aa0ff; }"
        )
