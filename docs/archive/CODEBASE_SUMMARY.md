# PySort Codebase Quick Reference

## File Organization

```
src/app/
├── app.py                          # LauncherWindow (mode selection)
├── algos/
│   ├── registry.py                 # Plugin system + metadata
│   ├── bubble.py, insertion.py, ... # 13 algorithm implementations
│   └── __init__.py                 # Empty (algos auto-imported)
├── core/
│   ├── step.py                     # Step dataclass (immutable)
│   ├── base.py                     # AlgorithmVisualizerBase widget
│   ├── player.py                   # Frame-accurate playback engine
│   ├── replay.py                   # Step replay & scrubbing
│   └── compare.py                  # Compare mode helpers
├── presets/
│   └── __init__.py                 # Dataset generators
├── ui_single/
│   └── window.py                   # SuiteWindow (tabbed view)
├── ui_compare/
│   ├── window.py                   # CompareWindow
│   ├── controller.py               # Dual-pane sync
│   └── compare_theme.py            # Theme application
└── ui_shared/
    ├── pane.py                     # Control surface adapter
    ├── constants.py                # App metadata
    ├── theme.py                    # Tooltip theming
    ├── professional_theme.py       # Full stylesheet
    ├── design_system.py            # Colors/spacing
    └── debug_panel.py              # Debug dock widget
```

## 13 Algorithms Included

**Comparison-based** (9):
- Bubble Sort
- Insertion Sort
- Selection Sort
- Heap Sort
- Shell Sort
- Merge Sort (bottom-up)
- Quick Sort (median-of-three)
- Cocktail Sort
- Comb Sort

**Non-comparison** (3):
- Counting Sort
- Radix Sort (LSD)
- Bucket Sort

**Hybrid** (1):
- Timsort Trace

## Key Design Patterns

| Pattern | Use | Location |
|---------|-----|----------|
| **Plugin Registry** | Self-registering algorithms | `algos/registry.py` |
| **Step-based Replay** | Immutable, deterministic operations | `core/step.py` |
| **Frame-accurate Timing** | Logical time tracking | `core/player.py` |
| **Checkpoint Scrubbing** | Efficient seek/rewind | `core/base.py` |
| **Pane Abstraction** | Clean control interface | `ui_shared/pane.py` |
| **Dual-pane Sync** | Fanout controller | `ui_compare/controller.py` |

## Critical Classes

### Step (`core/step.py`)
```python
@dataclass(frozen=True)
class Step:
    op: Op                      # Operation type (compare, swap, etc.)
    indices: tuple[int, ...]    # Array indices involved
    payload: Any = None         # Optional data
```

### AlgoInfo (`algos/registry.py`)
```python
@dataclass(frozen=True)
class AlgoInfo:
    name: str                   # Display name
    stable: bool
    in_place: bool
    comparison: bool
    complexity: dict[str, str]  # {best, avg, worst}
    description: str
    notes: tuple[str, ...]
```

### Player (`core/player.py`)
Main playback engine with signals:
- `stepped(int)`
- `elapsed_updated(float)`
- `logical_elapsed_updated(float)`
- `finished()`
- `backpressure(dict)`

### AlgorithmVisualizerBase (`core/base.py`)
Main widget with:
- Input controls
- Canvas rendering
- Export (CSV/JSON/PNG/GIF)
- Benchmark system
- Theme support

## UI Modes

### Single Visualizer
- One tab per algorithm
- All controls visible
- 1280x900 default
- Theme toggle (View menu)
- Debug panel (View menu)

### Compare Mode
- Two side-by-side visualizers
- Shared dataset
- Synchronized playback
- Independent algorithm selection

## Data Presets

1. **Random** - Uniform distribution
2. **Nearly Sorted** - Mostly sorted with random swaps
3. **Reverse Sorted** - Descending order
4. **Reverse Run** - Mostly descending with ascending segment
5. **Few Unique** - Only handful of distinct values
6. **Sorted Ascending** - Already sorted

All support:
- Reproducible seeding
- Configurable min/max values
- Array size (n) adjustment

## Export Formats

| Format | Contains | Use Case |
|--------|----------|----------|
| **CSV** | Step-by-step trace | Analysis/verification |
| **JSON** | Full metadata + steps | Sharing/archiving |
| **PNG** | Current canvas | Screenshots |
| **GIF** | Animation sequence | Presentations |

## Benchmark Output

CSV with columns:
- algo, context, run, preset, seed, n
- steps, comparisons, swaps
- duration_cpu_ms, duration_visual_ms, duration_wall_ms
- sorted, error

## Settings Persistence (QSettings)

**Keys saved:**
- `viz/fps` - Animation speed
- `viz/preset` - Last selected preset
- `viz/seed` - Last random seed
- `viz/last_input` - Manual array entry
- `viz/show_values` - Show bar labels
- `ui/theme` - dark or high-contrast
- `main/geometry` - Window size/position

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `Space` | Play/Pause |
| `S` | Start |
| `R` | Generate random |
| `Left Arrow` | Step backward |
| `Right Arrow` | Step forward |

## Testing

30+ test files covering:
- Algorithm correctness
- Step determinism
- Replay consistency
- Compare mode sync
- Export serialization
- UI components
- Property-based testing (Hypothesis)

Run tests:
```bash
pytest                                    # All tests
pytest tests/test_sorting_algorithms.py   # Algorithms only
pytest tests/test_compare_integration.py  # Compare mode
```

## Adding Features

### New Algorithm
1. Create `src/app/algos/my_sort.py`
2. Implement generator yielding Steps
3. Decorate with `@register(AlgoInfo(...))`
4. Add to `_ALGO_MODULES` in `registry.py`

### New Preset
1. Add generator function to `src/app/presets/__init__.py`
2. Append to `PRESETS` tuple
3. Appears in dropdown automatically

### New Theme
1. Add colors to `THEME_PRESETS` dict in `core/base.py`
2. Toggle in launcher/SuiteWindow

### New Export Format
1. Add `_export_xyz()` method to `AlgorithmVisualizerBase`
2. Update file dialog filters
3. Add format case to export handler

## Configuration

### Environment Variables
```bash
SORT_VIZ_DEFAULT_N=64       # Default array size
SORT_VIZ_MAX_N=256          # Maximum array size
SORT_VIZ_FPS_DEFAULT=30     # Default FPS
SORT_VIZ_MIN_VAL=1          # Minimum element value
SORT_VIZ_MAX_VAL=200        # Maximum element value
```

### Hardcoded Limits
- Step buffer cap: 10,000 steps (precompute limit)
- Per-tick steps: 8 (UI freeze prevention)
- Per-second steps: 1000 (overall rate limit)
- Checkpoint stride: 200 steps (scrub efficiency)

## Performance Notes

- Typical memory: 5-10 MB per visualizer
- Rendering: CPU-bound, 60 FPS achievable
- Step generation: <1ms for n=32
- Scrub: O(1) seek + O(k) replay

## Dependencies

Core:
- PyQt6
- Pillow (exports)
- platformdirs (optional, logging)

Development:
- pytest
- hypothesis (property testing)
- ruff, black, mypy

## Project Structure Summary

- Well-organized layered architecture
- Plugin system for algorithms
- Immutable step-based replay
- Professional PyQt6 UI
- Comprehensive testing
- Export and benchmark tools
- Theme and accessibility support
- QSettings persistence

The codebase is ready for expansion with clear patterns for adding algorithms, presets, themes, and export formats.
