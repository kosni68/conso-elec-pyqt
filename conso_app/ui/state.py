from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

from ..analysis import AnalysisSummary
from ..models import SimulationResult


SIMULATION_SCENARIO_KEYS = ("simulation_1", "simulation_2", "simulation_3")


@dataclass(slots=True)
class SimulationScenarioState:
    result: SimulationResult | None = None
    dataframe: pd.DataFrame | None = None


def _default_simulation_states() -> dict[str, SimulationScenarioState]:
    return {
        scenario_key: SimulationScenarioState()
        for scenario_key in SIMULATION_SCENARIO_KEYS
    }


@dataclass(slots=True)
class ApplicationState:
    raw_df: pd.DataFrame | None = None
    analysis_summary: AnalysisSummary | None = None
    annualized_df: pd.DataFrame | None = None
    simulation_result: SimulationResult | None = None
    simulation_df: pd.DataFrame | None = None
    simulation_states: dict[str, SimulationScenarioState] = field(default_factory=_default_simulation_states)
    current_file_path: Path | None = None
