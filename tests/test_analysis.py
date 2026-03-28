from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from conso_app.analysis import (
    build_annualized_consumption,
    compute_analysis_summary,
    load_consumption_csv,
    simulate_pv_battery,
)
from conso_app.models import BatteryConfig, SolarConfig, TariffConfig


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REAL_CSV_PATH = PROJECT_ROOT / "112486686-DUBOIS-NICOLAS heure.csv"


@pytest.fixture()
def sample_csv_path(tmp_path: Path) -> Path:
    csv_content = "\n".join(
        [
            "Énergie;Date;Consommation",
            'Électricité;"01/01/2026 06:30:00";"0.100 kWh"',
            'Électricité;"01/01/2026 07:00:00";"0.100 kWh"',
            'Électricité;"01/01/2026 21:30:00";"0.100 kWh"',
            'Électricité;"01/01/2026 22:00:00";"0.100 kWh"',
        ]
    )
    path = tmp_path / "sample.csv"
    path.write_text(csv_content, encoding="utf-8-sig")
    return path


def test_load_consumption_csv_parses_utf8_sig(sample_csv_path: Path) -> None:
    df = load_consumption_csv(sample_csv_path)

    assert df.index.min() == pd.Timestamp("2026-01-01 06:30:00")
    assert df.index.max() == pd.Timestamp("2026-01-01 22:00:00")
    assert df.loc[pd.Timestamp("2026-01-01 07:00:00"), "consumption_kwh"] == pytest.approx(0.1)
    assert df["consumption_kwh"].sum() == pytest.approx(0.4)


def test_compute_analysis_summary_respects_day_night_boundaries(sample_csv_path: Path) -> None:
    df = load_consumption_csv(sample_csv_path)
    tariff = TariffConfig(day_start=pd.Timestamp("2026-01-01 07:00:00").time(), day_end=pd.Timestamp("2026-01-01 22:00:00").time())
    summary = compute_analysis_summary(df, tariff)

    assert summary.total_kwh == pytest.approx(0.4)
    assert summary.day_kwh == pytest.approx(0.2)
    assert summary.night_kwh == pytest.approx(0.2)
    assert summary.hourly_profile.loc[7] == pytest.approx(0.1)
    assert summary.hourly_profile.loc[21] == pytest.approx(0.1)


def test_load_real_csv_keeps_all_intervals() -> None:
    df = load_consumption_csv(REAL_CSV_PATH)
    summary = compute_analysis_summary(df, TariffConfig())

    assert len(df) == 13424
    assert int(df["is_imputed"].sum()) == 0
    assert summary.total_kwh == pytest.approx(3486.442)


def test_build_annualized_consumption_reconstructs_missing_months() -> None:
    df = load_consumption_csv(REAL_CSV_PATH)
    annualized = build_annualized_consumption(df)

    assert len(annualized) == 17520
    assert annualized.index.min() == pd.Timestamp("2025-07-01 00:00:00")
    assert annualized.index.max() == pd.Timestamp("2026-06-30 23:30:00")
    assert annualized.loc[pd.Timestamp("2025-07-10 12:00:00"), "source_kind"] == "observed"
    assert annualized.loc[pd.Timestamp("2026-03-30 12:00:00"), "source_kind"] == "filled_profile"
    assert annualized.loc[pd.Timestamp("2026-04-15 12:00:00"), "source_kind"] == "interpolated"
    assert annualized.loc[pd.Timestamp("2026-06-20 12:00:00"), "source_kind"] == "observed_template"


def test_simulation_without_pv_keeps_same_grid_need() -> None:
    df = load_consumption_csv(REAL_CSV_PATH)
    annualized = build_annualized_consumption(df)
    result, _ = simulate_pv_battery(
        annualized,
        TariffConfig(base_rate_eur_kwh=0.25),
        SolarConfig(pv_kwc=0.0, specific_yield_kwh_per_kwc_year=1200.0, capex_eur=None),
        BatteryConfig(capacity_kwh=5.0, charge_power_kw=2.5, discharge_power_kw=2.5, roundtrip_efficiency=0.9, min_soc_pct=10.0, capex_eur=None),
    )

    assert result.pv_generated_kwh == pytest.approx(0.0)
    assert result.simulated_grid_kwh == pytest.approx(result.baseline_grid_kwh)
    assert result.annual_savings_eur == pytest.approx(0.0)
    assert result.battery_discharge_kwh == pytest.approx(0.0)


def test_simulation_with_pv_and_battery_improves_over_pv_only() -> None:
    df = load_consumption_csv(REAL_CSV_PATH)
    annualized = build_annualized_consumption(df)
    tariff = TariffConfig(base_rate_eur_kwh=0.2516)
    solar = SolarConfig(pv_kwc=6.0, specific_yield_kwh_per_kwc_year=1200.0, capex_eur=9000.0)

    pv_only, _ = simulate_pv_battery(
        annualized,
        tariff,
        solar,
        BatteryConfig(capacity_kwh=0.0, charge_power_kw=0.0, discharge_power_kw=0.0, roundtrip_efficiency=0.9, min_soc_pct=0.0, capex_eur=None),
    )
    pv_battery, _ = simulate_pv_battery(
        annualized,
        tariff,
        solar,
        BatteryConfig(capacity_kwh=5.0, charge_power_kw=2.5, discharge_power_kw=2.5, roundtrip_efficiency=0.9, min_soc_pct=10.0, capex_eur=3500.0),
    )

    assert pv_only.pv_generated_kwh == pytest.approx(7200.0)
    assert pv_only.battery_charge_kwh == pytest.approx(0.0)
    assert pv_battery.simulated_grid_kwh < pv_only.simulated_grid_kwh
    assert pv_battery.battery_charge_kwh > 0
    assert pv_battery.battery_discharge_kwh > 0
    assert pv_battery.annual_savings_eur > pv_only.annual_savings_eur


def test_payback_hidden_when_costs_missing() -> None:
    df = load_consumption_csv(REAL_CSV_PATH)
    annualized = build_annualized_consumption(df)
    result, _ = simulate_pv_battery(
        annualized,
        TariffConfig(base_rate_eur_kwh=0.25),
        SolarConfig(pv_kwc=6.0, specific_yield_kwh_per_kwc_year=1200.0, capex_eur=None),
        BatteryConfig(capacity_kwh=5.0, charge_power_kw=2.5, discharge_power_kw=2.5, roundtrip_efficiency=0.9, min_soc_pct=10.0, capex_eur=None),
    )

    assert result.annual_savings_eur > 0
    assert result.simple_payback_years is None
