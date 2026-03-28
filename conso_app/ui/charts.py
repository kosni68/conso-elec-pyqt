from __future__ import annotations

import numpy as np
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PyQt6.QtWidgets import QLabel, QSizePolicy, QVBoxLayout, QWidget

from ..analysis import AnalysisSummary
from ..theme import (
    ACCENT_BLUE,
    ACCENT_CYAN,
    ACCENT_GREEN,
    ACCENT_ORANGE,
    BORDER_COLOR,
    FILL_BLUE,
    PANEL_BACKGROUND,
    TEXT_MUTED,
    TEXT_PRIMARY,
    style_axis,
    style_figure,
)


class MatplotlibCanvas(FigureCanvas):
    def __init__(self, height: float = 5.0) -> None:
        figure = Figure(figsize=(10, height), tight_layout=True)
        super().__init__(figure)
        self.figure = figure
        style_figure(self.figure)


class OverviewChartView(QWidget):
    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        self.note_label = QLabel("Les graphiques apparaîtront après chargement du CSV.")
        self.note_label.setWordWrap(True)
        self.note_label.setStyleSheet(f"color: {TEXT_MUTED};")

        self.canvas = MatplotlibCanvas(height=8.5)
        layout.addWidget(self.note_label)
        layout.addWidget(self.canvas)

    def update_summary(self, summary: AnalysisSummary) -> None:
        figure = self.canvas.figure
        figure.clear()
        style_figure(figure)
        axes = figure.subplots(3, 1)

        if summary.filtered_df.empty:
            for axis in axes:
                axis.text(0.5, 0.5, "Aucune donnée sur cette plage.", ha="center", va="center")
                axis.set_axis_off()
            self.canvas.draw_idle()
            return

        daily = summary.daily_totals
        monthly = summary.monthly_totals
        hourly = summary.hourly_profile.reindex(range(24), fill_value=0.0)

        for axis in axes:
            style_axis(axis)

        axes[0].plot(daily.index, daily.values, color=ACCENT_BLUE, linewidth=1.8)
        axes[0].fill_between(daily.index, daily.values, color=FILL_BLUE, alpha=0.45)
        axes[0].set_title("Consommation journalière")
        axes[0].set_ylabel("kWh")

        month_labels = [value.strftime("%b %Y") for value in monthly.index]
        axes[1].bar(month_labels, monthly.values, color=ACCENT_ORANGE)
        axes[1].set_title("Totaux mensuels")
        axes[1].set_ylabel("kWh")
        axes[1].tick_params(axis="x", rotation=35)

        axes[2].plot(hourly.index, hourly.values, marker="o", color=ACCENT_GREEN)
        axes[2].set_title("Profil horaire moyen")
        axes[2].set_xlabel("Heure")
        axes[2].set_ylabel("kWh / heure")
        axes[2].set_xticks(range(0, 24, 2))

        self.note_label.setText(
            "La vue globale utilise la plage filtrée. Le profil horaire correspond à une moyenne journalière par heure."
        )
        figure.align_labels()
        self.canvas.draw_idle()


class SimulationChartView(QWidget):
    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.canvas = MatplotlibCanvas(height=4.5)
        self.canvas.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        layout.addWidget(self.canvas)

    def update_simulation(self, simulation_df) -> None:
        figure = self.canvas.figure
        figure.clear()
        style_figure(figure)
        axis = figure.subplots(1, 1)

        if simulation_df is None or simulation_df.empty:
            axis.text(0.5, 0.5, "Simulation indisponible.", ha="center", va="center")
            axis.set_axis_off()
            self.canvas.draw_idle()
            return

        style_axis(axis)
        monthly = simulation_df.resample("MS").agg(
            baseline_kwh=("consumption_kwh", "sum"),
            grid_kwh=("grid_kwh", "sum"),
            pv_kwh=("pv_generation_kwh", "sum"),
        )
        positions = np.arange(len(monthly))
        width = 0.34
        labels = [timestamp.strftime("%b %Y") for timestamp in monthly.index]

        axis.bar(positions - width / 2, monthly["baseline_kwh"], width=width, color=ACCENT_BLUE, label="Charge")
        axis.bar(
            positions + width / 2,
            monthly["grid_kwh"],
            width=width,
            color=ACCENT_ORANGE,
            label="Réseau après simulation",
        )
        axis.plot(positions, monthly["pv_kwh"], color=ACCENT_CYAN, marker="o", linewidth=2, label="Production PV")
        axis.set_xticks(positions)
        axis.set_xticklabels(labels, rotation=35)
        axis.set_ylabel("kWh / mois")
        axis.set_title("Comparaison mensuelle annualisée")
        legend = axis.legend()
        legend.get_frame().set_facecolor(PANEL_BACKGROUND)
        legend.get_frame().set_edgecolor(BORDER_COLOR)
        for text in legend.get_texts():
            text.set_color(TEXT_PRIMARY)
        self.canvas.draw_idle()
