# Project Phase Snapshot

This summary captures the current roadmap progress. For the full breakdown, see [ROADMAP.md](ROADMAP.md).

## Phase Status

- **Phase 1 – Foundations**: ✓ complete (project layout, registry, VizConfig, crash-safe logging).
- **Phase 2 – Correctness & Tests**: ✓ complete (property tests, replay determinism, strict mypy/ruff/black).
- **Phase 3 – Algorithms**: ✓ complete
  - Comparison sorts: Bubble, Insertion, Selection, Heap, Shell, Cocktail Shaker, Comb, Quick, Merge.
  - Non-comparison sorts: Counting, Radix LSD, Bucket.
  - Advanced: Timsort Trace.
  - Latest polish: all algorithms emit a final confirm sweep for consistent finish animations.
- **Phase 4 – UI/UX Polish**: In progress
  - TODO: toolbar/menu refinements, additional accessibility improvements.
  - Done: explanations panel, preset picker with seeded RNG and HUD integration, compare mode split view, high-contrast theme toggle.
- **Phase 5 – Performance & Rendering**: Not started
  - Planned: canvas batching, optional OpenGL backend, dynamic FPS throttling, advanced playback controls.
- **Phase 6 – Data, Export & Replay**: In progress
  - Done: deterministic seeds surfaced in HUD, JSON/PNG/GIF export, benchmark mode.
  - TODO: JSON session import, bulk replay tooling, long-run benchmark automation.
- **Phase 7 – CI/CD & Distribution**: Not started
  - Planned: GitHub Actions matrix, installer pipeline, changelog/versioning.

## Next Focus

1. Phase 4 polish (toolbar/menu refinements, accessibility follow-ups).
2. Phase 5 performance enhancements (canvas batching, OpenGL option, idle throttling).
3. Phase 6 replay/import automation (JSON import, batch benchmarks, session scripting).
4. Phase 7 automation/distribution (CI matrix, installers, release process).

Regression suite currently passes (`ruff`, `black --check`, `mypy src tests contrast_checker.py`, `pytest -q`).
