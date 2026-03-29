from __future__ import annotations

from datetime import time
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from conso_app.analysis import (
    PvBatterySimulator,
    build_annualized_consumption,
    compute_analysis_summary,
    load_consumption_csv,
    month_coverage,
    simulate_pv_battery,
)
from conso_app.models import BatteryConfig, EvChargingConfig, SolarConfig, TariffConfig


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REAL_CSV_PATH = PROJECT_ROOT / "112486686.csv"


def _write_sample_csv(
    tmp_path: Path,
    *,
    energy_header: str = "Énergie",
    energy_value: str = "Électricité",
) -> Path:
    csv_content = "\n".join(
        [
            f"{energy_header};Date;Consommation",
            f'{energy_value};"01/01/2026 06:30:00";"0.100 kWh"',
            f'{energy_value};"01/01/2026 07:00:00";"0.100 kWh"',
            f'{energy_value};"01/01/2026 21:30:00";"0.100 kWh"',
            f'{energy_value};"01/01/2026 22:00:00";"0.100 kWh"',
        ]
    )
    path = tmp_path / "sample.csv"
    path.write_text(csv_content, encoding="utf-8-sig")
    return path


@pytest.fixture()
def sample_csv_path(tmp_path: Path) -> Path:
    return _write_sample_csv(tmp_path)


def test_load_consumption_csv_parses_utf8_sig_headers(sample_csv_path: Path) -> None:
    df = load_consumption_csv(sample_csv_path)

    assert df.index.min() == pd.Timestamp("2026-01-01 06:30:00")
    assert df.index.max() == pd.Timestamp("2026-01-01 22:00:00")
    assert df.loc[pd.Timestamp("2026-01-01 07:00:00"), "consumption_kwh"] == pytest.approx(0.1)
    assert df["consumption_kwh"].sum() == pytest.approx(0.4)
    assert df["energy"].iloc[0] == "Électricité"


def test_load_consumption_csv_accepts_legacy_mojibake_headers(tmp_path: Path) -> None:
    csv_path = _write_sample_csv(
        tmp_path,
        energy_header="Ã‰nergie",
        energy_value="Ã‰lectricitÃ©",
    )

    df = load_consumption_csv(csv_path)

    assert df["energy"].iloc[0] == "Électricité"
    assert df["consumption_kwh"].sum() == pytest.approx(0.4)


def test_compute_analysis_summary_respects_day_night_boundaries(sample_csv_path: Path) -> None:
    df = load_consumption_csv(sample_csv_path)
    tariff = TariffConfig(
        day_start=pd.Timestamp("2026-01-01 07:00:00").time(),
        day_end=pd.Timestamp("2026-01-01 22:00:00").time(),
    )

    summary = compute_analysis_summary(df, tariff)

    assert summary.total_kwh == pytest.approx(0.4)
    assert summary.day_kwh == pytest.approx(0.2)
    assert summary.night_kwh == pytest.approx(0.2)
    assert summary.hourly_profile.loc[7] == pytest.approx(0.1)
    assert summary.hourly_profile.loc[21] == pytest.approx(0.1)


def test_compute_analysis_summary_filters_dates_inclusively(tmp_path: Path) -> None:
    csv_content = "\n".join(
        [
            "Énergie;Date;Consommation",
            'Électricité;"01/01/2026 23:30:00";"0.100 kWh"',
            'Électricité;"02/01/2026 07:00:00";"0.200 kWh"',
            'Électricité;"02/01/2026 21:30:00";"0.300 kWh"',
            'Électricité;"03/01/2026 00:00:00";"0.400 kWh"',
        ]
    )
    csv_path = tmp_path / "range.csv"
    csv_path.write_text(csv_content, encoding="utf-8-sig")

    df = load_consumption_csv(csv_path)
    summary = compute_analysis_summary(
        df,
        TariffConfig(),
        start_date=pd.Timestamp("2026-01-02").date(),
        end_date=pd.Timestamp("2026-01-02").date(),
    )

    assert summary.filtered_df.index.min() == pd.Timestamp("2026-01-02 00:00:00")
    assert summary.filtered_df.index.max() == pd.Timestamp("2026-01-02 23:30:00")
    assert summary.total_kwh == pytest.approx(0.5)


def test_month_coverage_detects_partial_and_full_months() -> None:
    january_days = pd.date_range("2026-01-01", "2026-01-31", freq="D")
    february_days = pd.date_range("2026-02-01", "2026-02-10", freq="D")
    index = january_days.append(february_days)
    df = pd.DataFrame({"consumption_kwh": 1.0}, index=index)

    coverage = month_coverage(df)

    assert coverage["period"].tolist() == [pd.Period("2026-01", freq="M"), pd.Period("2026-02", freq="M")]
    assert coverage["is_full"].tolist() == [True, False]


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
        BatteryConfig(
            capacity_kwh=5.0,
            charge_power_kw=2.5,
            discharge_power_kw=2.5,
            roundtrip_efficiency=0.9,
            min_soc_pct=10.0,
            capex_eur=None,
        ),
    )

    assert result.pv_generated_kwh == pytest.approx(0.0)
    assert result.simulated_grid_kwh == pytest.approx(result.baseline_grid_kwh)
    assert result.annual_savings_eur == pytest.approx(0.0)
    assert result.battery_discharge_kwh == pytest.approx(0.0)


def test_simulation_without_ev_config_matches_disabled_ev_config() -> None:
    df = load_consumption_csv(REAL_CSV_PATH)
    annualized = build_annualized_consumption(df)
    tariff = TariffConfig(base_rate_eur_kwh=0.25)
    solar = SolarConfig(pv_kwc=6.0, specific_yield_kwh_per_kwc_year=1200.0, capex_eur=None)
    battery = BatteryConfig(
        capacity_kwh=5.0,
        charge_power_kw=2.5,
        discharge_power_kw=2.5,
        roundtrip_efficiency=0.9,
        min_soc_pct=10.0,
        capex_eur=None,
    )

    without_ev, without_ev_df = simulate_pv_battery(annualized, tariff, solar, battery)
    disabled_ev, disabled_ev_df = simulate_pv_battery(
        annualized,
        tariff,
        solar,
        battery,
        EvChargingConfig(enabled=False),
    )

    assert disabled_ev == without_ev
    pd.testing.assert_frame_equal(disabled_ev_df, without_ev_df)


def test_build_ev_charging_series_respects_weekdays_and_overnight_window() -> None:
    simulator = PvBatterySimulator()
    index = pd.date_range("2026-01-05 00:00:00", "2026-01-07 23:30:00", freq="30min")
    ev_series = simulator.build_ev_charging_series(
        index,
        EvChargingConfig(
            enabled=True,
            daily_energy_kwh=15.0,
            charge_power_kw=5.0,
            start_time=time(22, 0),
            end_time=time(2, 0),
            active_weekdays=(True, False, False, False, False, False, False),
        ),
    )

    assert ev_series.sum() == pytest.approx(15.0)
    assert ev_series.loc[pd.Timestamp("2026-01-05 22:00:00")] == pytest.approx(2.5)
    assert ev_series.loc[pd.Timestamp("2026-01-05 23:30:00")] == pytest.approx(2.5)
    assert ev_series.loc[pd.Timestamp("2026-01-06 00:00:00")] == pytest.approx(2.5)
    assert ev_series.loc[pd.Timestamp("2026-01-06 00:30:00")] == pytest.approx(2.5)
    assert ev_series.loc[pd.Timestamp("2026-01-06 01:00:00")] == pytest.approx(0.0)
    assert ev_series.loc[pd.Timestamp("2026-01-06 01:30:00")] == pytest.approx(0.0)
    assert ev_series.loc[pd.Timestamp("2026-01-06 22:00:00")] == pytest.approx(0.0)


def test_build_ev_charging_series_rejects_unreachable_daily_target() -> None:
    simulator = PvBatterySimulator()
    index = pd.date_range("2026-01-01 00:00:00", "2026-01-03 23:30:00", freq="30min")

    with pytest.raises(ValueError, match="fenêtre de recharge VE est trop courte"):
        simulator.build_ev_charging_series(
            index,
            EvChargingConfig(
                enabled=True,
                daily_energy_kwh=20.0,
                charge_power_kw=3.0,
                start_time=time(22, 0),
                end_time=time(23, 0),
            ),
        )


def test_simulation_with_pv_and_battery_improves_over_pv_only() -> None:
    df = load_consumption_csv(REAL_CSV_PATH)
    annualized = build_annualized_consumption(df)
    tariff = TariffConfig(base_rate_eur_kwh=0.2516)
    solar = SolarConfig(pv_kwc=6.0, specific_yield_kwh_per_kwc_year=1200.0, capex_eur=9000.0)

    pv_only, _ = simulate_pv_battery(
        annualized,
        tariff,
        solar,
        BatteryConfig(
            capacity_kwh=0.0,
            charge_power_kw=0.0,
            discharge_power_kw=0.0,
            roundtrip_efficiency=0.9,
            min_soc_pct=0.0,
            capex_eur=None,
        ),
    )
    pv_battery, simulation_df = simulate_pv_battery(
        annualized,
        tariff,
        solar,
        BatteryConfig(
            capacity_kwh=5.0,
            charge_power_kw=2.5,
            discharge_power_kw=2.5,
            roundtrip_efficiency=0.9,
            min_soc_pct=10.0,
            capex_eur=3500.0,
        ),
    )

    assert pv_only.pv_generated_kwh == pytest.approx(7200.0)
    assert pv_only.battery_charge_kwh == pytest.approx(0.0)
    assert pv_battery.simulated_grid_kwh < pv_only.simulated_grid_kwh
    assert pv_battery.battery_charge_kwh > 0
    assert pv_battery.battery_discharge_kwh > 0
    assert pv_battery.annual_savings_eur > pv_only.annual_savings_eur
    assert simulation_df["curtailed_pv_kwh"].sum() == pytest.approx(pv_battery.curtailed_pv_kwh)
    assert (simulation_df["curtailed_pv_kwh"] >= 0).all()
    assert simulation_df["soc_kwh"].min() >= 0.5 - 1e-9
    assert simulation_df["soc_kwh"].max() <= 5.0 + 1e-9


def test_simulation_with_ev_adds_expected_charging_load() -> None:
    df = load_consumption_csv(REAL_CSV_PATH)
    annualized = build_annualized_consumption(df)
    result, simulation_df = simulate_pv_battery(
        annualized,
        TariffConfig(base_rate_eur_kwh=0.25),
        SolarConfig(pv_kwc=0.0, specific_yield_kwh_per_kwc_year=1200.0, capex_eur=None),
        BatteryConfig(
            capacity_kwh=0.0,
            charge_power_kw=0.0,
            discharge_power_kw=0.0,
            roundtrip_efficiency=0.9,
            min_soc_pct=0.0,
            capex_eur=None,
        ),
        EvChargingConfig(
            enabled=True,
            daily_energy_kwh=10.0,
            charge_power_kw=7.4,
            start_time=time(22, 0),
            end_time=time(6, 0),
        ),
    )

    assert "ev_charging_kwh" in simulation_df
    assert "home_consumption_kwh" in simulation_df
    assert result.ev_charging_kwh == pytest.approx(3650.0)
    assert simulation_df["ev_charging_kwh"].sum() == pytest.approx(result.ev_charging_kwh)
    assert np.allclose(
        (simulation_df["consumption_kwh"] - simulation_df["home_consumption_kwh"]).to_numpy(dtype=float),
        simulation_df["ev_charging_kwh"].to_numpy(dtype=float),
    )
    assert simulation_df["ev_charging_kwh"].sum() > 0


def test_payback_hidden_when_costs_missing() -> None:
    df = load_consumption_csv(REAL_CSV_PATH)
    annualized = build_annualized_consumption(df)
    result, _ = simulate_pv_battery(
        annualized,
        TariffConfig(base_rate_eur_kwh=0.25),
        SolarConfig(pv_kwc=6.0, specific_yield_kwh_per_kwc_year=1200.0, capex_eur=None),
        BatteryConfig(
            capacity_kwh=5.0,
            charge_power_kw=2.5,
            discharge_power_kw=2.5,
            roundtrip_efficiency=0.9,
            min_soc_pct=10.0,
            capex_eur=None,
        ),
    )

    assert result.annual_savings_eur > 0
    assert result.simple_payback_years is None
