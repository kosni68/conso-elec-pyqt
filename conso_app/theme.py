from __future__ import annotations

from matplotlib.figure import Figure
from PyQt6.QtWidgets import QApplication

APP_BACKGROUND = "#0f141d"
PANEL_BACKGROUND = "#161d2b"
CARD_BACKGROUND = "#182131"
BORDER_COLOR = "#2b3648"
TEXT_PRIMARY = "#edf2f7"
TEXT_MUTED = "#9aaabd"
GRID_COLOR = "#33445b"
ACCENT_BLUE = "#65b8ff"
ACCENT_CYAN = "#4dd7f2"
ACCENT_ORANGE = "#ff9f5a"
ACCENT_GREEN = "#63d2b2"
FILL_BLUE = "#274a63"

DARK_STYLESHEET = f"""
QMainWindow, QWidget {{
    background-color: {APP_BACKGROUND};
    color: {TEXT_PRIMARY};
}}
QGroupBox {{
    background-color: {PANEL_BACKGROUND};
    border: 1px solid {BORDER_COLOR};
    border-radius: 12px;
    margin-top: 14px;
    padding-top: 10px;
    font-weight: 600;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 6px;
    color: {TEXT_MUTED};
}}
QFrame {{
    background-color: {CARD_BACKGROUND};
    border: 1px solid {BORDER_COLOR};
    border-radius: 10px;
}}
QLabel {{
    color: {TEXT_PRIMARY};
}}
QLineEdit, QDateEdit, QTimeEdit, QDoubleSpinBox {{
    background-color: #0f1724;
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER_COLOR};
    border-radius: 8px;
    padding: 6px 8px;
    selection-background-color: {ACCENT_BLUE};
}}
QPushButton {{
    background-color: #223047;
    color: {TEXT_PRIMARY};
    border: 1px solid #314461;
    border-radius: 8px;
    padding: 7px 12px;
}}
QPushButton:hover {{
    background-color: #2c4060;
}}
QPushButton:pressed {{
    background-color: #1d2a40;
}}
QPushButton:checked {{
    background-color: #36557f;
    border-color: {ACCENT_BLUE};
}}
QPushButton:disabled {{
    color: #71839c;
    background-color: #1a2332;
    border-color: #263346;
}}
QTabWidget::pane {{
    border: 1px solid {BORDER_COLOR};
    border-radius: 12px;
    background-color: {PANEL_BACKGROUND};
    top: -1px;
}}
QTabBar::tab {{
    background-color: #111824;
    color: {TEXT_MUTED};
    border: 1px solid {BORDER_COLOR};
    border-bottom: none;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    padding: 10px 18px;
    margin-right: 4px;
}}
QTabBar::tab:selected {{
    background-color: {PANEL_BACKGROUND};
    color: {TEXT_PRIMARY};
}}
QStatusBar {{
    background-color: #0c1118;
    color: {TEXT_MUTED};
}}
QToolTip {{
    background-color: {CARD_BACKGROUND};
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER_COLOR};
}}
"""


def apply_dark_theme(app: QApplication) -> None:
    app.setStyle("Fusion")
    app.setStyleSheet(DARK_STYLESHEET)


def style_figure(figure: Figure) -> None:
    figure.set_facecolor(APP_BACKGROUND)


def style_axis(axis) -> None:
    axis.set_facecolor(PANEL_BACKGROUND)
    axis.title.set_color(TEXT_PRIMARY)
    axis.xaxis.label.set_color(TEXT_MUTED)
    axis.yaxis.label.set_color(TEXT_MUTED)
    axis.tick_params(axis="x", colors=TEXT_MUTED)
    axis.tick_params(axis="y", colors=TEXT_MUTED)
    for spine in axis.spines.values():
        spine.set_color(BORDER_COLOR)
    axis.grid(color=GRID_COLOR, alpha=0.35)
