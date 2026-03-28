from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication, QFileDialog, QFrame, QMainWindow, QMessageBox, QScrollArea, QTabWidget, QVBoxLayout, QWidget

from ..analysis import ConsumptionAnalyzer, ConsumptionAnnualizer, ConsumptionCsvLoader, PvBatterySimulator
from ..models import BatteryConfig, SolarConfig, TariffConfig
from ..theme import apply_dark_theme
from .charts import OverviewChartView, SimulationChartView
from .controls import FileSelectionBar, FilterPanel, KpiPanel
from .simulation_panel import SimulationPanel
from .state import ApplicationState


class ConsumptionMainWindow(QMainWindow):
    def __init__(self, initial_csv_path: Path | None = None) -> None:
        super().__init__()
        app = QApplication.instance()
        if app is not None:
            apply_dark_theme(app)

        self.state = ApplicationState()
        self.analyzer = ConsumptionAnalyzer()
        self.loader = ConsumptionCsvLoader(analyzer=self.analyzer)
        self.annualizer = ConsumptionAnnualizer(analyzer=self.analyzer)
        self.simulator = PvBatterySimulator(analyzer=self.analyzer)

        self.setWindowTitle("Analyse de consommation électrique")
        self.resize(1480, 980)
        self._build_ui()
        self._expose_legacy_widget_aliases()

        if initial_csv_path is not None and Path(initial_csv_path).exists():
            self.load_file(Path(initial_csv_path))

    @property
    def raw_df(self):
        return self.state.raw_df

    @property
    def analysis_summary(self):
        return self.state.analysis_summary

    @property
    def annualized_df(self):
        return self.state.annualized_df

    @property
    def simulation_result(self):
        return self.state.simulation_result

    @property
    def simulation_df(self):
        return self.state.simulation_df

    @property
    def current_file_path(self):
        return self.state.current_file_path

    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(12)

        self.file_selection_bar = FileSelectionBar()
        self.file_selection_bar.browse_requested.connect(self.browse_file)
        self.file_selection_bar.reload_requested.connect(self.reload_current_file)

        self.kpi_panel = KpiPanel()
        self.overview_chart = OverviewChartView()
        self.overview_chart.status_message_changed.connect(self.statusBar().showMessage)
        self.filter_panel = FilterPanel()
        self.filter_panel.apply_requested.connect(self.refresh_analysis)
        self.filter_panel.reset_requested.connect(self.reset_filters)

        self.simulation_panel = SimulationPanel()
        self.simulation_panel.run_requested.connect(self.run_simulation)
        self.simulation_chart = SimulationChartView()
        self.simulation_chart.status_message_changed.connect(self.statusBar().showMessage)

        self.filter_panel.base_rate_changed.connect(self.simulation_panel.set_base_rate)
        self.simulation_panel.base_rate_changed.connect(self.filter_panel.set_base_rate)

        self.tabs = QTabWidget()
        self.overview_scroll_area = self._wrap_scrollable(self.overview_chart)
        self.simulation_tab_content = self._build_simulation_tab()
        self.simulation_scroll_area = self._wrap_scrollable(self.simulation_tab_content)
        self.tabs.addTab(self.overview_scroll_area, "Vue globale")
        self.tabs.addTab(self.filter_panel, "Filtres")
        self.tabs.addTab(self.simulation_scroll_area, "Simulation")

        root.addWidget(self.file_selection_bar)
        root.addWidget(self.kpi_panel)
        root.addWidget(self.tabs)

        self.statusBar().showMessage("Sélectionnez un fichier CSV pour démarrer.")

    def _build_simulation_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        layout.addWidget(self.simulation_panel)
        layout.addWidget(self.simulation_chart)
        return tab

    def _wrap_scrollable(self, widget: QWidget) -> QScrollArea:
        scroll_area = QScrollArea()
        scroll_area.setWidget(widget)
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        return scroll_area

    def _expose_legacy_widget_aliases(self) -> None:
        self.file_path_edit = self.file_selection_bar.file_path_edit
        self.kpi_labels = self.kpi_panel.value_labels
        self.start_date_edit = self.filter_panel.start_date_edit
        self.end_date_edit = self.filter_panel.end_date_edit
        self.day_start_edit = self.filter_panel.day_start_edit
        self.day_end_edit = self.filter_panel.day_end_edit
        self.base_rate_filter_spin = self.filter_panel.base_rate_spin
        self.filter_labels = self.filter_panel.summary_labels
        self.filter_note_label = self.filter_panel.note_label
        self.base_rate_sim_spin = self.simulation_panel.base_rate_spin
        self.pv_power_spin = self.simulation_panel.pv_power_spin
        self.pv_yield_spin = self.simulation_panel.pv_yield_spin
        self.pv_cost_spin = self.simulation_panel.pv_cost_spin
        self.battery_capacity_spin = self.simulation_panel.battery_capacity_spin
        self.charge_power_spin = self.simulation_panel.charge_power_spin
        self.discharge_power_spin = self.simulation_panel.discharge_power_spin
        self.efficiency_spin = self.simulation_panel.efficiency_spin
        self.min_soc_spin = self.simulation_panel.min_soc_spin
        self.battery_cost_spin = self.simulation_panel.battery_cost_spin
        self.simulation_labels = self.simulation_panel.result_labels
        self.simulation_note_label = self.simulation_panel.note_label
        self.overview_note_label = self.overview_chart.note_label
        self.overview_canvas = self.overview_chart.canvas
        self.simulation_canvas = self.simulation_chart.canvas
        self.overview_toolbar = self.overview_chart.toolbar
        self.simulation_toolbar = self.simulation_chart.toolbar

    def browse_file(self) -> None:
        start_directory = self.current_file_path.parent if self.current_file_path else Path.cwd()
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Choisir un fichier CSV",
            str(start_directory),
            "CSV (*.csv)",
        )
        if file_path:
            self.load_file(Path(file_path))

    def reload_current_file(self, path_text: str | None = None) -> None:
        path_text = path_text or self.file_selection_bar.current_path_text()
        if not path_text:
            return
        self.load_file(Path(path_text))

    def load_file(self, path: Path) -> None:
        try:
            raw_df = self.loader.load(path, self.current_tariff())
        except Exception as exc:
            QMessageBox.critical(self, "Erreur de chargement", str(exc))
            return

        self.state.raw_df = raw_df
        self.state.current_file_path = Path(path)
        self.file_selection_bar.set_file_path(path)
        self._set_date_bounds(reset_selection=True)
        self.refresh_analysis()
        self.statusBar().showMessage(f"Fichier chargé : {path.name}")

    def _set_date_bounds(self, *, reset_selection: bool) -> None:
        if self.raw_df is None or self.raw_df.empty:
            return
        min_date = self.raw_df.index.min().date()
        max_date = self.raw_df.index.max().date()
        self.filter_panel.set_date_bounds(min_date, max_date, reset_selection=reset_selection)

    def reset_filters(self) -> None:
        if self.raw_df is None or self.raw_df.empty:
            return
        min_date = self.raw_df.index.min().date()
        max_date = self.raw_df.index.max().date()
        self.filter_panel.reset_controls(min_date, max_date)
        self.refresh_analysis()

    def current_tariff(self) -> TariffConfig:
        return self.filter_panel.current_tariff()

    def current_solar_config(self) -> SolarConfig:
        return self.simulation_panel.current_solar_config()

    def current_battery_config(self) -> BatteryConfig:
        return self.simulation_panel.current_battery_config()

    def refresh_analysis(self) -> None:
        if self.raw_df is None:
            return

        start_date, end_date = self.filter_panel.selected_dates()
        if start_date > end_date:
            QMessageBox.warning(self, "Dates invalides", "La date de début doit être antérieure à la date de fin.")
            return

        summary = self.analyzer.compute_summary(
            self.raw_df,
            self.current_tariff(),
            start_date=start_date,
            end_date=end_date,
        )
        self.state.analysis_summary = summary
        self.kpi_panel.update_summary(summary)
        self.filter_panel.update_summary(summary)
        self.overview_chart.update_summary(summary)
        self.run_simulation()

    def run_simulation(self) -> None:
        if self.raw_df is None:
            return

        try:
            annualized_df = self.annualizer.build_annualized_consumption(self.raw_df, self.current_tariff())
            simulation_result, simulation_df = self.simulator.simulate(
                annualized_df,
                self.current_tariff(),
                self.current_solar_config(),
                self.current_battery_config(),
            )
        except Exception as exc:
            QMessageBox.critical(self, "Erreur de simulation", str(exc))
            return

        self.state.annualized_df = annualized_df
        self.state.simulation_result = simulation_result
        self.state.simulation_df = simulation_df
        self.simulation_panel.update_summary(simulation_result)
        self.simulation_chart.update_simulation(simulation_df)
        self.simulation_panel.update_note(self._build_simulation_note())

    def _build_simulation_note(self) -> str:
        if self.annualized_df is None or self.raw_df is None:
            return "La simulation s'affichera après chargement du CSV."

        coverage = self.annualizer.month_coverage(self.raw_df)
        first_period = self.annualized_df.index.min().strftime("%m/%Y")
        last_period = self.annualized_df.index.max().strftime("%m/%Y")
        counts = self.annualized_df["source_kind"].value_counts().to_dict()
        return (
            f"Simulation annualisée sur {first_period} → {last_period}. "
            f"Mois observés : {int(coverage['is_full'].sum())} complets, "
            f"compléments/interpolations : {counts.get('interpolated', 0)} pas interpolés et "
            f"{counts.get('filled_profile', 0) + counts.get('observed_template', 0)} pas reconstruits."
        )
