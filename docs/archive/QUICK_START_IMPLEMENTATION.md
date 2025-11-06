# 🚀 Quick Start Implementation Guide

## Enhanced Launcher - Immediate Implementation

This guide shows how to quickly upgrade the launcher to support 9 modes with a modern grid layout.

---

## Step 1: Update LauncherWindow in app.py

```python
class LauncherWindow(QMainWindow):
    """Enhanced landing window with 9 mode options."""

    def __init__(self) -> None:
        super().__init__()
        self._settings = QSettings(ORG_NAME, APP_NAME)
        self.setWindowTitle("Algorithm Education Suite")
        self.resize(800, 600)  # Larger for grid layout

        self._child_window: QMainWindow | None = None

        # Main layout
        central = QWidget(self)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(32, 24, 32, 24)

        # Header
        self._add_header(main_layout)

        # Grid of buttons
        self._add_mode_grid(main_layout)

        # Footer
        self._add_footer(main_layout)

        self.setCentralWidget(central)
        self._apply_theme_from_settings()

    def _add_header(self, layout: QVBoxLayout) -> None:
        """Add header with title and description."""
        title = QLabel("Algorithm Education Suite")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setObjectName("launcher_title")
        title.setStyleSheet("font-size: 24px; font-weight: bold; margin: 10px;")

        subtitle = QLabel("Choose a mode to begin your algorithm journey")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setObjectName("launcher_subtitle")
        subtitle.setStyleSheet("font-size: 14px; color: #888; margin-bottom: 20px;")

        layout.addWidget(title)
        layout.addWidget(subtitle)

    def _add_mode_grid(self, layout: QVBoxLayout) -> None:
        """Add 3x3 grid of mode buttons."""
        grid = QGridLayout()
        grid.setSpacing(16)

        modes = [
            {
                "name": "Single Visualizer",
                "icon": "🔍",
                "description": "Explore algorithms individually",
                "callback": self._launch_single,
                "enabled": True
            },
            {
                "name": "Compare Mode",
                "icon": "⚖️",
                "description": "Compare algorithms side-by-side",
                "callback": self._launch_compare,
                "enabled": True
            },
            {
                "name": "Learning Mode",
                "icon": "📚",
                "description": "Interactive tutorials & quizzes",
                "callback": self._launch_learning,
                "enabled": False  # Coming soon
            },
            {
                "name": "Algorithm Playground",
                "icon": "🧪",
                "description": "Create custom algorithms",
                "callback": self._launch_playground,
                "enabled": False
            },
            {
                "name": "Performance Analyzer",
                "icon": "📊",
                "description": "Deep performance analysis",
                "callback": self._launch_analyzer,
                "enabled": False
            },
            {
                "name": "Battle Arena",
                "icon": "🎮",
                "description": "Algorithm competitions",
                "callback": self._launch_arena,
                "enabled": False
            },
            {
                "name": "Data Structures",
                "icon": "🏗️",
                "description": "Trees, graphs, and more",
                "callback": self._launch_structures,
                "enabled": False
            },
            {
                "name": "Code Generator",
                "icon": "💻",
                "description": "Generate code in any language",
                "callback": self._launch_generator,
                "enabled": False
            },
            {
                "name": "Algorithm Studio",
                "icon": "🎯",
                "description": "Advanced development tools",
                "callback": self._launch_studio,
                "enabled": False
            }
        ]

        for i, mode in enumerate(modes):
            button = self._create_mode_button(mode)
            row = i // 3
            col = i % 3
            grid.addWidget(button, row, col)

        layout.addLayout(grid)

    def _create_mode_button(self, mode: dict) -> QPushButton:
        """Create a styled button for each mode."""
        button = QPushButton()
        button.setMinimumHeight(120)
        button.setMinimumWidth(240)

        # Create rich content with icon and text
        button_html = f"""
        <div style='text-align: center;'>
            <div style='font-size: 32px;'>{mode['icon']}</div>
            <div style='font-size: 16px; font-weight: bold; margin: 5px;'>
                {mode['name']}
            </div>
            <div style='font-size: 11px; color: #888;'>
                {mode['description']}
            </div>
        </div>
        """
        button.setText("")  # Clear text

        # Use QLabel for rich content
        label = QLabel(button_html)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setWordWrap(True)

        # Layout for button
        button_layout = QVBoxLayout(button)
        button_layout.addWidget(label)

        if mode['enabled']:
            button.clicked.connect(mode['callback'])
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.setStyleSheet("""
                QPushButton {
                    border: 2px solid #4A90E2;
                    border-radius: 10px;
                    background: qlineargradient(
                        x1: 0, y1: 0, x2: 0, y2: 1,
                        stop: 0 #2C3E50,
                        stop: 1 #1A252F
                    );
                }
                QPushButton:hover {
                    background: qlineargradient(
                        x1: 0, y1: 0, x2: 0, y2: 1,
                        stop: 0 #34495E,
                        stop: 1 #2C3E50
                    );
                    border: 2px solid #5BA0F2;
                }
            """)
        else:
            button.setEnabled(False)
            button.setStyleSheet("""
                QPushButton {
                    border: 1px solid #333;
                    border-radius: 10px;
                    background: #1A1A1A;
                    color: #555;
                }
            """)
            # Add "Coming Soon" overlay
            label.setText(label.text() + "<div style='color: #FFA500; margin-top: 5px;'>Coming Soon!</div>")

        return button

    def _add_footer(self, layout: QVBoxLayout) -> None:
        """Add footer with version and links."""
        layout.addStretch()

        footer = QLabel("v2.0.0 | Algorithm Education Suite | © 2024")
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        footer.setStyleSheet("color: #666; font-size: 11px; margin-top: 20px;")
        layout.addWidget(footer)

    # Placeholder methods for new modes
    def _launch_learning(self) -> None:
        QMessageBox.information(self, "Coming Soon",
                               "Learning Mode is under development!\n"
                               "Check back in the next update.")

    def _launch_playground(self) -> None:
        QMessageBox.information(self, "Coming Soon",
                               "Algorithm Playground is under development!")

    def _launch_analyzer(self) -> None:
        QMessageBox.information(self, "Coming Soon",
                               "Performance Analyzer is under development!")

    def _launch_arena(self) -> None:
        QMessageBox.information(self, "Coming Soon",
                               "Battle Arena is under development!")

    def _launch_structures(self) -> None:
        QMessageBox.information(self, "Coming Soon",
                               "Data Structure Visualizer is under development!")

    def _launch_generator(self) -> None:
        QMessageBox.information(self, "Coming Soon",
                               "Code Generator is under development!")

    def _launch_studio(self) -> None:
        QMessageBox.information(self, "Coming Soon",
                               "Algorithm Studio is under development!")
```

---

## Step 2: Add Sound Effects (Quick Win)

Create a new file `src/app/core/sound.py`:

```python
from PyQt6.QtMultimedia import QSoundEffect
from PyQt6.QtCore import QUrl
from pathlib import Path

class SoundManager:
    """Manages sound effects for the visualizer."""

    def __init__(self, enabled: bool = True):
        self.enabled = enabled
        self.sounds = {}
        self._load_sounds()

    def _load_sounds(self):
        """Load sound files."""
        sound_dir = Path(__file__).parent.parent / "resources" / "sounds"

        # Create these sound files or use system sounds
        sound_files = {
            "compare": "beep.wav",
            "swap": "swoosh.wav",
            "complete": "success.wav",
            "step": "tick.wav"
        }

        for name, filename in sound_files.items():
            sound = QSoundEffect()
            sound.setSource(QUrl.fromLocalFile(str(sound_dir / filename)))
            sound.setVolume(0.5)
            self.sounds[name] = sound

    def play(self, sound_name: str):
        """Play a sound effect."""
        if self.enabled and sound_name in self.sounds:
            self.sounds[sound_name].play()

    def toggle(self):
        """Toggle sound on/off."""
        self.enabled = not self.enabled
```

---

## Step 3: Add Basic Achievements

Create `src/app/core/achievements.py`:

```python
from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime
import json
from pathlib import Path

@dataclass
class Achievement:
    id: str
    name: str
    description: str
    icon: str
    points: int
    unlocked: bool = False
    unlock_date: Optional[datetime] = None

class AchievementManager:
    """Manages user achievements and progress."""

    def __init__(self):
        self.achievements = self._init_achievements()
        self.save_file = Path.home() / ".pysort" / "achievements.json"
        self.load_progress()

    def _init_achievements(self) -> List[Achievement]:
        """Initialize all available achievements."""
        return [
            Achievement("first_sort", "First Steps",
                       "Complete your first sort", "🎯", 10),
            Achievement("speed_demon", "Speed Demon",
                       "Sort 1000 elements", "⚡", 50),
            Achievement("explorer", "Algorithm Explorer",
                       "Try all algorithms", "🔍", 100),
            Achievement("perfectionist", "Perfectionist",
                       "Complete all tutorials", "⭐", 200),
            Achievement("creator", "Creator",
                       "Build a custom algorithm", "🎨", 150),
            Achievement("competitor", "Competitor",
                       "Win 10 algorithm battles", "🏆", 100),
            Achievement("researcher", "Researcher",
                       "Generate 100 benchmarks", "📊", 75),
            Achievement("teacher", "Teacher",
                       "Share 10 visualizations", "👨‍🏫", 80),
        ]

    def check_achievement(self, action: str, value: any) -> Optional[Achievement]:
        """Check if an action unlocks an achievement."""
        # Implementation for checking achievements
        # Returns the achievement if newly unlocked
        pass

    def unlock(self, achievement_id: str):
        """Unlock an achievement."""
        for ach in self.achievements:
            if ach.id == achievement_id and not ach.unlocked:
                ach.unlocked = True
                ach.unlock_date = datetime.now()
                self.save_progress()
                return ach
        return None

    def get_total_points(self) -> int:
        """Get total points earned."""
        return sum(a.points for a in self.achievements if a.unlocked)

    def save_progress(self):
        """Save achievement progress to file."""
        self.save_file.parent.mkdir(exist_ok=True)
        data = {
            a.id: {
                "unlocked": a.unlocked,
                "unlock_date": a.unlock_date.isoformat() if a.unlock_date else None
            }
            for a in self.achievements
        }
        with open(self.save_file, 'w') as f:
            json.dump(data, f, indent=2)

    def load_progress(self):
        """Load achievement progress from file."""
        if self.save_file.exists():
            with open(self.save_file) as f:
                data = json.load(f)
                for ach in self.achievements:
                    if ach.id in data:
                        ach.unlocked = data[ach.id]["unlocked"]
                        if data[ach.id]["unlock_date"]:
                            ach.unlock_date = datetime.fromisoformat(
                                data[ach.id]["unlock_date"]
                            )
```

---

## Step 4: Achievement Toast Notifications

Create `src/app/ui_shared/toast.py`:

```python
from PyQt6.QtWidgets import QWidget, QLabel, QGraphicsOpacityEffect
from PyQt6.QtCore import QTimer, QPropertyAnimation, pyqtProperty, Qt
from PyQt6.QtGui import QPainter, QBrush, QColor

class ToastNotification(QWidget):
    """Toast notification for achievements."""

    def __init__(self, parent, achievement):
        super().__init__(parent)
        self.achievement = achievement
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint |
                           Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self._setup_ui()
        self._setup_animation()

    def _setup_ui(self):
        """Setup the toast UI."""
        self.setFixedSize(300, 80)

        # Position at top-right corner
        parent_rect = self.parent().rect()
        x = parent_rect.width() - self.width() - 20
        y = 20
        self.move(x, y)

        # Create label with achievement info
        label = QLabel(self)
        label.setText(f"""
            <div style='color: white; padding: 10px;'>
                <div style='font-size: 24px;'>{self.achievement.icon}</div>
                <div style='font-size: 14px; font-weight: bold;'>
                    {self.achievement.name}
                </div>
                <div style='font-size: 11px;'>
                    {self.achievement.description}
                </div>
                <div style='font-size: 10px; color: gold;'>
                    +{self.achievement.points} points
                </div>
            </div>
        """)
        label.setGeometry(0, 0, 300, 80)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)

    def paintEvent(self, event):
        """Custom paint for rounded corners."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Draw rounded rectangle background
        brush = QBrush(QColor(40, 40, 40, 230))
        painter.setBrush(brush)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(self.rect(), 10, 10)

    def _setup_animation(self):
        """Setup fade in/out animation."""
        self.opacity_effect = QGraphicsOpacityEffect()
        self.setGraphicsEffect(self.opacity_effect)

        # Fade in
        self.fade_in = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_in.setDuration(500)
        self.fade_in.setStartValue(0)
        self.fade_in.setEndValue(1)

        # Stay visible for 3 seconds
        self.timer = QTimer()
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.fade_out_animation)

        # Fade out
        self.fade_out = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_out.setDuration(500)
        self.fade_out.setStartValue(1)
        self.fade_out.setEndValue(0)
        self.fade_out.finished.connect(self.close)

        # Start animation
        self.show()
        self.fade_in.start()
        self.timer.start(3000)

    def fade_out_animation(self):
        """Start fade out."""
        self.fade_out.start()
```

---

## Step 5: Quick Testing

Test the enhanced launcher:

```python
# In main.py or test file
if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)

    # Test enhanced launcher
    launcher = LauncherWindow()
    launcher.show()

    # Test achievement toast
    from app.core.achievements import Achievement
    from app.ui_shared.toast import ToastNotification

    test_achievement = Achievement(
        "test", "Test Achievement",
        "You tested the system!", "🎉", 100
    )
    test_achievement.unlocked = True

    toast = ToastNotification(launcher, test_achievement)

    sys.exit(app.exec())
```

---

## Next Steps

After implementing the enhanced launcher:

1. **Add Learning Mode** (1 week)
   - Create tutorial content
   - Build quiz system
   - Add progress tracking

2. **Add Sound Effects** (2 days)
   - Record/find sound files
   - Integrate with step events
   - Add settings toggle

3. **Complete Achievement System** (3 days)
   - Hook into existing events
   - Add persistent storage
   - Create achievement gallery

4. **Add Algorithm Playground** (1 week)
   - Code editor widget
   - Safe execution sandbox
   - Visual programming blocks

5. **Performance Analyzer** (1 week)
   - Real-time graphing
   - Statistical analysis
   - Report generation

---

## Benefits of This Approach

1. **Incremental**: Each feature can be added independently
2. **Backward Compatible**: Existing modes continue to work
3. **Extensible**: Easy to add new modes to the grid
4. **Professional**: Modern UI with hover effects and animations
5. **Engaging**: Achievements and sound effects add gamification
6. **Educational**: Learning mode provides structured education

This implementation can be completed in stages, with the enhanced launcher being ready in just a few hours of work!