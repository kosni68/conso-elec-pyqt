from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import matplotlib.dates as mdates
import numpy as np
from matplotlib.artist import Artist
from matplotlib.axes import Axes
from matplotlib.backend_bases import MouseButton
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QFileDialog, QHBoxLayout, QLabel, QPushButton, QSizePolicy, QVBoxLayout, QWidget

from ..analysis import AnalysisSummary
from ..theme import (
    ACCENT_BLUE,
    ACCENT_CYAN,
    ACCENT_GOLD,
    ACCENT_GREEN,
    ACCENT_ORANGE,
    BORDER_COLOR,
    CARD_BACKGROUND,
    FILL_BLUE,
    PANEL_BACKGROUND,
    TEXT_MUTED,
    TEXT_PRIMARY,
    style_axis,
    style_figure,
)
from .chart_utils import (
    find_bar_index,
    find_nearest_line_point,
    find_nearest_x_index,
    format_daily_tooltip,
    format_hourly_profile_tooltip,
    format_month_total_tooltip,
    format_simulation_tooltip,
)

DEFAULT_HELP_TEXT = "Survol: détails | Molette: zoom | Double-clic: reset | Esc: quitter pan/zoom"


@dataclass(frozen=True, slots=True)
class AxisViewState:
    xlim: tuple[float, float]
    ylim: tuple[float, float]


@dataclass(slots=True)
class PanState:
    axis: Axes
    start_xdata: float
    start_ydata: float
    original_xlim: tuple[float, float]
    original_ylim: tuple[float, float]


@dataclass(slots=True)
class ZoomState:
    axis: Axes
    start_xdata: float
    start_ydata: float
    rectangle: Rectangle


@dataclass(slots=True)
class LegendToggleGroup:
    artists: list[Artist]
    legend_handle: Artist
    legend_text: Artist


class ChartToolbar(QWidget):
    def __init__(self) -> None:
        super().__init__()
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self.button_map: dict[str, QPushButton] = {}
        button_specs = [
            ("home", "Accueil", False),
            ("back", "Retour", False),
            ("forward", "Avancer", False),
            ("pan", "Pan", True),
            ("zoom", "Zoom", True),
            ("reset", "Reset", False),
            ("save", "PNG", False),
        ]
        for key, label, checkable in button_specs:
            button = QPushButton(label)
            button.setCheckable(checkable)
            self.button_map[key] = button
            layout.addWidget(button)

        layout.addStretch(1)

    def set_mode(self, mode: str) -> None:
        self.button_map["pan"].setChecked(mode == "pan")
        self.button_map["zoom"].setChecked(mode == "zoom")

    def set_navigation_state(self, *, can_go_back: bool, can_go_forward: bool) -> None:
        self.button_map["back"].setEnabled(can_go_back)
        self.button_map["forward"].setEnabled(can_go_forward)

    def set_navigation_enabled(self, enabled: bool) -> None:
        for key in ("home", "back", "forward", "pan", "zoom", "reset"):
            self.button_map[key].setEnabled(enabled)


class MatplotlibCanvas(FigureCanvas):
    def __init__(self, height: float = 5.0) -> None:
        figure = Figure(figsize=(10, height), tight_layout=True)
        super().__init__(figure)
        self.figure = figure
        style_figure(self.figure)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setMouseTracking(True)


class InteractiveChartView(QWidget):
    status_message_changed = pyqtSignal(str)

    def __init__(
        self,
        *,
        height: float,
        help_text: str = DEFAULT_HELP_TEXT,
        note_text: str | None = None,
        export_name: str = "chart",
    ) -> None:
        super().__init__()
        self.export_name = export_name
        self._base_help_text = help_text
        self._mode = "inspect"
        self._plot_axes: list[Axes] = []
        self._tooltip_annotations: dict[Axes, Artist] = {}
        self._view_history: list[tuple[AxisViewState, ...]] = []
        self._view_history_index = -1
        self._pan_state: PanState | None = None
        self._zoom_state: ZoomState | None = None
        self._legend_groups: dict[str, LegendToggleGroup] = {}
        self._legend_artist_map: dict[Artist, str] = {}

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        self.note_label: QLabel | None = None
        if note_text is not None:
            self.note_label = QLabel(note_text)
            self.note_label.setWordWrap(True)
            self.note_label.setStyleSheet(f"color: {TEXT_MUTED};")
            layout.addWidget(self.note_label)

        self.toolbar = ChartToolbar()
        layout.addWidget(self.toolbar)

        self.canvas = MatplotlibCanvas(height=height)
        self.canvas.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        layout.addWidget(self.canvas)

        self.help_label = QLabel(help_text)
        self.help_label.setWordWrap(True)
        self.help_label.setStyleSheet(f"color: {TEXT_MUTED};")
        layout.addWidget(self.help_label)

        self._connect_toolbar()
        self._connect_canvas_events()

    @property
    def plot_axes(self) -> list[Axes]:
        return self._plot_axes

    @property
    def current_mode(self) -> str:
        return self._mode

    @property
    def tooltip_annotations(self) -> dict[Axes, Artist]:
        return self._tooltip_annotations

    def set_note_text(self, text: str) -> None:
        if self.note_label is not None:
            self.note_label.setText(text)

    def set_help_text(self, text: str) -> None:
        self.help_label.setText(text)

    def _navigation_axes(self) -> tuple[Axes, ...]:
        return tuple(self._plot_axes)

    def _has_navigation(self) -> bool:
        return len(self._navigation_axes()) > 0

    def _is_navigable_axis(self, axis: Axes | None) -> bool:
        return axis is not None and axis in self._navigation_axes()

    def _pan_components(self, axis: Axes, dx: float, dy: float) -> tuple[float, float]:
        return dx, dy

    def _pan_status_text(self) -> str:
        return "Mode pan actif. Glissez pour déplacer la vue."

    def _zoom_status_text(self) -> str:
        return "Mode zoom actif. Tracez un rectangle pour zoomer."

    def _sync_navigation_controls(self) -> None:
        has_navigation = self._has_navigation()
        self.toolbar.set_navigation_enabled(has_navigation)
        self.toolbar.set_navigation_state(
            can_go_back=has_navigation and self._view_history_index > 0,
            can_go_forward=has_navigation and self._view_history_index < len(self._view_history) - 1,
        )

    def _after_view_changed(self) -> None:
        pass

    def home(self) -> None:
        if not self._has_navigation() or not self._view_history:
            return
        self._restore_history_index(0)
        self._emit_status("Vue initiale restaurée.")

    def back(self) -> None:
        if not self._has_navigation() or self._view_history_index <= 0:
            return
        self._restore_history_index(self._view_history_index - 1)
        self._emit_status("Vue précédente restaurée.")

    def forward(self) -> None:
        if not self._has_navigation() or self._view_history_index >= len(self._view_history) - 1:
            return
        self._restore_history_index(self._view_history_index + 1)
        self._emit_status("Vue suivante restaurée.")

    def reset_view(self) -> None:
        if not self._has_navigation():
            return
        self.home()
        self.set_mode("inspect")
        self.clear_hover_state()

    def set_mode(self, mode: str) -> None:
        normalized_mode = mode if mode in {"inspect", "pan", "zoom"} else "inspect"
        if not self._has_navigation():
            normalized_mode = "inspect"
        self._mode = normalized_mode
        self._pan_state = None
        self._clear_zoom_rectangle()
        self.toolbar.set_mode(normalized_mode)

        if normalized_mode == "pan":
            self.canvas.setCursor(Qt.CursorShape.OpenHandCursor)
            self._emit_status(self._pan_status_text())
        elif normalized_mode == "zoom":
            self.canvas.setCursor(Qt.CursorShape.CrossCursor)
            self._emit_status(self._zoom_status_text())
        else:
            self.canvas.setCursor(Qt.CursorShape.ArrowCursor)
            self._emit_status(self._base_help_text)

    def save_png(self) -> None:
        default_name = f"{self.export_name}.png"
        target_path, _ = QFileDialog.getSaveFileName(
            self,
            "Enregistrer le graphique",
            str(Path.cwd() / default_name),
            "PNG (*.png)",
        )
        if not target_path:
            return
        self.canvas.figure.savefig(target_path, dpi=160, facecolor=self.canvas.figure.get_facecolor())
        self._emit_status(f"Graphique enregistré : {Path(target_path).name}")

    def clear_hover_state(self) -> None:
        self._clear_hover_artists()
        self._hide_all_tooltips()
        self.canvas.draw_idle()

    def _connect_toolbar(self) -> None:
        self.toolbar.button_map["home"].clicked.connect(self.home)
        self.toolbar.button_map["back"].clicked.connect(self.back)
        self.toolbar.button_map["forward"].clicked.connect(self.forward)
        self.toolbar.button_map["reset"].clicked.connect(self.reset_view)
        self.toolbar.button_map["save"].clicked.connect(self.save_png)
        self.toolbar.button_map["pan"].clicked.connect(
            lambda checked: self.set_mode("pan" if checked else "inspect")
        )
        self.toolbar.button_map["zoom"].clicked.connect(
            lambda checked: self.set_mode("zoom" if checked else "inspect")
        )
        self._sync_navigation_controls()

    def _connect_canvas_events(self) -> None:
        self.canvas.mpl_connect("motion_notify_event", self._on_motion)
        self.canvas.mpl_connect("scroll_event", self._on_scroll)
        self.canvas.mpl_connect("button_press_event", self._on_button_press)
        self.canvas.mpl_connect("button_release_event", self._on_button_release)
        self.canvas.mpl_connect("figure_leave_event", self._on_figure_leave)
        self.canvas.mpl_connect("key_press_event", self._on_key_press)
        self.canvas.mpl_connect("pick_event", self._on_pick)

    def _set_plot_axes(self, axes: list[Axes]) -> None:
        self._plot_axes = axes
        self._tooltip_annotations = {axis: self._create_tooltip(axis) for axis in axes}
        self._legend_groups.clear()
        self._legend_artist_map.clear()
        self._pan_state = None
        self._clear_zoom_rectangle()
        self._reset_history()
        self.set_mode("inspect")
        self._after_view_changed()

    def _reset_history(self) -> None:
        if not self._plot_axes:
            self._view_history = []
            self._view_history_index = -1
            self._sync_navigation_controls()
            return

        self._view_history = [self._capture_current_view()]
        self._view_history_index = 0
        self._sync_navigation_controls()

    def _capture_current_view(self) -> tuple[AxisViewState, ...]:
        return tuple(
            AxisViewState(
                xlim=tuple(float(value) for value in axis.get_xlim()),
                ylim=tuple(float(value) for value in axis.get_ylim()),
            )
            for axis in self._plot_axes
        )

    def _restore_history_index(self, index: int) -> None:
        if not (0 <= index < len(self._view_history)):
            return
        self._view_history_index = index
        self._apply_view_state(self._view_history[index])
        self._sync_navigation_controls()

    def _apply_view_state(self, view_state: tuple[AxisViewState, ...]) -> None:
        for axis, axis_state in zip(self._plot_axes, view_state, strict=False):
            axis.set_xlim(axis_state.xlim)
            axis.set_ylim(axis_state.ylim)
        self._after_view_changed()
        self.canvas.draw_idle()

    def _push_current_view(self) -> None:
        current_view = self._capture_current_view()
        if self._view_history and current_view == self._view_history[self._view_history_index]:
            return

        if self._view_history_index < len(self._view_history) - 1:
            self._view_history = self._view_history[: self._view_history_index + 1]
        self._view_history.append(current_view)
        self._view_history_index = len(self._view_history) - 1
        self._sync_navigation_controls()

    def _create_tooltip(self, axis: Axes):
        annotation = axis.annotate(
            "",
            xy=(0, 0),
            xytext=(14, 14),
            textcoords="offset points",
            fontsize=9,
            color=TEXT_PRIMARY,
            bbox={
                "boxstyle": "round,pad=0.4",
                "facecolor": CARD_BACKGROUND,
                "edgecolor": BORDER_COLOR,
                "alpha": 0.96,
            },
            arrowprops={"arrowstyle": "->", "color": BORDER_COLOR, "alpha": 0.9},
            annotation_clip=False,
        )
        annotation.set_visible(False)
        return annotation

    def _show_tooltip(self, axis: Axes, *, x_value: float, y_value: float, text: str) -> None:
        for current_axis, annotation in self._tooltip_annotations.items():
            annotation.set_visible(current_axis is axis)
        annotation = self._tooltip_annotations[axis]
        annotation.xy = (x_value, y_value)
        annotation.set_text(text)
        annotation.set_visible(True)
        self.canvas.draw_idle()

    def _hide_all_tooltips(self) -> None:
        for annotation in self._tooltip_annotations.values():
            annotation.set_visible(False)

    def _emit_status(self, message: str) -> None:
        self.status_message_changed.emit(message)

    def _clear_zoom_rectangle(self) -> None:
        if self._zoom_state is None:
            return
        rectangle = self._zoom_state.rectangle
        if rectangle.axes is not None:
            rectangle.remove()
        self._zoom_state = None

    def _on_motion(self, event) -> None:
        if self._pan_state is not None:
            self._update_pan(event)
            return

        if self._zoom_state is not None:
            self._update_zoom_rectangle(event)
            return

        if not self._update_hover(event):
            self.clear_hover_state()

    def _on_scroll(self, event) -> None:
        axis = event.inaxes
        if axis is None or not self._is_navigable_axis(axis) or event.xdata is None or event.ydata is None:
            return

        scale_factor = 1 / 1.2 if getattr(event, "step", 0) > 0 or getattr(event, "button", None) == "up" else 1.2
        x_left, x_right = axis.get_xlim()
        y_bottom, y_top = axis.get_ylim()
        x_value = event.xdata
        y_value = event.ydata

        new_xlim = (
            x_value - (x_value - x_left) * scale_factor,
            x_value + (x_right - x_value) * scale_factor,
        )
        new_ylim = (
            y_value - (y_value - y_bottom) * scale_factor,
            y_value + (y_top - y_value) * scale_factor,
        )
        axis.set_xlim(new_xlim)
        axis.set_ylim(new_ylim)
        self._after_view_changed()
        self._push_current_view()
        self.canvas.draw_idle()

    def _on_button_press(self, event) -> None:
        self.canvas.setFocus()
        if event.inaxes is None:
            return

        if getattr(event, "dblclick", False) and self._is_navigable_axis(event.inaxes):
            self.reset_view()
            return

        if getattr(event, "button", None) not in {1, MouseButton.LEFT}:
            return
        if event.xdata is None or event.ydata is None:
            return
        if not self._is_navigable_axis(event.inaxes):
            return

        if self._mode == "pan":
            self._pan_state = PanState(
                axis=event.inaxes,
                start_xdata=float(event.xdata),
                start_ydata=float(event.ydata),
                original_xlim=tuple(float(value) for value in event.inaxes.get_xlim()),
                original_ylim=tuple(float(value) for value in event.inaxes.get_ylim()),
            )
            self.canvas.setCursor(Qt.CursorShape.ClosedHandCursor)
            return

        if self._mode == "zoom":
            rectangle = Rectangle(
                (event.xdata, event.ydata),
                0.0,
                0.0,
                fill=False,
                linestyle="--",
                linewidth=1.6,
                edgecolor=TEXT_PRIMARY,
                alpha=0.9,
            )
            event.inaxes.add_patch(rectangle)
            self._zoom_state = ZoomState(
                axis=event.inaxes,
                start_xdata=float(event.xdata),
                start_ydata=float(event.ydata),
                rectangle=rectangle,
            )
            self.canvas.draw_idle()

    def _on_button_release(self, event) -> None:
        if self._pan_state is not None:
            self._pan_state = None
            self.canvas.setCursor(Qt.CursorShape.OpenHandCursor if self._mode == "pan" else Qt.CursorShape.ArrowCursor)
            self._push_current_view()
            return

        if self._zoom_state is not None:
            self._finalize_zoom_rectangle(event)

    def _on_figure_leave(self, _event) -> None:
        if self._pan_state is None and self._zoom_state is None:
            self.clear_hover_state()

    def _on_key_press(self, event) -> None:
        if getattr(event, "key", None) == "escape":
            self.set_mode("inspect")

    def _on_pick(self, event) -> None:
        if self._handle_pick(event):
            self.canvas.draw_idle()

    def _update_pan(self, event) -> None:
        if self._pan_state is None or event.inaxes is not self._pan_state.axis:
            return
        if event.xdata is None or event.ydata is None:
            return

        dx = float(event.xdata) - self._pan_state.start_xdata
        dy = float(event.ydata) - self._pan_state.start_ydata
        dx, dy = self._pan_components(self._pan_state.axis, dx, dy)
        x_left, x_right = self._pan_state.original_xlim
        y_bottom, y_top = self._pan_state.original_ylim
        self._pan_state.axis.set_xlim((x_left - dx, x_right - dx))
        self._pan_state.axis.set_ylim((y_bottom - dy, y_top - dy))
        self._after_view_changed()
        self.canvas.draw_idle()

    def _update_zoom_rectangle(self, event) -> None:
        if self._zoom_state is None or event.inaxes is not self._zoom_state.axis:
            return
        if event.xdata is None or event.ydata is None:
            return

        start_x = self._zoom_state.start_xdata
        start_y = self._zoom_state.start_ydata
        x0, x1 = sorted((start_x, float(event.xdata)))
        y0, y1 = sorted((start_y, float(event.ydata)))
        self._zoom_state.rectangle.set_bounds(x0, y0, x1 - x0, y1 - y0)
        self.canvas.draw_idle()

    def _finalize_zoom_rectangle(self, event) -> None:
        if self._zoom_state is None:
            return

        zoom_state = self._zoom_state
        self._clear_zoom_rectangle()

        if event.inaxes is not zoom_state.axis or event.xdata is None or event.ydata is None:
            self.canvas.draw_idle()
            return

        x0, x1 = sorted((zoom_state.start_xdata, float(event.xdata)))
        y0, y1 = sorted((zoom_state.start_ydata, float(event.ydata)))
        if abs(x1 - x0) < 1e-9 or abs(y1 - y0) < 1e-9:
            self.canvas.draw_idle()
            return

        zoom_state.axis.set_xlim((x0, x1))
        zoom_state.axis.set_ylim((y0, y1))
        self._after_view_changed()
        self._push_current_view()
        self.canvas.draw_idle()

    def _register_legend_group(
        self,
        *,
        key: str,
        artists: list[Artist],
        legend_handle: Artist,
        legend_text: Artist,
    ) -> None:
        self._legend_groups[key] = LegendToggleGroup(
            artists=artists,
            legend_handle=legend_handle,
            legend_text=legend_text,
        )
        legend_handle.set_picker(True)
        legend_text.set_picker(True)
        self._legend_artist_map[legend_handle] = key
        self._legend_artist_map[legend_text] = key

    def _toggle_legend_group(self, key: str) -> bool:
        group = self._legend_groups.get(key)
        if group is None:
            return False

        is_visible = any(artist.get_visible() for artist in group.artists)
        new_visible = not is_visible
        for artist in group.artists:
            artist.set_visible(new_visible)
        group.legend_handle.set_alpha(1.0 if new_visible else 0.35)
        group.legend_text.set_alpha(1.0 if new_visible else 0.45)
        return True

    def _update_hover(self, event) -> bool:
        return False

    def _clear_hover_artists(self) -> None:
        pass

    def _handle_pick(self, event) -> bool:
        return False


class OverviewChartView(InteractiveChartView):
    def __init__(self) -> None:
        super().__init__(
            height=9.4,
            help_text="Survol partout | Zoom, pan et déplacement horizontal uniquement sur la consommation journalière",
            note_text="Les graphiques apparaîtront après chargement du CSV.",
            export_name="vue_globale",
        )
        self.canvas.setMinimumHeight(860)
        self._daily_data: dict[str, object] = {}
        self._monthly_data: dict[str, object] = {}
        self._hourly_data: dict[str, object] = {}
        self._daily_highlight: Line2D | None = None
        self._hourly_highlight: Line2D | None = None
        self._active_month_bar: Rectangle | None = None

    def update_summary(self, summary: AnalysisSummary) -> None:
        figure = self.canvas.figure
        figure.clear()
        style_figure(figure)
        axes = list(np.atleast_1d(figure.subplots(3, 1, gridspec_kw={"height_ratios": [2.55, 1.15, 1.15]})))

        self._daily_data = {}
        self._monthly_data = {}
        self._hourly_data = {}
        self._daily_highlight = None
        self._hourly_highlight = None
        self._active_month_bar = None

        if summary.filtered_df.empty:
            for axis in axes:
                axis.text(0.5, 0.5, "Aucune donnée sur cette plage.", ha="center", va="center")
                axis.set_axis_off()
            self._set_plot_axes(axes)
            self.canvas.draw_idle()
            return

        daily = summary.daily_totals
        monthly = summary.monthly_totals
        hourly = summary.hourly_profile.reindex(range(24), fill_value=0.0)

        for axis in axes:
            style_axis(axis)

        daily_line, = axes[0].plot(daily.index, daily.values, color=ACCENT_BLUE, linewidth=1.8)
        axes[0].fill_between(daily.index, daily.values, color=FILL_BLUE, alpha=0.45)
        axes[0].set_title("Consommation journalière")
        axes[0].set_ylabel("kWh")
        self._daily_highlight, = axes[0].plot(
            [],
            [],
            marker="o",
            linestyle="None",
            markersize=9,
            markerfacecolor=ACCENT_BLUE,
            markeredgecolor=TEXT_PRIMARY,
            markeredgewidth=1.2,
            visible=False,
        )

        month_positions = np.arange(len(monthly), dtype=float)
        month_labels = [value.strftime("%b %Y") for value in monthly.index]
        month_bars = axes[1].bar(month_positions, monthly.values, color=ACCENT_ORANGE, width=0.65)
        axes[1].set_title("Totaux mensuels")
        axes[1].set_ylabel("kWh")
        axes[1].set_xticks(month_positions)
        axes[1].set_xticklabels(month_labels, rotation=35)

        hourly_line, = axes[2].plot(hourly.index, hourly.values, marker="o", color=ACCENT_GREEN)
        axes[2].set_title("Profil horaire moyen")
        axes[2].set_xlabel("Heure")
        axes[2].set_ylabel("kWh / heure")
        axes[2].set_xticks(range(0, 24, 2))
        self._hourly_highlight, = axes[2].plot(
            [],
            [],
            marker="o",
            linestyle="None",
            markersize=9,
            markerfacecolor=ACCENT_GREEN,
            markeredgecolor=TEXT_PRIMARY,
            markeredgewidth=1.2,
            visible=False,
        )

        self._daily_data = {
            "axis": axes[0],
            "line": daily_line,
            "x_values": mdates.date2num(daily.index.to_pydatetime()),
            "y_values": daily.to_numpy(dtype=float),
            "labels": [timestamp.strftime("%d/%m/%Y") for timestamp in daily.index],
            "plot_x": daily.index.to_list(),
        }
        self._monthly_data = {
            "axis": axes[1],
            "bars": list(month_bars),
            "labels": month_labels,
            "values": monthly.to_numpy(dtype=float),
            "positions": month_positions,
        }
        self._hourly_data = {
            "axis": axes[2],
            "line": hourly_line,
            "x_values": hourly.index.to_numpy(dtype=float),
            "y_values": hourly.to_numpy(dtype=float),
            "labels": [f"{int(hour):02d}:00" for hour in hourly.index],
        }

        self.set_note_text(
            "La vue globale utilise la plage filtrée. Le profil horaire correspond à une moyenne journalière par heure."
        )
        figure.align_labels()
        self._set_plot_axes(axes)
        self.canvas.draw_idle()

    def _navigation_axes(self) -> tuple[Axes, ...]:
        daily_axis = getattr(self, "_daily_data", {}).get("axis")
        return (daily_axis,) if daily_axis is not None else ()

    def _pan_components(self, axis: Axes, dx: float, dy: float) -> tuple[float, float]:
        if axis is getattr(self, "_daily_data", {}).get("axis"):
            return dx, 0.0
        return super()._pan_components(axis, dx, dy)

    def _pan_status_text(self) -> str:
        return "Mode pan actif. Glissez horizontalement sur la consommation journalière."

    def _zoom_status_text(self) -> str:
        return "Mode zoom actif uniquement sur la consommation journalière."

    def _update_hover(self, event) -> bool:
        if event.inaxes is None:
            return False

        if event.inaxes is self._daily_data.get("axis"):
            match = find_nearest_line_point(
                event.inaxes,
                event.xdata,
                event.ydata,
                self._daily_data["x_values"],
                self._daily_data["y_values"],
            )
            if match is None:
                return False
            plot_x = self._daily_data["plot_x"][match.index]
            plot_y = self._daily_data["y_values"][match.index]
            self._daily_highlight.set_data([plot_x], [plot_y])
            self._daily_highlight.set_visible(True)
            self._show_tooltip(
                event.inaxes,
                x_value=mdates.date2num(plot_x),
                y_value=plot_y,
                text=format_daily_tooltip(self._daily_data["labels"][match.index], plot_y),
            )
            return True

        if event.inaxes is self._monthly_data.get("axis"):
            bar_index = find_bar_index(event.xdata, event.ydata, self._monthly_data["bars"])
            if bar_index is None:
                return False
            bar = self._monthly_data["bars"][bar_index]
            self._highlight_month_bar(bar)
            x_value = bar.get_x() + (bar.get_width() / 2)
            y_value = bar.get_height()
            self._show_tooltip(
                event.inaxes,
                x_value=x_value,
                y_value=y_value,
                text=format_month_total_tooltip(self._monthly_data["labels"][bar_index], self._monthly_data["values"][bar_index]),
            )
            return True

        if event.inaxes is self._hourly_data.get("axis"):
            match = find_nearest_line_point(
                event.inaxes,
                event.xdata,
                event.ydata,
                self._hourly_data["x_values"],
                self._hourly_data["y_values"],
            )
            if match is None:
                return False
            x_value = self._hourly_data["x_values"][match.index]
            y_value = self._hourly_data["y_values"][match.index]
            self._hourly_highlight.set_data([x_value], [y_value])
            self._hourly_highlight.set_visible(True)
            self._show_tooltip(
                event.inaxes,
                x_value=x_value,
                y_value=y_value,
                text=format_hourly_profile_tooltip(self._hourly_data["labels"][match.index], y_value),
            )
            return True

        return False

    def _highlight_month_bar(self, active_bar: Rectangle) -> None:
        for bar in self._monthly_data.get("bars", []):
            bar.set_linewidth(0.0)
            bar.set_edgecolor(BORDER_COLOR)
            bar.set_alpha(0.9)
        active_bar.set_linewidth(1.8)
        active_bar.set_edgecolor(TEXT_PRIMARY)
        active_bar.set_alpha(1.0)
        self._active_month_bar = active_bar

    def _clear_hover_artists(self) -> None:
        if self._daily_highlight is not None:
            self._daily_highlight.set_visible(False)
        if self._hourly_highlight is not None:
            self._hourly_highlight.set_visible(False)
        if self._monthly_data:
            for bar in self._monthly_data["bars"]:
                bar.set_linewidth(0.0)
                bar.set_edgecolor(BORDER_COLOR)
                bar.set_alpha(0.9)
        self._active_month_bar = None


class SimulationChartView(InteractiveChartView):
    def __init__(self) -> None:
        super().__init__(
            height=4.5,
            help_text="Survol et légende cliquable | Zoom et pan désactivés sur ce graphique",
            export_name="simulation_annuelle",
        )
        self._monthly_summary = None
        self._baseline_bars: list[Rectangle] = []
        self._grid_bars: list[Rectangle] = []
        self._curtailed_bars: list[Rectangle] = []
        self._pv_line: Line2D | None = None
        self._ev_line: Line2D | None = None
        self._pv_highlight: Line2D | None = None
        self._ev_highlight: Line2D | None = None
        self._legend = None

    def _navigation_axes(self) -> tuple[Axes, ...]:
        return ()

    def update_simulation(self, simulation_df) -> None:
        figure = self.canvas.figure
        figure.clear()
        style_figure(figure)
        axis = figure.subplots(1, 1)

        self._monthly_summary = None
        self._baseline_bars = []
        self._grid_bars = []
        self._curtailed_bars = []
        self._pv_line = None
        self._ev_line = None
        self._pv_highlight = None
        self._ev_highlight = None
        self._legend = None

        if simulation_df is None or simulation_df.empty:
            axis.text(0.5, 0.5, "Simulation indisponible.", ha="center", va="center")
            axis.set_axis_off()
            self._set_plot_axes([axis])
            self.canvas.draw_idle()
            return

        style_axis(axis)
        monthly = simulation_df.resample("MS").agg(
            baseline_kwh=("consumption_kwh", "sum"),
            grid_kwh=("grid_kwh", "sum"),
            pv_kwh=("pv_generation_kwh", "sum"),
            curtailed_kwh=("curtailed_pv_kwh", "sum"),
            ev_kwh=("ev_charging_kwh", "sum"),
        )
        positions = np.arange(len(monthly), dtype=float)
        width = 0.24
        labels = [timestamp.strftime("%b %Y") for timestamp in monthly.index]

        baseline_container = axis.bar(
            positions - width,
            monthly["baseline_kwh"],
            width=width,
            color=ACCENT_BLUE,
            label="Charge",
        )
        grid_container = axis.bar(
            positions,
            monthly["grid_kwh"],
            width=width,
            color=ACCENT_ORANGE,
            label="Réseau après simulation",
        )
        curtailed_container = axis.bar(
            positions + width,
            -monthly["curtailed_kwh"],
            width=width,
            color=ACCENT_GREEN,
            label="Surplus perdu",
        )
        self._pv_line, = axis.plot(
            positions,
            monthly["pv_kwh"],
            color=ACCENT_CYAN,
            marker="o",
            linewidth=2,
            label="Production PV",
        )
        self._ev_line, = axis.plot(
            positions,
            monthly["ev_kwh"],
            color=ACCENT_GOLD,
            marker="s",
            linestyle="--",
            linewidth=1.8,
            label="Recharge VE",
        )
        axis.axhline(0.0, color=BORDER_COLOR, linewidth=1.1, alpha=0.9)
        axis.set_xticks(positions)
        axis.set_xticklabels(labels, rotation=35)
        axis.set_ylabel("kWh / mois")
        axis.set_title("Comparaison mensuelle annualisée")

        self._pv_highlight, = axis.plot(
            [],
            [],
            marker="o",
            linestyle="None",
            markersize=9,
            markerfacecolor=ACCENT_CYAN,
            markeredgecolor=TEXT_PRIMARY,
            markeredgewidth=1.2,
            visible=False,
        )
        self._ev_highlight, = axis.plot(
            [],
            [],
            marker="s",
            linestyle="None",
            markersize=8,
            markerfacecolor=ACCENT_GOLD,
            markeredgecolor=TEXT_PRIMARY,
            markeredgewidth=1.2,
            visible=False,
        )

        self._legend = axis.legend()
        self._style_legend(self._legend)
        self._baseline_bars = list(baseline_container)
        self._grid_bars = list(grid_container)
        self._curtailed_bars = list(curtailed_container)
        self._monthly_summary = monthly

        self._set_plot_axes([axis])
        legend_handles = list(getattr(self._legend, "legend_handles", []))
        legend_texts = list(self._legend.get_texts())
        group_specs = [
            ("baseline", self._baseline_bars),
            ("grid", self._grid_bars),
            ("curtailed", self._curtailed_bars),
            ("pv", [self._pv_line]),
            ("ev", [self._ev_line]),
        ]
        for (key, artists), legend_handle, legend_text in zip(group_specs, legend_handles, legend_texts, strict=False):
            self._register_legend_group(
                key=key,
                artists=artists,
                legend_handle=legend_handle,
                legend_text=legend_text,
            )

        self.canvas.draw_idle()

    def _style_legend(self, legend) -> None:
        legend.get_frame().set_facecolor(PANEL_BACKGROUND)
        legend.get_frame().set_edgecolor(BORDER_COLOR)
        for text in legend.get_texts():
            text.set_color(TEXT_PRIMARY)

    def _visible_group_value(self, key: str, index: int) -> float | None:
        if self._monthly_summary is None:
            return None
        if key == "baseline" and any(bar.get_visible() for bar in self._baseline_bars):
            return float(self._monthly_summary["baseline_kwh"].iloc[index])
        if key == "grid" and any(bar.get_visible() for bar in self._grid_bars):
            return float(self._monthly_summary["grid_kwh"].iloc[index])
        if key == "curtailed" and any(bar.get_visible() for bar in self._curtailed_bars):
            return float(self._monthly_summary["curtailed_kwh"].iloc[index])
        if key == "pv" and self._pv_line is not None and self._pv_line.get_visible():
            return float(self._monthly_summary["pv_kwh"].iloc[index])
        if key == "ev" and self._ev_line is not None and self._ev_line.get_visible():
            return float(self._monthly_summary["ev_kwh"].iloc[index])
        return None

    @staticmethod
    def _tooltip_anchor_y(
        *,
        preferred_series: str | None,
        baseline_value: float | None,
        grid_value: float | None,
        pv_value: float | None,
        curtailed_value: float | None,
        ev_value: float | None,
    ) -> float:
        negative_curtailed = -curtailed_value if curtailed_value is not None else None
        positive_values = [value for value in (baseline_value, grid_value, pv_value, ev_value) if value is not None]
        if preferred_series == "curtailed" and negative_curtailed is not None:
            return negative_curtailed
        if preferred_series == "pv" and pv_value is not None:
            return pv_value
        if preferred_series == "ev" and ev_value is not None:
            return ev_value
        if positive_values:
            return max(positive_values)
        if negative_curtailed is not None:
            return negative_curtailed
        return 0.0

    def _update_hover(self, event) -> bool:
        if event.inaxes is None or self._monthly_summary is None:
            return False
        axis = self.plot_axes[0]
        if event.inaxes is not axis:
            return False

        preferred_series: str | None = None
        bar_index = find_bar_index(event.xdata, event.ydata, self._baseline_bars)
        if bar_index is not None:
            preferred_series = "baseline"
        if bar_index is None:
            bar_index = find_bar_index(event.xdata, event.ydata, self._grid_bars)
            if bar_index is not None:
                preferred_series = "grid"
        if bar_index is None:
            bar_index = find_bar_index(event.xdata, event.ydata, self._curtailed_bars)
            if bar_index is not None:
                preferred_series = "curtailed"
        if bar_index is None:
            line_matches: list[tuple[str, object]] = []
            if self._pv_line is not None and self._pv_line.get_visible():
                pv_match = find_nearest_line_point(
                    axis,
                    event.xdata,
                    event.ydata,
                    np.arange(len(self._monthly_summary), dtype=float),
                    self._monthly_summary["pv_kwh"].to_numpy(dtype=float),
                )
                if pv_match is not None:
                    line_matches.append(("pv", pv_match))
            if self._ev_line is not None and self._ev_line.get_visible():
                ev_match = find_nearest_line_point(
                    axis,
                    event.xdata,
                    event.ydata,
                    np.arange(len(self._monthly_summary), dtype=float),
                    self._monthly_summary["ev_kwh"].to_numpy(dtype=float),
                )
                if ev_match is not None:
                    line_matches.append(("ev", ev_match))
            if line_matches:
                preferred_series, match = min(line_matches, key=lambda item: item[1].pixel_distance)
                bar_index = match.index
        if bar_index is None:
            bar_index = find_nearest_x_index(axis, event.xdata, np.arange(len(self._monthly_summary), dtype=float))
        if bar_index is None:
            return False

        period_label = self._monthly_summary.index[bar_index].strftime("%b %Y")
        baseline_value = self._visible_group_value("baseline", bar_index)
        grid_value = self._visible_group_value("grid", bar_index)
        pv_value = self._visible_group_value("pv", bar_index)
        curtailed_value = self._visible_group_value("curtailed", bar_index)
        ev_value = self._visible_group_value("ev", bar_index)
        if baseline_value is None and grid_value is None and pv_value is None and curtailed_value is None and ev_value is None:
            return False

        self._highlight_simulation_month(bar_index)
        tooltip_y = self._tooltip_anchor_y(
            preferred_series=preferred_series,
            baseline_value=baseline_value,
            grid_value=grid_value,
            pv_value=pv_value,
            curtailed_value=curtailed_value,
            ev_value=ev_value,
        )
        self._show_tooltip(
            axis,
            x_value=float(bar_index),
            y_value=tooltip_y,
            text=format_simulation_tooltip(period_label, baseline_value, grid_value, pv_value, curtailed_value, ev_value),
        )
        return True

    def _highlight_simulation_month(self, index: int) -> None:
        for bar in self._baseline_bars + self._grid_bars + self._curtailed_bars:
            bar.set_linewidth(0.0)
            bar.set_edgecolor(BORDER_COLOR)
            bar.set_alpha(0.9 if bar.get_visible() else 0.0)

        for bar_group in (self._baseline_bars, self._grid_bars, self._curtailed_bars):
            if index < len(bar_group) and bar_group[index].get_visible():
                bar_group[index].set_linewidth(1.8)
                bar_group[index].set_edgecolor(TEXT_PRIMARY)
                bar_group[index].set_alpha(1.0)

        if self._pv_highlight is not None and self._pv_line is not None and self._pv_line.get_visible():
            x_data = np.arange(len(self._monthly_summary), dtype=float)
            y_data = self._monthly_summary["pv_kwh"].to_numpy(dtype=float)
            self._pv_highlight.set_data([x_data[index]], [y_data[index]])
            self._pv_highlight.set_visible(True)
        elif self._pv_highlight is not None:
            self._pv_highlight.set_visible(False)

        if self._ev_highlight is not None and self._ev_line is not None and self._ev_line.get_visible():
            x_data = np.arange(len(self._monthly_summary), dtype=float)
            y_data = self._monthly_summary["ev_kwh"].to_numpy(dtype=float)
            self._ev_highlight.set_data([x_data[index]], [y_data[index]])
            self._ev_highlight.set_visible(True)
        elif self._ev_highlight is not None:
            self._ev_highlight.set_visible(False)

    def _clear_hover_artists(self) -> None:
        for bar in self._baseline_bars + self._grid_bars + self._curtailed_bars:
            bar.set_linewidth(0.0)
            bar.set_edgecolor(BORDER_COLOR)
            if bar.get_visible():
                bar.set_alpha(0.9)
        if self._pv_highlight is not None:
            self._pv_highlight.set_visible(False)
        if self._ev_highlight is not None:
            self._ev_highlight.set_visible(False)

    def _handle_pick(self, event) -> bool:
        key = self._legend_artist_map.get(event.artist)
        if key is None:
            return False
        toggled = self._toggle_legend_group(key)
        if toggled:
            self.clear_hover_state()
            self._emit_status("Série mise à jour depuis la légende.")
        return toggled
