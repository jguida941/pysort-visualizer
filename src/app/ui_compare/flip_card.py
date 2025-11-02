"""Flip card widget for algorithm details with smooth animation."""

from PyQt6.QtCore import QPropertyAnimation, QRect, Qt, pyqtProperty
from PyQt6.QtGui import QPainter, QBrush, QColor, QPen
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame, QHBoxLayout

from ..ui_shared.design_system import COLORS, FONTS, SPACING, SHADOWS


class FlipCard(QWidget):
    """A card widget that can flip between summary and detailed views."""

    def __init__(self, title: str, summary: str, details_widget: QWidget | None = None, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("flip_card")
        self._is_flipped = False
        self._title = title
        self._summary = summary
        self._details_widget = details_widget

        self.setMinimumHeight(200)
        self.setMaximumHeight(400)
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Setup the card UI with front and back faces."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Create the card container
        self.card_container = QFrame()
        self.card_container.setObjectName("algorithm_details_card")
        card_layout = QVBoxLayout(self.card_container)
        card_layout.setContentsMargins(SPACING["md"], SPACING["md"], SPACING["md"], SPACING["md"])
        card_layout.setSpacing(SPACING["sm"])

        # Header with title and flip indicator
        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)

        self.title_label = QLabel(self._title)
        self.title_label.setObjectName("detail_heading")
        self.title_label.setWordWrap(True)

        self.flip_indicator = QLabel("▶ Click for details")
        self.flip_indicator.setObjectName("flip_indicator")
        self.flip_indicator.setStyleSheet(f"""
            color: {COLORS['text_secondary']};
            font-size: {FONTS['size']['xs']}px;
            font-style: italic;
        """)

        header.addWidget(self.title_label)
        header.addStretch()
        header.addWidget(self.flip_indicator)
        card_layout.addLayout(header)

        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet(f"background: {COLORS['border_subtle']}; height: 1px;")
        card_layout.addWidget(separator)

        # Content area (front face - summary)
        self.front_content = QWidget()
        front_layout = QVBoxLayout(self.front_content)
        front_layout.setContentsMargins(0, 0, 0, 0)

        self.summary_label = QLabel(self._summary)
        self.summary_label.setObjectName("detail_subheading")
        self.summary_label.setWordWrap(True)
        self.summary_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        front_layout.addWidget(self.summary_label)

        # Content area (back face - details)
        self.back_content = self._details_widget if self._details_widget else QWidget()
        self.back_content.setVisible(False)

        card_layout.addWidget(self.front_content)
        card_layout.addWidget(self.back_content)
        card_layout.addStretch()

        main_layout.addWidget(self.card_container)

        # Apply styling
        self._apply_card_style()

    def _apply_card_style(self) -> None:
        """Apply the card styling with shadow and hover effects."""
        self.card_container.setStyleSheet(f"""
            QFrame#algorithm_details_card {{
                background: {COLORS['bg_secondary']};
                border: 1px solid {COLORS['border_default']};
                border-radius: 8px;
            }}
            QFrame#algorithm_details_card:hover {{
                border-color: {COLORS['accent']};
                background: {COLORS['bg_tertiary']};
            }}
        """)

    def mousePressEvent(self, event) -> None:
        """Handle mouse click to flip the card."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.flip()
        super().mousePressEvent(event)

    def flip(self) -> None:
        """Flip the card between front and back."""
        self._is_flipped = not self._is_flipped

        if self._is_flipped:
            self.front_content.setVisible(False)
            self.back_content.setVisible(True)
            self.flip_indicator.setText("▼ Click for summary")
        else:
            self.front_content.setVisible(True)
            self.back_content.setVisible(False)
            self.flip_indicator.setText("▶ Click for details")

        # Add a subtle animation effect by changing the background
        if self._is_flipped:
            self.card_container.setStyleSheet(f"""
                QFrame#algorithm_details_card {{
                    background: {COLORS['bg_tertiary']};
                    border: 2px solid {COLORS['accent']};
                    border-radius: 8px;
                }}
            """)
        else:
            self._apply_card_style()


class AlgorithmDetailsCard(FlipCard):
    """Specialized flip card for algorithm details with structured information."""

    def __init__(self, algo_info: dict, parent: QWidget | None = None):
        # Extract algorithm information
        title = algo_info.get("name", "Algorithm")
        summary = self._create_summary(algo_info)
        details = self._create_details_widget(algo_info)

        super().__init__(title, summary, details, parent)

    def _create_summary(self, info: dict) -> str:
        """Create a summary text from algorithm info."""
        stability = "Stable" if info.get("stable", False) else "Unstable"
        in_place = "In-place" if info.get("in_place", False) else "Out-of-place"
        category = info.get("category", "Comparison sort")

        description = info.get("description", "")
        if len(description) > 150:
            description = description[:147] + "..."

        return f"{stability} • {in_place} • {category}\n\n{description}"

    def _create_details_widget(self, info: dict) -> QWidget:
        """Create the detailed view widget."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(SPACING["sm"])

        # Full description
        desc_label = QLabel(info.get("description", ""))
        desc_label.setWordWrap(True)
        desc_label.setObjectName("detail_text")
        layout.addWidget(desc_label)

        # Highlights section
        if "highlights" in info and info["highlights"]:
            highlights_label = QLabel("Highlights:")
            highlights_label.setObjectName("detail_subheading")
            highlights_label.setStyleSheet(f"font-weight: {FONTS['weight']['semibold']};")
            layout.addWidget(highlights_label)

            for highlight in info["highlights"]:
                h_label = QLabel(f"• {highlight}")
                h_label.setWordWrap(True)
                h_label.setObjectName("detail_text")
                h_label.setStyleSheet(f"margin-left: {SPACING['sm']}px;")
                layout.addWidget(h_label)

        # Complexity section
        complexity_label = QLabel("Complexity:")
        complexity_label.setObjectName("detail_subheading")
        complexity_label.setStyleSheet(f"font-weight: {FONTS['weight']['semibold']};")
        layout.addWidget(complexity_label)

        complexities = [
            ("Best case:", info.get("best_case", "O(?)")),
            ("Average case:", info.get("avg_case", "O(?)")),
            ("Worst case:", info.get("worst_case", "O(?)")),
            ("Space:", info.get("space", "O(?)"))
        ]

        for label, value in complexities:
            c_layout = QHBoxLayout()
            c_layout.setContentsMargins(SPACING["sm"], 0, 0, 0)

            l = QLabel(label)
            l.setObjectName("detail_text")
            v = QLabel(value)
            v.setObjectName("detail_text")
            v.setStyleSheet(f"font-family: {FONTS['family']['mono']};")

            c_layout.addWidget(l)
            c_layout.addWidget(v)
            c_layout.addStretch()
            layout.addLayout(c_layout)

        layout.addStretch()
        return widget