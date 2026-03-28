from __future__ import annotations

from pathlib import Path
from typing import Optional

import pandas as pd

from ._helpers import add_derived_columns, filter_consumption, parse_time_text
from .annualizer import ConsumptionAnnualizer
from .analyzer import ConsumptionAnalyzer
from .csv_loader import ConsumptionCsvLoader
from .simulation import PvBatterySimulator, build_pv_generation_series
from .types import AnalysisSummary
from ..models import BatteryConfig, SimulationResult, SolarConfig, TariffConfig

_DEFAULT_ANALYZER = ConsumptionAnalyzer()
_DEFAULT_LOADER = ConsumptionCsvLoader(analyzer=_DEFAULT_ANALYZER)
_DEFAULT_ANNUALIZER = ConsumptionAnnualizer(analyzer=_DEFAULT_ANALYZER)
_DEFAULT_SIMULATOR = PvBatterySimulator(analyzer=_DEFAULT_ANALYZER)


def load_consumption_csv(path: str | Path, tariff: Optional[TariffConfig] = None) -> pd.DataFrame:
    return _DEFAULT_LOADER.load(path, tariff)


def compute_analysis_summary(
    df: pd.DataFrame,
    tariff: TariffConfig,
    start_date=None,
    end_date=None,
) -> AnalysisSummary:
    return _DEFAULT_ANALYZER.compute_summary(df, tariff, start_date=start_date, end_date=end_date)


def month_coverage(df: pd.DataFrame) -> pd.DataFrame:
    return _DEFAULT_ANNUALIZER.month_coverage(df)


def build_annualized_consumption(
    df: pd.DataFrame,
    tariff: Optional[TariffConfig] = None,
) -> pd.DataFrame:
    return _DEFAULT_ANNUALIZER.build_annualized_consumption(df, tariff)


def simulate_pv_battery(
    annualized_df: pd.DataFrame,
    tariff: TariffConfig,
    solar_config: SolarConfig,
    battery_config: BatteryConfig,
) -> tuple[SimulationResult, pd.DataFrame]:
    return _DEFAULT_SIMULATOR.simulate(annualized_df, tariff, solar_config, battery_config)


__all__ = [
    "AnalysisSummary",
    "ConsumptionAnalyzer",
    "ConsumptionAnnualizer",
    "ConsumptionCsvLoader",
    "PvBatterySimulator",
    "add_derived_columns",
    "build_annualized_consumption",
    "build_pv_generation_series",
    "compute_analysis_summary",
    "filter_consumption",
    "load_consumption_csv",
    "month_coverage",
    "parse_time_text",
    "simulate_pv_battery",
]
