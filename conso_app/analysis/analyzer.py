from __future__ import annotations

from datetime import date
from typing import Optional

import pandas as pd

from ..models import TariffConfig
from ._helpers import add_derived_columns, filter_consumption
from .types import AnalysisSummary


class ConsumptionAnalyzer:
    def add_derived_columns(self, df: pd.DataFrame, tariff: Optional[TariffConfig] = None) -> pd.DataFrame:
        return add_derived_columns(df, tariff)

    def filter_consumption(
        self,
        df: pd.DataFrame,
        tariff: TariffConfig,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> pd.DataFrame:
        return filter_consumption(df, tariff, start_date=start_date, end_date=end_date)

    def compute_summary(
        self,
        df: pd.DataFrame,
        tariff: TariffConfig,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> AnalysisSummary:
        filtered = self.filter_consumption(df, tariff, start_date=start_date, end_date=end_date)
        if filtered.empty:
            return self._empty_summary(filtered)

        daily_totals = filtered["consumption_kwh"].resample("D").sum()
        monthly_totals = filtered["consumption_kwh"].resample("MS").sum()
        hourly_profile = self._build_hourly_profile(filtered)

        total_kwh = float(filtered["consumption_kwh"].sum())
        day_kwh = float(filtered.loc[filtered["is_day"], "consumption_kwh"].sum())
        night_kwh = float(filtered.loc[~filtered["is_day"], "consumption_kwh"].sum())
        average_daily_kwh = float(daily_totals.mean()) if not daily_totals.empty else 0.0
        cost_eur = total_kwh * tariff.base_rate_eur_kwh

        return AnalysisSummary(
            filtered_df=filtered,
            daily_totals=daily_totals,
            monthly_totals=monthly_totals,
            hourly_profile=hourly_profile,
            total_kwh=total_kwh,
            average_daily_kwh=average_daily_kwh,
            day_kwh=day_kwh,
            night_kwh=night_kwh,
            cost_eur=cost_eur,
        )

    @staticmethod
    def _build_hourly_profile(filtered: pd.DataFrame) -> pd.Series:
        hourly_totals = filtered.groupby([filtered.index.normalize(), filtered.index.hour])["consumption_kwh"].sum()
        hourly_profile = hourly_totals.groupby(level=1).mean()
        hourly_profile.index.name = "hour"
        return hourly_profile

    @staticmethod
    def _empty_summary(filtered: pd.DataFrame) -> AnalysisSummary:
        empty_series = pd.Series(dtype=float)
        return AnalysisSummary(
            filtered_df=filtered,
            daily_totals=empty_series,
            monthly_totals=empty_series,
            hourly_profile=empty_series,
            total_kwh=0.0,
            average_daily_kwh=0.0,
            day_kwh=0.0,
            night_kwh=0.0,
            cost_eur=0.0,
        )
