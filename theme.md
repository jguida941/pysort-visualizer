# Professional-Grade UI Overhaul Plan for PySort Visualizer

## 🎯 Objectives
1. Transform the UI into a professional, modern visualization tool
2. Implement 8px grid system for perfect alignment
3. Reduce control size and improve space efficiency
4. Add tooltips, better borders, and visual hierarchy
5. Create a cohesive, production-ready interface

## 📋 Implementation Plan

### Phase 1: Core Layout Restructure
**Goal:** Create a professional grid-based layout with proper spacing

#### 1.1 Implement 8px Grid System
```python
# Create ui_shared/design_system.py
GRID_UNIT = 8
SPACING = {
    'xs': GRID_UNIT,      # 8px
    'sm': GRID_UNIT * 2,  # 16px
    'md': GRID_UNIT * 3,  # 24px
    'lg': GRID_UNIT * 4,  # 32px
    'xl': GRID_UNIT * 6,  # 48px
}
CONTROL_HEIGHT = 32  # 4 grid units
TOOLBAR_HEIGHT = 48  # 6 grid units
STATUSBAR_HEIGHT = 24  # 3 grid units
```

#### 1.2 Reorganize Window Layout
- **Top Toolbar** (48px): Compact controls in groups
- **Main Canvas**: Full focus on visualization
- **Bottom Status** (24px): Metrics and progress
- **Right Panel**: Collapsible details (hidden by default)

### Phase 2: Control Redesign
**Goal:** Smaller, grouped, professional controls

#### 2.1 Control Groups
```
[Input Section]
Array: [___________] Preset: [▼] Seed: [___] [↻Generate]

[Playback Controls]
[▶] [⏸] [◀] [▶] [↻] | Speed: ━━━●━━━ 24 FPS | [□ Values]

[Export Tools]
[📊] [💾] [🎬] (Icons only with tooltips)
```

#### 2.2 Button Specifications
- Standard button: 32x32px (icons) or 80x32px (text)
- Remove emojis from button text ("Export" not "Export 📁")
- Consistent 2px border radius
- Subtle hover effects (opacity change, not color)

### Phase 3: Visual Polish
**Goal:** Professional appearance with subtle animations

#### 3.1 Color Scheme Update
```python
COLORS = {
    'background': '#0f1115',
    'surface': '#1a1d23',
    'border': '#2a2e38',
    'border_focus': '#4a9eff',
    'text_primary': '#e6e6e6',
    'text_secondary': '#a0a6b8',
    'accent': '#4a9eff',
    'success': '#4ade80',
    'warning': '#fbbf24',
    'error': '#f87171'
}
```

#### 3.2 Typography System
```python
FONTS = {
    'mono': 'SF Mono, Consolas, monospace',
    'sans': '-apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif'
}
SIZES = {
    'xs': 11,
    'sm': 12,
    'md': 13,
    'lg': 14,
    'xl': 16
}
```

### Phase 4: Enhanced Components

#### 4.1 Card-Based Layout
- Algorithm details in expandable cards
- Step list in scrollable card
- Log in dedicated card
- All with consistent padding and shadows

#### 4.2 Professional Tooltips
```python
# Add to every control
button.setToolTip("Step Forward (Right Arrow)")
button.setWhatsThis("Advance the algorithm by one step")
```

#### 4.3 Improved Borders
- 1px subtle borders (not 2px)
- Consistent border-radius: 4px
- Focus state: Blue glow, not thick border

### Phase 5: Advanced Features

#### 5.1 Snap-to-Grid Splitters
```python
def snap_to_grid(value):
    return round(value / GRID_UNIT) * GRID_UNIT
```

#### 5.2 Flip Card Algorithm Selection
- Visual algorithm cards with preview
- Flip animation on hover
- Quick info on back

#### 5.3 Floating Control Panel Option
- Draggable control panel
- Can dock to any edge
- Remembers position

### Phase 6: State Persistence

#### 6.1 Save UI Preferences
- Window size and position
- Splitter positions
- Panel visibility
- Control preferences

#### 6.2 Theme System
- Dark theme (default)
- Light theme (high contrast)
- Custom theme editor

## 🔧 Technical Implementation

### Files to Create:
1. `src/app/ui_shared/design_system.py` - Central design tokens
2. `src/app/ui_shared/components.py` - Reusable UI components
3. `src/app/ui_single/toolbar.py` - New toolbar widget
4. `src/app/ui_single/statusbar.py` - New status bar
5. `src/app/styles/professional.qss` - Main stylesheet

### Files to Modify:
1. `src/app/core/base.py` - Remove UI construction, use new components
2. `src/app/ui_single/window.py` - Implement new layout
3. `src/app/ui_compare/window.py` - Apply same improvements

## 📊 Success Metrics
- [ ] All controls fit in 48px toolbar height
- [ ] No text overflow or clipping
- [ ] All elements align to 8px grid
- [ ] Tooltips on every interactive element
- [ ] <2 second load time
- [ ] Smooth 60fps animations
- [ ] Settings persist between sessions

## 🚀 Implementation Order
1. Design system and tokens (30 min)
2. Toolbar and status bar (1 hour)
3. Control groups and sizing (1 hour)
4. Visual polish and themes (1 hour)
5. Tooltips and help text (30 min)
6. State persistence (30 min)
7. Testing and refinement (30 min)

Total estimated time: 5 hours

## 🎨 Visual Design Principles

### Spacing and Alignment
- All spacing must be multiples of 8px
- Buttons aligned to baseline grid
- Consistent margins: 16px outer, 8px inner
- Group related controls with 24px spacing

### Visual Hierarchy
1. **Primary Actions**: Blue accent, larger size
2. **Secondary Actions**: Neutral with border
3. **Tertiary Actions**: Text only, no border
4. **Destructive Actions**: Red accent, confirmation required

### Animation Guidelines
- Duration: 200-300ms for UI transitions
- Easing: cubic-bezier(0.4, 0, 0.2, 1)
- No animation during algorithm playback (performance)
- Subtle fade/scale for hover states

### Accessibility
- Minimum touch target: 44x44px
- Color contrast ratio: 4.5:1 minimum
- Keyboard navigation for all controls
- Screen reader compatible labels
- Focus indicators on all interactive elements

## 📐 Component Specifications

### Toolbar Component
```
Height: 48px
Background: #1a1d23
Border-bottom: 1px solid #2a2e38
Padding: 8px horizontal
Layout: Flexbox with gap: 16px
```

### Control Button
```
Size: 32x32px (icon only) or height: 32px with padding: 0 16px (text)
Border: 1px solid #2a2e38
Border-radius: 4px
Background: transparent
Hover: background: rgba(74, 158, 255, 0.1)
Active: background: rgba(74, 158, 255, 0.2)
Focus: box-shadow: 0 0 0 2px rgba(74, 158, 255, 0.5)
```

### Input Field
```
Height: 32px
Padding: 0 12px
Border: 1px solid #2a2e38
Border-radius: 4px
Background: #0f1115
Focus: border-color: #4a9eff
Font: 13px mono
```

### Slider
```
Height: 32px
Track height: 4px
Handle: 16x16px circle
Track color: #2a2e38
Progress color: #4a9eff
Handle color: #e6e6e6
```

### Status Bar
```
Height: 24px
Background: #1a1d23
Border-top: 1px solid #2a2e38
Font: 11px mono
Padding: 0 8px
Layout: Flex with separator: " | "
```