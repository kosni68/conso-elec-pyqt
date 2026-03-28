from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from ..analysis import AnalysisSummary
from ..models import SimulationResult


@dataclass(slots=True)
class ApplicationState:
    raw_df: pd.DataFrame | None = None
    analysis_summary: AnalysisSummary | None = None
    annualized_df: pd.DataFrame | None = None
    simulation_result: SimulationResult | None = None
    simulation_df: pd.DataFrame | None = None
    current_file_path: Path | None = None
