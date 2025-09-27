# Audit – Current State vs. Roadmap

## Phase 1: Foundations & Architecture
- Project layout (`src/app/...`) ✔
- Registry ✔
- Config/Prefs ✔ (QSettings for FPS/input/theme, VizConfig overrides)
- Logging/crash handler ✔

## Phase 2: Correctness & Tests
- Unit/property tests ✔
- Step replay determinism ✔
- Static quality ✔ (`ruff`, `black`, `mypy`, pre-commit)

## Phase 3: Algorithms
Implemented and fully covered:
- Bubble Sort
- Insertion Sort
- Selection Sort
- Heap Sort
- Shell Sort
- Cocktail Shaker Sort
- Comb Sort
- Quick Sort
- Merge Sort (bottom-up trace)
- Counting Sort
- Radix Sort LSD
- Bucket Sort
- Timsort Trace

Recent polish:
- All comparison sorts now emit a uniform `confirm` sweep so the visualizer highlights completion consistently.
- Algorithm metadata now renders in-app via a dedicated explanations panel (traits, complexity, highlights).
- Preset picker + seeded RNG landed alongside multi-format export (CSV/JSON/PNG/GIF) and a benchmark runner.
- Compare mode delivers linked split-view playback with shared controls and high-contrast theme support.

Outstanding priorities:
1. JSON import & replay scripting (automate round-tripping saved sessions).
2. Performance and distribution: canvas batching/OpenGL experiments, CI matrix, installers.
3. Documentation & community files: user guide, CONTRIBUTING/CODE_OF_CONDUCT, crash-report UX.

## Phase 4: UI/UX Polish
- Legend, manual step controls, value labels DONE
- Remaining high-impact items:
  * Toolbar/menu shortcuts beyond the core controls
  * Additional accessibility polish (focus cues, narration tweaks)

## Phase 5+: Deferred
- Canvas batching / OpenGL backend
- Dynamic FPS reduction when idle/offscreen
- Advanced playback controls
- Replay import tooling, extended benchmark sweep automation
- CI matrix, installers, docs, community files

## Immediate Next Steps (Suggested)
1. Add JSON import/replay tooling so saved sessions round-trip through the UI and CLI alike.
2. Begin the performance/distribution push (canvas batching experiments + CI matrix spin-up).
3. Draft user-facing docs and community files (guide, CONTRIBUTING, CODE_OF_CONDUCT, crash-report UX).
## Latest Regression Run (2024-XX-XX)
- `ruff check` → pass
- `mypy src tests contrast_checker.py` → pass (20+ files)
- `pytest -q` → pass (14 tests)
- `pytest tests/test_step_invariants.py -q` → pass (2 tests)
