"""Renderer abstractions and VisPy spike scaffolding.

This module introduces a minimal abstraction layer so the core visualizer can drive
additional rendering backends (e.g., a future 3D view) without hard-coding VisPy
details into the main QWidget code. The VisPy implementation now renders a basic
bar mesh and reacts to `StepRenderEvent` updates so we can evaluate performance
before making UI commitments.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
import logging
import os
from collections.abc import Iterable, Sequence
from typing import Any

try:  # Optional dependency that only matters when VisPy is enabled
    import numpy as _np
except ImportError:
    _np = None  # type: ignore[assignment]

from .step_translator import STEP_COLOR_MAP, StepRenderEvent

LOGGER = logging.getLogger("sorting_viz.renderer")


def _env_flag(name: str, default: str = "0") -> bool:
    raw = os.getenv(name, default)
    return str(raw).strip().lower() not in {"0", "false", "no", "off", ""}


def _require_numpy():
    if _np is None:  # pragma: no cover - only happens when numpy missing
        raise RuntimeError("NumPy is required for the VisPy renderer. Install `numpy`.")
    return _np


class AbstractRenderer(ABC):
    """Minimal renderer interface consumed by the visualizer."""

    @abstractmethod
    def on_step_event(self, event: StepRenderEvent) -> None:
        """Update the renderer with a new step."""

    def reset(  # pragma: no cover - default is trivial
        self, *, n: int | None = None, values: Sequence[int] | None = None
    ) -> None:
        """Reset internal state for a new dataset."""

    def shutdown(self) -> None:  # pragma: no cover - default is trivial
        """Dispose of renderer resources."""


class NullRenderer(AbstractRenderer):
    """No-op renderer used when the 3D flag is disabled or unavailable."""

    def on_step_event(self, event: StepRenderEvent) -> None:  # pragma: no cover - trivial
        return

    def reset(  # pragma: no cover - trivial
        self, *, n: int | None = None, values: Sequence[int] | None = None
    ) -> None:
        return

    def shutdown(self) -> None:  # pragma: no cover - trivial
        return


class VispyRenderer(AbstractRenderer):
    """Prototype VisPy renderer for the spike."""

    def __init__(self, *, show_canvas: bool = False) -> None:
        try:
            from vispy import app, scene  # type: ignore import-not-found
        except ImportError as exc:  # pragma: no cover - import guard
            raise RuntimeError(
                "VisPy is not installed. Install `vispy` to enable USE_3D_RENDERER."
            ) from exc
        except Exception as exc:  # pragma: no cover - import guard
            raise RuntimeError("VisPy failed to import") from exc

        try:
            vispy_app = app.use_app("pyqt6")
        except Exception as backend_exc:  # pragma: no cover - backend selection
            LOGGER.info(
                "VisPy PyQt6 backend unavailable (%s); falling back to default backend.",
                backend_exc,
            )
            vispy_app = app.use_app()

        self._scene = scene
        self._vispy_app = vispy_app
        LOGGER.info("VisPy renderer using backend: %s", vispy_app.backend_name)

        self._canvas = scene.SceneCanvas(
            keys="interactive",
            bgcolor="#0f1115",
            show=show_canvas,
        )
        self._view = self._canvas.central_widget.add_view()
        self._view.camera = scene.cameras.PanZoomCamera(aspect=1.0)
        self._view.camera.interactive = False
        self._view.camera.set_range(x=(0.0, 1.0), y=(0.0, 1.0))

        self._status = scene.visuals.Text(
            "VisPy renderer ready",
            color="white",
            anchor_x="left",
            anchor_y="top",
            parent=self._view.scene,
            pos=(10, 10, 0),
        )

        if show_canvas:
            LOGGER.info("VisPy canvas visible at %sx%s", *self._canvas.size)

        self._values = None
        self._vertices = None
        self._faces = None
        self._vertex_colors = None
        self._bar_colors = None
        self._mesh = None
        self._max_value = 1.0
        self._active_indices: set[int] = set()
        self._color_cache: dict[str, Any] = {}
        self._default_color = self._color_from_hex(STEP_COLOR_MAP["default"])
        self._log_fps = _env_flag("VISPY_LOG_FPS", "0")
        self._frame_counter = 0
        self._shutting_down = False

    def reset(
        self, *, n: int | None = None, values: Sequence[int] | None = None
    ) -> None:
        np = _require_numpy()
        self._shutting_down = False
        self._color_cache.clear()
        if values is not None:
            arr = np.asarray(values, dtype=np.float32)
            n = int(arr.size)
        else:
            arr = np.zeros(int(n or 0), dtype=np.float32)
        self._values = arr
        self._max_value = float(arr.max(initial=1.0)) if arr.size else 1.0
        if self._max_value <= 0:
            self._max_value = 1.0
        self._frame_counter = 0
        self._active_indices.clear()
        self._build_geometry()
        self._update_status(f"Elements: {int(n or arr.size)}")
        LOGGER.info("VisPy renderer reset for %d elements", int(n or arr.size))

    def on_step_event(self, event: StepRenderEvent) -> None:
        if self._shutting_down:
            return
        if self._mesh is None or self._values is None or self._values.size == 0:
            return
        np = _require_numpy()
        changed_indices = self._apply_operation(event)
        highlight_indices = self._indices_for_event(event)

        if changed_indices:
            new_max = float(self._values.max(initial=1.0)) if self._values.size else 1.0
            new_max = max(new_max, 1.0)
            if not np.isclose(new_max, self._max_value):
                self._max_value = new_max
                self._update_all_heights()
            else:
                self._update_heights_for_indices(changed_indices)
        else:
            # Ensure we at least refresh heights for highlighted bars if they changed elsewhere.
            self._update_heights_for_indices(highlight_indices)

        self._update_colors(highlight_indices, event)
        self._mesh.set_data(
            vertices=self._vertices,
            faces=self._faces,
            vertex_colors=self._vertex_colors,
        )

        if self._status is not None:
            preview = ", ".join(str(i) for i in list(highlight_indices)[:3])
            suffix = f"[{preview}]" if preview else "(no indices)"
            self._status.text = f"{event.kind} {suffix}"

        self._frame_counter += 1
        if self._log_fps and self._frame_counter % 120 == 0:
            fps = self._canvas.measure_fps()
            if fps:
                LOGGER.info("VisPy renderer FPS ~ %.1f", fps)

    def shutdown(self) -> None:
        self._shutting_down = True
        LOGGER.info("VisPy renderer shutting down")
        try:
            if self._mesh is not None:
                self._mesh.parent = None
        except Exception:  # pragma: no cover - defensive cleanup
            LOGGER.exception("Failed to detach VisPy mesh")
        self._mesh = None
        self._vertices = None
        self._faces = None
        self._vertex_colors = None
        self._bar_colors = None
        try:
            self._canvas.close()
        except Exception:  # pragma: no cover - defensive close
            LOGGER.exception("Failed to close VisPy canvas")
        self._canvas = None
        self._view = None
        self._status = None
        self._values = None
        self._active_indices.clear()

    # ---------- internal helpers -------------------------------------------------

    def _build_geometry(self) -> None:
        np = _require_numpy()
        values = self._values
        if values is None or values.size == 0:
            if self._mesh is not None:
                self._mesh.parent = None
                self._mesh = None
            self._vertices = np.zeros((0, 3), dtype=np.float32)
            self._faces = np.zeros((0, 3), dtype=np.uint32)
            self._vertex_colors = np.zeros((0, 4), dtype=np.float32)
            self._bar_colors = np.zeros((0, 4), dtype=np.float32)
            return

        n = values.size
        spacing = 1.0 / max(n, 1)
        width = spacing * 0.9
        centers = (np.arange(n, dtype=np.float32) + 0.5) * spacing
        x_left = centers - width / 2
        x_right = centers + width / 2
        heights = self._normalized_values()

        vertices = np.zeros((n * 4, 3), dtype=np.float32)
        vertices[0::4, 0] = x_left
        vertices[1::4, 0] = x_left
        vertices[2::4, 0] = x_right
        vertices[3::4, 0] = x_right
        vertices[0::4, 1] = 0.0
        vertices[2::4, 1] = 0.0
        vertices[1::4, 1] = heights
        vertices[3::4, 1] = heights

        faces = np.zeros((n * 2, 3), dtype=np.uint32)
        base = np.arange(0, n * 4, 4, dtype=np.uint32)
        faces[0::2, 0] = base
        faces[0::2, 1] = base + 1
        faces[0::2, 2] = base + 2
        faces[1::2, 0] = base + 2
        faces[1::2, 1] = base + 1
        faces[1::2, 2] = base + 3

        bar_colors = np.tile(self._default_color, (n, 1))
        vertex_colors = np.zeros((n * 4, 4), dtype=np.float32)
        vertex_colors[0::4] = bar_colors
        vertex_colors[1::4] = bar_colors
        vertex_colors[2::4] = bar_colors
        vertex_colors[3::4] = bar_colors

        self._vertices = vertices
        self._faces = faces
        self._bar_colors = bar_colors
        self._vertex_colors = vertex_colors

        if self._mesh is None:
            self._mesh = self._scene.visuals.Mesh(
                vertices=vertices,
                faces=faces,
                vertex_colors=vertex_colors,
                shading=None,
                parent=self._view.scene,
            )
        else:
            self._mesh.set_data(vertices=vertices, faces=faces, vertex_colors=vertex_colors)

        self._view.camera.set_range(x=(0.0, 1.0), y=(0.0, 1.05))

    def _normalized_values(self):
        np = _require_numpy()
        if self._values is None or self._values.size == 0:
            return np.zeros(0, dtype=np.float32)
        return self._values / self._max_value if self._max_value else self._values

    def _apply_operation(self, event: StepRenderEvent) -> set[int]:
        if self._values is None or self._values.size == 0:
            return set()
        changed: set[int] = set()
        if event.op == "swap" and len(event.indices) >= 2:
            i, j = event.indices[:2]
            if 0 <= i < self._values.size and 0 <= j < self._values.size:
                self._values[i], self._values[j] = self._values[j], self._values[i]
                changed.update({i, j})
        elif event.op in {"set", "write", "shift"} and event.indices:
            idx = event.indices[0]
            if 0 <= idx < self._values.size and isinstance(event.payload, (int, float)):
                self._values[idx] = float(event.payload)
                changed.add(idx)
        return changed

    def _indices_for_event(self, event: StepRenderEvent) -> set[int]:
        indices: set[int] = set()
        if event.op == "merge_mark" and len(event.indices) == 2:
            lo, hi = event.indices
            if lo <= hi:
                indices.update(range(int(lo), int(hi) + 1))
        else:
            indices.update(int(i) for i in event.indices)
        if event.op == "merge_compare" and isinstance(event.payload, int):
            indices.add(int(event.payload))
        if event.op == "swap" and len(event.indices) >= 2:
            indices.update(int(i) for i in event.indices[:2])
        # Clamp to dataset size
        if self._values is not None and self._values.size:
            indices = {idx for idx in indices if 0 <= idx < self._values.size}
        return indices

    def _update_heights_for_indices(self, indices: Iterable[int]) -> None:
        if self._vertices is None or self._values is None or self._values.size == 0:
            return
        np = _require_numpy()
        idx_arr = np.array(sorted(set(indices)), dtype=np.int32)
        if idx_arr.size == 0:
            return
        heights = (
            self._values[idx_arr] / self._max_value if self._max_value else self._values[idx_arr]
        )
        base = idx_arr * 4
        self._vertices[base + 1, 1] = heights
        self._vertices[base + 3, 1] = heights

    def _update_all_heights(self) -> None:
        if self._vertices is None:
            return
        np = _require_numpy()
        heights = self._normalized_values()
        if heights.size == 0:
            return
        base = np.arange(0, heights.size * 4, 4, dtype=np.int32)
        self._vertices[base + 1, 1] = heights
        self._vertices[base + 3, 1] = heights

    def _update_colors(self, indices: Iterable[int], event: StepRenderEvent) -> None:
        if self._vertex_colors is None or self._bar_colors is None:
            return
        active = set(indices)
        to_reset = self._active_indices - active
        for idx in to_reset:
            self._apply_color(idx, self._default_color)
        color = self._color_from_hex(event.color())
        for idx in active:
            self._apply_color(idx, color)
        self._active_indices = active

    def _apply_color(self, idx: int, color) -> None:
        if self._bar_colors is None or self._vertex_colors is None:
            return
        if idx < 0 or idx >= self._bar_colors.shape[0]:
            return
        self._bar_colors[idx] = color
        start = idx * 4
        self._vertex_colors[start : start + 4] = color

    def _color_from_hex(self, value: str):
        key = value.lower()
        cached = self._color_cache.get(key)
        if cached is not None:
            return cached.copy()
        hex_str = key.lstrip("#")
        if len(hex_str) != 6:
            raise ValueError(f"Unsupported color value: {value!r}")
        np = _require_numpy()
        rgb = [int(hex_str[i : i + 2], 16) / 255.0 for i in (0, 2, 4)]
        rgba = np.array([*rgb, 1.0], dtype=np.float32)
        self._color_cache[key] = rgba
        return rgba.copy()

    def _update_status(self, text: str) -> None:
        if self._status is not None:
            self._status.text = text
