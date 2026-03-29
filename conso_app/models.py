from __future__ import annotations

from dataclasses import dataclass
from datetime import time
from typing import Optional

DEFAULT_BASE_RATE_EUR_KWH = 0.1927


@dataclass(frozen=True, slots=True)
class TariffConfig:
    mode: str = "base"
    base_rate_eur_kwh: float = DEFAULT_BASE_RATE_EUR_KWH
    day_start: time = time(7, 0)
    day_end: time = time(22, 0)


@dataclass(frozen=True, slots=True)
class SolarConfig:
    pv_kwc: float = 6.0
    specific_yield_kwh_per_kwc_year: float = 1200.0
    capex_eur: Optional[float] = None


@dataclass(frozen=True, slots=True)
class BatteryConfig:
    capacity_kwh: float = 5.0
    charge_power_kw: float = 2.5
    discharge_power_kw: float = 2.5
    roundtrip_efficiency: float = 0.90
    min_soc_pct: float = 10.0
    capex_eur: Optional[float] = None


@dataclass(frozen=True, slots=True)
class EvChargingConfig:
    enabled: bool = False
    daily_energy_kwh: float = 10.0
    charge_power_kw: float = 7.4
    start_time: time = time(22, 0)
    end_time: time = time(6, 0)
    active_weekdays: tuple[bool, bool, bool, bool, bool, bool, bool] = (True, True, True, True, True, True, True)


@dataclass(frozen=True, slots=True)
class SimulationResult:
    baseline_grid_kwh: float
    simulated_grid_kwh: float
    pv_generated_kwh: float
    pv_self_consumed_kwh: float
    battery_charge_kwh: float
    battery_discharge_kwh: float
    curtailed_pv_kwh: float
    baseline_day_kwh: float
    baseline_night_kwh: float
    simulated_day_kwh: float
    simulated_night_kwh: float
    baseline_cost_eur: float
    simulated_cost_eur: float
    annual_savings_eur: float
    self_consumption_rate: float
    autonomy_rate: float
    simple_payback_years: Optional[float]
    ev_charging_kwh: float = 0.0
