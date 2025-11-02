# 🧩 Sorting Algorithm Visualizer

> **Project status:** The **Single Visualizer** experience is production-ready. **Compare Mode** ships in this repository but is still under active development and not ready for everyday use yet.

A PyQt6 desktop playground for exploring classic sorting algorithms through deterministic, step-by-step animation. Every frame comes from a concrete `Step` object emitted by the algorithm, making runs reproducible, exportable, and easy to replay for teaching or research.

---

## Gallery

- Bubble Sort  
  <img width="1196" height="863" alt="Bubble Sort" src="https://github.com/user-attachments/assets/d0890b71-0cf3-4524-852b-1460731cac60" />
- Insertion Sort  
  <img width="1196" height="862" alt="Insertion Sort" src="https://github.com/user-attachments/assets/3efada78-2c30-4170-8ea4-e0770952a4e0" />
- Merge Sort  
  <img width="1198" height="870" alt="Merge Sort" src="https://github.com/user-attachments/assets/b39540ec-da03-49f7-83c7-a479b16e32f0" />
- Quick Sort  
  <img width="1192" height="869" alt="Quick Sort" src="https://github.com/user-attachments/assets/d429b449-798e-4d88-b59a-f573cc720f6b" />
- CSV Export workflow  
  <img width="1191" height="873" alt="CSV Export" src="https://github.com/user-attachments/assets/6da7494c-9210-465f-bb83-a0428e118929" />

---

## Feature Highlights

- **Single Visualizer (stable):** One tab per algorithm with synced HUD, narration, export tools, theme toggle, and keyboard/mouse controls.
- **Compare Mode (WIP):** Launch a dual-pane workspace from the launcher to evaluate two algorithms side by side. The UI loads, but final UX polish, keyboard overrides, and replay parity are still in progress—treat this as a preview build.
- **Deterministic algorithm engine:** Bubble, Insertion, Selection, Heap, Shell, Merge (bottom-up), Quick (median-of-three), Cocktail, Counting, Radix (LSD), Bucket, Comb, and a Timsort trace all register through a plugin system and emit strongly typed `Step` records.
- **Reproducible data presets:** Generate random, nearly-sorted, reverse, reverse-run, few-unique, or already-sorted datasets with a visible seed so anyone can recreate a run exactly.
- **Instrumented playback:** Stepping, scrubbing, and timed playback all derive from the same checkpointed replay buffer. You can always step backward or jump to any frame without drift.
- **Export & benchmark suite:** Export traces to CSV/JSON/PNG/GIF and run a batch benchmark that sweeps algorithms against the active dataset configuration and writes a CSV report.
- **Accessibility & persistence:** Dark and high-contrast themes, tooltip theming, saved window geometry, FPS, presets, and the last custom array all round-trip through `QSettings`.
- **Robust logging:** A hardened `sys.excepthook` writes to a rotating log via `platformdirs` (if available) before surfacing runtime errors in the UI.

---

## Quick Start

### 1. Requirements

- Python 3.10 or newer
- Qt runtime (bundled automatically via `PyQt6`)
- macOS, Windows, or Linux desktop environment

### 2. Install dependencies

Clone the repository, then choose one of the following setup paths:

```bash
# macOS / Linux
./scripts/setup.sh
```

```batch
:: Windows
scripts\setup.bat
```

Both scripts create `.venv/`, activate it temporarily, and install `requirements.txt`.  
Prefer manual setup? Run the equivalent commands yourself:

```bash
python -m venv .venv
source .venv/bin/activate  # .venv\Scripts\activate on Windows
pip install -r requirements.txt
```

### 3. Launch the app

From the project root:

```bash
python main.py
```

You will land on the launcher window:

1. **Single Visualizer** loads the production-ready tabbed workspace.  
2. **Compare Mode** opens the in-progress dual-pane view. Use it for exploratory testing only—the UX and determinism guarantees are still being finalized.

---

## Working with the Single Visualizer

- Enter comma-separated integers or click **Randomize** to use the active preset/seed.
- Use **Play**, **Step ▶**, **Step ◀**, the timeline slider, or keyboard shortcuts to navigate. Every action replays the canonical `Step` sequence—no frame skipping.
- Toggle **Show values** at small `n` to annotate each bar.
- Click **Export** to choose CSV, JSON, PNG, or GIF. PNG renders the current canvas. GIF synthesizes the animation from captured frames; you must play through the run first.
- Hit **Benchmark** to produce `benchmark.csv` with wall-clock timing for every registered algorithm against the current preset (including any custom array).
- The **Details** pane surfaces algorithm notes, complexity tables, and metadata pulled from the registry.
- **View → High Contrast Mode** switches to a light theme. **View → Show Debug Panel** reveals live internals (player state, timers, recent steps) for the active tab.

---

## Algorithm Catalog

| Algorithm          | Category        | Stable | In-place | Typical Complexity (best / avg / worst) | Notes |
|--------------------|-----------------|--------|----------|-----------------------------------------|-------|
| Bubble Sort        | Comparison      | ✓      | ✓        | O(n) / O(n²) / O(n²)                    | Early exit once no swaps occur; ideal baseline for demos. |
| Insertion Sort     | Comparison      | ✓      | ✓        | O(n) / O(n²) / O(n²)                    | Highlights key vs. shift operations with distinct colors. |
| Selection Sort     | Comparison      | ✗      | ✓        | O(n²) / O(n²) / O(n²)                   | Emits compare/swap pairs to visualize the selection process. |
| Heap Sort          | Comparison      | ✗      | ✓        | O(n log n)                              | Instrumented heapify and pop phases with pivot highlights. |
| Shell Sort         | Comparison      | ✗      | ✓        | O(n log n) average                       | Uses Pratt-inspired gap sequence; shows gap comparisons distinctly. |
| Merge Sort (BU)    | Comparison      | ✓      | ✗        | O(n log n)                              | Bottom-up merges with violet merge markers and auxiliary array snapshots. |
| Quick Sort         | Comparison      | ✗      | ✓        | O(n log n) / O(n log n) / O(n²)         | Median-of-three pivot selection with pivot/bounds instrumentation. |
| Cocktail Shaker    | Comparison      | ✓      | ✓        | O(n) / O(n²) / O(n²)                    | Bi-directional pass emphasises swap direction changes. |
| Comb Sort          | Comparison      | ✗      | ✓        | O(n log n) average                       | Gap shrink factor 1.3 with final bubble clean-up. |
| Counting Sort      | Non-comparison  | ✓      | ✗        | O(n + k)                                | Tracks histogram, prefix sums, and stable placements. |
| Radix Sort (LSD)   | Non-comparison  | ✓      | ✗        | O(d (n + k))                            | Offsets negatives once then streams digit passes through Counting Sort. |
| Bucket Sort        | Non-comparison  | ✓      | ✗        | O(n) average / O(n²) worst              | Normalizes values into buckets and sorts each with Python’s Timsort. |
| Timsort Trace      | Hybrid          | ✓      | ✗        | O(n) / O(n log n) / O(n log n)          | Replays Python’s run-detection logic, merges, and galloping breakpoints. |

All algorithms emit immutable `Step` objects so the UI, export system, and property tests remain in lock-step. Replaying the recorded steps produces the exact sorted output you would get from `sorted(data)`.

---

## Under the Hood

- **Step model (`src/app/core/step.py`):** Defines the allowed operations (`compare`, `swap`, `set`, `pivot`, `merge_mark`, etc.) and enforces immutability for deterministic replay.
- **Algorithm registry (`src/app/algos/registry.py`):** Decorators register algorithms with metadata (`stable`, `in_place`, complexity notes, description). `load_all_algorithms()` eagerly imports every module so the UI and tests can enumerate them.
- **Visualizer base (`src/app/core/base.py`):** Contains the shared control bar, canvas rendering, checkpointed replay buffer, export/benchmark logic, preset management, narration, and log viewer hooks.
- **Presets (`src/app/presets/__init__.py`):** Central place for dataset generators. Each preset records its key, label, description, and generator callable.
- **UI layers:**
  - `ui_single/` holds the production tabbed window (`SuiteWindow`) and hook-up for the debug dock and theme switching.
  - `ui_compare/` houses the still-evolving compare workspace. It already synchronizes seeds, playback, and presets, but expect UX rough edges.
  - `ui_shared/` packages reusable widgets (pane HUD, theme helpers, constants, narration cards).
- **Core replay helpers (`src/app/core/player.py`, `replay.py`, `compare.py`):** Encapsulate forward/back stepping, GIF frame capture, and dual-pane synchronization.
- **Native experiments:** `native/radix_simd.cpp` is a standalone NEON prototype for fast digit counting. It is not required for normal operation but documents future optimization ideas.

---

## Developer Workflow

Install development tooling:

```bash
pip install -e .[dev]
```

Useful commands:

```bash
ruff check src tests
black --check src tests
mypy src
pytest
```

- `tests/` contains property-based checks (Hypothesis), deterministic replay validation, keyboard shortcut coverage, export serialization, and UI smoke tests.
- `debug_controls.py` adds instrumentation widgets used by several tests—launch with `python debug_controls.py` if you need to inspect signals manually.
- Logs live under `~/Library/Logs/org.pysort/sorting-visualizer/` on macOS or the platformdirs equivalent on other OSes. The app falls back to `./logs/` if platformdirs is unavailable.
- `docs/ROADMAP.md` tracks upcoming milestones; `docs/audit.md` and `docs/phase.md` store UX and technical audits.

---

## Repository Layout

```
UI_UPDATE_PYSORT/
├── main.py                  # Entry point that boots the PyQt6 application
├── src/
│   └── app/
│       ├── algos/           # Algorithm implementations + registry
│       ├── core/            # Visualization engine, replay, exports
│       ├── presets/         # Dataset generators and metadata
│       ├── ui_single/       # Production-ready single visualizer window
│       ├── ui_compare/      # Experimental compare mode
│       └── ui_shared/       # Reusable widgets, panes, themes, constants
├── scripts/
│   ├── setup.sh             # macOS/Linux bootstrap (venv + pip install)
│   └── setup.bat            # Windows bootstrap (venv + pip install)
├── tests/                   # Pytest + Hypothesis suite
├── docs/                    # Roadmap, audits, supporting notes
├── native/radix_simd.cpp    # Optional SIMD prototype
├── requirements.txt         # Runtime dependencies
├── pyproject.toml           # Build, lint, and type-check configuration
└── README.md
```

---

## Roadmap & Known Gaps

- **Compare Mode polish:** Remaining work includes narration parity with Single Visualizer, better keyboard shortcuts, synchronized benchmarking, and enhanced detail panes. Treat current Compare Mode sessions as beta quality.
- **Packaging & distribution:** Installers and CI pipelines are tracked in `docs/ROADMAP.md` and not yet implemented—run from source for now.
- **Documentation:** CONTRIBUTING guidelines and an in-depth user guide are planned. This README, roadmap, and inline code comments are the authoritative references today.

---

## License & Support

- License: Educator Non-Commercial (see `LICENSE.txt`). Contact the maintainer for commercial usage.
- Maintainer: **Justin Guida** — justn.guida@snhu.edu
- Please include exported step traces (`Export → CSV`) and the RNG seed when reporting bugs.

Enjoy exploring the algorithms—and remember that Compare Mode is still maturing, so rely on the Single Visualizer for demos, classrooms, and production scenarios.
