from __future__ import annotations

import calendar
import math
from dataclasses import dataclass
from datetime import date, time
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

from .models import BatteryConfig, SimulationResult, SolarConfig, TariffConfig

CSV_DELIMITER = ";"
CSV_DATE_FORMAT = "%d/%m/%Y %H:%M:%S"
HALF_HOUR_FREQUENCY = "30min"
INTERVAL_HOURS = 0.5
MONTHLY_PV_WEIGHTS = {
    1: 0.03,
    2: 0.05,
    3: 0.08,
    4: 0.11,
    5: 0.13,
    6: 0.14,
    7: 0.14,
    8: 0.12,
    9: 0.09,
    10: 0.06,
    11: 0.03,
    12: 0.02,
}
MONTHLY_SOLAR_WINDOWS = {
    1: ("08:00", "17:00"),
    2: ("07:30", "18:00"),
    3: ("07:00", "19:00"),
    4: ("06:30", "20:00"),
    5: ("06:00", "20:30"),
    6: ("05:30", "21:00"),
    7: ("06:00", "20:30"),
    8: ("06:30", "20:00"),
    9: ("07:00", "19:30"),
    10: ("07:30", "18:30"),
    11: ("08:00", "17:00"),
    12: ("08:30", "16:30"),
}


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


def parse_time_text(value: str) -> time:
    hour, minute = value.split(":")
    return time(int(hour), int(minute))


def _time_to_minutes(value: time) -> int:
    return (value.hour * 60) + value.minute


def _is_daytime(index: pd.DatetimeIndex, day_start: time, day_end: time) -> np.ndarray:
    minutes = (index.hour * 60) + index.minute
    start_minutes = _time_to_minutes(day_start)
    end_minutes = _time_to_minutes(day_end)
    if start_minutes == end_minutes:
        return np.ones(len(index), dtype=bool)
    if start_minutes < end_minutes:
        return (minutes >= start_minutes) & (minutes < end_minutes)
    return (minutes >= start_minutes) | (minutes < end_minutes)


def add_derived_columns(df: pd.DataFrame, tariff: Optional[TariffConfig] = None) -> pd.DataFrame:
    tariff = tariff or TariffConfig()
    out = df.copy()
    out.index = pd.DatetimeIndex(out.index)
    out.index.name = "timestamp"
    out["date"] = out.index.date
    out["month"] = out.index.month
    out["day"] = out.index.day
    out["hour"] = out.index.hour
    out["slot_30min"] = (out.index.hour * 2) + (out.index.minute // 30)
    out["is_day"] = _is_daytime(out.index, tariff.day_start, tariff.day_end)
    out["period_label"] = np.where(out["is_day"], "Jour", "Nuit")
    if "energy" not in out.columns:
        out["energy"] = "Électricité"
    if "is_imputed" not in out.columns:
        out["is_imputed"] = False
    if "source_kind" not in out.columns:
        out["source_kind"] = "observed"
    return out


def load_consumption_csv(path: str | Path, tariff: Optional[TariffConfig] = None) -> pd.DataFrame:
    raw = pd.read_csv(
        path,
        sep=CSV_DELIMITER,
        encoding="utf-8-sig",
        dtype=str,
    )
    required_columns = {"Énergie", "Date", "Consommation"}
    if not required_columns.issubset(set(raw.columns)):
        raise ValueError(f"Colonnes attendues introuvables: {required_columns}")

    frame = pd.DataFrame(
        {
            "energy": raw["Énergie"].fillna("Électricité").astype(str).str.strip(),
            "timestamp": pd.to_datetime(raw["Date"], format=CSV_DATE_FORMAT),
            "consumption_kwh": raw["Consommation"]
            .astype(str)
            .str.replace("kWh", "", regex=False)
            .str.replace('"', "", regex=False)
            .str.replace(" ", "", regex=False)
            .str.replace(",", ".", regex=False)
            .astype(float),
        }
    )
    frame = frame.sort_values("timestamp")
    grouped = frame.groupby("timestamp", as_index=True).agg(
        consumption_kwh=("consumption_kwh", "sum"),
        energy=("energy", "first"),
    )
    full_index = pd.date_range(
        start=grouped.index.min(),
        end=grouped.index.max(),
        freq=HALF_HOUR_FREQUENCY,
    )
    reindexed = grouped.reindex(full_index)
    is_imputed = reindexed["consumption_kwh"].isna()
    reindexed["consumption_kwh"] = reindexed["consumption_kwh"].fillna(0.0)
    reindexed["energy"] = reindexed["energy"].fillna("Électricité")
    reindexed["is_imputed"] = is_imputed
    return add_derived_columns(reindexed, tariff)


def filter_consumption(
    df: pd.DataFrame,
    tariff: TariffConfig,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
) -> pd.DataFrame:
    out = add_derived_columns(df, tariff)
    if start_date is not None:
        out = out[out.index >= pd.Timestamp(start_date)]
    if end_date is not None:
        out = out[out.index <= pd.Timestamp(end_date) + pd.Timedelta(hours=23, minutes=30)]
    return out


def compute_analysis_summary(
    df: pd.DataFrame,
    tariff: TariffConfig,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
) -> AnalysisSummary:
    filtered = filter_consumption(df, tariff, start_date=start_date, end_date=end_date)
    if filtered.empty:
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

    daily_totals = filtered["consumption_kwh"].resample("D").sum()
    monthly_totals = filtered["consumption_kwh"].resample("MS").sum()
    hourly_totals = filtered.groupby([filtered.index.normalize(), filtered.index.hour])["consumption_kwh"].sum()
    hourly_profile = hourly_totals.groupby(level=1).mean()
    hourly_profile.index.name = "hour"

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


def month_coverage(df: pd.DataFrame) -> pd.DataFrame:
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


def _interpolated_profiles(month_profiles: dict[int, pd.Series]) -> dict[int, pd.Series]:
    if 3 not in month_profiles or 6 not in month_profiles:
        raise ValueError("Les profils de mars et juin sont nécessaires pour interpoler avril et mai.")
    march = month_profiles[3]
    june = month_profiles[6]
    return {
        4: (march * (2.0 / 3.0)) + (june * (1.0 / 3.0)),
        5: (march * (1.0 / 3.0)) + (june * (2.0 / 3.0)),
    }


def build_annualized_consumption(
    df: pd.DataFrame,
    tariff: Optional[TariffConfig] = None,
) -> pd.DataFrame:
    tariff = tariff or TariffConfig()
    coverage = month_coverage(df)
    first_full = coverage.loc[coverage["is_full"]].head(1)
    start_period = first_full.iloc[0]["period"] if not first_full.empty else coverage.iloc[0]["period"]
    target_periods = [start_period + offset for offset in range(12)]

    month_profiles = {
        int(month): group.groupby("slot_30min")["consumption_kwh"].mean().reindex(range(48), fill_value=0.0)
        for month, group in df.groupby("month")
    }
    interpolated_profiles = _interpolated_profiles(month_profiles)
    template_lookup = (
        df.groupby(["month", "day", "slot_30min"])["consumption_kwh"]
        .mean()
        .sort_index()
    )
    exact_lookup = df["consumption_kwh"].sort_index()

    records: list[dict[str, object]] = []
    for period in target_periods:
        period_start = period.to_timestamp()
        days_in_month = period.days_in_month
        for day_number in range(1, days_in_month + 1):
            for slot in range(48):
                timestamp = period_start + pd.Timedelta(days=day_number - 1, minutes=slot * 30)
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
                records.append(
                    {
                        "timestamp": timestamp,
                        "consumption_kwh": consumption,
                        "energy": "Électricité",
                        "is_imputed": source_kind != "observed",
                        "source_kind": source_kind,
                    }
                )

    annualized = pd.DataFrame.from_records(records).set_index("timestamp")
    return add_derived_columns(annualized, tariff)


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


def build_pv_generation_series(index: pd.DatetimeIndex, solar_config: SolarConfig) -> pd.Series:
    annual_energy = max(0.0, solar_config.pv_kwc) * max(0.0, solar_config.specific_yield_kwh_per_kwc_year)
    pv_series = pd.Series(0.0, index=index, dtype=float)
    if annual_energy <= 0 or len(index) == 0:
        return pv_series

    profile_cache = {
        month: _build_daily_pv_shape(*MONTHLY_SOLAR_WINDOWS[month])
        for month in MONTHLY_SOLAR_WINDOWS
    }
    month_starts = sorted({ts.to_period("M") for ts in index})
    for period in month_starts:
        month_mask = index.to_period("M") == period
        month_index = index[month_mask]
        month_energy = annual_energy * MONTHLY_PV_WEIGHTS[period.month]
        unique_days = sorted({ts.normalize() for ts in month_index})
        if not unique_days:
            continue
        daily_energy = month_energy / len(unique_days)
        daily_shape = profile_cache[period.month]
        month_values = np.concatenate([daily_shape * daily_energy for _ in unique_days])
        pv_series.loc[month_index] = month_values
    return pv_series


def simulate_pv_battery(
    annualized_df: pd.DataFrame,
    tariff: TariffConfig,
    solar_config: SolarConfig,
    battery_config: BatteryConfig,
) -> tuple[SimulationResult, pd.DataFrame]:
    working = add_derived_columns(annualized_df, tariff)
    loads = working["consumption_kwh"].to_numpy(dtype=float)
    pv_generation = build_pv_generation_series(working.index, solar_config).to_numpy(dtype=float)
    is_day = working["is_day"].to_numpy(dtype=bool)

    capacity_kwh = max(0.0, battery_config.capacity_kwh)
    charge_power_kw = max(0.0, battery_config.charge_power_kw)
    discharge_power_kw = max(0.0, battery_config.discharge_power_kw)
    roundtrip_efficiency = min(max(battery_config.roundtrip_efficiency, 0.01), 1.0)
    charge_efficiency = math.sqrt(roundtrip_efficiency)
    discharge_efficiency = math.sqrt(roundtrip_efficiency)
    min_soc_kwh = min(capacity_kwh, max(0.0, battery_config.min_soc_pct / 100.0) * capacity_kwh)
    soc_kwh = min_soc_kwh

    grid_values = np.zeros_like(loads)
    direct_pv_values = np.zeros_like(loads)
    battery_charge_values = np.zeros_like(loads)
    battery_discharge_values = np.zeros_like(loads)
    curtailed_values = np.zeros_like(loads)
    soc_values = np.zeros_like(loads)

    for index, load in enumerate(loads):
        pv = pv_generation[index]
        direct_pv = min(load, pv)
        remaining_load = load - direct_pv
        surplus_pv = pv - direct_pv
        charged_from_pv = 0.0
        discharged_to_load = 0.0

        if capacity_kwh > 0 and surplus_pv > 0 and charge_power_kw > 0:
            max_charge_input = min(surplus_pv, charge_power_kw * INTERVAL_HOURS)
            remaining_storage = max(0.0, capacity_kwh - soc_kwh)
            if charge_efficiency > 0:
                max_charge_by_capacity = remaining_storage / charge_efficiency
                charged_from_pv = min(max_charge_input, max_charge_by_capacity)
            soc_kwh += charged_from_pv * charge_efficiency
            surplus_pv -= charged_from_pv

        if capacity_kwh > 0 and remaining_load > 0 and discharge_power_kw > 0:
            max_discharge_to_load = discharge_power_kw * INTERVAL_HOURS
            available_to_load = max(0.0, soc_kwh - min_soc_kwh) * discharge_efficiency
            discharged_to_load = min(remaining_load, max_discharge_to_load, available_to_load)
            if discharge_efficiency > 0:
                soc_kwh -= discharged_to_load / discharge_efficiency
            remaining_load -= discharged_to_load

        soc_kwh = min(capacity_kwh, max(min_soc_kwh, soc_kwh))
        direct_pv_values[index] = direct_pv
        battery_charge_values[index] = charged_from_pv
        battery_discharge_values[index] = discharged_to_load
        grid_values[index] = remaining_load
        curtailed_values[index] = surplus_pv
        soc_values[index] = soc_kwh

    baseline_grid_kwh = float(loads.sum())
    simulated_grid_kwh = float(grid_values.sum())
    pv_generated_kwh = float(pv_generation.sum())
    pv_self_consumed_kwh = float(direct_pv_values.sum() + battery_discharge_values.sum())
    battery_charge_kwh = float(battery_charge_values.sum())
    battery_discharge_kwh = float(battery_discharge_values.sum())
    curtailed_pv_kwh = float(curtailed_values.sum())
    baseline_day_kwh = float(loads[is_day].sum())
    baseline_night_kwh = float(loads[~is_day].sum())
    simulated_day_kwh = float(grid_values[is_day].sum())
    simulated_night_kwh = float(grid_values[~is_day].sum())
    baseline_cost_eur = baseline_grid_kwh * tariff.base_rate_eur_kwh
    simulated_cost_eur = simulated_grid_kwh * tariff.base_rate_eur_kwh
    annual_savings_eur = baseline_cost_eur - simulated_cost_eur
    self_consumption_rate = (pv_self_consumed_kwh / pv_generated_kwh) if pv_generated_kwh else 0.0
    autonomy_rate = (1.0 - (simulated_grid_kwh / baseline_grid_kwh)) if baseline_grid_kwh else 0.0

    total_capex = 0.0
    has_capex = False
    if solar_config.capex_eur is not None and solar_config.capex_eur > 0:
        total_capex += solar_config.capex_eur
        has_capex = True
    if battery_config.capex_eur is not None and battery_config.capex_eur > 0:
        total_capex += battery_config.capex_eur
        has_capex = True
    simple_payback_years = None
    if has_capex and annual_savings_eur > 0:
        simple_payback_years = total_capex / annual_savings_eur

    simulation_df = working.copy()
    simulation_df["pv_generation_kwh"] = pv_generation
    simulation_df["direct_pv_kwh"] = direct_pv_values
    simulation_df["battery_charge_kwh"] = battery_charge_values
    simulation_df["battery_discharge_kwh"] = battery_discharge_values
    simulation_df["grid_kwh"] = grid_values
    simulation_df["curtailed_pv_kwh"] = curtailed_values
    simulation_df["soc_kwh"] = soc_values

    result = SimulationResult(
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
    )
    return result, simulation_df
