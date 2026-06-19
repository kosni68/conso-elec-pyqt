from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Optional

import pandas as pd

from ..models import BatteryConfig, EvChargingConfig, SolarConfig, TariffConfig
from .analyzer import ConsumptionAnalyzer
from .simulation import BatteryRuntimeConfig, PvBatterySimulator, simulate_sizing_metrics

# Critères d'optimisation (clé interne -> libellé affiché)
CRITERION_AUTONOMY = "autonomy"
CRITERION_PAYBACK = "payback"
CRITERION_SAVINGS = "savings"
CRITERION_NET_GAIN = "net_gain"

CRITERION_LABELS = {
    CRITERION_AUTONOMY: "Autonomie maximale (au meilleur prix)",
    CRITERION_PAYBACK: "Retour sur investissement le plus rapide",
    CRITERION_SAVINGS: "Économies annuelles maximales",
    CRITERION_NET_GAIN: "Meilleur gain net sur l'horizon",
}


@dataclass(frozen=True, slots=True)
class CostModel:
    """Modèle de coût linéaire dérivé de l'installation réelle (Doc/cout_installation.md).

    Référence : 9 kWc + 14,4 kWh ≈ 10 344 € → 833 €/kWc et 198 €/kWh.
    """

    pv_cost_per_kwc: float = 833.0
    battery_cost_per_kwh: float = 198.0
    fixed_cost_eur: float = 0.0

    def pv_capex(self, pv_kwc: float) -> float:
        if pv_kwc <= 0:
            return 0.0
        return self.fixed_cost_eur + pv_kwc * self.pv_cost_per_kwc

    def battery_capex(self, capacity_kwh: float) -> float:
        return max(0.0, capacity_kwh) * self.battery_cost_per_kwh


@dataclass(frozen=True, slots=True)
class SearchSpace:
    pv_max_kwc: float = 18.0
    pv_step_kwc: float = 1.0
    battery_max_kwh: float = 24.0
    battery_step_kwh: float = 4.8

    def pv_values(self) -> list[float]:
        return _inclusive_range(0.0, self.pv_max_kwc, self.pv_step_kwc)

    def battery_values(self) -> list[float]:
        return _inclusive_range(0.0, self.battery_max_kwh, self.battery_step_kwh)


@dataclass(frozen=True, slots=True)
class SizingCandidate:
    pv_kwc: float
    capacity_kwh: float
    pv_capex_eur: float
    battery_capex_eur: float
    annual_savings_eur: float
    baseline_grid_kwh: float
    simulated_grid_kwh: float
    pv_generated_kwh: float
    curtailed_pv_kwh: float
    autonomy_rate: float
    self_consumption_rate: float
    payback_years: Optional[float]
    net_gain_eur: float

    @property
    def capex_eur(self) -> float:
        return self.pv_capex_eur + self.battery_capex_eur

    @property
    def is_install(self) -> bool:
        return self.pv_kwc > 0 or self.capacity_kwh > 0


@dataclass(frozen=True, slots=True)
class OptimizationResult:
    criterion: str
    best: SizingCandidate
    ranking: tuple[SizingCandidate, ...]
    autonomy_target: float
    horizon_years: int
    candidate_count: int


def _inclusive_range(start: float, stop: float, step: float) -> list[float]:
    if step <= 0 or stop < start:
        return [round(start, 3)]
    count = int(round((stop - start) / step))
    values = [round(start + index * step, 3) for index in range(count + 1)]
    if values[-1] < stop - 1e-9:
        values.append(round(stop, 3))
    return values


class InstallationOptimizer:
    """Balaye une grille de dimensionnements PV/batterie et retient le meilleur selon un critère."""

    def __init__(self, analyzer: ConsumptionAnalyzer | None = None, *, horizon_years: int = 20) -> None:
        self.analyzer = analyzer or ConsumptionAnalyzer()
        self.simulator = PvBatterySimulator(self.analyzer)
        self.horizon_years = max(1, horizon_years)

    def optimize(
        self,
        annualized_df: pd.DataFrame,
        tariff: TariffConfig,
        *,
        cost_model: CostModel,
        search_space: SearchSpace,
        criterion: str,
        autonomy_target: float = 1.0,
        specific_yield_kwh_per_kwc_year: float = 1200.0,
        battery_template: BatteryConfig | None = None,
        ev_config: EvChargingConfig | None = None,
        ranking_size: int = 8,
    ) -> OptimizationResult:
        if criterion not in CRITERION_LABELS:
            raise ValueError(f"Critère d'optimisation inconnu : {criterion}")

        template = battery_template or BatteryConfig()
        working = self.analyzer.add_derived_columns(annualized_df, tariff)
        loads = working["consumption_kwh"].to_numpy(dtype=float)
        if ev_config is not None and ev_config.enabled:
            ev_series = self.simulator.build_ev_charging_series(working.index, ev_config)
            loads = loads + ev_series.to_numpy(dtype=float)

        baseline_grid_kwh = float(loads.sum())
        unit_pv = self.simulator.build_pv_generation_series(
            working.index,
            SolarConfig(pv_kwc=1.0, specific_yield_kwh_per_kwc_year=specific_yield_kwh_per_kwc_year),
        ).to_numpy(dtype=float)
        unit_pv_energy = float(unit_pv.sum())
        rate = tariff.base_rate_eur_kwh

        candidates: list[SizingCandidate] = []
        for pv_kwc in search_space.pv_values():
            pv_generation = unit_pv * pv_kwc
            pv_generated_kwh = unit_pv_energy * pv_kwc
            pv_capex = cost_model.pv_capex(pv_kwc)
            for capacity_kwh in search_space.battery_values():
                runtime = BatteryRuntimeConfig.from_config(replace(template, capacity_kwh=capacity_kwh))
                metrics = simulate_sizing_metrics(loads, pv_generation, runtime)
                candidates.append(
                    self._build_candidate(
                        pv_kwc=pv_kwc,
                        capacity_kwh=capacity_kwh,
                        pv_capex=pv_capex,
                        battery_capex=cost_model.battery_capex(capacity_kwh),
                        baseline_grid_kwh=baseline_grid_kwh,
                        pv_generated_kwh=pv_generated_kwh,
                        rate=rate,
                        metrics=metrics,
                    )
                )

        autonomy_target = min(max(autonomy_target, 0.0), 1.0)
        ranked = self._rank(candidates, criterion, autonomy_target)
        best = ranked[0]
        return OptimizationResult(
            criterion=criterion,
            best=best,
            ranking=tuple(ranked[:ranking_size]),
            autonomy_target=autonomy_target,
            horizon_years=self.horizon_years,
            candidate_count=len(candidates),
        )

    def _build_candidate(
        self,
        *,
        pv_kwc: float,
        capacity_kwh: float,
        pv_capex: float,
        battery_capex: float,
        baseline_grid_kwh: float,
        pv_generated_kwh: float,
        rate: float,
        metrics,
    ) -> SizingCandidate:
        simulated_grid_kwh = metrics.simulated_grid_kwh
        self_consumed_kwh = metrics.direct_pv_kwh + metrics.battery_discharge_kwh
        annual_savings_eur = (baseline_grid_kwh - simulated_grid_kwh) * rate
        capex = pv_capex + battery_capex
        autonomy_rate = (1.0 - simulated_grid_kwh / baseline_grid_kwh) if baseline_grid_kwh else 0.0
        self_consumption_rate = (self_consumed_kwh / pv_generated_kwh) if pv_generated_kwh else 0.0
        payback_years = (capex / annual_savings_eur) if (capex > 0 and annual_savings_eur > 0) else None
        net_gain_eur = annual_savings_eur * self.horizon_years - capex
        return SizingCandidate(
            pv_kwc=pv_kwc,
            capacity_kwh=capacity_kwh,
            pv_capex_eur=pv_capex,
            battery_capex_eur=battery_capex,
            annual_savings_eur=annual_savings_eur,
            baseline_grid_kwh=baseline_grid_kwh,
            simulated_grid_kwh=simulated_grid_kwh,
            pv_generated_kwh=pv_generated_kwh,
            curtailed_pv_kwh=metrics.curtailed_pv_kwh,
            autonomy_rate=autonomy_rate,
            self_consumption_rate=self_consumption_rate,
            payback_years=payback_years,
            net_gain_eur=net_gain_eur,
        )

    @staticmethod
    def _rank(
        candidates: list[SizingCandidate],
        criterion: str,
        autonomy_target: float,
    ) -> list[SizingCandidate]:
        installs = [candidate for candidate in candidates if candidate.is_install]
        if not installs:
            return list(candidates)

        if criterion == CRITERION_AUTONOMY:
            reaching = [c for c in installs if c.autonomy_rate >= autonomy_target - 1e-9]
            if reaching:
                # objectif atteint : on minimise le coût, puis on maximise l'autonomie
                return sorted(reaching, key=lambda c: (c.capex_eur, -c.autonomy_rate))
            # objectif hors de portée : au plus proche, puis le moins cher
            return sorted(installs, key=lambda c: (-c.autonomy_rate, c.capex_eur))

        if criterion == CRITERION_PAYBACK:
            payable = [c for c in installs if c.payback_years is not None]
            pool = payable or installs
            return sorted(pool, key=lambda c: (c.payback_years if c.payback_years is not None else float("inf"), -c.annual_savings_eur))

        if criterion == CRITERION_SAVINGS:
            return sorted(installs, key=lambda c: (-c.annual_savings_eur, c.capex_eur))

        # CRITERION_NET_GAIN
        return sorted(installs, key=lambda c: (-c.net_gain_eur, c.capex_eur))
