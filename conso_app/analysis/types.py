from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(slots=True)
class AnalysisSummary:
    filtered_df: pd.DataFrame
    daily_totals: pd.Series
    monthly_totals: pd.Series
    hourly_profile: pd.Series
    total_kwh: float
    average_daily_kwh: float
    day_kwh: float
    night_kwh: float
    cost_eur: float
