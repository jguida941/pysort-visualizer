"""Professional theme stylesheet for Compare Mode."""

from ..ui_shared.design_system import COLORS, DIMENSIONS, FONTS, SPACING, SHADOWS


def generate_compare_stylesheet(theme: str = "dark") -> str:
    """Generate the complete professional stylesheet for compare mode."""

    # Theme-specific overrides
    if theme == "high-contrast":
        bg_primary = "#f8f9fa"
        bg_secondary = "#ffffff"
        bg_tertiary = "#f3f4f6"
        bg_card = "#ffffff"
        text_primary = "#111827"
        text_secondary = "#4b5563"
        text_tertiary = "#9ca3af"
        border_default = "#e5e7eb"
        border_strong = "#d1d5db"
        border_subtle = "#f3f4f6"
        accent = "#2563eb"
        accent_hover = "#1d4ed8"
    else:  # dark theme - unified with single visualizer
        bg_primary = COLORS["bg_primary"]  # #0f1115 - Main dark background
        bg_secondary = COLORS["bg_secondary"]  # #1a1d23 - Slightly lighter
        bg_tertiary = COLORS["bg_tertiary"]  # #22252e - Even lighter for cards
        bg_card = COLORS["bg_secondary"]  # Use secondary instead of custom
        text_primary = COLORS["text_primary"]
        text_secondary = COLORS["text_secondary"]
        text_tertiary = COLORS["text_tertiary"]
        border_default = COLORS["border_default"]
        border_strong = COLORS["border_strong"]
        border_subtle = COLORS["border_subtle"]
        accent = COLORS["accent"]
        accent_hover = COLORS["accent_hover"]

    # Convert dimensions to strings
    button_h = DIMENSIONS["button_height"]
    input_h = DIMENSIONS["input_height"]
    radius = DIMENSIONS["border_radius"]

    # Spacing values
    xs = SPACING["xs"]
    sm = SPACING["sm"]
    md = SPACING["md"]
    lg = SPACING["lg"]

    stylesheet = f"""
    /* ========================================================================
       COMPARE MODE ROOT - Main dark background
       ======================================================================== */

    QWidget#compare_root {{
        background: {bg_primary};  /* Main dark background #0f1115 */
    }}

    QWidget {{
        background: transparent;  /* Ensure child widgets don't have white background */
        color: {text_primary};  /* Default text color for all widgets */
    }}

    /* ========================================================================
       CONTROL CARDS - Dark background consistent with main theme
       ======================================================================== */

    QFrame#compare_card {{
        background-color: {bg_secondary};  /* Force dark background */
        border: 1px solid {border_subtle};
        border-radius: 6px;
        padding: 4px;
    }}

    QFrame {{
        background-color: transparent;
        border: none;
    }}

    /* ========================================================================
       PANE CONTAINERS - Clean separation between algorithms
       ======================================================================== */

    QWidget#compare_pane_container {{
        background: {bg_secondary};
        border: 1px solid {border_default};
        border-radius: 6px;
        padding: {sm}px;
    }}

    /* ========================================================================
       LABELS AND TEXT
       ======================================================================== */

    QLabel {{
        color: {text_primary};
        font-family: {FONTS['family']['sans']};
        font-size: {FONTS['size']['md']}px;
    }}

    QLabel#control_label {{
        color: {text_secondary};
        font-size: {FONTS['size']['sm']}px;
        font-weight: {FONTS['weight']['medium']};
        margin-right: {xs}px;
    }}

    QLabel#compare_hint {{
        color: {text_tertiary};
        font-size: {FONTS['size']['xs']}px;
        padding: 2px 0px;
        background: transparent;
    }}

    QLabel#compare_status {{
        color: {text_primary};
        font-weight: {FONTS['weight']['medium']};
        font-size: {FONTS['size']['sm']}px;
        padding: {xs}px {sm}px;
        background: {bg_tertiary};
        border-radius: {radius}px;
    }}

    QLabel#compare_pane_title {{
        font-weight: {FONTS['weight']['semibold']};
        font-size: {FONTS['size']['md']}px;
        color: {text_primary};
    }}

    QLabel#compare_pane_status {{
        color: {text_tertiary};
        font-family: {FONTS['family']['mono']};
        font-size: {FONTS['size']['xs']}px;
    }}

    /* ========================================================================
       INPUT FIELDS - Consistent with single mode
       ======================================================================== */

    QLineEdit {{
        background: {bg_primary};
        border: 1px solid {border_default};
        border-radius: {radius}px;
        padding: 0px {sm}px;
        min-height: {input_h}px;
        max-height: {input_h}px;
        color: {text_primary};
        font-family: {FONTS['family']['mono']};
        font-size: {FONTS['size']['sm']}px;
        selection-background-color: {accent};
    }}

    QLineEdit:focus {{
        border-color: {accent};
        box-shadow: 0 0 0 2px {accent}33;
    }}

    QLineEdit:disabled {{
        background: {bg_tertiary};
        color: {text_tertiary};
        border-color: {border_subtle};
    }}

    /* ========================================================================
       COMBO BOXES - Professional dropdowns
       ======================================================================== */

    QComboBox {{
        background: {bg_primary};
        border: 1px solid {border_default};
        border-radius: {radius}px;
        padding: 0px {sm}px;
        min-height: {input_h}px;
        max-height: {input_h}px;
        color: {text_primary};
        font-size: {FONTS['size']['sm']}px;
    }}

    QComboBox:hover {{
        border-color: {border_strong};
        background: {bg_secondary};
    }}

    QComboBox:focus {{
        border-color: {accent};
        box-shadow: 0 0 0 2px {accent}33;
    }}

    QComboBox::drop-down {{
        border: none;
        width: {md}px;
        background: transparent;
    }}

    QComboBox::down-arrow {{
        image: none;
        border-left: 4px solid transparent;
        border-right: 4px solid transparent;
        border-top: 5px solid {text_secondary};
        width: 0;
        height: 0;
        margin-right: {xs}px;
    }}

    QComboBox QAbstractItemView {{
        background: {bg_secondary};
        border: 1px solid {border_strong};
        border-radius: {radius}px;
        padding: {xs}px 0px;
        selection-background-color: {accent};
        color: {text_primary};
        outline: none;
    }}

    QComboBox QAbstractItemView::item {{
        padding: {xs}px {sm}px;
        min-height: {button_h}px;
    }}

    QComboBox QAbstractItemView::item:hover {{
        background: {accent}1a;
    }}

    QComboBox QAbstractItemView::item:selected {{
        background: {accent};
        color: {bg_primary};
    }}

    /* ========================================================================
       BUTTONS - Modern, flat design with hover effects
       ======================================================================== */

    QPushButton {{
        background: {bg_tertiary};
        border: 1px solid {border_default};
        border-radius: {radius}px;
        padding: 0px {sm}px;
        min-height: {button_h}px;
        max-height: {button_h}px;
        color: {text_primary};
        font-size: {FONTS['size']['sm']}px;
        font-weight: {FONTS['weight']['medium']};
        transition: all 0.2s ease;
    }}

    QPushButton:hover {{
        background: {accent}1a;
        border-color: {accent};
        transform: translateY(-1px);
        box-shadow: {SHADOWS['sm']};
    }}

    QPushButton:pressed {{
        background: {accent}2d;
        border-color: {accent};
        transform: translateY(0px);
    }}

    QPushButton:disabled {{
        color: {text_tertiary};
        border-color: {border_subtle};
        background: {bg_secondary};
    }}

    /* Generate button - matches single visualizer style */
    QPushButton#generate_button {{
        background: {accent};
        color: {bg_primary};
        border: none;
        border-radius: {radius}px;
        font-weight: {FONTS['weight']['medium']};
        padding: 2px {sm}px;
        min-height: {button_h - 4}px;  /* Slightly smaller */
        max-height: {button_h - 4}px;
    }}

    QPushButton#generate_button:hover {{
        background: {accent_hover};
    }}

    QPushButton#generate_button:pressed {{
        background: {accent}cc;
    }}

    /* Transport buttons - compact with icons */
    QPushButton#transport_button {{
        background: transparent;
        border: 1px solid {border_default};
        border-radius: {radius}px;
        padding: 2px {xs}px;
        min-height: {button_h - 4}px;
        max-height: {button_h - 4}px;
        min-width: 60px;
    }}

    QPushButton#transport_button:hover {{
        background: {accent}1a;
        border-color: {accent};
    }}

    QPushButton#transport_button:pressed {{
        background: {accent}2d;
        border-color: {accent};
    }}

    /* ========================================================================
       TOOL BUTTONS - Compact toggle buttons
       ======================================================================== */

    QToolButton {{
        background: {bg_tertiary};
        border: 1px solid {border_default};
        border-radius: {radius}px;
        padding: {xs}px {sm}px;
        color: {text_primary};
        font-size: {FONTS['size']['sm']}px;
        font-weight: {FONTS['weight']['medium']};
    }}

    QToolButton:hover {{
        background: {accent}1a;
        border-color: {accent};
    }}

    QToolButton:checked {{
        background: {accent};
        color: {bg_primary};
        border-color: {accent};
    }}

    /* ========================================================================
       SLIDERS - Smooth, modern controls
       ======================================================================== */

    QSlider::groove:horizontal {{
        background: {border_default};
        height: 4px;
        border-radius: 2px;
    }}

    QSlider::handle:horizontal {{
        background: {text_primary};
        border: 2px solid {bg_primary};
        width: 18px;
        height: 18px;
        border-radius: 9px;
        margin: -7px 0;
    }}

    QSlider::handle:horizontal:hover {{
        background: {accent};
        border-color: {accent}33;
        box-shadow: 0 0 0 4px {accent}1a;
    }}

    QSlider::sub-page:horizontal {{
        background: {accent};
        height: 4px;
        border-radius: 2px;
    }}

    /* ========================================================================
       SPIN BOXES - Numeric inputs
       ======================================================================== */

    QSpinBox {{
        background: {bg_primary};
        border: 1px solid {border_default};
        border-radius: {radius}px;
        padding: 0px {xs}px;
        min-height: {input_h}px;
        max-height: {input_h}px;
        color: {text_primary};
        font-family: {FONTS['family']['mono']};
        font-size: {FONTS['size']['sm']}px;
    }}

    QSpinBox:focus {{
        border-color: {accent};
        box-shadow: 0 0 0 2px {accent}33;
    }}

    QSpinBox::up-button, QSpinBox::down-button {{
        width: 0px;
        height: 0px;
        border: none;
    }}

    /* ========================================================================
       CHECKBOXES - Clean, modern checkboxes
       ======================================================================== */

    QCheckBox {{
        spacing: {xs}px;
        color: {text_primary};
        font-size: {FONTS['size']['sm']}px;
    }}

    QCheckBox::indicator {{
        width: 18px;
        height: 18px;
        border: 2px solid {border_default};
        border-radius: {radius}px;
        background: {bg_primary};
    }}

    QCheckBox::indicator:hover {{
        border-color: {accent};
        background: {accent}1a;
    }}

    QCheckBox::indicator:checked {{
        background: {accent};
        border-color: {accent};
        image: url(checkmark.png);  /* Will need to add checkmark image */
    }}

    /* ========================================================================
       SCROLL AREAS - Minimal scrollbars
       ======================================================================== */

    QScrollArea {{
        background: transparent;
        border: none;
    }}

    QScrollBar:vertical {{
        background: {bg_primary};
        width: {DIMENSIONS['scrollbar_width']}px;
        border: none;
        border-radius: {radius}px;
    }}

    QScrollBar::handle:vertical {{
        background: {border_strong};
        border-radius: {radius}px;
        min-height: 30px;
    }}

    QScrollBar::handle:vertical:hover {{
        background: {accent};
    }}

    QScrollBar::add-line:vertical,
    QScrollBar::sub-line:vertical {{
        height: 0px;
    }}

    /* ========================================================================
       SPLITTERS - Subtle dividers
       ======================================================================== */

    QSplitter::handle {{
        background: {border_default};
    }}

    QSplitter::handle:horizontal {{
        width: 2px;
    }}

    QSplitter::handle:vertical {{
        height: 2px;
    }}

    QSplitter::handle:hover {{
        background: {accent};
    }}

    /* ========================================================================
       ALGORITHM DETAILS PANEL - Card-style with flip animation potential
       ======================================================================== */

    QWidget#algorithm_details_card {{
        background: {bg_card};
        border: 1px solid {border_default};
        border-radius: 8px;
        padding: {sm}px;
        margin: {xs}px;
    }}

    QWidget#algorithm_details_card QLabel {{
        color: {text_primary} !important;
    }}

    /* Force all labels to have proper text color */
    QScrollArea QWidget QLabel {{
        color: {text_primary};
        background: transparent;
    }}

    /* Details panel specific text styling */
    QScrollArea {{
        color: {text_primary};
    }}

    QTextEdit, QPlainTextEdit {{
        color: {text_primary};
        background: {bg_secondary};
        border: 1px solid {border_subtle};
    }}

    QWidget#algorithm_details_card QLabel#detail_heading {{
        font-size: {FONTS['size']['lg']}px;
        font-weight: {FONTS['weight']['semibold']};
        color: {text_primary};
        margin-bottom: {xs}px;
    }}

    QWidget#algorithm_details_card QLabel#detail_subheading {{
        font-size: {FONTS['size']['sm']}px;
        color: {text_secondary};
        margin-bottom: {sm}px;
    }}

    /* ========================================================================
       FOCUS INDICATORS - Visual feedback for keyboard navigation
       ======================================================================== */

    QWidget:focus {{
        outline: none;
        border-color: {accent};
        box-shadow: 0 0 0 2px {accent}33;
    }}

    /* ========================================================================
       ANIMATIONS AND TRANSITIONS
       ======================================================================== */

    * {{
        transition-property: background, border-color, transform, box-shadow;
        transition-duration: 0.2s;
        transition-timing-function: ease-in-out;
    }}
    """

    return stylesheet


def apply_compare_theme(widget, theme: str = "dark") -> None:
    """Apply the professional theme to the compare mode widget."""
    stylesheet = generate_compare_stylesheet(theme)
    widget.setStyleSheet(stylesheet)