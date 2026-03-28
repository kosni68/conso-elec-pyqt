from __future__ import annotations

from pathlib import Path
from typing import Optional

import numpy as np
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PyQt6.QtCore import QDate, QSignalBlocker, Qt, QTime
from PyQt6.QtWidgets import (
    QApplication,
    QDateEdit,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QTabWidget,
    QTimeEdit,
    QVBoxLayout,
    QWidget,
)

from .analysis import (
    AnalysisSummary,
    build_annualized_consumption,
    compute_analysis_summary,
    load_consumption_csv,
    month_coverage,
    simulate_pv_battery,
)
from .models import BatteryConfig, SimulationResult, SolarConfig, TariffConfig
from .theme import (
    ACCENT_BLUE,
    ACCENT_CYAN,
    ACCENT_GREEN,
    ACCENT_ORANGE,
    BORDER_COLOR,
    CARD_BACKGROUND,
    FILL_BLUE,
    PANEL_BACKGROUND,
    TEXT_MUTED,
    TEXT_PRIMARY,
    apply_dark_theme,
    style_axis,
    style_figure,
)


class MatplotlibCanvas(FigureCanvas):
    def __init__(self, height: float = 5.0) -> None:
        figure = Figure(figsize=(10, height), tight_layout=True)
        super().__init__(figure)
        self.figure = figure
        style_figure(self.figure)


class ConsumptionMainWindow(QMainWindow):
    def __init__(self, initial_csv_path: Optional[Path] = None) -> None:
        super().__init__()
        app = QApplication.instance()
        if app is not None:
            apply_dark_theme(app)
        self.raw_df = None
        self.analysis_summary: Optional[AnalysisSummary] = None
        self.annualized_df = None
        self.simulation_result: Optional[SimulationResult] = None
        self.simulation_df = None
        self.current_file_path: Optional[Path] = None

        self.setWindowTitle("Analyse de consommation électrique")
        self.resize(1480, 980)
        self._build_ui()

        if initial_csv_path is not None and Path(initial_csv_path).exists():
            self.load_file(Path(initial_csv_path))

    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(12)

        root.addWidget(self._build_file_bar())
        root.addLayout(self._build_kpi_row())
        self.tabs = QTabWidget()
        self.tabs.addTab(self._build_overview_tab(), "Vue globale")
        self.tabs.addTab(self._build_filters_tab(), "Filtres")
        self.tabs.addTab(self._build_simulation_tab(), "Simulation")
        root.addWidget(self.tabs)

        self.statusBar().showMessage("Sélectionne un fichier CSV pour démarrer.")

    def _build_file_bar(self) -> QWidget:
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        label = QLabel("Fichier CSV")
        label.setStyleSheet(f"font-weight: 600; color: {TEXT_PRIMARY};")
        self.file_path_edit = QLineEdit()
        self.file_path_edit.setPlaceholderText("Choisir un export CSV Linky ou équivalent")
        self.file_path_edit.returnPressed.connect(self.reload_current_file)

        browse_button = QPushButton("Parcourir…")
        browse_button.clicked.connect(self.browse_file)
        reload_button = QPushButton("Recharger")
        reload_button.clicked.connect(self.reload_current_file)

        layout.addWidget(label)
        layout.addWidget(self.file_path_edit, stretch=1)
        layout.addWidget(browse_button)
        layout.addWidget(reload_button)
        return container

    def _build_kpi_row(self) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setSpacing(10)
        self.kpi_labels: dict[str, QLabel] = {}
        cards = [
            ("total", "Consommation filtrée"),
            ("average", "Moyenne / jour"),
            ("cost", "Coût base estimé"),
            ("day", "Part jour"),
            ("night", "Part nuit"),
        ]
        for key, title in cards:
            frame = QFrame()
            frame.setFrameShape(QFrame.Shape.StyledPanel)
            frame.setStyleSheet(
                f"QFrame {{ background: {CARD_BACKGROUND}; border: 1px solid {BORDER_COLOR}; border-radius: 10px; }}"
            )
            frame_layout = QVBoxLayout(frame)
            frame_layout.setContentsMargins(14, 12, 14, 12)
            frame_layout.setSpacing(4)

            title_label = QLabel(title)
            title_label.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 12px;")
            value_label = QLabel("—")
            value_label.setStyleSheet(f"font-size: 22px; font-weight: 700; color: {TEXT_PRIMARY};")
            self.kpi_labels[key] = value_label

            frame_layout.addWidget(title_label)
            frame_layout.addWidget(value_label)
            row.addWidget(frame)
        return row

    def _build_overview_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        self.overview_note_label = QLabel("Les graphiques apparaîtront après chargement du CSV.")
        self.overview_note_label.setWordWrap(True)
        self.overview_note_label.setStyleSheet(f"color: {TEXT_MUTED};")
        self.overview_canvas = MatplotlibCanvas(height=8.5)
        layout.addWidget(self.overview_note_label)
        layout.addWidget(self.overview_canvas)
        return tab

    def _build_filters_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        controls_box = QGroupBox("Paramètres d'analyse")
        controls_layout = QGridLayout(controls_box)
        controls_layout.setHorizontalSpacing(14)
        controls_layout.setVerticalSpacing(10)

        self.start_date_edit = QDateEdit(calendarPopup=True)
        self.end_date_edit = QDateEdit(calendarPopup=True)
        self.start_date_edit.setDisplayFormat("dd/MM/yyyy")
        self.end_date_edit.setDisplayFormat("dd/MM/yyyy")
        self.day_start_edit = QTimeEdit(QTime(7, 0))
        self.day_end_edit = QTimeEdit(QTime(22, 0))
        self.day_start_edit.setDisplayFormat("HH:mm")
        self.day_end_edit.setDisplayFormat("HH:mm")
        self.base_rate_filter_spin = self._make_spinbox(0.0, 5.0, 4, 0.2516, suffix=" €/kWh")

        apply_button = QPushButton("Appliquer les filtres")
        apply_button.clicked.connect(self.refresh_analysis)
        reset_button = QPushButton("Réinitialiser")
        reset_button.clicked.connect(self.reset_filters)

        controls_layout.addWidget(QLabel("Date de début"), 0, 0)
        controls_layout.addWidget(self.start_date_edit, 0, 1)
        controls_layout.addWidget(QLabel("Date de fin"), 0, 2)
        controls_layout.addWidget(self.end_date_edit, 0, 3)
        controls_layout.addWidget(QLabel("Début jour"), 1, 0)
        controls_layout.addWidget(self.day_start_edit, 1, 1)
        controls_layout.addWidget(QLabel("Fin jour"), 1, 2)
        controls_layout.addWidget(self.day_end_edit, 1, 3)
        controls_layout.addWidget(QLabel("Tarif base"), 2, 0)
        controls_layout.addWidget(self.base_rate_filter_spin, 2, 1)
        controls_layout.addWidget(apply_button, 2, 2)
        controls_layout.addWidget(reset_button, 2, 3)

        summary_box = QGroupBox("Synthèse du filtre")
        summary_layout = QGridLayout(summary_box)
        summary_layout.setHorizontalSpacing(20)
        summary_layout.setVerticalSpacing(8)
        self.filter_labels: dict[str, QLabel] = {}
        info_rows = [
            ("range", "Période affichée"),
            ("days", "Nombre de jours"),
            ("intervals", "Pas de 30 min"),
            ("imputed", "Pas reconstitués"),
        ]
        for row_index, (key, title) in enumerate(info_rows):
            title_label = QLabel(title)
            title_label.setStyleSheet(f"color: {TEXT_MUTED};")
            value_label = QLabel("—")
            value_label.setStyleSheet("font-weight: 600;")
            self.filter_labels[key] = value_label
            summary_layout.addWidget(title_label, row_index, 0)
            summary_layout.addWidget(value_label, row_index, 1)

        self.filter_note_label = QLabel(
            "Le filtre jour/nuit est analytique: il découpe les consommations mais n'applique pas de tarif HP/HC."
        )
        self.filter_note_label.setWordWrap(True)
        self.filter_note_label.setStyleSheet(f"color: {TEXT_MUTED};")

        layout.addWidget(controls_box)
        layout.addWidget(summary_box)
        layout.addWidget(self.filter_note_label)
        layout.addStretch(1)
        return tab

    def _build_simulation_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        top_row = QHBoxLayout()
        top_row.setSpacing(12)

        controls_box = QGroupBox("Paramètres de simulation")
        controls_form = QFormLayout(controls_box)
        controls_form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)

        self.base_rate_sim_spin = self._make_spinbox(0.0, 5.0, 4, 0.2516, suffix=" €/kWh")
        self.pv_power_spin = self._make_spinbox(0.0, 30.0, 2, 6.0, suffix=" kWc")
        self.pv_yield_spin = self._make_spinbox(100.0, 2000.0, 0, 1200.0, suffix=" kWh/kWc/an")
        self.pv_cost_spin = self._make_optional_money_spinbox()
        self.battery_capacity_spin = self._make_spinbox(0.0, 100.0, 2, 5.0, suffix=" kWh")
        self.charge_power_spin = self._make_spinbox(0.0, 30.0, 2, 2.5, suffix=" kW")
        self.discharge_power_spin = self._make_spinbox(0.0, 30.0, 2, 2.5, suffix=" kW")
        self.efficiency_spin = self._make_spinbox(1.0, 100.0, 1, 90.0, suffix=" %")
        self.min_soc_spin = self._make_spinbox(0.0, 100.0, 1, 10.0, suffix=" %")
        self.battery_cost_spin = self._make_optional_money_spinbox()

        controls_form.addRow("Tarif base", self.base_rate_sim_spin)
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
        run_button.clicked.connect(self.run_simulation)
        controls_form.addRow(run_button)

        results_box = QGroupBox("Résultats annuels")
        results_layout = QGridLayout(results_box)
        results_layout.setHorizontalSpacing(18)
        results_layout.setVerticalSpacing(8)
        self.simulation_labels: dict[str, QLabel] = {}
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
            value_label = QLabel("—")
            value_label.setStyleSheet("font-weight: 600;")
            value_label.setWordWrap(True)
            self.simulation_labels[key] = value_label
            results_layout.addWidget(title_label, row_index, 0)
            results_layout.addWidget(value_label, row_index, 1)

        top_row.addWidget(controls_box, stretch=0)
        top_row.addWidget(results_box, stretch=1)

        self.simulation_note_label = QLabel("La simulation s'appuie sur une année annualisée après chargement du CSV.")
        self.simulation_note_label.setWordWrap(True)
        self.simulation_note_label.setStyleSheet(f"color: {TEXT_MUTED};")

        self.simulation_canvas = MatplotlibCanvas(height=4.5)
        self.simulation_canvas.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        layout.addLayout(top_row)
        layout.addWidget(self.simulation_note_label)
        layout.addWidget(self.simulation_canvas)

        self.base_rate_filter_spin.valueChanged.connect(self._sync_base_rate_from_filter)
        self.base_rate_sim_spin.valueChanged.connect(self._sync_base_rate_from_sim)
        return tab

    def _make_spinbox(
        self,
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

    def _sync_base_rate_from_filter(self, value: float) -> None:
        with QSignalBlocker(self.base_rate_sim_spin):
            self.base_rate_sim_spin.setValue(value)

    def _sync_base_rate_from_sim(self, value: float) -> None:
        with QSignalBlocker(self.base_rate_filter_spin):
            self.base_rate_filter_spin.setValue(value)

    def browse_file(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Choisir un fichier CSV",
            str(self.current_file_path.parent if self.current_file_path else Path.cwd()),
            "CSV (*.csv)",
        )
        if file_path:
            self.load_file(Path(file_path))

    def reload_current_file(self) -> None:
        path_text = self.file_path_edit.text().strip()
        if not path_text:
            return
        self.load_file(Path(path_text))

    def load_file(self, path: Path) -> None:
        try:
            df = load_consumption_csv(path, self.current_tariff())
        except Exception as exc:
            QMessageBox.critical(self, "Erreur de chargement", str(exc))
            return

        self.raw_df = df
        self.current_file_path = Path(path)
        self.file_path_edit.setText(str(path))
        self._set_date_bounds()
        self.refresh_analysis()
        self.statusBar().showMessage(f"Fichier chargé: {path.name}")

    def _set_date_bounds(self) -> None:
        if self.raw_df is None or self.raw_df.empty:
            return
        min_date = self.raw_df.index.min().date()
        max_date = self.raw_df.index.max().date()
        min_qdate = QDate(min_date.year, min_date.month, min_date.day)
        max_qdate = QDate(max_date.year, max_date.month, max_date.day)
        for widget in (self.start_date_edit, self.end_date_edit):
            widget.setDateRange(min_qdate, max_qdate)
        self.start_date_edit.setDate(min_qdate)
        self.end_date_edit.setDate(max_qdate)

    def reset_filters(self) -> None:
        if self.raw_df is None or self.raw_df.empty:
            return
        self._set_date_bounds()
        self.day_start_edit.setTime(QTime(7, 0))
        self.day_end_edit.setTime(QTime(22, 0))
        self.base_rate_filter_spin.setValue(0.2516)
        self.refresh_analysis()

    def current_tariff(self) -> TariffConfig:
        return TariffConfig(
            mode="base",
            base_rate_eur_kwh=self.base_rate_filter_spin.value(),
            day_start=self.day_start_edit.time().toPyTime(),
            day_end=self.day_end_edit.time().toPyTime(),
        )

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

    def refresh_analysis(self) -> None:
        if self.raw_df is None:
            return

        start_date = self.start_date_edit.date().toPyDate()
        end_date = self.end_date_edit.date().toPyDate()
        if start_date > end_date:
            QMessageBox.warning(self, "Dates invalides", "La date de début doit être antérieure à la date de fin.")
            return

        tariff = self.current_tariff()
        self.analysis_summary = compute_analysis_summary(
            self.raw_df,
            tariff,
            start_date=start_date,
            end_date=end_date,
        )
        self._update_kpis(self.analysis_summary)
        self._update_filter_summary(self.analysis_summary)
        self._update_overview_plot(self.analysis_summary)
        self.run_simulation()

    def run_simulation(self) -> None:
        if self.raw_df is None:
            return

        try:
            tariff = self.current_tariff()
            self.annualized_df = build_annualized_consumption(self.raw_df, tariff)
            self.simulation_result, self.simulation_df = simulate_pv_battery(
                self.annualized_df,
                tariff,
                self.current_solar_config(),
                self.current_battery_config(),
            )
        except Exception as exc:
            QMessageBox.critical(self, "Erreur de simulation", str(exc))
            return

        self._update_simulation_summary(self.simulation_result)
        self._update_simulation_plot()
        self._update_simulation_note()

    def _update_kpis(self, summary: AnalysisSummary) -> None:
        self.kpi_labels["total"].setText(self._format_kwh(summary.total_kwh))
        self.kpi_labels["average"].setText(self._format_kwh(summary.average_daily_kwh))
        self.kpi_labels["cost"].setText(self._format_currency(summary.cost_eur))
        self.kpi_labels["day"].setText(self._format_percent(summary.day_kwh / summary.total_kwh if summary.total_kwh else 0.0))
        self.kpi_labels["night"].setText(
            self._format_percent(summary.night_kwh / summary.total_kwh if summary.total_kwh else 0.0)
        )

    def _update_filter_summary(self, summary: AnalysisSummary) -> None:
        if summary.filtered_df.empty:
            for label in self.filter_labels.values():
                label.setText("—")
            return
        start = summary.filtered_df.index.min().strftime("%d/%m/%Y")
        end = summary.filtered_df.index.max().strftime("%d/%m/%Y")
        self.filter_labels["range"].setText(f"{start} → {end}")
        self.filter_labels["days"].setText(str(summary.daily_totals.shape[0]))
        self.filter_labels["intervals"].setText(str(summary.filtered_df.shape[0]))
        self.filter_labels["imputed"].setText(str(int(summary.filtered_df["is_imputed"].sum())))

    def _update_overview_plot(self, summary: AnalysisSummary) -> None:
        figure = self.overview_canvas.figure
        figure.clear()
        style_figure(figure)
        axes = figure.subplots(3, 1)

        if summary.filtered_df.empty:
            for axis in axes:
                axis.text(0.5, 0.5, "Aucune donnée sur cette plage.", ha="center", va="center")
                axis.set_axis_off()
            self.overview_canvas.draw_idle()
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

        self.overview_note_label.setText(
            "La vue globale utilise la plage filtrée. Le profil horaire correspond à une moyenne journalière par heure."
        )
        figure.align_labels()
        self.overview_canvas.draw_idle()

    def _update_simulation_summary(self, result: SimulationResult) -> None:
        self.simulation_labels["baseline_grid"].setText(self._format_kwh(result.baseline_grid_kwh))
        self.simulation_labels["simulated_grid"].setText(self._format_kwh(result.simulated_grid_kwh))
        self.simulation_labels["baseline_cost"].setText(self._format_currency(result.baseline_cost_eur))
        self.simulation_labels["simulated_cost"].setText(self._format_currency(result.simulated_cost_eur))
        self.simulation_labels["savings"].setText(self._format_currency(result.annual_savings_eur))
        self.simulation_labels["autonomy"].setText(self._format_percent(result.autonomy_rate))
        self.simulation_labels["self_consumption"].setText(self._format_percent(result.self_consumption_rate))
        self.simulation_labels["pv_generation"].setText(self._format_kwh(result.pv_generated_kwh))
        self.simulation_labels["battery_charge"].setText(self._format_kwh(result.battery_charge_kwh))
        self.simulation_labels["battery_discharge"].setText(self._format_kwh(result.battery_discharge_kwh))
        self.simulation_labels["curtailed"].setText(self._format_kwh(result.curtailed_pv_kwh))
        self.simulation_labels["payback"].setText(
            "Non calculé" if result.simple_payback_years is None else f"{self._fr_number(result.simple_payback_years, 1)} ans"
        )
        self.simulation_labels["baseline_daynight"].setText(
            f"Jour {self._format_kwh(result.baseline_day_kwh)} / Nuit {self._format_kwh(result.baseline_night_kwh)}"
        )
        self.simulation_labels["simulated_daynight"].setText(
            f"Jour {self._format_kwh(result.simulated_day_kwh)} / Nuit {self._format_kwh(result.simulated_night_kwh)}"
        )

    def _update_simulation_plot(self) -> None:
        figure = self.simulation_canvas.figure
        figure.clear()
        style_figure(figure)
        axis = figure.subplots(1, 1)

        if self.simulation_df is None or self.simulation_df.empty:
            axis.text(0.5, 0.5, "Simulation indisponible.", ha="center", va="center")
            axis.set_axis_off()
            self.simulation_canvas.draw_idle()
            return

        style_axis(axis)
        monthly = self.simulation_df.resample("MS").agg(
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
        self.simulation_canvas.draw_idle()

    def _update_simulation_note(self) -> None:
        if self.annualized_df is None:
            self.simulation_note_label.setText("La simulation s'affichera après chargement du CSV.")
            return
        coverage = month_coverage(self.raw_df)
        first_period = self.annualized_df.index.min().strftime("%m/%Y")
        last_period = self.annualized_df.index.max().strftime("%m/%Y")
        counts = self.annualized_df["source_kind"].value_counts().to_dict()
        note = (
            f"Simulation annualisée sur {first_period} → {last_period}. "
            f"Mois observés: {int(coverage['is_full'].sum())} complets, "
            f"compléments/interpolations: {counts.get('interpolated', 0)} pas interpolés et "
            f"{counts.get('filled_profile', 0) + counts.get('observed_template', 0)} pas reconstruits."
        )
        self.simulation_note_label.setText(note)

    @staticmethod
    def _fr_number(value: float, decimals: int = 2) -> str:
        formatted = f"{value:,.{decimals}f}"
        return formatted.replace(",", " ").replace(".", ",")

    @classmethod
    def _format_kwh(cls, value: float) -> str:
        return f"{cls._fr_number(value, 2)} kWh"

    @classmethod
    def _format_currency(cls, value: float) -> str:
        return f"{cls._fr_number(value, 2)} €"

    @classmethod
    def _format_percent(cls, value: float) -> str:
        return f"{cls._fr_number(value * 100.0, 1)} %"
