# 🧩 Sorting Algorithm Visualizer

A PyQt6 desktop playground for exploring classic sorting algorithms through deterministic, step-by-step animation. Every frame comes from a concrete `Step` object emitted by the algorithm, making runs reproducible, exportable, and easy to replay for teaching or research.


## Demo

https://github.com/user-attachments/assets/f12479b1-5313-40b8-a8ac-8794449105e7


## Algorithm Visualizations

### Bubble Sort
<img width="1196" height="863" alt="Bubble Sort" src="https://github.com/user-attachments/assets/d0890b71-0cf3-4524-852b-1460731cac60" />

### Insertion Sort
<img width="1196" height="862" alt="Insertion Sort" src="https://github.com/user-attachments/assets/3efada78-2c30-4170-8ea4-e0770952a4e0" />

### Merge Sort
<img width="1198" height="870" alt="Merge Sort" src="https://github.com/user-attachments/assets/b39540ec-da03-49f7-83c7-a479b16e32f0" />

### Quick Sort
<img width="1192" height="869" alt="Quick Sort" src="https://github.com/user-attachments/assets/d429b449-798e-4d88-b59a-f573cc720f6b" />

### CSV Export
<img width="1191" height="873" alt="CSV Export" src="https://github.com/user-attachments/assets/6da7494c-9210-465f-bb83-a0428e118929" />


## Feature Highlights

- **Single Visualizer:** One tab per algorithm with synced HUD, narration, export tools, theme toggle, and keyboard/mouse controls. Manual input fields automatically apply values 1.5 seconds after you stop typing.
- **Compare Mode (Fixed!):** Launch a dual-pane workspace from the launcher to evaluate two algorithms side by side. Recent fixes ensure proper synchronization and stepping behavior between both panes.
- **Deterministic algorithm engine:** Bubble, Insertion, Selection, Heap, Shell, Merge (bottom-up), Quick (median-of-three), Cocktail, Counting, Radix (LSD), Bucket, Comb, and a Timsort trace all register through a plugin system and emit strongly typed `Step` records.
- **Reproducible data presets:** Generate random, nearly-sorted, reverse, reverse-run, few-unique, or already-sorted datasets with a visible seed so anyone can recreate a run exactly.
- **Instrumented playback:** Stepping, scrubbing, and timed playback all derive from the same checkpointed replay buffer. You can always step backward or jump to any frame without drift.
- **Export & benchmark suite:** Export traces to CSV/JSON/PNG/GIF and run a batch benchmark that sweeps algorithms against the active dataset configuration and writes a CSV report.
- **Metrics Verification Tool:** New `scripts/verify_metrics.py` allows offline verification of algorithm metrics including step counts, comparisons, swaps, and inversion counts.
- **Accessibility & persistence:** Dark and high-contrast themes, tooltip theming, saved window geometry, FPS, presets, and the last custom array all round-trip through `QSettings`.
- **Robust logging:** A hardened `sys.excepthook` writes to a rotating log via `platformdirs` (if available) before surfacing runtime errors in the UI.
- **Comprehensive test suite:** Over 30 test files covering UI components, algorithm correctness, keyboard shortcuts, replay determinism, export serialization, and property-based testing with Hypothesis.


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

From the project root, choose one of these methods:

**Option A: Direct launch** (requires manual venv activation)
```bash
python main.py
```

**Option B: Automated launch script** (handles venv and dependencies automatically)
```bash
# macOS / Linux
./scripts/run.sh

# Or use the Python version (cross-platform)
python scripts/run.py
```

The automated scripts (`run.sh` and `run.py`) will create the virtual environment if needed, install/update dependencies, and launch the app—ideal for quick development.

You will land on the launcher window:

1. **Single Visualizer** loads the production-ready tabbed workspace.
2. **Compare Mode** opens a dual-pane view to compare different algorithms' runtimes against each other.


## Working with the Single Visualizer or Compare Mode

### Single Visualizer
- Enter comma-separated integers in the input field (numbers are automatically applied 1.5 seconds after you stop typing) or click **Generate** to use the active preset/seed.
- Use **Start**, **Step ▶**, **Step ◀**, the timeline slider, or keyboard shortcuts to navigate. Every action replays the canonical `Step` sequence—no frame skipping.
- Toggle **Show values** at small `n` to annotate each bar.
- Click **Export** to choose CSV, JSON, PNG, or GIF. PNG renders the current canvas. GIF synthesizes the animation from captured frames; you must play through the run first.
- Hit **Benchmark** to produce `benchmark.csv` with wall-clock timing for the active algorithm (three sequential seeds per preset, including any custom array).
- The **Details** pane surfaces algorithm notes, complexity tables, and metadata pulled from the registry.

### Compare Mode (Recently Fixed!)
- Launch two algorithms side by side for direct comparison
- Synchronized playback controls affect both panes simultaneously
- Independent algorithm selection for each pane
- Shared dataset configuration ensures fair comparison
- Fixed stepping behavior ensures both algorithms advance in sync
- Perfect for teaching algorithm efficiency differences

### UI Features
- **View → High Contrast Mode** switches to a light theme
- **View → Show Debug Panel** reveals live internals (player state, timers, recent steps) for the active tab
- **Auto-apply input** with 1.5-second debouncing prevents accidental changes while typing
- **Keyboard shortcuts** for all major functions (Space for play/pause, Left/Right arrows for stepping, etc.)


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
| Cocktail Shaker    | Comparison      | ✓      | ✓        | O(n) / O(n²) / O(n²)                    | Bi-directional pass emphasizes swap direction changes. |
| Comb Sort          | Comparison      | ✗      | ✓        | O(n log n) average                       | Gap shrink factor 1.3 with final bubble clean-up. |
| Counting Sort      | Non-comparison  | ✓      | ✗        | O(n + k)                                | Tracks histogram, prefix sums, and stable placements. |
| Radix Sort (LSD)   | Non-comparison  | ✓      | ✗        | O(d (n + k))                            | Offsets negatives once then streams digit passes through Counting Sort. |
| Bucket Sort        | Non-comparison  | ✓      | ✗        | O(n) average / O(n²) worst              | Normalizes values into buckets and sorts each with Python's Timsort. |
| Timsort Trace      | Hybrid          | ✓      | ✗        | O(n) / O(n log n) / O(n log n)          | Replays Python's run-detection logic, merges, and galloping breakpoints. |

All algorithms emit immutable `Step` objects so the UI, export system, and property tests remain in lock-step. Replaying the recorded steps produces the exact sorted output you would get from `sorted(data)`.


## Under the Hood

- **Step model (`src/app/core/step.py`):** Defines the allowed operations (`compare`, `swap`, `set`, `pivot`, `merge_mark`, etc.) and enforces immutability for deterministic replay.
- **Algorithm registry (`src/app/algos/registry.py`):** Decorators register algorithms with metadata (`stable`, `in_place`, complexity notes, description). `load_all_algorithms()` eagerly imports every module so the UI and tests can enumerate them.
- **Visualizer base (`src/app/core/base.py`):** Contains the shared control bar, canvas rendering, checkpointed replay buffer, export/benchmark logic, preset management, narration, and log viewer hooks. Recent updates improve UI integration and input handling.
- **Player module (`src/app/core/player.py`):** Enhanced with proper state management and synchronization features for compare mode.
- **Presets (`src/app/presets/__init__.py`):** Central place for dataset generators. Each preset records its key, label, description, and generator callable.
- **UI layers:**
  - `ui_single/` holds the production tabbed window (`SuiteWindow`) and hook-up for the debug dock and theme switching.
  - `ui_compare/` houses the compare workspace with fixed synchronization and stepping logic.
  - `ui_shared/` packages reusable widgets (pane HUD, theme helpers, constants, narration cards) with enhanced functionality.
- **Core replay helpers (`src/app/core/player.py`, `replay.py`, `compare.py`):** Encapsulate forward/back stepping, GIF frame capture, and dual-pane synchronization.
- **Native experiments:** `native/radix_simd.cpp` is a standalone NEON prototype for fast digit counting. It is not required for normal operation but documents future optimization ideas.


## Developer Workflow

### Development Setup

Install development tooling:

```bash
pip install -e .[dev]
```

### Code Quality Tools

```bash
# Linting and formatting
ruff check src tests
black --check src tests

# Type checking
mypy src

# Run test suite
pytest

# Run specific test categories
pytest tests/test_compare_integration.py  # Compare mode tests
pytest tests/test_export_serialization.py  # Export functionality tests
pytest tests/test_ui_components.py         # UI component tests
```

### Metrics Verification

The new `verify_metrics.py` script allows offline verification of algorithm behavior:

```bash
# Run metrics verification for specific presets and seeds
python scripts/verify_metrics.py --preset reverse_run --seed 34554345 34554346

# Output to CSV for analysis
python scripts/verify_metrics.py --preset random --csv verify_test.csv
```

This tool helps validate that algorithms produce expected step counts, comparisons, swaps, and maintain deterministic behavior across runs.

### Testing

- `tests/` contains comprehensive test coverage:
  - Property-based checks using Hypothesis
  - Deterministic replay validation
  - Keyboard shortcut coverage
  - Export serialization tests (recently updated)
  - UI smoke tests
  - Compare mode integration tests with full stepping verification

### Logging

- Logs live under `~/Library/Logs/org.pysort/sorting-visualizer/` on macOS or the platformdirs equivalent on other OSes
- The app falls back to `./logs/` if platformdirs is unavailable
- Comprehensive error handling with rotating log files

### Documentation

- `docs/ARCHITECTURE.md` provides comprehensive system architecture overview
- `docs/3D_VISUALIZATION_FEATURES.md` documents 3D visualization capabilities
- Inline code comments provide implementation details

### Feature Flags & Rollback

- `USE_STEP_TRANSLATOR` enables the normalized step-to-render pipeline that both 2D and upcoming 3D
  renderers consume. Set it before launching the app:
  ```bash
  USE_STEP_TRANSLATOR=1 python main.py
  ```
  Leaving it unset (or `0`) keeps the legacy path active.
- `USE_3D_RENDERER` (experimental) turns on the VisPy spike that consumes `StepRenderEvent` data. Enable
  it alongside the translator flag:
  ```bash
  USE_STEP_TRANSLATOR=1 USE_3D_RENDERER=1 python main.py
  ```
  The renderer logs its status (`3D renderer ready for N elements`) and falls back automatically if
  VisPy is unavailable. For local debugging you can surface the VisPy canvas with
  `VISPY_SHOW_CANVAS=1`.
- When the translator flag is on, the HUD shows translator timing and the log records an entry such as
  `Step translator avg=0.0123 ms over 143 steps`. On macOS logs live under
  `~/Library/Logs/org.pysort/sorting-visualizer/`; other platforms follow the `platformdirs`
  location, falling back to `./logs/`.
- If a regression is reported in production, launch with `USE_STEP_TRANSLATOR=0` to fall back instantly
  while you investigate. We’ll flip the default to `1` once the new renderer has soaked in production.

### Upcoming Renderer Milestones

The translator telemetry (~0.7 µs/step across algorithms) unlocks the next phase of renderer work:

1. **VisPy/pyqtgraph spike** – prototype instanced bars that consume `StepRenderEvent` objects while the
   2D canvas remains the default via the feature flag.
2. **Dual-render integration** – add a 3D pane behind an opt-in toggle; compare translator timings and
   frame rates with the HUD data.
3. **Flip default & soak** – once stable, default `USE_STEP_TRANSLATOR` to `1`, keep the env flag for
   rollback, and gather production telemetry before removing the legacy path.


## Repository Layout

```
pysort-visualizer/                # Project root directory
├── main.py                       # Entry point that boots the PyQt6 application
├── src/
│   └── app/
│       ├── algos/                # Algorithm implementations + registry
│       │   ├── bubble.py         # Recently enhanced with better instrumentation
│       │   ├── insertion.py      # Updated with improved step tracking
│       │   └── ...               # 13 total algorithm implementations
│       ├── core/                 # Visualization engine, replay, exports
│       │   ├── base.py           # Recently refactored for better UI integration
│       │   ├── player.py         # Enhanced with compare mode fixes
│       │   └── ...
│       ├── presets/              # Dataset generators and metadata
│       ├── ui_single/            # Single visualizer window
│       ├── ui_compare/           # Compare mode (recently fixed!)
│       └── ui_shared/            # Reusable widgets with enhanced functionality
├── scripts/
│   ├── setup.sh                  # macOS/Linux bootstrap (venv + pip install)
│   ├── setup.bat                 # Windows bootstrap (venv + pip install)
│   ├── run.sh                    # macOS/Linux automated launcher
│   ├── run.py                    # Cross-platform automated launcher
│   └── verify_metrics.py         # NEW: Metrics verification tool
├── tests/                        # Comprehensive test suite (30+ test files)
├── docs/                         # Roadmap, audits, supporting notes
├── native/radix_simd.cpp         # Optional SIMD prototype
├── requirements.txt              # Runtime dependencies
├── pyproject.toml                # Build, lint, and type-check configuration
└── README.md                     # This file
```


## Recent Updates

### Compare Mode Fix
- Fixed synchronization issues between dual panes
- Proper stepping behavior now ensures both algorithms advance correctly
- Enhanced state management for consistent playback

### Input Handling Improvements
- Auto-apply input with 1.5-second debounce timer
- Prevents animation restart when sorted array is detected
- Better HUD display and input field state management

### Core Module Refactoring
- Updated `base.py` and `player.py` for better UI integration
- Enhanced `pane.py` in ui_shared for improved functionality
- Removed deprecated `debug_controls.py` module

### New Tools
- Added `verify_metrics.py` for offline algorithm metrics verification
- Supports CSV output for detailed analysis
- Validates step counts, comparisons, swaps, and inversions


## Roadmap & Known Gaps

- **Packaging & distribution:** Installers and CI pipelines are tracked in `docs/ROADMAP.md` and not yet implemented—run from source for now.
- **Documentation:** CONTRIBUTING guidelines and an in-depth user guide are planned. This README, roadmap, and inline code comments are the authoritative references today.
- **Performance optimizations:** SIMD implementations for certain algorithms are experimental (see `native/radix_simd.cpp`).
- **Additional algorithms:** Future additions may include Introsort, Gnome Sort, and other educational algorithms.


## License & Support

- **License:** Educator Non-Commercial (see `LICENSE.txt`). Contact the maintainer for commercial usage.
- **Maintainer:** Justin Guida — justn.guida@snhu.edu
- **Repository:** https://github.com/jguida941/pysort-visualizer
- **Bug Reports:** Please include exported step traces (`Export → CSV`) and the RNG seed when reporting bugs.

Enjoy exploring the algorithms!
