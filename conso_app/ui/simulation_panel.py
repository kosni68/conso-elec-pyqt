from __future__ import annotations

from PyQt6.QtCore import QSignalBlocker, Qt, pyqtSignal
from PyQt6.QtWidgets import QDoubleSpinBox, QFormLayout, QGridLayout, QGroupBox, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from ..models import BatteryConfig, SolarConfig, DEFAULT_BASE_RATE_EUR_KWH
from ..theme import TEXT_MUTED
from .formatting import format_currency, format_kwh, format_percent, fr_number

EMPTY_VALUE = "—"


class SimulationPanel(QWidget):
    run_requested = pyqtSignal()
    base_rate_changed = pyqtSignal(float)

    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        top_row = QHBoxLayout()
        top_row.setSpacing(12)

        controls_box = QGroupBox("Paramètres de simulation")
        controls_form = QFormLayout(controls_box)
        controls_form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)

        self.base_rate_spin = self._make_spinbox(0.0, 5.0, 4, DEFAULT_BASE_RATE_EUR_KWH, suffix=" €/kWh")
        self.base_rate_spin.valueChanged.connect(self.base_rate_changed.emit)
        self.pv_power_spin = self._make_spinbox(0.0, 30.0, 2, 6.0, suffix=" kWc")
        self.pv_yield_spin = self._make_spinbox(100.0, 2000.0, 0, 1200.0, suffix=" kWh/kWc/an")
        self.pv_cost_spin = self._make_optional_money_spinbox()
        self.battery_capacity_spin = self._make_spinbox(0.0, 100.0, 2, 5.0, suffix=" kWh")
        self.charge_power_spin = self._make_spinbox(0.0, 30.0, 2, 2.5, suffix=" kW")
        self.discharge_power_spin = self._make_spinbox(0.0, 30.0, 2, 2.5, suffix=" kW")
        self.efficiency_spin = self._make_spinbox(1.0, 100.0, 1, 90.0, suffix=" %")
        self.min_soc_spin = self._make_spinbox(0.0, 100.0, 1, 10.0, suffix=" %")
        self.battery_cost_spin = self._make_optional_money_spinbox()

        controls_form.addRow("Tarif base", self.base_rate_spin)
        controls_form.addRow("Puissance PV", self.pv_power_spin)
        controls_form.addRow("Productible", self.pv_yield_spin)
        controls_form.addRow("Coût PV", self.pv_cost_spin)
        controls_form.addRow("Capacité batterie", self.battery_capacity_spin)
        controls_form.addRow("Puissance charge", self.charge_power_spin)
        controls_form.addRow("Puissance décharge", self.discharge_power_spin)
        controls_form.addRow("Rendement A/R", self.efficiency_spin)
        controls_form.addRow("SOC mini", self.min_soc_spin)
        controls_form.addRow("Coût batterie", self.battery_cost_spin)

        run_button = QPushButton("Recalculer la simulation")
        run_button.clicked.connect(self.run_requested.emit)
        controls_form.addRow(run_button)

        results_box = QGroupBox("Résultats annuels")
        results_layout = QGridLayout(results_box)
        results_layout.setHorizontalSpacing(18)
        results_layout.setVerticalSpacing(8)

        self.result_labels: dict[str, QLabel] = {}
        result_rows = [
            ("baseline_grid", "Énergie réseau avant"),
            ("simulated_grid", "Énergie réseau après"),
            ("baseline_cost", "Coût avant"),
            ("simulated_cost", "Coût après"),
            ("savings", "Économies annuelles"),
            ("autonomy", "Taux d'autonomie"),
            ("self_consumption", "Taux d'autoconsommation"),
            ("pv_generation", "Production PV"),
            ("battery_charge", "Charge batterie"),
            ("battery_discharge", "Décharge batterie"),
            ("curtailed", "Surplus perdu"),
            ("payback", "Retour simple"),
            ("baseline_daynight", "Jour / nuit avant"),
            ("simulated_daynight", "Jour / nuit après"),
        ]
        for row_index, (key, title) in enumerate(result_rows):
            title_label = QLabel(title)
            title_label.setStyleSheet(f"color: {TEXT_MUTED};")
            value_label = QLabel(EMPTY_VALUE)
            value_label.setStyleSheet("font-weight: 600;")
            value_label.setWordWrap(True)
            self.result_labels[key] = value_label
            results_layout.addWidget(title_label, row_index, 0)
            results_layout.addWidget(value_label, row_index, 1)

        top_row.addWidget(controls_box, stretch=0)
        top_row.addWidget(results_box, stretch=1)

        self.note_label = QLabel("La simulation s'appuie sur une année annualisée après chargement du CSV.")
        self.note_label.setWordWrap(True)
        self.note_label.setStyleSheet(f"color: {TEXT_MUTED};")

        layout.addLayout(top_row)
        layout.addWidget(self.note_label)

    def current_solar_config(self) -> SolarConfig:
        pv_cost = self.pv_cost_spin.value()
        return SolarConfig(
            pv_kwc=self.pv_power_spin.value(),
            specific_yield_kwh_per_kwc_year=self.pv_yield_spin.value(),
            capex_eur=pv_cost if pv_cost > 0 else None,
        )

    def current_battery_config(self) -> BatteryConfig:
        battery_cost = self.battery_cost_spin.value()
        return BatteryConfig(
            capacity_kwh=self.battery_capacity_spin.value(),
            charge_power_kw=self.charge_power_spin.value(),
            discharge_power_kw=self.discharge_power_spin.value(),
            roundtrip_efficiency=self.efficiency_spin.value() / 100.0,
            min_soc_pct=self.min_soc_spin.value(),
            capex_eur=battery_cost if battery_cost > 0 else None,
        )

    def set_base_rate(self, value: float) -> None:
        with QSignalBlocker(self.base_rate_spin):
            self.base_rate_spin.setValue(value)

    def update_summary(self, result) -> None:
        self.result_labels["baseline_grid"].setText(format_kwh(result.baseline_grid_kwh))
        self.result_labels["simulated_grid"].setText(format_kwh(result.simulated_grid_kwh))
        self.result_labels["baseline_cost"].setText(format_currency(result.baseline_cost_eur))
        self.result_labels["simulated_cost"].setText(format_currency(result.simulated_cost_eur))
        self.result_labels["savings"].setText(format_currency(result.annual_savings_eur))
        self.result_labels["autonomy"].setText(format_percent(result.autonomy_rate))
        self.result_labels["self_consumption"].setText(format_percent(result.self_consumption_rate))
        self.result_labels["pv_generation"].setText(format_kwh(result.pv_generated_kwh))
        self.result_labels["battery_charge"].setText(format_kwh(result.battery_charge_kwh))
        self.result_labels["battery_discharge"].setText(format_kwh(result.battery_discharge_kwh))
        self.result_labels["curtailed"].setText(format_kwh(result.curtailed_pv_kwh))
        self.result_labels["payback"].setText(
            "Non calculé" if result.simple_payback_years is None else f"{fr_number(result.simple_payback_years, 1)} ans"
        )
        self.result_labels["baseline_daynight"].setText(
            f"Jour {format_kwh(result.baseline_day_kwh)} / Nuit {format_kwh(result.baseline_night_kwh)}"
        )
        self.result_labels["simulated_daynight"].setText(
            f"Jour {format_kwh(result.simulated_day_kwh)} / Nuit {format_kwh(result.simulated_night_kwh)}"
        )

    def update_note(self, note: str) -> None:
        self.note_label.setText(note)

    @staticmethod
    def _make_spinbox(
        minimum: float,
        maximum: float,
        decimals: int,
        value: float,
        suffix: str = "",
    ) -> QDoubleSpinBox:
        widget = QDoubleSpinBox()
        widget.setRange(minimum, maximum)
        widget.setDecimals(decimals)
        widget.setValue(value)
        widget.setSuffix(suffix)
        widget.setAlignment(Qt.AlignmentFlag.AlignRight)
        widget.setSingleStep(0.1 if decimals else 1.0)
        return widget

    def _make_optional_money_spinbox(self) -> QDoubleSpinBox:
        widget = self._make_spinbox(0.0, 100000.0, 0, 0.0, suffix=" €")
        widget.setSpecialValueText("Non renseigné")
        return widget
