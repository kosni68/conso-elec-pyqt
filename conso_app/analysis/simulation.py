from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
import pandas as pd

from ..models import BatteryConfig, EvChargingConfig, SimulationResult, SolarConfig, TariffConfig
from ._constants import INTERVAL_HOURS, MONTHLY_PV_WEIGHTS, MONTHLY_SOLAR_WINDOWS
from ._helpers import parse_time_text
from .analyzer import ConsumptionAnalyzer


@dataclass(frozen=True, slots=True)
class BatteryRuntimeConfig:
    capacity_kwh: float
    charge_input_limit_kwh: float
    discharge_output_limit_kwh: float
    charge_efficiency: float
    discharge_efficiency: float
    min_soc_kwh: float

    @classmethod
    def from_config(cls, battery_config: BatteryConfig) -> "BatteryRuntimeConfig":
        capacity_kwh = max(0.0, battery_config.capacity_kwh)
        roundtrip_efficiency = min(max(battery_config.roundtrip_efficiency, 0.01), 1.0)
        charge_efficiency = math.sqrt(roundtrip_efficiency)
        discharge_efficiency = math.sqrt(roundtrip_efficiency)
        return cls(
            capacity_kwh=capacity_kwh,
            charge_input_limit_kwh=max(0.0, battery_config.charge_power_kw) * INTERVAL_HOURS,
            discharge_output_limit_kwh=max(0.0, battery_config.discharge_power_kw) * INTERVAL_HOURS,
            charge_efficiency=charge_efficiency,
            discharge_efficiency=discharge_efficiency,
            min_soc_kwh=min(capacity_kwh, max(0.0, battery_config.min_soc_pct / 100.0) * capacity_kwh),
        )


@dataclass(frozen=True, slots=True)
class IntervalSimulation:
    direct_pv_kwh: float
    battery_charge_kwh: float
    battery_discharge_kwh: float
    grid_kwh: float
    curtailed_pv_kwh: float
    soc_kwh: float


class PvBatterySimulator:
    def __init__(self, analyzer: ConsumptionAnalyzer | None = None) -> None:
        self.analyzer = analyzer or ConsumptionAnalyzer()

    def build_pv_generation_series(self, index: pd.DatetimeIndex, solar_config: SolarConfig) -> pd.Series:
        annual_energy = max(0.0, solar_config.pv_kwc) * max(0.0, solar_config.specific_yield_kwh_per_kwc_year)
        pv_series = pd.Series(0.0, index=index, dtype=float)
        if annual_energy <= 0 or len(index) == 0:
            return pv_series

        profile_cache = {
            month: self._build_daily_pv_shape(*MONTHLY_SOLAR_WINDOWS[month])
            for month in MONTHLY_SOLAR_WINDOWS
        }
        for period in sorted({timestamp.to_period("M") for timestamp in index}):
            month_mask = index.to_period("M") == period
            month_index = index[month_mask]
            month_energy = annual_energy * MONTHLY_PV_WEIGHTS[period.month]
            unique_days = sorted({timestamp.normalize() for timestamp in month_index})
            if not unique_days:
                continue
            daily_energy = month_energy / len(unique_days)
            daily_shape = profile_cache[period.month]
            month_values = np.concatenate([daily_shape * daily_energy for _ in unique_days])
            pv_series.loc[month_index] = month_values
        return pv_series

    def simulate(
        self,
        annualized_df: pd.DataFrame,
        tariff: TariffConfig,
        solar_config: SolarConfig,
        battery_config: BatteryConfig,
        ev_config: EvChargingConfig | None = None,
    ) -> tuple[SimulationResult, pd.DataFrame]:
        working = self.analyzer.add_derived_columns(annualized_df, tariff)
        working["home_consumption_kwh"] = working["consumption_kwh"].to_numpy(dtype=float)
        ev_charging = self.build_ev_charging_series(working.index, ev_config)
        working["ev_charging_kwh"] = ev_charging.to_numpy(dtype=float)
        working["consumption_kwh"] = working["home_consumption_kwh"] + working["ev_charging_kwh"]
        loads = working["consumption_kwh"].to_numpy(dtype=float)
        pv_generation = self.build_pv_generation_series(working.index, solar_config).to_numpy(dtype=float)
        is_day = working["is_day"].to_numpy(dtype=bool)
        battery_runtime = BatteryRuntimeConfig.from_config(battery_config)

        soc_kwh = battery_runtime.min_soc_kwh
        interval_results: list[IntervalSimulation] = []
        for load_kwh, pv_kwh in zip(loads, pv_generation, strict=False):
            interval = self._simulate_interval(load_kwh, pv_kwh, soc_kwh, battery_runtime)
            interval_results.append(interval)
            soc_kwh = interval.soc_kwh

        arrays = self._interval_results_to_arrays(interval_results)
        result = self._build_result_summary(
            loads=loads,
            pv_generation=pv_generation,
            is_day=is_day,
            tariff=tariff,
            solar_config=solar_config,
            battery_config=battery_config,
            arrays=arrays,
            ev_charging=ev_charging.to_numpy(dtype=float),
        )
        simulation_df = self._build_simulation_dataframe(working, pv_generation, arrays)
        return result, simulation_df

    def build_ev_charging_series(
        self,
        index: pd.DatetimeIndex,
        ev_config: EvChargingConfig | None,
    ) -> pd.Series:
        series = pd.Series(0.0, index=index, dtype=float)
        if len(index) == 0 or ev_config is None or not ev_config.enabled:
            return series

        self._validate_ev_config(ev_config)
        step_energy_kwh = ev_config.charge_power_kw * INTERVAL_HOURS
        period_duration = (index[-1] + pd.Timedelta(minutes=30)) - index[0]

        for day in sorted(pd.Timestamp(value) for value in pd.Index(index.normalize()).unique()):
            if not ev_config.active_weekdays[day.dayofweek]:
                continue

            session_start = pd.Timestamp.combine(day.date(), ev_config.start_time)
            session_end = pd.Timestamp.combine(day.date(), ev_config.end_time)
            if session_end <= session_start:
                session_end += pd.Timedelta(days=1)

            session_slots = pd.date_range(session_start, session_end, freq="30min", inclusive="left")
            remaining_energy = ev_config.daily_energy_kwh
            if len(session_slots) == 0:
                continue

            for slot in session_slots:
                target_slot = slot
                if target_slot > index[-1]:
                    target_slot -= period_duration
                delivered = min(step_energy_kwh, remaining_energy)
                series.loc[target_slot] += delivered
                remaining_energy -= delivered
                if remaining_energy <= 1e-9:
                    break

            if remaining_energy > 1e-9:
                raise ValueError("La recharge VE demandée dépasse la capacité de la fenêtre sélectionnée.")

        return series

    @staticmethod
    def _validate_ev_config(ev_config: EvChargingConfig) -> None:
        if ev_config.daily_energy_kwh <= 0:
            raise ValueError("L'énergie VE journalière doit être supérieure à 0 kWh.")
        if ev_config.charge_power_kw <= 0:
            raise ValueError("La puissance de charge VE doit être supérieure à 0 kW.")
        if len(ev_config.active_weekdays) != 7:
            raise ValueError("La recharge VE doit définir 7 jours d'activation.")
        if not any(ev_config.active_weekdays):
            raise ValueError("Sélectionnez au moins un jour actif pour la recharge VE.")
        if ev_config.start_time == ev_config.end_time:
            raise ValueError("Les heures de début et de fin de recharge VE doivent être différentes.")

        session_start = pd.Timestamp.combine(pd.Timestamp("2026-01-01").date(), ev_config.start_time)
        session_end = pd.Timestamp.combine(pd.Timestamp("2026-01-01").date(), ev_config.end_time)
        if session_end <= session_start:
            session_end += pd.Timedelta(days=1)
        slot_count = len(pd.date_range(session_start, session_end, freq="30min", inclusive="left"))
        if slot_count == 0:
            raise ValueError("La fenêtre de recharge VE ne contient aucun créneau exploitable.")
        max_deliverable_kwh = slot_count * ev_config.charge_power_kw * INTERVAL_HOURS
        if ev_config.daily_energy_kwh - max_deliverable_kwh > 1e-9:
            raise ValueError("La fenêtre de recharge VE est trop courte pour délivrer l'énergie quotidienne demandée.")

    @staticmethod
    def _build_daily_pv_shape(start_text: str, end_text: str) -> np.ndarray:
        start_time = parse_time_text(start_text)
        end_time = parse_time_text(end_text)
        start_hour = start_time.hour + (start_time.minute / 60.0)
        end_hour = end_time.hour + (end_time.minute / 60.0)
        slot_centers = (np.arange(48) * 0.5) + 0.25
        shape = np.zeros(48, dtype=float)
        if end_hour <= start_hour:
            return shape
        mask = (slot_centers >= start_hour) & (slot_centers <= end_hour)
        fractions = (slot_centers[mask] - start_hour) / (end_hour - start_hour)
        shape[mask] = np.sin(np.pi * fractions)
        total = shape.sum()
        if total > 0:
            shape /= total
        return shape

    @staticmethod
    def _simulate_interval(
        load_kwh: float,
        pv_kwh: float,
        soc_kwh: float,
        runtime: BatteryRuntimeConfig,
    ) -> IntervalSimulation:
        direct_pv_kwh = min(load_kwh, pv_kwh)
        remaining_load = load_kwh - direct_pv_kwh
        surplus_pv = pv_kwh - direct_pv_kwh
        battery_charge_kwh = 0.0
        battery_discharge_kwh = 0.0

        if runtime.capacity_kwh > 0 and surplus_pv > 0 and runtime.charge_input_limit_kwh > 0:
            max_charge_input = min(surplus_pv, runtime.charge_input_limit_kwh)
            remaining_storage = max(0.0, runtime.capacity_kwh - soc_kwh)
            max_charge_by_capacity = remaining_storage / runtime.charge_efficiency
            battery_charge_kwh = min(max_charge_input, max_charge_by_capacity)
            soc_kwh += battery_charge_kwh * runtime.charge_efficiency
            surplus_pv -= battery_charge_kwh

        if runtime.capacity_kwh > 0 and remaining_load > 0 and runtime.discharge_output_limit_kwh > 0:
            available_to_load = max(0.0, soc_kwh - runtime.min_soc_kwh) * runtime.discharge_efficiency
            battery_discharge_kwh = min(remaining_load, runtime.discharge_output_limit_kwh, available_to_load)
            soc_kwh -= battery_discharge_kwh / runtime.discharge_efficiency
            remaining_load -= battery_discharge_kwh

        soc_kwh = min(runtime.capacity_kwh, max(runtime.min_soc_kwh, soc_kwh))
        return IntervalSimulation(
            direct_pv_kwh=direct_pv_kwh,
            battery_charge_kwh=battery_charge_kwh,
            battery_discharge_kwh=battery_discharge_kwh,
            grid_kwh=remaining_load,
            curtailed_pv_kwh=surplus_pv,
            soc_kwh=soc_kwh,
        )

    @staticmethod
    def _interval_results_to_arrays(interval_results: list[IntervalSimulation]) -> dict[str, np.ndarray]:
        return {
            "direct_pv_kwh": np.array([item.direct_pv_kwh for item in interval_results], dtype=float),
            "battery_charge_kwh": np.array([item.battery_charge_kwh for item in interval_results], dtype=float),
            "battery_discharge_kwh": np.array([item.battery_discharge_kwh for item in interval_results], dtype=float),
            "grid_kwh": np.array([item.grid_kwh for item in interval_results], dtype=float),
            "curtailed_pv_kwh": np.array([item.curtailed_pv_kwh for item in interval_results], dtype=float),
            "soc_kwh": np.array([item.soc_kwh for item in interval_results], dtype=float),
        }

    @staticmethod
    def _build_result_summary(
        *,
        loads: np.ndarray,
        pv_generation: np.ndarray,
        is_day: np.ndarray,
        tariff: TariffConfig,
        solar_config: SolarConfig,
        battery_config: BatteryConfig,
        arrays: dict[str, np.ndarray],
        ev_charging: np.ndarray,
    ) -> SimulationResult:
        baseline_grid_kwh = float(loads.sum())
        simulated_grid_kwh = float(arrays["grid_kwh"].sum())
        pv_generated_kwh = float(pv_generation.sum())
        pv_self_consumed_kwh = float(arrays["direct_pv_kwh"].sum() + arrays["battery_discharge_kwh"].sum())
        battery_charge_kwh = float(arrays["battery_charge_kwh"].sum())
        battery_discharge_kwh = float(arrays["battery_discharge_kwh"].sum())
        curtailed_pv_kwh = float(arrays["curtailed_pv_kwh"].sum())
        baseline_day_kwh = float(loads[is_day].sum())
        baseline_night_kwh = float(loads[~is_day].sum())
        simulated_day_kwh = float(arrays["grid_kwh"][is_day].sum())
        simulated_night_kwh = float(arrays["grid_kwh"][~is_day].sum())
        baseline_cost_eur = baseline_grid_kwh * tariff.base_rate_eur_kwh
        simulated_cost_eur = simulated_grid_kwh * tariff.base_rate_eur_kwh
        annual_savings_eur = baseline_cost_eur - simulated_cost_eur
        self_consumption_rate = (pv_self_consumed_kwh / pv_generated_kwh) if pv_generated_kwh else 0.0
        autonomy_rate = (1.0 - (simulated_grid_kwh / baseline_grid_kwh)) if baseline_grid_kwh else 0.0
        simple_payback_years = PvBatterySimulator._compute_payback_years(
            solar_config=solar_config,
            battery_config=battery_config,
            annual_savings_eur=annual_savings_eur,
        )

        return SimulationResult(
            baseline_grid_kwh=baseline_grid_kwh,
            simulated_grid_kwh=simulated_grid_kwh,
            pv_generated_kwh=pv_generated_kwh,
            pv_self_consumed_kwh=pv_self_consumed_kwh,
            battery_charge_kwh=battery_charge_kwh,
            battery_discharge_kwh=battery_discharge_kwh,
            curtailed_pv_kwh=curtailed_pv_kwh,
            baseline_day_kwh=baseline_day_kwh,
            baseline_night_kwh=baseline_night_kwh,
            simulated_day_kwh=simulated_day_kwh,
            simulated_night_kwh=simulated_night_kwh,
            baseline_cost_eur=baseline_cost_eur,
            simulated_cost_eur=simulated_cost_eur,
            annual_savings_eur=annual_savings_eur,
            self_consumption_rate=self_consumption_rate,
            autonomy_rate=autonomy_rate,
            simple_payback_years=simple_payback_years,
            ev_charging_kwh=float(ev_charging.sum()),
        )

    @staticmethod
    def _compute_payback_years(
        *,
        solar_config: SolarConfig,
        battery_config: BatteryConfig,
        annual_savings_eur: float,
    ) -> float | None:
        total_capex = 0.0
        has_capex = False
        if solar_config.capex_eur is not None and solar_config.capex_eur > 0:
            total_capex += solar_config.capex_eur
            has_capex = True
        if battery_config.capex_eur is not None and battery_config.capex_eur > 0:
            total_capex += battery_config.capex_eur
            has_capex = True
        if not has_capex or annual_savings_eur <= 0:
            return None
        return total_capex / annual_savings_eur

    @staticmethod
    def _build_simulation_dataframe(
        working: pd.DataFrame,
        pv_generation: np.ndarray,
        arrays: dict[str, np.ndarray],
    ) -> pd.DataFrame:
        simulation_df = working.copy()
        simulation_df["pv_generation_kwh"] = pv_generation
        simulation_df["direct_pv_kwh"] = arrays["direct_pv_kwh"]
        simulation_df["battery_charge_kwh"] = arrays["battery_charge_kwh"]
        simulation_df["battery_discharge_kwh"] = arrays["battery_discharge_kwh"]
        simulation_df["grid_kwh"] = arrays["grid_kwh"]
        simulation_df["curtailed_pv_kwh"] = arrays["curtailed_pv_kwh"]
        simulation_df["soc_kwh"] = arrays["soc_kwh"]
        return simulation_df


def build_pv_generation_series(index: pd.DatetimeIndex, solar_config: SolarConfig) -> pd.Series:
    return PvBatterySimulator().build_pv_generation_series(index, solar_config)
