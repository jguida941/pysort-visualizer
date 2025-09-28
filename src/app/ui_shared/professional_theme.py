"""Professional theme stylesheet generator for PySort Visualizer."""

from .design_system import COLORS, DIMENSIONS, FONTS, SPACING


def generate_stylesheet() -> str:
    """Generate the complete professional stylesheet."""

    # Convert dimensions to strings
    toolbar_h = DIMENSIONS["toolbar_height"]
    button_h = DIMENSIONS["button_height"]
    input_h = DIMENSIONS["input_height"]
    radius = DIMENSIONS["border_radius"]

    # Spacing values
    xs = SPACING["xs"]
    sm = SPACING["sm"]
    md = SPACING["md"]

    stylesheet = f"""
    /* ========================================================================
       GLOBAL STYLES
       ======================================================================== */

    QWidget {{
        color: {COLORS['text_primary']};
        background-color: {COLORS['bg_primary']};
        font-family: {FONTS['family']['sans']};
        font-size: {FONTS['size']['md']}px;
    }}

    /* ========================================================================
       TOOLBAR
       ======================================================================== */

    QToolBar {{
        background: {COLORS['bg_secondary']};
        border: none;
        border-bottom: 1px solid {COLORS['border_default']};
        spacing: {sm}px;
        padding: {xs}px;
        min-height: {toolbar_h}px;
        max-height: {toolbar_h}px;
    }}

    QToolBar::separator {{
        background: {COLORS['border_default']};
        width: 1px;
        margin: {xs}px {sm}px;
    }}

    /* ========================================================================
       BUTTONS - Compact and professional
       ======================================================================== */

    QPushButton {{
        background: transparent;
        border: 1px solid {COLORS['border_default']};
        border-radius: {radius}px;
        padding: 0px {sm}px;
        min-height: {button_h}px;
        max-height: {button_h}px;
        font-size: {FONTS['size']['sm']}px;
        font-weight: {FONTS['weight']['medium']};
    }}

    QPushButton:hover {{
        background: {COLORS['accent']}1a;  /* 10% opacity */
        border-color: {COLORS['border_strong']};
    }}

    QPushButton:pressed {{
        background: {COLORS['accent']}2d;  /* 18% opacity */
        border-color: {COLORS['accent']};
    }}

    QPushButton:checked {{
        background: {COLORS['accent']}2d;
        border-color: {COLORS['accent']};
    }}

    QPushButton:disabled {{
        color: {COLORS['text_tertiary']};
        border-color: {COLORS['border_subtle']};
        background: transparent;
    }}

    QPushButton:focus {{
        outline: none;
        border-color: {COLORS['accent']};
    }}

    /* Primary action buttons */
    QPushButton#primary {{
        background: {COLORS['accent']};
        color: {COLORS['text_inverse']};
        border-color: {COLORS['accent']};
    }}

    QPushButton#primary:hover {{
        background: {COLORS['accent_hover']};
        border-color: {COLORS['accent_hover']};
    }}

    QPushButton#primary:pressed {{
        background: {COLORS['accent_active']};
        border-color: {COLORS['accent_active']};
    }}

    /* Icon-only buttons */
    QPushButton#icon_button {{
        padding: 0px;
        min-width: {button_h}px;
        max-width: {button_h}px;
    }}

    /* ========================================================================
       INPUT FIELDS
       ======================================================================== */

    QLineEdit {{
        background: {COLORS['bg_primary']};
        border: 1px solid {COLORS['border_default']};
        border-radius: {radius}px;
        padding: 0px {sm}px;
        min-height: {input_h}px;
        max-height: {input_h}px;
        font-family: {FONTS['family']['mono']};
        font-size: {FONTS['size']['sm']}px;
        selection-background-color: {COLORS['accent']};
    }}

    QLineEdit:focus {{
        border-color: {COLORS['accent']};
        outline: none;
    }}

    QLineEdit:disabled {{
        background: {COLORS['bg_secondary']};
        color: {COLORS['text_tertiary']};
        border-color: {COLORS['border_subtle']};
    }}

    /* ========================================================================
       COMBO BOXES
       ======================================================================== */

    QComboBox {{
        background: {COLORS['bg_primary']};
        border: 1px solid {COLORS['border_default']};
        border-radius: {radius}px;
        padding: 0px {sm}px;
        min-height: {input_h}px;
        max-height: {input_h}px;
        font-size: {FONTS['size']['sm']}px;
    }}

    QComboBox:hover {{
        border-color: {COLORS['border_strong']};
    }}

    QComboBox:focus {{
        border-color: {COLORS['accent']};
    }}

    QComboBox::drop-down {{
        border: none;
        width: {md}px;
    }}

    QComboBox::down-arrow {{
        image: none;
        border-left: 4px solid transparent;
        border-right: 4px solid transparent;
        border-top: 5px solid {COLORS['text_secondary']};
        width: 0;
        height: 0;
        margin-right: {xs}px;
    }}

    QComboBox QAbstractItemView {{
        background: {COLORS['bg_secondary']};
        border: 1px solid {COLORS['border_strong']};
        border-radius: {radius}px;
        padding: {xs}px 0px;
        selection-background-color: {COLORS['accent']};
        outline: none;
    }}

    /* ========================================================================
       SLIDERS
       ======================================================================== */

    QSlider::groove:horizontal {{
        background: {COLORS['border_default']};
        height: 4px;
        border-radius: 2px;
    }}

    QSlider::handle:horizontal {{
        background: {COLORS['text_primary']};
        border: 2px solid {COLORS['bg_primary']};
        width: 16px;
        height: 16px;
        border-radius: 8px;
        margin: -6px 0;
    }}

    QSlider::handle:horizontal:hover {{
        background: {COLORS['accent']};
    }}

    QSlider::sub-page:horizontal {{
        background: {COLORS['accent']};
        height: 4px;
        border-radius: 2px;
    }}

    /* ========================================================================
       SPIN BOXES
       ======================================================================== */

    QSpinBox {{
        background: {COLORS['bg_primary']};
        border: 1px solid {COLORS['border_default']};
        border-radius: {radius}px;
        padding: 0px {xs}px;
        min-height: {input_h}px;
        max-height: {input_h}px;
        font-family: {FONTS['family']['mono']};
        font-size: {FONTS['size']['sm']}px;
    }}

    QSpinBox:focus {{
        border-color: {COLORS['accent']};
    }}

    QSpinBox::up-button, QSpinBox::down-button {{
        width: 0px;
        height: 0px;
        border: none;
    }}

    /* ========================================================================
       CHECKBOXES
       ======================================================================== */

    QCheckBox {{
        spacing: {xs}px;
        font-size: {FONTS['size']['sm']}px;
    }}

    QCheckBox::indicator {{
        width: 16px;
        height: 16px;
        border: 1px solid {COLORS['border_default']};
        border-radius: {radius}px;
        background: {COLORS['bg_primary']};
    }}

    QCheckBox::indicator:hover {{
        border-color: {COLORS['border_strong']};
        background: {COLORS['bg_secondary']};
    }}

    QCheckBox::indicator:checked {{
        background: {COLORS['accent']};
        border-color: {COLORS['accent']};
    }}

    QCheckBox::indicator:checked:hover {{
        background: {COLORS['accent_hover']};
        border-color: {COLORS['accent_hover']};
    }}

    /* ========================================================================
       LABELS
       ======================================================================== */

    QLabel {{
        color: {COLORS['text_primary']};
        font-size: {FONTS['size']['sm']}px;
    }}

    QLabel#heading {{
        font-size: {FONTS['size']['lg']}px;
        font-weight: {FONTS['weight']['semibold']};
        color: {COLORS['text_primary']};
    }}

    QLabel#caption {{
        font-size: {FONTS['size']['xs']}px;
        color: {COLORS['text_secondary']};
    }}

    /* ========================================================================
       GROUP BOXES
       ======================================================================== */

    QGroupBox {{
        border: 1px solid {COLORS['border_subtle']};
        border-radius: {radius}px;
        margin-top: {sm}px;
        padding-top: {sm}px;
        font-size: {FONTS['size']['sm']}px;
        font-weight: {FONTS['weight']['medium']};
    }}

    QGroupBox::title {{
        subcontrol-origin: margin;
        left: {sm}px;
        padding: 0px {xs}px;
        background: {COLORS['bg_primary']};
        color: {COLORS['text_secondary']};
    }}

    /* ========================================================================
       STATUS BAR
       ======================================================================== */

    QStatusBar {{
        background: {COLORS['bg_secondary']};
        border-top: 1px solid {COLORS['border_default']};
        font-family: {FONTS['family']['mono']};
        font-size: {FONTS['size']['xs']}px;
        color: {COLORS['text_secondary']};
        min-height: {DIMENSIONS['statusbar_height']}px;
        max-height: {DIMENSIONS['statusbar_height']}px;
    }}

    /* ========================================================================
       SCROLL BARS
       ======================================================================== */

    QScrollBar:vertical {{
        background: {COLORS['bg_primary']};
        width: {DIMENSIONS['scrollbar_width']}px;
        border: none;
    }}

    QScrollBar::handle:vertical {{
        background: {COLORS['border_strong']};
        border-radius: {radius}px;
        min-height: 20px;
    }}

    QScrollBar::handle:vertical:hover {{
        background: {COLORS['accent']};
    }}

    QScrollBar::add-line:vertical,
    QScrollBar::sub-line:vertical {{
        height: 0px;
    }}

    /* ========================================================================
       TEXT AREAS
       ======================================================================== */

    QTextEdit, QTextBrowser, QListWidget {{
        background: {COLORS['bg_primary']};
        border: 1px solid {COLORS['border_default']};
        border-radius: {radius}px;
        padding: {xs}px;
        font-family: {FONTS['family']['mono']};
        font-size: {FONTS['size']['xs']}px;
        selection-background-color: {COLORS['accent']};
    }}

    QTextEdit:focus, QTextBrowser:focus, QListWidget:focus {{
        border-color: {COLORS['accent']};
    }}

    QListWidget::item {{
        padding: {xs}px;
        border-bottom: 1px solid {COLORS['border_subtle']};
    }}

    QListWidget::item:selected {{
        background: {COLORS['accent']}2d;
        color: {COLORS['text_primary']};
    }}

    QListWidget::item:hover {{
        background: {COLORS['bg_secondary']};
    }}

    /* ========================================================================
       SPLITTERS
       ======================================================================== */

    QSplitter::handle {{
        background: {COLORS['border_default']};
    }}

    QSplitter::handle:horizontal {{
        width: 1px;
    }}

    QSplitter::handle:vertical {{
        height: 1px;
    }}

    QSplitter::handle:hover {{
        background: {COLORS['accent']};
    }}

    /* ========================================================================
       TAB WIDGET - Dark theme tabs
       ======================================================================== */

    QTabWidget {{
        background: {COLORS['bg_primary']};
    }}

    QTabWidget::pane {{
        border: 1px solid {COLORS['border_default']};
        background: {COLORS['bg_primary']};
        border-radius: 0px;
    }}

    QTabWidget::tab-bar {{
        alignment: left;
    }}

    QTabBar {{
        background: {COLORS['bg_secondary']};
    }}

    QTabBar::tab {{
        background: {COLORS['bg_secondary']};
        color: {COLORS['text_secondary']};
        padding: 8px 16px;
        margin-right: 2px;
        border: 1px solid {COLORS['border_default']};
        border-bottom: none;
        border-top-left-radius: 4px;
        border-top-right-radius: 4px;
        font-size: {FONTS['size']['sm']}px;
        font-weight: {FONTS['weight']['medium']};
    }}

    QTabBar::tab:selected {{
        background: {COLORS['bg_primary']};
        color: {COLORS['text_primary']};
        border-color: {COLORS['border_strong']};
        border-bottom: 1px solid {COLORS['bg_primary']};
    }}

    QTabBar::tab:hover:!selected {{
        background: {COLORS['bg_tertiary']};
        color: {COLORS['text_primary']};
    }}

    QTabBar::tab:selected {{
        margin-bottom: -1px;
    }}
    """

    return stylesheet
