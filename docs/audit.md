# Audit – Current State vs. Roadmap

## Audit_Friday (2025-09-26)

### Snapshot – 2025-09-27 sanity check

Recent inspection (src/app/app.py, core/base.py & player.py, ui_compare/window.py & controller.py, ui_shared/pane.py, tests/test_player.py) surfaced several regressions and incomplete refactors. After the 2025‑09‑27 pass:

- ✅ Launcher split restored – `LauncherWindow` now routes to either `SuiteWindow` (Single) or `CompareWindow` without mixing tabs.
- ✅ Pane adapter complete – `ui_shared/pane.Pane` exposes only public visualizer hooks and forwards Player signals; no more `_advance_step` / `_step_idx` reach-in.
- ✅ Compare panes ride the Player – window/controller exclusively use the pane API; HUD/detail state persists in QSettings and per-pane finish freezes elapsed labels independently.
- ✅ Player contract hardened – jitter/back-pressure still in place; finished fires once; manual stepping triggers completion when totals are known.
- ✅ Prime path capped – `prime_external_run` short-circuits after 10k steps; unknown totals mark `true_total=False` capability and stream live steps.
- ✅ Guard test landed – fails if any test files reference `_on_*`, `_timer`, `_step_idx`, `_show_hud`.
- ℹ️ Shortcuts still originate inside the legacy visualizer; move them onto the pane/player layer during the controller rewrite (slice 2).
- ℹ️ Splitter persistence/detachable panes remain outstanding; geometry keys now persist HUD state only.

Treat the remaining ℹ️ items as the entry point for Slice 2 (controller shortcut unification, detachable panes, splitter persistence).

- **Hot Files To Refactor**
- `src/app/core/base.py` – still a god-object (UI + playback + exports). Next up: pull the remaining timer/shortcut logic into `core/player` and dedicated services.
- `src/app/ui_compare/window.py` – now on the Pane API; focus shifts to splitter persistence, detachable panes, and the shortcut/controller rewrite.
- `src/app/ui_single/window.py` – mirrors the legacy visualizer tabs; update once Pane/Player work solidifies.
- `src/app/app.py` – launcher restored; follow-on is lazy-loading and theme propagation once modules split further.
- `src/app/core/step.py` & `core/player.py` – maintain frozen protocol; add the remaining dataset/export hooks after base.py is slimmed down.
- `tests/` – continue growing coverage for pane capabilities, finished-state behaviour, splitter persistence, and the guard rails (no privates).
- Documented file map (for reference):
  * `src/app/app.py` – launcher + theme management.
  * `src/app/algos/` – individual algorithm generators emitting `Step`.
  * `src/app/core/base.py` – current God-object visualizer; source of most cross-mode coupling.
  * `src/app/core/replay.py` – step replay utilities (tests).
  * `src/app/ui_single/window.py` – tab suite built on `AlgorithmVisualizerBase`.
  * `src/app/ui_compare/window.py` – compare window, controls, splitters, controller wiring.
  * `src/app/ui_compare/controller.py` – transport fan-out (needs upgrade to use public player API).
  * `src/app/ui_shared/{constants,theme}.py` – shared settings/theming.
  * `tests/test_compare_*` – shortcut/step tests currently accessing privates; must transition to public Pane API post-refactor.
 - (done) Tests now rely on the Pane API (`step_index`, `hud_visible`, etc.); guard in place to block private access.
 - (done) Compare controller and panes migrated to the public surface; future work is UX (splitters/layout persistence).
- Persist splitter ratios (controls, pane widths, detail heights) via `QSettings`; add a "Reset layout" command.
- Theme tokens must be applied everywhere (status strip, control labels, pane titles) so white-on-light never happens.

**UI / UX Issues (per screenshots)**
- Provide both horizontal and vertical `QSplitter`s so controls/details can be snapped out, collapsed, or detached into floating panes.
- Default theme renders pane titles/labels white on light backgrounds; apply contrast tokens (`#e6efff` dark, `#102a57` light).
- “Details” view should flip the card and remove the HUD overlay/hud box so charts stay unobscured.
- Full-screen mode must preserve control sizes; splitter ratios should persist via `QSettings` and offer a “reset layout”.

**Functional Gaps**
- Step ◀/▶ rely on `AlgorithmVisualizerBase._on_step_*`, which re-creates generators and halts mid-run; move stepping to a shared `Player` so manual walks reach the end without hitting Start.
- Timer keeps accumulating even after steps finish; emit `finished` per player and stop/update status once both panes complete.
- Keyboard shortcuts vs. buttons need one code path (same player methods) to avoid drift.
- Dataset generation/export/benchmark logic still lives inside `AlgorithmVisualizerBase`; move to dedicated services to prevent UI/file I/O coupling.
- Independent elapsed/timing should be owned by the new `Player`; GUI should only listen to signals.
- Controls/detach UX: current compare splitter only hides controls; add horizontal + vertical splitters with detachable panes and “snap back” behaviour to match UI requirements.
- `_dataset_ready` flag is a stopgap to prevent generator resets; replace with player state so edits don’t null `_current_array` unexpectedly.
- Keyboard `<` / `>` buttons in compare depend on `_on_step_*` and stall mid-run; align with shortcut handler once player API exists.
- Build artefacts (`build/`, `sorting_viz.egg-info/`, `.pytest_cache`, `.hypothesis`) should be cleaned/ignored to prevent stale imports.
- Need a dedicated, headless `measure_algorithm` (or equivalent) using `perf_counter` so benchmark CSVs and UI “true time” don’t depend on UI FPS.
- Expose public Pane/Player API (e.g., `play/pause/step`, `step_index`, `elapsed_seconds`) so tests/controllers avoid `_timer`, `_step_idx`, `_show_hud`.
- `ui_compare/controller.py` still falls back to private `_on_*`; drop fallbacks after pane API exists to prevent future regressions.
- `ui_compare/window.py` continues to touch private fields (`_step_idx`, `_show_hud`, `_on_*`). Needs refactor to public pane surface; details toggle must also hide HUD overlay.
- Splitter sizing/persistence missing: persist control + pane splitters to QSettings; add “Reset layout”; initialize details splitter to sensible ratio.
- No per-pane elapsed display / finish handling in compare window; add labels or summary that freezes on finish while the other pane keeps running.
- Click-to-focus on each canvas (StronFocus + mousePress override) required to guarantee shortcut routing. Currently absent in compare layout.
- Publish a versioned public API contract (e.g., `STEP_SCHEMA_VERSION`, `PLAYER_API_VERSION`) so panes/controllers/tests never touch privates again. Document required methods/properties (`play/pause/step`, `elapsed_seconds`, `step_index`, `toggle_details`).
- Add a capabilities map (supports step_back, elapsed_seconds, detach) so compare/single can feature-gate cleanly.
- Centralize exception/logging: install QApplication hook that logs JSON records (algo, preset, seed, fps, traceback) and shows a non-modal error banner with “copy diagnostics”.
- QSettings management: use `ui_shared.constants` as a single source of keys, add migration stubs when keys move, persist seeds per run for reproducibility/export.
- Headless benchmarking should be the source of truth: GUI shows both visual elapsed and headless `measure_algorithm` time.
- Performance guardrails: frame-budget watchdog (warn if paint > 16 ms @ 60 fps), optional OpenGL/batched painter behind a feature flag, avoid allocations in paint path.
- Jitter smoothing/back-pressure: Player should schedule ticks against perf_counter (ideal t*) with jitter budget (~10 ms), step caps (per tick/per second), and emit backpressure telemetry when throttling engages.
- Testing enhancements: add elapsed-vs-FPS test, independent finish test, splitter persistence test, detach/reattach test (when docking lands).
- Plugin surface: plan for algorithm/dataset plugins (entry points or folder scan) with validation and safety limits (max array size, step rate).
- Packaging & CI: ignore build artefacts, run `ruff`, `mypy`, `pytest -q` in CI; consider optional Qt snapshot tests; prep PyInstaller/Briefcase bundles.
- Security/I/O: sanitize export paths, validate JSON imports, avoid `eval` for configs.
- UX/Docs: add “Reset layout/theme” menu item; document timing decoupling, compare workflow, and a minimal user guide.
- Repository hygiene: update `.gitignore` for `build/`, `dist/`, `*.egg-info/`, `.pytest_cache/`, `.hypothesis/`; clean tracked caches.

**Repository Inventory (issues & owners)**
- Root: remove `build/`, `sorting_viz.egg-info/`, `.pytest_cache`, `.hypothesis` from VCS; add to `.gitignore`.
- `main.py`: CLI shim mutating `sys.path`; long term replace with proper console entry point.
- `pyproject.toml`/`requirements.txt`: align dev/test dependencies with planned CI matrix (ruff, mypy, pytest, hypothesis).
- `src/app/app.py`: launcher duplicates CSS with compare window; consolidate styling; ensure lazy imports still valid post-refactor.
- `src/app/ui_shared/theme.py`: currently tooltip-only; must expose palette tokens + global stylesheet so cards/labels/buttons respect contrast and themes remain consistent.
- `src/app/core/base.py`: God object—contains playback timer, dataset/export, HUD, benchmarking, shortcuts. High-risk coupling; must be split into `core/player.py` + service modules + thin view.
- `src/app/core/replay.py`: applies `Step` sequences; confirm naming consistent (uses `indices`).
- `src/app/ui_single/window.py`: instantiates `AlgorithmVisualizerBase` directly; replace with pane wrapper (splitter + details), add lazy tab creation, persist per-algorithm splitter state, and expose elapsed readout using public pane API.
- `src/app/ui_compare/window.py`: improved but still manipulates base internals; lacks detachable panes, splitter persistence, full contrast fixes, and independent timing.
- `src/app/ui_compare/controller.py`: calls `_on_*` privates; replace with pane/player API once exposed.
- `src/app/ui_shared/constants.py`: only holds org/app names; add centralized QSettings keys, layout metrics, feature flags, and a helper `settings()` so callers stop hardcoding strings.
- `src/app/presets/*`: dataset generation; candidate for `services/dataset.py` extraction.
- `src/app/algos/*`: emit `Step`; add consistent instrumentation (compare/swap steps, final confirm sweep and confirm per-pass where relevant), upgrade metadata (complexities, stability, non-comparison flags), and guard algorithms (e.g., counting sort on negatives). Implement registry validation to enforce required fields. Selection/Shell currently miss confirm sweeps; Timsort trace emits sparse steps and needs documentation/decisions on fidelity.
- Tests (`tests/test_compare_*`): access privates (`_step_idx`, `_show_hud`); refactor once public API exists.
- `tests/test_compare_shortcuts.py` and `tests/test_compare_step_manual.py` currently assert on private fields (`_step_idx`, `_show_hud`) and call private helpers (`_on_step_forward`). Once the pane/player API lands, update these tests to use public accessors (`step_index`, `elapsed_seconds`, `toggle_details`) and drive behaviour via the controller/pane surface.
- Remaining tests (`test_step_*`, `test_export_serialization.py`, etc.): keep running post-refactor.
- `native/radix_simd.cpp`: unused; decide to integrate or remove.

**Public API & Logging Requirements**
- Define `STEP_SCHEMA_VERSION = 1` and `PLAYER_API_VERSION = 1`; document required methods/properties for Player/Panes (`play`, `pause`, `toggle_pause`, `step_forward`, `step_back`, `reset`, `elapsed_seconds`, `step_index`, `set_hud_visible`, `toggle_details`, `details_visible`).
- Expose `capabilities` per pane (e.g., `{"step_back": True, "detach": False, "true_time": True}`) so UI feature-gates without probing internals.
- Install a global QApplication exception/logging hook that writes structured JSON (algo, preset, seed, fps, traceback, timestamp) and shows a non-modal error banner with “Copy diagnostics”.
- Use headless timing (`replay.measure_algorithm()` + `perf_counter`) as source of truth; GUI displays Visual elapsed and True time side by side.
- Persist run seeds in QSettings and exported artifacts for reproducibility; include in logs/benchmarks.
- Implement `validate_registry()` to enforce algorithm metadata completeness and uniqueness.

**Success Criteria (“Done Means”)**
- `core/player.py`
  * Manual stepping traverses entire run without invoking Start.
  * `elapsed_seconds()` independent of FPS; per-pane finish emits once.
  * Resets idempotent; unit tests cover play/pause/step/back/reset/error paths.
- `ui_compare`
  * Controller/window never touch private attributes (`_timer`, `_step_idx`, `_on_*`, `_show_hud`).
  * Details toggle hides HUD; canvases unobscured; click-to-focus routes shortcuts correctly.
  * Per-pane elapsed labels update/freeze independently; splitters persist and “Reset layout/theme” restores defaults.
  * Pane exposes `capabilities` map for feature gating.
- `ui_single`
  * Pane wrapper (vertical splitter + details) with lazy tab init.
  * Per-algorithm splitter state persisted/restored; elapsed label wired to `elapsed_seconds()`.
- Algorithms
  * Consistent compare/swap instrumentation; confirm sweep at end/per pass.
  * Guard invalid domains (e.g., counting negatives); metadata complete; registry validation passes.
- Tests
  * No private attribute access (CI guard). New tests cover elapsed-vs-FPS decoupling, independent finish, splitter persistence/reset, and detach/reattach (post-docking).
- Theme/Settings
  * Palette tokens applied globally; QSettings keys centralized with migrations.
- Packaging/CI/Docs
  * CI runs `ruff`, `mypy`, `pytest -q` (optional Qt snapshots). Repo ignores artefacts; PyInstaller/Briefcase builds verified. Docs explain timing decoupling, compare workflow, reset/layout tools, and diagnostics.

**Testing & QA Plan**
- Unit: add coverage for the new `core/player.py`, dataset/export services, and detached-pane helpers.
- Integration: pane stepping to completion, compare sync, splitter snap/detach behaviour, theme contrast assertions.
- Visual/Snapshot: capture canvas frames at key steps to catch HUD/label regressions.
- CI: run full `pytest` (headless) + lint/type checks; keep visual tests as optional manual gate.
- Acceptance: work items only marked complete after local QA run (manual Step/Start/Detach flows) and your sign-off.
- Add success criteria per work item (see section below) so “done” is objectively testable.


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
1. Restore the launcher choice (Single vs Compare) and untangle the tabbed MainWindow so the two surfaces boot independently.
2. Finish Slice 1: wire Compare panes through `ui_shared/pane.Pane` + `core/player.Player` only (no `_advance_step`), migrate shortcuts/timer ownership to Player, and update tests to assert no private attr access.
3. Rework `prime_external_run()` (or the new Player API) so dataset primes do not block the UI; add HUD persistence and per-pane finished/elapsed handling before tackling detachable panes.
## Latest Regression Run (2024-XX-XX)
- `ruff check` → pass
- `mypy src tests contrast_checker.py` → pass (20+ files)
- `pytest -q` → pass (14 tests)
- `pytest tests/test_step_invariants.py -q` → pass (2 tests)
- Documented file map (for reference):
  * `src/app/app.py` – launcher + theme management.
  * `src/app/algos/` – individual algorithm generators emitting `Step`.
  * `src/app/core/base.py` – current God-object visualizer; source of most cross-mode coupling.
  * `src/app/core/replay.py` – step replay utilities (tests).
  * `src/app/ui_single/window.py` – tab suite built on `AlgorithmVisualizerBase`.
  * `src/app/ui_compare/window.py` – compare window, controls, splitters, controller wiring.
  * `src/app/ui_compare/controller.py` – transport fan-out (needs upgrade to use public player API).
  * `src/app/ui_shared/{constants,theme}.py` – shared settings/theming.
  * `tests/test_compare_*` – shortcut/step tests currently accessing privates; must transition to public Pane API post-refactor.

**Outstanding Problems Snapshot**
- `AlgorithmVisualizerBase` still owns QTimer, dataset generation, export, benchmarking, HUD, and playback state. Consumers (compare/single/tests) reach into `_timer`, `_step_source`, `_on_step_*` causing crashes when swapped. → Extract `core/player.py` + dataset/export services; leave base.py as pure view.
- Manual step buttons call `_on_step_forward/_on_step_back`, which rebuild generators via `_ensure_dataset()`; stepping halts mid-run. → After player split, use `player.step_once()` to walk entire trace.
- Timers keep accumulating after completion; compare doesn’t stop elapsed clock on one side. → Player must own `perf_counter` bookkeeping per pane and emit `finished`.
- Compare controller falls back to private methods (`_on_start` etc.). → Publish a stable Pane API (`play/pause/step/reset/current_step/elasped_s`) and refactor controller/tests accordingly.
- UI splitters lack persistence/detach logic. Controls can be hidden but not dragged into separate panes, and ratios reset each launch. → Store in `QSettings`, add “Reset layout”, implement detachable panes (dock or floating widgets).
- Theme contrast: pane titles, status strip, preset labels still render white on light backgrounds. → Apply palette tokens to every label and status element.
- Prime path blocks UI on large inputs – `prime_external_run()` materialises every step before playback. → Move counting into Player (lazy iterator) or background worker with progress + guardrails.
- Dataset/export logic still in base widget. → Move to `services/dataset.py` / `services/export.py`, keep UI async-safe.
- Tests `test_compare_shortcuts.py` / `test_compare_step_manual.py` assert `_step_idx`, `_show_hud`. → Replace with public getters and signal-driven assertions. Add new tests for elapsed-vs-FPS decoupling, independent finish, splitter persistence/reset, and (once docking lands) detach/reattach behaviour.
- `src/app/core/compare.py` is a compatibility shim; remove once UI modules import directly to avoid confusion.
- Build artefacts (`build/`, `sorting_viz.egg-info/`, `.pytest_cache`, `.hypothesis`) should be ignored/clean to prevent stale imports; clean currently tracked `.hypothesis/` constants/examples and add ignore entries.
