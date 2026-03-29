from __future__ import annotations

from collections.abc import Mapping

from PyQt6.QtWidgets import QGridLayout, QGroupBox, QLabel, QSizePolicy, QVBoxLayout, QWidget

from ..models import SimulationResult
from ..theme import TEXT_MUTED
from .charts import SimulationChartView, SimulationComparisonChartView
from .formatting import format_currency, format_kwh, format_percent, fr_number
from .simulation_panel import EMPTY_VALUE, SimulationPanel

COMPARISON_RESULT_ROWS = (
    ("simulated_grid", "Énergie réseau après"),
    ("simulated_cost", "Coût après"),
    ("savings", "Économies annuelles"),
    ("autonomy", "Taux d'autonomie"),
    ("self_consumption", "Taux d'autoconsommation"),
    ("pv_generation", "Production PV"),
    ("ev_charge", "Recharge VE"),
    ("battery_charge", "Charge batterie"),
    ("battery_discharge", "Décharge batterie"),
    ("curtailed", "Surplus perdu"),
    ("payback", "Retour simple"),
)


class SimulationScenarioView(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setMinimumWidth(1140)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        layout.setSizeConstraint(QVBoxLayout.SizeConstraint.SetMinimumSize)

        self.panel = SimulationPanel()
        self.chart = SimulationChartView()
        self.panel.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.chart.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        layout.addWidget(self.panel)
        layout.addWidget(self.chart)
        self.setMinimumHeight(self.sizeHint().height())


class SimulationComparisonView(QWidget):
    def __init__(self, scenario_labels: Mapping[str, str]) -> None:
        super().__init__()
        self.setMinimumWidth(1220)
        self.scenario_labels = dict(scenario_labels)
        self.result_labels: dict[str, dict[str, QLabel]] = {}

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)
        layout.setSizeConstraint(QVBoxLayout.SizeConstraint.SetMinimumSize)

        summary_box = QGroupBox("Comparaison annuelle")
        summary_layout = QGridLayout(summary_box)
        summary_layout.setHorizontalSpacing(18)
        summary_layout.setVerticalSpacing(8)

        header = QLabel("Indicateur")
        header.setStyleSheet("font-weight: 600;")
        summary_layout.addWidget(header, 0, 0)
        for column_index, scenario_key in enumerate(self.scenario_labels, start=1):
            header_label = QLabel(self.scenario_labels[scenario_key])
            header_label.setStyleSheet("font-weight: 600;")
            summary_layout.addWidget(header_label, 0, column_index)

        for row_index, (metric_key, title) in enumerate(COMPARISON_RESULT_ROWS, start=1):
            title_label = QLabel(title)
            title_label.setStyleSheet(f"color: {TEXT_MUTED};")
            summary_layout.addWidget(title_label, row_index, 0)

            self.result_labels[metric_key] = {}
            for column_index, scenario_key in enumerate(self.scenario_labels, start=1):
                value_label = QLabel(EMPTY_VALUE)
                value_label.setStyleSheet("font-weight: 600;")
                value_label.setWordWrap(True)
                summary_layout.addWidget(value_label, row_index, column_index)
                self.result_labels[metric_key][scenario_key] = value_label

        self.chart = SimulationComparisonChartView(self.scenario_labels)
        self.chart.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.note_label = QLabel("La comparaison s'affichera après calcul des scénarios.")
        self.note_label.setWordWrap(True)
        self.note_label.setStyleSheet(f"color: {TEXT_MUTED};")

        layout.addWidget(summary_box)
        layout.addWidget(self.chart)
        layout.addWidget(self.note_label)
        self.setMinimumHeight(self.sizeHint().height())

    def update_summary(self, results: Mapping[str, SimulationResult | None]) -> None:
        for metric_key, labels_by_scenario in self.result_labels.items():
            for scenario_key, value_label in labels_by_scenario.items():
                result = results.get(scenario_key)
                value_label.setText(self._format_metric(metric_key, result) if result is not None else EMPTY_VALUE)

    def update_comparison(
        self,
        annualized_df,
        simulation_frames,
    ) -> None:
        self.chart.update_comparison(annualized_df, simulation_frames)

    def update_note(self, note: str) -> None:
        self.note_label.setText(note)

    @staticmethod
    def _format_metric(metric_key: str, result: SimulationResult) -> str:
        metric_map = {
            "simulated_grid": format_kwh(result.simulated_grid_kwh),
            "simulated_cost": format_currency(result.simulated_cost_eur),
            "savings": format_currency(result.annual_savings_eur),
            "autonomy": format_percent(result.autonomy_rate),
            "self_consumption": format_percent(result.self_consumption_rate),
            "pv_generation": format_kwh(result.pv_generated_kwh),
            "ev_charge": format_kwh(result.ev_charging_kwh),
            "battery_charge": format_kwh(result.battery_charge_kwh),
            "battery_discharge": format_kwh(result.battery_discharge_kwh),
            "curtailed": format_kwh(result.curtailed_pv_kwh),
            "payback": "Non calculé"
            if result.simple_payback_years is None
            else f"{fr_number(result.simple_payback_years, 1)} ans",
        }
        return metric_map[metric_key]
