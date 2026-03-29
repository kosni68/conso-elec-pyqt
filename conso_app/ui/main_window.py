from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication, QFileDialog, QFrame, QMainWindow, QMessageBox, QScrollArea, QTabWidget, QVBoxLayout, QWidget

from ..analysis import ConsumptionAnalyzer, ConsumptionAnnualizer, ConsumptionCsvLoader, PvBatterySimulator
from ..models import BatteryConfig, EvChargingConfig, SolarConfig, TariffConfig
from ..theme import apply_dark_theme
from .charts import OverviewChartView
from .controls import FileSelectionBar, FilterPanel, KpiPanel
from .formatting import format_kwh
from .simulation_views import SimulationComparisonView, SimulationScenarioView
from .state import ApplicationState, SIMULATION_SCENARIO_KEYS

SIMULATION_SCENARIO_TITLES = {
    "simulation_1": "Simulation 1",
    "simulation_2": "Simulation 2",
    "simulation_3": "Simulation 3",
}
LEGACY_SCENARIO_KEY = SIMULATION_SCENARIO_KEYS[0]


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
        self._last_applied_tariff_rate: float | None = None

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

    @property
    def simulation_results(self) -> dict[str, object]:
        return {
            scenario_key: self.state.simulation_states[scenario_key].result
            for scenario_key in SIMULATION_SCENARIO_KEYS
        }

    @property
    def simulation_frames(self) -> dict[str, object]:
        return {
            scenario_key: self.state.simulation_states[scenario_key].dataframe
            for scenario_key in SIMULATION_SCENARIO_KEYS
        }

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
        self.filter_panel.base_rate_changed.connect(self._sync_shared_base_rate)

        self.scenario_views = {
            scenario_key: SimulationScenarioView()
            for scenario_key in SIMULATION_SCENARIO_KEYS
        }
        for scenario_key, scenario_view in self.scenario_views.items():
            scenario_view.panel.run_requested.connect(lambda key=scenario_key: self.run_simulation(key))
            scenario_view.panel.base_rate_changed.connect(self._sync_shared_base_rate)
            scenario_view.chart.status_message_changed.connect(self.statusBar().showMessage)

        self.simulation_comparison_view = SimulationComparisonView(SIMULATION_SCENARIO_TITLES)
        self.simulation_comparison_view.chart.status_message_changed.connect(self.statusBar().showMessage)

        self.tabs = QTabWidget()
        self.overview_scroll_area = self._wrap_scrollable(self.overview_chart)
        self.simulation_subtabs = self._build_simulation_subtabs()
        self.simulation_tab_content = self.simulation_subtabs
        self.tabs.addTab(self.overview_scroll_area, "Vue globale")
        self.tabs.addTab(self.filter_panel, "Filtres")
        self.tabs.addTab(self.simulation_tab_content, "Simulation")

        root.addWidget(self.file_selection_bar)
        root.addWidget(self.kpi_panel)
        root.addWidget(self.tabs)

        self._sync_shared_base_rate(self.filter_panel.base_rate_spin.value())
        self.statusBar().showMessage("Sélectionnez un fichier CSV pour démarrer.")

    def _build_simulation_subtabs(self) -> QTabWidget:
        subtabs = QTabWidget()
        subtabs.setUsesScrollButtons(True)
        subtabs.tabBar().setElideMode(Qt.TextElideMode.ElideNone)
        self.scenario_scroll_areas: dict[str, QScrollArea] = {}
        for scenario_key in SIMULATION_SCENARIO_KEYS:
            scroll_area = self._wrap_scrollable(self.scenario_views[scenario_key])
            self.scenario_scroll_areas[scenario_key] = scroll_area
            subtabs.addTab(scroll_area, SIMULATION_SCENARIO_TITLES[scenario_key])
        self.comparison_scroll_area = self._wrap_scrollable(self.simulation_comparison_view)
        subtabs.addTab(self.comparison_scroll_area, "Comparaison")
        return subtabs

    def _wrap_scrollable(self, widget: QWidget) -> QScrollArea:
        scroll_area = QScrollArea()
        scroll_area.setWidget(widget)
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        return scroll_area

    def _expose_legacy_widget_aliases(self) -> None:
        simulation_view = self.scenario_views[LEGACY_SCENARIO_KEY]

        self.file_path_edit = self.file_selection_bar.file_path_edit
        self.kpi_labels = self.kpi_panel.value_labels
        self.start_date_edit = self.filter_panel.start_date_edit
        self.end_date_edit = self.filter_panel.end_date_edit
        self.day_start_edit = self.filter_panel.day_start_edit
        self.day_end_edit = self.filter_panel.day_end_edit
        self.base_rate_filter_spin = self.filter_panel.base_rate_spin
        self.filter_labels = self.filter_panel.summary_labels
        self.filter_note_label = self.filter_panel.note_label

        self.simulation_panel = simulation_view.panel
        self.simulation_chart = simulation_view.chart
        self.base_rate_sim_spin = simulation_view.panel.base_rate_spin
        self.pv_power_spin = simulation_view.panel.pv_power_spin
        self.pv_yield_spin = simulation_view.panel.pv_yield_spin
        self.pv_cost_spin = simulation_view.panel.pv_cost_spin
        self.battery_capacity_spin = simulation_view.panel.battery_capacity_spin
        self.charge_power_spin = simulation_view.panel.charge_power_spin
        self.discharge_power_spin = simulation_view.panel.discharge_power_spin
        self.efficiency_spin = simulation_view.panel.efficiency_spin
        self.min_soc_spin = simulation_view.panel.min_soc_spin
        self.battery_cost_spin = simulation_view.panel.battery_cost_spin
        self.ev_enabled_checkbox = simulation_view.panel.ev_enabled_checkbox
        self.ev_daily_energy_spin = simulation_view.panel.ev_daily_energy_spin
        self.ev_charge_power_spin = simulation_view.panel.ev_charge_power_spin
        self.ev_start_time_edit = simulation_view.panel.ev_start_time_edit
        self.ev_end_time_edit = simulation_view.panel.ev_end_time_edit
        self.ev_day_buttons = simulation_view.panel.ev_day_buttons
        self.simulation_labels = simulation_view.panel.result_labels
        self.simulation_note_label = simulation_view.panel.note_label
        self.simulation_canvas = simulation_view.chart.canvas
        self.simulation_toolbar = simulation_view.chart.toolbar

        self.overview_note_label = self.overview_chart.note_label
        self.overview_canvas = self.overview_chart.canvas
        self.overview_toolbar = self.overview_chart.toolbar

        self.simulation_panel_2 = self.scenario_views["simulation_2"].panel
        self.simulation_panel_3 = self.scenario_views["simulation_3"].panel
        self.simulation_chart_2 = self.scenario_views["simulation_2"].chart
        self.simulation_chart_3 = self.scenario_views["simulation_3"].chart
        self.simulation_scroll_area = self.scenario_scroll_areas[LEGACY_SCENARIO_KEY]
        self.simulation_scroll_area_2 = self.scenario_scroll_areas["simulation_2"]
        self.simulation_scroll_area_3 = self.scenario_scroll_areas["simulation_3"]
        self.simulation_labels_2 = self.scenario_views["simulation_2"].panel.result_labels
        self.simulation_labels_3 = self.scenario_views["simulation_3"].panel.result_labels
        self.simulation_note_label_2 = self.scenario_views["simulation_2"].panel.note_label
        self.simulation_note_label_3 = self.scenario_views["simulation_3"].panel.note_label
        self.comparison_view = self.simulation_comparison_view
        self.comparison_chart = self.simulation_comparison_view.chart
        self.comparison_labels = self.simulation_comparison_view.result_labels
        self.comparison_note_label = self.simulation_comparison_view.note_label

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

    def current_solar_config(self, scenario_key: str = LEGACY_SCENARIO_KEY) -> SolarConfig:
        return self.scenario_views[scenario_key].panel.current_solar_config()

    def current_battery_config(self, scenario_key: str = LEGACY_SCENARIO_KEY) -> BatteryConfig:
        return self.scenario_views[scenario_key].panel.current_battery_config()

    def current_ev_config(self, scenario_key: str = LEGACY_SCENARIO_KEY) -> EvChargingConfig:
        return self.scenario_views[scenario_key].panel.current_ev_config()

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
        self.run_all_simulations()

    def run_all_simulations(self) -> None:
        if self.raw_df is None:
            return

        try:
            annualized_df = self.annualizer.build_annualized_consumption(self.raw_df, self.current_tariff())
            simulation_payloads = {
                scenario_key: self._simulate_scenario(scenario_key, annualized_df)
                for scenario_key in SIMULATION_SCENARIO_KEYS
            }
        except Exception as exc:
            QMessageBox.critical(self, "Erreur de simulation", str(exc))
            return

        self.state.annualized_df = annualized_df
        for scenario_key, (simulation_result, simulation_df) in simulation_payloads.items():
            self._store_simulation_state(scenario_key, simulation_result, simulation_df)
            self._update_scenario_view(scenario_key)
        self._refresh_comparison_view()
        self._last_applied_tariff_rate = self.current_tariff().base_rate_eur_kwh

    def run_simulation(self, scenario_key: str = LEGACY_SCENARIO_KEY) -> None:
        if self.raw_df is None:
            return

        current_rate = self.current_tariff().base_rate_eur_kwh
        if self._last_applied_tariff_rate is None or abs(current_rate - self._last_applied_tariff_rate) > 1e-9:
            self.refresh_analysis()
            return

        try:
            annualized_df = self.annualizer.build_annualized_consumption(self.raw_df, self.current_tariff())
            simulation_result, simulation_df = self._simulate_scenario(scenario_key, annualized_df)
        except Exception as exc:
            QMessageBox.critical(self, f"Erreur de simulation - {SIMULATION_SCENARIO_TITLES[scenario_key]}", str(exc))
            return

        self.state.annualized_df = annualized_df
        self._store_simulation_state(scenario_key, simulation_result, simulation_df)
        self._update_scenario_view(scenario_key)
        self._refresh_comparison_view()
        self._last_applied_tariff_rate = current_rate

    def _simulate_scenario(self, scenario_key: str, annualized_df):
        return self.simulator.simulate(
            annualized_df,
            self.current_tariff(),
            self.current_solar_config(scenario_key),
            self.current_battery_config(scenario_key),
            ev_config=self.current_ev_config(scenario_key),
        )

    def _store_simulation_state(self, scenario_key: str, simulation_result, simulation_df) -> None:
        scenario_state = self.state.simulation_states[scenario_key]
        scenario_state.result = simulation_result
        scenario_state.dataframe = simulation_df
        if scenario_key == LEGACY_SCENARIO_KEY:
            self.state.simulation_result = simulation_result
            self.state.simulation_df = simulation_df

    def _update_scenario_view(self, scenario_key: str) -> None:
        scenario_state = self.state.simulation_states[scenario_key]
        scenario_view = self.scenario_views[scenario_key]
        if scenario_state.result is not None:
            scenario_view.panel.update_summary(scenario_state.result)
        scenario_view.chart.update_simulation(scenario_state.dataframe)
        scenario_view.panel.update_note(self._build_simulation_note(scenario_key))

    def _refresh_comparison_view(self) -> None:
        self.simulation_comparison_view.update_summary(self.simulation_results)
        self.simulation_comparison_view.update_comparison(self.annualized_df, self.simulation_frames)
        self.simulation_comparison_view.update_note(self._build_comparison_note())

    def _sync_shared_base_rate(self, value: float) -> None:
        self.filter_panel.set_base_rate(value)
        for scenario_view in self.scenario_views.values():
            scenario_view.panel.set_base_rate(value)

    def _build_simulation_note(self, scenario_key: str) -> str:
        if self.annualized_df is None or self.raw_df is None:
            return "La simulation s'affichera après chargement du CSV."

        coverage = self.annualizer.month_coverage(self.raw_df)
        first_period = self.annualized_df.index.min().strftime("%m/%Y")
        last_period = self.annualized_df.index.max().strftime("%m/%Y")
        counts = self.annualized_df["source_kind"].value_counts().to_dict()
        note = (
            f"{SIMULATION_SCENARIO_TITLES[scenario_key]} annualisée sur {first_period} → {last_period}. "
            f"Mois observés : {int(coverage['is_full'].sum())} complets, "
            f"compléments/interpolations : {counts.get('interpolated', 0)} pas interpolés et "
            f"{counts.get('filled_profile', 0) + counts.get('observed_template', 0)} pas reconstruits."
        )
        ev_config = self.current_ev_config(scenario_key)
        result = self.state.simulation_states[scenario_key].result
        if ev_config.enabled and result is not None:
            note += f" Recharge VE activee: {format_kwh(result.ev_charging_kwh)} / an, scenario avant/apres incluant le VE."
        return note

    def _build_comparison_note(self) -> str:
        if self.annualized_df is None:
            return "La comparaison s'affichera après calcul des scénarios."

        first_period = self.annualized_df.index.min().strftime("%m/%Y")
        last_period = self.annualized_df.index.max().strftime("%m/%Y")
        return (
            f"Comparaison de 3 scénarios techniques calculés sur la même période annualisée "
            f"({first_period} → {last_period}) et le même tarif base partagé."
        )
