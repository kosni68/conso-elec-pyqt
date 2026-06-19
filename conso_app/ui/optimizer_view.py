from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ..analysis import CRITERION_LABELS, CostModel, OptimizationResult, SearchSpace, SizingCandidate
from ..analysis.optimizer import CRITERION_AUTONOMY
from ..theme import ACCENT_GREEN, TEXT_MUTED
from .formatting import format_currency, format_kwh, format_percent, fr_number
from .input_widgets import NoWheelDoubleSpinBox

EMPTY_VALUE = "—"

# Ordre d'affichage des critères dans le sélecteur.
CRITERION_ORDER = (
    CRITERION_AUTONOMY,
    "payback",
    "savings",
    "net_gain",
)

RANKING_COLUMNS = (
    "PV (kWc)",
    "Batterie (kWh)",
    "Coût",
    "Autonomie",
    "Autoconso.",
    "Économies/an",
    "Retour",
    "Gain net",
)


class OptimizerView(QWidget):
    optimize_requested = pyqtSignal()
    apply_requested = pyqtSignal()

    def __init__(self) -> None:
        super().__init__()
        self.setMinimumWidth(1180)
        self._last_result: OptimizationResult | None = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)
        layout.setSizeConstraint(QVBoxLayout.SizeConstraint.SetMinimumSize)

        top_row = QHBoxLayout()
        top_row.setSpacing(12)
        top_row.addWidget(self._build_controls_box(), stretch=0)
        top_row.addWidget(self._build_result_box(), stretch=1)
        layout.addLayout(top_row)

        layout.addWidget(self._build_ranking_box())

        self.note_label = QLabel(
            "Le dimensionnement idéal est recherché par balayage de combinaisons PV/batterie "
            "sur l'année annualisée. Chargez un CSV puis lancez le calcul."
        )
        self.note_label.setWordWrap(True)
        self.note_label.setStyleSheet(f"color: {TEXT_MUTED};")
        layout.addWidget(self.note_label)

        self._on_criterion_changed()
        self.setMinimumHeight(self.sizeHint().height())

    # ------------------------------------------------------------------ build
    def _build_controls_box(self) -> QGroupBox:
        controls_box = QGroupBox("Critère et hypothèses")
        controls_box.setMinimumWidth(440)
        controls_layout = QVBoxLayout(controls_box)
        controls_layout.setSpacing(12)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)

        self.criterion_combo = QComboBox()
        for criterion_key in CRITERION_ORDER:
            self.criterion_combo.addItem(CRITERION_LABELS[criterion_key], criterion_key)
        self.criterion_combo.currentIndexChanged.connect(self._on_criterion_changed)

        self.autonomy_target_spin = self._make_spinbox(0.0, 100.0, 0, 100.0, suffix=" %")
        self.horizon_spin = self._make_spinbox(1.0, 40.0, 0, 20.0, suffix=" ans")
        self.pv_yield_spin = self._make_spinbox(100.0, 2000.0, 0, 1200.0, suffix=" kWh/kWc/an")

        self.pv_cost_spin = self._make_spinbox(0.0, 5000.0, 0, 833.0, suffix=" €/kWc")
        self.battery_cost_spin = self._make_spinbox(0.0, 2000.0, 0, 198.0, suffix=" €/kWh")
        self.fixed_cost_spin = self._make_spinbox(0.0, 50000.0, 0, 0.0, suffix=" €")

        self.pv_max_spin = self._make_spinbox(1.0, 40.0, 1, 18.0, suffix=" kWc")
        self.pv_step_spin = self._make_spinbox(0.5, 5.0, 1, 1.0, suffix=" kWc")
        self.battery_max_spin = self._make_spinbox(0.0, 60.0, 1, 24.0, suffix=" kWh")
        self.battery_step_spin = self._make_spinbox(0.5, 10.0, 1, 4.8, suffix=" kWh")

        form.addRow("Critère", self.criterion_combo)
        form.addRow("Objectif autonomie", self.autonomy_target_spin)
        form.addRow("Horizon", self.horizon_spin)
        form.addRow("Productible", self.pv_yield_spin)
        form.addRow("Coût PV", self.pv_cost_spin)
        form.addRow("Coût batterie", self.battery_cost_spin)
        form.addRow("Coût fixe", self.fixed_cost_spin)
        form.addRow("PV max", self.pv_max_spin)
        form.addRow("Pas PV", self.pv_step_spin)
        form.addRow("Batterie max", self.battery_max_spin)
        form.addRow("Pas batterie", self.battery_step_spin)
        controls_layout.addLayout(form)

        self.include_ev_checkbox = QCheckBox("Inclure la recharge VE (Simulation 1)")
        controls_layout.addWidget(self.include_ev_checkbox)

        self.run_button = QPushButton("Calculer l'installation idéale")
        self.run_button.clicked.connect(self.optimize_requested.emit)
        controls_layout.addWidget(self.run_button)

        return controls_box

    def _build_result_box(self) -> QGroupBox:
        result_box = QGroupBox("Installation recommandée")
        result_box.setMinimumWidth(560)
        grid = QGridLayout(result_box)
        grid.setHorizontalSpacing(18)
        grid.setVerticalSpacing(8)

        self.result_labels: dict[str, QLabel] = {}
        rows = [
            ("pv_power", "Puissance PV"),
            ("battery_capacity", "Capacité batterie"),
            ("capex", "Coût total estimé"),
            ("capex_breakdown", "Détail PV / batterie"),
            ("autonomy", "Taux d'autonomie"),
            ("self_consumption", "Taux d'autoconsommation"),
            ("savings", "Économies annuelles"),
            ("payback", "Retour simple"),
            ("net_gain", "Gain net (horizon)"),
            ("pv_generation", "Production PV"),
            ("curtailed", "Surplus perdu"),
        ]
        for row_index, (key, title) in enumerate(rows):
            title_label = QLabel(title)
            title_label.setStyleSheet(f"color: {TEXT_MUTED};")
            value_label = QLabel(EMPTY_VALUE)
            value_label.setWordWrap(True)
            if key in ("pv_power", "battery_capacity", "capex"):
                value_label.setStyleSheet(f"font-weight: 700; color: {ACCENT_GREEN};")
            else:
                value_label.setStyleSheet("font-weight: 600;")
            self.result_labels[key] = value_label
            grid.addWidget(title_label, row_index, 0)
            grid.addWidget(value_label, row_index, 1)

        self.apply_button = QPushButton("Appliquer à Simulation 1")
        self.apply_button.setEnabled(False)
        self.apply_button.clicked.connect(self.apply_requested.emit)
        grid.addWidget(self.apply_button, len(rows), 0, 1, 2)

        return result_box

    def _build_ranking_box(self) -> QGroupBox:
        ranking_box = QGroupBox("Meilleures combinaisons")
        ranking_layout = QVBoxLayout(ranking_box)
        self.ranking_table = QTableWidget(0, len(RANKING_COLUMNS))
        self.ranking_table.setHorizontalHeaderLabels(RANKING_COLUMNS)
        self.ranking_table.verticalHeader().setVisible(False)
        self.ranking_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.ranking_table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.ranking_table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.ranking_table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.ranking_table.setMinimumHeight(240)
        header = self.ranking_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        ranking_layout.addWidget(self.ranking_table)
        return ranking_box

    # ------------------------------------------------------------- accessors
    def current_criterion(self) -> str:
        return self.criterion_combo.currentData()

    def current_cost_model(self) -> CostModel:
        return CostModel(
            pv_cost_per_kwc=self.pv_cost_spin.value(),
            battery_cost_per_kwh=self.battery_cost_spin.value(),
            fixed_cost_eur=self.fixed_cost_spin.value(),
        )

    def current_search_space(self) -> SearchSpace:
        return SearchSpace(
            pv_max_kwc=self.pv_max_spin.value(),
            pv_step_kwc=self.pv_step_spin.value(),
            battery_max_kwh=self.battery_max_spin.value(),
            battery_step_kwh=self.battery_step_spin.value(),
        )

    def current_autonomy_target(self) -> float:
        return self.autonomy_target_spin.value() / 100.0

    def current_horizon_years(self) -> int:
        return int(round(self.horizon_spin.value()))

    def current_specific_yield(self) -> float:
        return self.pv_yield_spin.value()

    def include_ev(self) -> bool:
        return self.include_ev_checkbox.isChecked()

    def best_candidate(self) -> SizingCandidate | None:
        return self._last_result.best if self._last_result is not None else None

    # ---------------------------------------------------------------- render
    def display_result(self, result: OptimizationResult) -> None:
        self._last_result = result
        best = result.best
        horizon = result.horizon_years

        self.result_labels["pv_power"].setText(f"{fr_number(best.pv_kwc, 1)} kWc")
        self.result_labels["battery_capacity"].setText(format_kwh(best.capacity_kwh))
        self.result_labels["capex"].setText(format_currency(best.capex_eur))
        self.result_labels["capex_breakdown"].setText(
            f"PV {format_currency(best.pv_capex_eur)} / Batterie {format_currency(best.battery_capex_eur)}"
        )
        self.result_labels["autonomy"].setText(format_percent(best.autonomy_rate))
        self.result_labels["self_consumption"].setText(format_percent(best.self_consumption_rate))
        self.result_labels["savings"].setText(format_currency(best.annual_savings_eur))
        self.result_labels["payback"].setText(self._format_payback(best.payback_years))
        self.result_labels["net_gain"].setText(f"{format_currency(best.net_gain_eur)} sur {horizon} ans")
        self.result_labels["pv_generation"].setText(format_kwh(best.pv_generated_kwh))
        self.result_labels["curtailed"].setText(format_kwh(best.curtailed_pv_kwh))

        self._fill_ranking_table(result)
        self.apply_button.setEnabled(True)

    def update_note(self, note: str) -> None:
        self.note_label.setText(note)

    def _fill_ranking_table(self, result: OptimizationResult) -> None:
        headers = list(RANKING_COLUMNS)
        headers[-1] = f"Gain {result.horizon_years} ans"
        self.ranking_table.setHorizontalHeaderLabels(headers)

        self.ranking_table.setRowCount(len(result.ranking))
        for row_index, candidate in enumerate(result.ranking):
            cells = (
                fr_number(candidate.pv_kwc, 1),
                fr_number(candidate.capacity_kwh, 1),
                format_currency(candidate.capex_eur),
                format_percent(candidate.autonomy_rate),
                format_percent(candidate.self_consumption_rate),
                format_currency(candidate.annual_savings_eur),
                self._format_payback(candidate.payback_years),
                format_currency(candidate.net_gain_eur),
            )
            for column_index, text in enumerate(cells):
                item = QTableWidgetItem(text)
                item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                if row_index == 0:
                    font = item.font()
                    font.setBold(True)
                    item.setFont(font)
                self.ranking_table.setItem(row_index, column_index, item)

    def _on_criterion_changed(self) -> None:
        self.autonomy_target_spin.setEnabled(self.current_criterion() == CRITERION_AUTONOMY)

    @staticmethod
    def _format_payback(payback_years: float | None) -> str:
        if payback_years is None:
            return "Non rentable"
        return f"{fr_number(payback_years, 1)} ans"

    @staticmethod
    def _make_spinbox(
        minimum: float,
        maximum: float,
        decimals: int,
        value: float,
        suffix: str = "",
    ) -> NoWheelDoubleSpinBox:
        widget = NoWheelDoubleSpinBox()
        widget.setRange(minimum, maximum)
        widget.setDecimals(decimals)
        widget.setValue(value)
        widget.setSuffix(suffix)
        widget.setAlignment(Qt.AlignmentFlag.AlignRight)
        widget.setSingleStep(0.1 if decimals else 1.0)
        return widget
