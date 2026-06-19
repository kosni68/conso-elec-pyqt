from __future__ import annotations

from pathlib import Path

import pytest

from conso_app.analysis import (
    CostModel,
    InstallationOptimizer,
    SearchSpace,
    build_annualized_consumption,
    load_consumption_csv,
)
from conso_app.analysis.analyzer import ConsumptionAnalyzer
from conso_app.analysis.optimizer import (
    CRITERION_AUTONOMY,
    CRITERION_NET_GAIN,
    CRITERION_PAYBACK,
    CRITERION_SAVINGS,
    _inclusive_range,
)
from conso_app.analysis.simulation import BatteryRuntimeConfig, PvBatterySimulator, simulate_sizing_metrics
from conso_app.models import BatteryConfig, SolarConfig, TariffConfig

PROJECT_ROOT = Path(__file__).resolve().parents[1]
REAL_CSV_PATH = PROJECT_ROOT / "112486686.csv"

SMALL_SPACE = SearchSpace(pv_max_kwc=6.0, pv_step_kwc=2.0, battery_max_kwh=9.6, battery_step_kwh=4.8)


@pytest.fixture(scope="module")
def annualized():
    df = load_consumption_csv(REAL_CSV_PATH)
    return build_annualized_consumption(df)


def test_sizing_metrics_match_full_simulation(annualized) -> None:
    tariff = TariffConfig(base_rate_eur_kwh=0.25)
    analyzer = ConsumptionAnalyzer()
    simulator = PvBatterySimulator(analyzer)
    solar = SolarConfig(pv_kwc=9.0, specific_yield_kwh_per_kwc_year=1200.0)
    battery = BatteryConfig(capacity_kwh=14.4, charge_power_kw=8.0, discharge_power_kw=8.0)

    result, _ = simulator.simulate(annualized, tariff, solar, battery)

    working = analyzer.add_derived_columns(annualized, tariff)
    loads = working["consumption_kwh"].to_numpy(dtype=float)
    pv_generation = simulator.build_pv_generation_series(working.index, solar).to_numpy(dtype=float)
    runtime = BatteryRuntimeConfig.from_config(battery)
    metrics = simulate_sizing_metrics(loads, pv_generation, runtime)

    assert metrics.simulated_grid_kwh == pytest.approx(result.simulated_grid_kwh)
    assert metrics.battery_charge_kwh == pytest.approx(result.battery_charge_kwh)
    assert metrics.battery_discharge_kwh == pytest.approx(result.battery_discharge_kwh)
    assert metrics.curtailed_pv_kwh == pytest.approx(result.curtailed_pv_kwh)
    assert metrics.direct_pv_kwh + metrics.battery_discharge_kwh == pytest.approx(result.pv_self_consumed_kwh)


def test_inclusive_range_includes_bounds() -> None:
    assert _inclusive_range(0.0, 18.0, 1.0)[0] == 0.0
    assert _inclusive_range(0.0, 18.0, 1.0)[-1] == 18.0
    assert _inclusive_range(0.0, 24.0, 4.8) == [0.0, 4.8, 9.6, 14.4, 19.2, 24.0]
    # le pas ne tombant pas pile sur la borne, celle-ci est tout de même ajoutée
    assert _inclusive_range(0.0, 5.0, 2.0) == [0.0, 2.0, 4.0, 5.0]


def test_cost_model_capex_matches_reference_installation() -> None:
    cost = CostModel()
    total = cost.pv_capex(9.0) + cost.battery_capex(14.4)
    assert total == pytest.approx(833.0 * 9.0 + 198.0 * 14.4)
    assert cost.pv_capex(0.0) == 0.0


def test_optimizer_payback_picks_fastest_return(annualized) -> None:
    optimizer = InstallationOptimizer()
    result = optimizer.optimize(
        annualized,
        TariffConfig(base_rate_eur_kwh=0.25),
        cost_model=CostModel(),
        search_space=SMALL_SPACE,
        criterion=CRITERION_PAYBACK,
    )

    best = result.best
    assert best is result.ranking[0]
    assert best.is_install
    assert best.payback_years is not None
    payable = [c.payback_years for c in result.ranking if c.payback_years is not None]
    assert best.payback_years == pytest.approx(min(payable))


def test_optimizer_savings_picks_largest_savings(annualized) -> None:
    optimizer = InstallationOptimizer()
    result = optimizer.optimize(
        annualized,
        TariffConfig(base_rate_eur_kwh=0.25),
        cost_model=CostModel(),
        search_space=SMALL_SPACE,
        criterion=CRITERION_SAVINGS,
    )

    best = result.best
    assert best.annual_savings_eur == pytest.approx(max(c.annual_savings_eur for c in result.ranking))


def test_optimizer_autonomy_target_returns_cheapest_reaching_it(annualized) -> None:
    optimizer = InstallationOptimizer()
    result = optimizer.optimize(
        annualized,
        TariffConfig(base_rate_eur_kwh=0.25),
        cost_model=CostModel(),
        search_space=SMALL_SPACE,
        criterion=CRITERION_AUTONOMY,
        autonomy_target=0.1,
    )

    best = result.best
    assert best.autonomy_rate >= 0.1 - 1e-9
    reaching = [c for c in result.ranking if c.autonomy_rate >= 0.1 - 1e-9]
    assert best.capex_eur == pytest.approx(min(c.capex_eur for c in reaching))


def test_optimizer_autonomy_unreachable_target_falls_back_to_max_autonomy(annualized) -> None:
    optimizer = InstallationOptimizer()
    result = optimizer.optimize(
        annualized,
        TariffConfig(base_rate_eur_kwh=0.25),
        cost_model=CostModel(),
        search_space=SMALL_SPACE,
        criterion=CRITERION_AUTONOMY,
        autonomy_target=1.0,
    )

    best = result.best
    assert best.autonomy_rate < 1.0
    assert best.autonomy_rate == pytest.approx(max(c.autonomy_rate for c in result.ranking))


def test_optimizer_net_gain_uses_horizon(annualized) -> None:
    optimizer = InstallationOptimizer(horizon_years=20)
    result = optimizer.optimize(
        annualized,
        TariffConfig(base_rate_eur_kwh=0.25),
        cost_model=CostModel(),
        search_space=SMALL_SPACE,
        criterion=CRITERION_NET_GAIN,
    )

    best = result.best
    assert result.horizon_years == 20
    assert best.net_gain_eur == pytest.approx(best.annual_savings_eur * 20 - best.capex_eur)
    assert best.net_gain_eur == pytest.approx(max(c.net_gain_eur for c in result.ranking))
