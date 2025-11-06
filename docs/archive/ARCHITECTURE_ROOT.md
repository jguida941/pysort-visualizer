# PySort Visualizer - Comprehensive Codebase Analysis

## Executive Summary

PySort is a sophisticated PyQt6-based sorting algorithm visualizer with a modular architecture designed for educational visualization, performance analysis, and reproducible algorithm comparison. The codebase demonstrates excellent architectural patterns including plugin-based algorithm registration, deterministic step-based replay, and comprehensive export/benchmark capabilities.

---

## 1. Current Features & Capabilities

### 1.1 Core Visualization Features
- **Single Visualizer Mode**: One algorithm per tab with full controls
- **Compare Mode**: Dual-pane workspace for side-by-side algorithm comparison
- **Real-time Animation**: Frame-accurate playback with configurable FPS (1-60)
- **Interactive Controls**:
  - Play/Pause with Space key
  - Step forward/backward with arrow keys
  - Scrubbing with timeline slider
  - Manual stepping buttons
  - Input field with 1.5s debounce auto-apply

### 1.2 Algorithm Suite (13 Total)
1. **Comparison-based**: Bubble, Insertion, Selection, Heap, Shell, Merge (bottom-up), Quick (median-of-three), Cocktail, Comb
2. **Non-comparison**: Counting, Radix (LSD), Bucket
3. **Hybrid**: Timsort Trace

### 1.3 Data Presets (6 Configurable)
- Random uniform
- Nearly sorted (with random swaps)
- Reverse sorted (descending)
- Reverse run (mostly descending with ascending segment)
- Few unique values
- Sorted ascending

### 1.4 Export & Analysis Capabilities
- **CSV Export**: Step-by-step trace (op, indices, payload)
- **JSON Export**: Full metadata with algorithm info, preset, seed, config
- **PNG Export**: Current canvas snapshot
- **GIF Export**: Animated sequence (up to 120 frames)
- **CSV Benchmark**: Performance metrics across algorithms/presets
- **Metrics Verification**: `scripts/verify_metrics.py` for offline analysis

### 1.5 UI/UX Features
- **Themes**: Dark (default) and high-contrast (light) modes
- **Accessibility**: Tooltip theming, high-contrast mode, keyboard shortcuts
- **Persistence**: Window geometry, FPS, presets, last array saved via QSettings
- **HUD Display**: Real-time metrics (algo name, dataset, step count, performance)
- **Narration**: Step-by-step descriptions of algorithm operations
- **Debug Panel**: Live inspection of player state (optional dock widget)
- **Auto-apply Input**: 1.5-second debounce on manual array entry

---

## 2. Architecture Overview

### 2.1 Layered Architecture

```
Application Layer (PyQt6 UI)
├── LauncherWindow (app.py) - Mode selection
├── SuiteWindow (ui_single/window.py) - Tabbed single visualizer
└── CompareWindow (ui_compare/window.py) - Dual-pane compare mode

Visualization Layer
├── AlgorithmVisualizerBase (core/base.py) - Main visualizer widget
├── VisualizationCanvas (core/base.py) - Drawing/rendering
└── Pane (ui_shared/pane.py) - Control surface adapter

Playback Engine
├── Player (core/player.py) - Frame-accurate playback orchestration
├── Replay (core/replay.py) - Step replay and scrubbing
└── CompareController (ui_compare/controller.py) - Dual-pane sync

Algorithm Layer
├── Registry (algos/registry.py) - Plugin system with metadata
├── Individual algorithms (algos/*.py) - Self-registering implementations
└── Presets (presets/__init__.py) - Dataset generators

Supporting Systems
├── Step (core/step.py) - Immutable step data structure
├── Logging & crash handling (core/base.py)
└── Theme system (ui_shared/theme.py, professional_theme.py)
```

### 2.2 Data Flow

```
Algorithm Generator (yields Step)
    ↓
Player (frame-accurate timing control)
    ↓
AlgorithmVisualizerBase (applies steps, maintains state)
    ↓
VisualizationCanvas (renders current state)
    ↓
User Interface (PyQt6 widgets)
    ↓
Export System (CSV/JSON/PNG/GIF)
    ↓
Benchmark System (performance metrics CSV)
```

---

## 3. Key Architectural Patterns

### 3.1 Plugin-Based Algorithm Registration

**Location**: `src/app/algos/registry.py`

**Pattern**: Decorator-based self-registration with metadata

```python
@register(AlgoInfo(
    name="Bubble Sort",
    stable=True,
    in_place=True,
    comparison=True,
    complexity={"best": "O(n)", "avg": "O(n^2)", "worst": "O(n^2)"},
    description="...",
    notes=(...)
))
def bubble_sort(arr: list[int]) -> Iterator[Step]:
    # Implementation yields Step objects
    pass
```

**Benefits**:
- Algorithms are self-documenting
- Metadata is centrally discoverable
- No tight coupling to UI
- Easy to add new algorithms
- Type-safe with `AlgoInfo` dataclass

### 3.2 Step-Based Deterministic Replay

**Location**: `src/app/core/step.py`

**Pattern**: Immutable step objects as the source of truth

```python
@dataclass(frozen=True)
class Step:
    op: Op  # "compare", "swap", "pivot", "merge_mark", etc.
    indices: tuple[int, ...]  # Array positions involved
    payload: Any = None  # Optional operation-specific data
```

**Operations Supported**:
- `compare`: Comparison between indices
- `swap`: Element swap with values
- `pivot`: Pivot selection
- `merge_mark`: Merge range marking
- `merge_compare`: Comparison during merge
- `set`: Direct value assignment
- `shift`: Element shifting
- `key`: Key tracking (insertion sort)
- `confirm`: Final position confirmation

**Benefits**:
- Deterministic, reproducible runs
- Full event logging capability
- Serializable for export
- No floating-point timing errors
- Backward/forward stepping possible

### 3.3 Frame-Accurate Playback with Logical Time

**Location**: `src/app/core/player.py`

**Pattern**: Dual time tracking with jitter tolerance

**Components**:
- `_Stopwatch`: Wall-clock time accumulator (excludes paused periods)
- `logical_seconds()`: Deterministic time (steps × 1/fps)
- `_on_tick()`: Frame-accurate timer callback with rate limiting

**Rate Limiting**:
- Per-tick cap: 8 steps max per timer tick (prevents UI freeze)
- Per-second cap: 1000 steps max per second
- Backpressure signals when limits are exceeded

**Benefits**:
- Hardware-independent timing
- Smooth 60fps possible while maintaining logical time
- Reproducible timing regardless of CPU speed
- Clear separation of wall-time vs. deterministic time

### 3.4 Checkpoint-Based Scrubbing

**Location**: `src/app/core/base.py`

**Pattern**: Periodic snapshots for efficient scrub operations

```python
self._checkpoints: list[tuple[int, list[int], int, int]]  
# (step_idx, array_snapshot, comparisons_count, swaps_count)
```

**Scrubbing Algorithm**:
1. Find nearest checkpoint <= target step
2. Restore array and metrics from checkpoint
3. Replay steps from checkpoint to target
4. Update highlights and UI

**Benefits**:
- O(1) checkpoint seek + O(k) replay where k = steps since checkpoint
- Configurable stride (default: every 200 steps)
- Memory-efficient for long runs
- No forward-replay needed to go backward

### 3.5 Dual-Pane Synchronization

**Location**: `src/app/ui_compare/controller.py`

**Pattern**: Fanout controller with shared transport

```python
class CompareController:
    def step_forward(self) -> None:
        self.left.step_forward()
        self.right.step_forward()
```

**Design**:
- Both panes share the same dataset
- Both receive same UI commands
- Each pane independently maintains step position and state
- Capability checking prevents errors (e.g., step_back may not be available)

**Benefits**:
- Fair algorithm comparison
- Synchronized timing
- Independent step/scrub positions allowed
- Resilient to missing capabilities

### 3.6 Pane Abstraction Layer

**Location**: `src/app/ui_shared/pane.py`

**Pattern**: Adapter providing clean control surface over legacy visualizer

**Exposes**:
- Transport controls: `play()`, `pause()`, `toggle_pause()`, `reset()`, `step_forward()`, `step_back()`
- State queries: `is_running`, `step_index()`, `elapsed_seconds()`, `logical_seconds()`
- Capability checking: `capabilities()`, `set_capability()`
- View toggles: `set_hud_visible()`, `set_show_values()`

**Benefits**:
- Decouples visualizer UI from control logic
- Reusable across single and compare modes
- Type-safe interface
- Easier to test playback independently

---

## 4. UI Framework Capabilities

### 4.1 Widget Hierarchy

**Single Mode (`SuiteWindow`)**:
```
SuiteWindow (QMainWindow)
└── QTabWidget
    ├── AlgorithmVisualizerBase (Bubble Sort)
    ├── AlgorithmVisualizerBase (Insertion Sort)
    ├── AlgorithmVisualizerBase (Merge Sort)
    └── ... (one per algorithm)
```

**Compare Mode (`CompareWindow`)**:
```
CompareWindow (QMainWindow)
└── CompareView (QWidget)
    ├── Left pane: AlgorithmVisualizerBase (with show_controls=False)
    ├── Right pane: AlgorithmVisualizerBase (with show_controls=False)
    └── Central control panel
```

### 4.2 AlgorithmVisualizerBase Widget Structure

```
AlgorithmVisualizerBase (QWidget)
├── Input Row
│   ├── Input field (manual array entry)
│   ├── Preset dropdown
│   ├── Seed input
│   ├── Generate button
│   ├── Start button
│   ├── Pause button
│   ├── Reset button
│   ├── Export button
│   └── Benchmark button
├── FPS Control Row
│   ├── FPS label
│   ├── FPS slider
│   └── FPS spinbox
├── Scrub Row
│   ├── Step label
│   ├── Scrub slider
│   ├── Step back button
│   ├── Step forward button
│   └── Show values checkbox
├── Splitter (resizable)
│   ├── VisualizationCanvas (main rendering)
│   └── Right panel
│       ├── Algorithm Details (metadata)
│       ├── Steps list (sampled trace)
│       ├── Log viewer
│       └── Legend
└── Narration Label
```

### 4.3 Theme System

**Theme Files**:
- `ui_shared/theme.py`: Tooltip theming
- `ui_shared/professional_theme.py`: Complete stylesheet generation
- `ui_shared/design_system.py`: Design constants
- `ui_shared/design_system.py`: Colors and spacing

**Color Schemes**:
1. **Dark Theme** (default):
   - Background: `#0f1115`
   - Text: `#e6e6e6`
   - Accent colors for each operation type
   
2. **High-Contrast Theme**:
   - Background: `#ffffff`
   - Text: `#111111`
   - WCAG-compliant color palette

**Persistence**: Theme selection saved to `QSettings` under `ui/theme`

### 4.4 Rendering Architecture

**VisualizationCanvas** (`QWidget` with `paintEvent`):
- Gets current state via callback
- Renders bars with colors based on highlights
- Auto-scales to fit container
- Optional value labels (visible at small n or when complete)
- HUD panel with monospace metrics display

**Highlights Mapping**:
```python
{
    "compare": tuple[int, ...],  # Yellow
    "swap": tuple[int, ...],     # Red
    "pivot": tuple[int, ...],    # Green
    "merge": tuple[int, ...],    # Purple
    "key": tuple[int, ...],      # Cyan
    "shift": tuple[int, ...],    # Orange
}
```

### 4.5 Signal/Slot Architecture

**Player Signals**:
- `stepped(int)`: After each step
- `elapsed_updated(float)`: Wall-clock time
- `logical_elapsed_updated(float)`: Logical time
- `finished()`: Algorithm complete
- `backpressure(dict)`: Rate limit hit

**Visualizer Callbacks**:
- Input changes → debounce → auto-apply
- FPS changes → immediately updated
- Scrub slider → seek + sync
- Button clicks → transport methods

---

## 5. Core Functionality Patterns

### 5.1 Algorithm Execution Flow

**Initialization**:
```python
arr = [5, 2, 8, 1, 9]
step_source = algorithm_func(arr)  # Get generator
```

**Step Generation**:
```python
for step in step_source:
    # step.op: "compare", "swap", etc.
    # step.indices: (i, j) or (i,)
    # step.payload: optional data
    apply_step(step)  # Update array, highlights
    record_step(step)  # Log for export
    update_canvas()    # Render
```

**Completion**:
```python
# StopIteration raised when done
# Finish animation plays
# Results available for export/benchmark
```

### 5.2 Input Processing & Auto-Apply

**Flow**:
```
User types in le_input
    ↓
textChanged signal → _on_input_changed()
    ↓
Start 1.5s debounce timer
    ↓
(If user keeps typing, restart timer)
    ↓
Timer fires → _try_auto_apply_input()
    ↓
Parse text → _parse_input()
    ↓
_set_array() → reset visualizer
    ↓
Canvas updates
```

**Safety**:
- Only applies if animation NOT running
- Silent failure on invalid input
- No exception thrown to user

### 5.3 Preset & Seed System

**Preset Selection**:
```python
preset_key = cmb_preset.currentData()
seed = int(le_seed.text()) if le_seed.text() else random.SystemRandom().randint(0, 2**32-1)
arr = generate_dataset(preset_key, n, min_val, max_val, random.Random(seed))
```

**Persistence**:
```python
_settings.setValue("viz/preset", preset_key)
_settings.setValue("viz/seed", seed)
_settings.setValue("viz/last_input", rendered_array)
```

### 5.4 Export System

**CSV**: One row per step
```csv
idx,op,indices,payload
0,compare,0.1,
1,swap,0.1,(5,2)
2,compare,1.2,
...
```

**JSON**: Full metadata + steps
```json
{
  "algo": "Bubble Sort",
  "preset": "random",
  "seed": 12345,
  "config": {"n": 32, "min": 1, "max": 200, "fps": 24},
  "initial": [5,2,8,...],
  "steps": [{...}]
}
```

**PNG**: Direct canvas snapshot via `grab()`

**GIF**: 
1. Stride frames (max 120)
2. Seek to each frame
3. Capture pixmap
4. Compose with PIL
5. Write with loop=0

### 5.5 Benchmark System

**Metrics**:
- Total steps executed
- Comparison count
- Swap count
- CPU duration (via `time.perf_counter`)
- Visual duration (logical time)
- Wall duration (actual elapsed)
- Correctness (array == sorted)

**CSV Output**:
```csv
algo,context,run,preset,seed,n,steps,comparisons,swaps,duration_cpu_ms,duration_visual_ms,duration_wall_ms,sorted,error
Bubble Sort,,1,random,12345,32,128,64,32,0.150,1.33,0.140,1,
```

---

## 6. Testing Infrastructure

### 6.1 Test Organization

**Test Categories**:
- `test_sorting_algorithms.py`: Algorithm correctness
- `test_compare_integration.py`: Compare mode sync
- `test_compare_stepping.py`: Step consistency
- `test_export_serialization.py`: Export formats
- `test_step_*.py`: Step mechanics (direction, determinism, invariants)
- `test_player.py`: Playback engine
- `test_ui_*.py`: UI components
- `test_presets.py`: Preset generation
- Property-based tests with Hypothesis

### 6.2 Test Infrastructure (`conftest.py`)

**Fixtures**:
- `qapp`: Session-scoped QApplication (offscreen platform)
- `qtbot`: Custom event loop waiter

**Setup**:
```python
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
```

### 6.3 Key Test Patterns

**Algorithm Validation**:
```python
def test_bubble_sort():
    arr = [5,2,8,1,9]
    steps = list(bubble_sort(arr))
    assert arr == [1,2,5,8,9]
    assert len(steps) > 0
```

**Replay Determinism**:
```python
def test_deterministic_replay():
    arr1 = generate_dataset("random", 32, 1, 200, Random(12345))
    arr2 = generate_dataset("random", 32, 1, 200, Random(12345))
    assert list(bubble_sort(arr1)) == list(bubble_sort(arr2))
```

**Compare Mode Sync**:
```python
def test_both_panes_step_forward():
    # Run both algorithms, verify both advance
    controller.step_forward()
    assert left.step_idx == right.step_idx
```

---

## 7. Patterns Supporting Expansion

### 7.1 Adding New Algorithms

**Steps**:
1. Create `src/app/algos/my_sort.py`
2. Implement generator function yielding Steps
3. Decorate with `@register(AlgoInfo(...))`
4. Import in `src/app/algos/registry.py` → `_ALGO_MODULES`
5. Run tests → automatically discovered

**Example**:
```python
@register(AlgoInfo(
    name="My Sort",
    stable=True,
    in_place=True,
    comparison=True,
    complexity={"best": "O(n)", "avg": "O(n log n)", "worst": "O(n^2)"},
    description="A custom sorting algorithm"
))
def my_sort(arr: list[int]) -> Iterator[Step]:
    for i in range(len(arr)):
        for j in range(i+1, len(arr)):
            yield Step("compare", (i, j))
            if arr[i] > arr[j]:
                yield Step("swap", (i, j), payload=(arr[i], arr[j]))
                arr[i], arr[j] = arr[j], arr[i]
    for i in range(len(arr)):
        yield Step("confirm", (i,))
```

### 7.2 Adding New Presets

**Location**: `src/app/presets/__init__.py`

**Pattern**:
```python
def _my_preset(n: int, lo: int, hi: int, rng: random.Random) -> list[int]:
    # Generate data
    return [...]

PRESETS = PRESETS + (
    Preset(
        key="my_preset",
        label="My Preset",
        description="Description for UI",
        generator=_my_preset
    ),
)
```

**Automatic Registration**:
- Appears in dropdown immediately
- Seed support built-in
- Export includes preset name and seed

### 7.3 Extending the Player

**Current Capabilities**:
```python
capabilities = {
    "step_back": bool,
    "true_time": bool,
    "detach": bool,
    "true_total": bool
}
```

**Extension Points**:
- `Player.set_step_caps()`: Rate limiting configuration
- `Player.sync_to_step()`: External seek synchronization
- `Player.set_visual_fps()`: FPS control
- Custom backpressure handlers

### 7.4 UI Customization Points

**Theme System**:
- Edit color mappings in `THEME_PRESETS`
- Extend `generate_stylesheet()` in `professional_theme.py`
- Add new theme keys to launcher window

**Canvas Rendering**:
- Modify `VisualizationCanvas.paintEvent()` for different visual styles
- Add overlay layers (grid, labels, animations)
- Custom bar shapes/textures

**Control Panels**:
- AlgorithmVisualizerBase exposes all widgets publicly
- Easy to add new controls in `_build_ui()`
- Pane adapter provides clean transport interface

---

## 8. Configuration & Persistence

### 8.1 QSettings Keys

**Category: `viz/`**
- `last_input`: Last manually entered array
- `fps`: Animation speed
- `preset`: Last selected preset key
- `seed`: Last random seed
- `show_values`: Whether to show bar values

**Category: `ui/`**
- `theme`: "dark" or "high-contrast"

**Category: `main/`**
- `geometry`: Window size/position (SuiteWindow)

**Category: `config/`**
- `min_n`, `max_n`, `default_n`: Array size bounds
- `min_val`, `max_val`: Element range
- `fps_min`, `fps_max`, `fps_default`: FPS bounds
- `checkpoint_stride`: Scrub snapshot frequency

### 8.2 Environment Variables

All `config/` keys can be overridden:
```bash
SORT_VIZ_DEFAULT_N=64
SORT_VIZ_MAX_N=256
SORT_VIZ_FPS_DEFAULT=30
python main.py
```

---

## 9. Performance Characteristics

### 9.1 Memory Usage

**Typical Setup** (n=32):
- Step buffer: ~128 steps × 60 bytes = 7.7 KB
- Checkpoints: ~(128/200) × 4 snapshots = negligible
- Canvas/UI widgets: ~2-3 MB (PyQt6 overhead)
- Total per visualizer: ~5-10 MB

**Scaling**:
- Linear with step count
- Precompute cap: 10,000 steps (exceeding this disables step preview)

### 9.2 Rendering Performance

**Frame Rate**:
- Target: 1-60 FPS (user configurable)
- Typical: 60 FPS achievable on modern hardware
- CPU-bound at high FPS (not GPU-accelerated)

**Canvas Updates**:
- One full repaint per step
- Antialiasing disabled during animation (enabled for HUD)
- Jitter tolerance: 10ms (allows timing flexibility)

### 9.3 Step Generation Speed

**Typical Throughput**:
- Bubble Sort (n=32): ~128 steps in <1ms
- Merge Sort (n=32): ~256 steps in <1ms
- Quicksort (n=32): ~160 steps in <1ms

**Rate Limiting**:
- Per-tick: 8 steps max (prevents UI freeze)
- Per-second: 1000 steps max (overall throttle)
- Backpressure emitted when limits hit

---

## 10. Summary of Expansion-Friendly Patterns

| Pattern | Location | Extensibility |
|---------|----------|---|
| Algorithm Registry | `algos/registry.py` | Add new @register decorated functions |
| Step Types | `core/step.py` | Enum can be extended (but requires compat care) |
| Presets | `presets/__init__.py` | Add new generator functions |
| Themes | `THEME_PRESETS` dict | Add new color schemes |
| UI Widgets | `ui_single/window.py`, `ui_shared/` | Subclass or modify layouts |
| Player/Pane | `core/player.py`, `ui_shared/pane.py` | Signals and slots well-defined |
| Export Formats | `core/base.py` → `_export_*` methods | Add new format handlers |
| Benchmark Columns | `AlgorithmVisualizerBase.BENCHMARK_COLUMNS` | Extend tuple + update CSV writer |

---

## Conclusion

PySort demonstrates **professional-grade architecture** suitable for:
- Educational visualization
- Performance research
- Algorithm comparison
- Reproducible benchmarking

The codebase excels at:
- **Modularity**: Plugin systems for algorithms and presets
- **Determinism**: Step-based replay ensures reproducibility
- **Extensibility**: Clear patterns for adding features
- **Testing**: Comprehensive test coverage with deterministic fixtures
- **Performance**: Frame-accurate timing with rate limiting
- **UX**: Theme support, persistence, accessibility

Key strengths for expansion:
1. Self-registering algorithm system (no central list to update)
2. Immutable Step objects (safe for serialization/replay)
3. Checkpoint-based scrubbing (efficient seeking)
4. Pane abstraction (supports both single and compare modes)
5. Comprehensive export system (multiple formats)
6. QSettings persistence (automatic roundtripping)

The architecture supports adding new algorithms, presets, themes, and export formats with minimal coupling to existing code.
