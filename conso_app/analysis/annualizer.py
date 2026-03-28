from __future__ import annotations

import pandas as pd

from ..models import TariffConfig
from ._constants import DEFAULT_ENERGY_NAME, HALF_HOUR_SLOTS_PER_DAY
from .analyzer import ConsumptionAnalyzer


class ConsumptionAnnualizer:
    def __init__(self, analyzer: ConsumptionAnalyzer | None = None) -> None:
        self.analyzer = analyzer or ConsumptionAnalyzer()

    def month_coverage(self, df: pd.DataFrame) -> pd.DataFrame:
        rows = []
        for period, group in df.groupby(df.index.to_period("M")):
            observed_days = int(group.index.normalize().nunique())
            rows.append(
                {
                    "period": period,
                    "year": period.year,
                    "month": period.month,
                    "observed_days": observed_days,
                    "days_in_month": period.days_in_month,
                    "is_full": observed_days == period.days_in_month,
                }
            )
        coverage = pd.DataFrame(rows)
        if coverage.empty:
            raise ValueError("Aucune donnée de consommation à annualiser.")
        return coverage.sort_values("period").reset_index(drop=True)

    def build_annualized_consumption(
        self,
        df: pd.DataFrame,
        tariff: TariffConfig | None = None,
    ) -> pd.DataFrame:
        tariff = tariff or TariffConfig()
        coverage = self.month_coverage(df)
        start_period = self._pick_start_period(coverage)
        target_periods = [start_period + offset for offset in range(12)]

        month_profiles = self._build_month_profiles(df)
        self._ensure_profiles_for_target_months(month_profiles, target_periods)
        interpolated_profiles = self._build_interpolated_profiles(month_profiles)
        template_lookup = (
            df.groupby(["month", "day", "slot_30min"])["consumption_kwh"]
            .mean()
            .sort_index()
        )
        exact_lookup = df["consumption_kwh"].sort_index()

        records: list[dict[str, object]] = []
        for period in target_periods:
            period_start = period.to_timestamp()
            for day_number in range(1, period.days_in_month + 1):
                for slot in range(HALF_HOUR_SLOTS_PER_DAY):
                    timestamp = period_start + pd.Timedelta(days=day_number - 1, minutes=slot * 30)
                    records.append(
                        self._build_record(
                            timestamp=timestamp,
                            day_number=day_number,
                            slot=slot,
                            period=period,
                            exact_lookup=exact_lookup,
                            interpolated_profiles=interpolated_profiles,
                            month_profiles=month_profiles,
                            template_lookup=template_lookup,
                        )
                    )

        annualized = pd.DataFrame.from_records(records).set_index("timestamp")
        return self.analyzer.add_derived_columns(annualized, tariff)

    @staticmethod
    def _pick_start_period(coverage: pd.DataFrame):
        first_full = coverage.loc[coverage["is_full"]].head(1)
        return first_full.iloc[0]["period"] if not first_full.empty else coverage.iloc[0]["period"]

    @staticmethod
    def _build_month_profiles(df: pd.DataFrame) -> dict[int, pd.Series]:
        return {
            int(month): group.groupby("slot_30min")["consumption_kwh"].mean().reindex(range(HALF_HOUR_SLOTS_PER_DAY), fill_value=0.0)
            for month, group in df.groupby("month")
        }

    @staticmethod
    def _ensure_profiles_for_target_months(month_profiles: dict[int, pd.Series], target_periods) -> None:
        target_months = {period.month for period in target_periods}
        missing_months = sorted(month for month in target_months if month not in month_profiles and month not in {4, 5})
        if missing_months:
            missing_text = ", ".join(str(month) for month in missing_months)
            raise ValueError(f"Impossible d'annualiser sans profil pour les mois: {missing_text}.")

    @staticmethod
    def _build_interpolated_profiles(month_profiles: dict[int, pd.Series]) -> dict[int, pd.Series]:
        if 3 not in month_profiles or 6 not in month_profiles:
            return {}
        march = month_profiles[3]
        june = month_profiles[6]
        return {
            4: (march * (2.0 / 3.0)) + (june * (1.0 / 3.0)),
            5: (march * (1.0 / 3.0)) + (june * (2.0 / 3.0)),
        }

    @staticmethod
    def _build_record(
        *,
        timestamp: pd.Timestamp,
        day_number: int,
        slot: int,
        period,
        exact_lookup: pd.Series,
        interpolated_profiles: dict[int, pd.Series],
        month_profiles: dict[int, pd.Series],
        template_lookup: pd.Series,
    ) -> dict[str, object]:
        if timestamp in exact_lookup.index:
            consumption = float(exact_lookup.loc[timestamp])
            source_kind = "observed"
        elif period.month in interpolated_profiles:
            consumption = float(interpolated_profiles[period.month].loc[slot])
            source_kind = "interpolated"
        elif (period.month, day_number, slot) in template_lookup.index:
            consumption = float(template_lookup.loc[(period.month, day_number, slot)])
            source_kind = "observed_template"
        else:
            consumption = float(month_profiles[period.month].loc[slot])
            source_kind = "filled_profile"

        return {
            "timestamp": timestamp,
            "consumption_kwh": consumption,
            "energy": DEFAULT_ENERGY_NAME,
            "is_imputed": source_kind != "observed",
            "source_kind": source_kind,
        }
