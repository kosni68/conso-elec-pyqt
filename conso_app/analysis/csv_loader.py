from __future__ import annotations

from pathlib import Path
from typing import Optional

import pandas as pd

from ..models import TariffConfig
from ._constants import CSV_DATE_FORMAT, CSV_DELIMITER, DEFAULT_ENERGY_NAME, HALF_HOUR_FREQUENCY
from ._helpers import add_derived_columns, normalize_text


class ConsumptionCsvLoader:
    REQUIRED_COLUMNS = {"Énergie", "Date", "Consommation"}

    def __init__(self, analyzer=None) -> None:
        self.analyzer = analyzer

    def load(self, path: str | Path, tariff: Optional[TariffConfig] = None) -> pd.DataFrame:
        raw = pd.read_csv(path, sep=CSV_DELIMITER, encoding="utf-8-sig", dtype=str)
        raw.columns = [normalize_text(str(column)).strip() for column in raw.columns]

        if not self.REQUIRED_COLUMNS.issubset(set(raw.columns)):
            raise ValueError(f"Colonnes attendues introuvables: {self.REQUIRED_COLUMNS}")

        frame = pd.DataFrame(
            {
                "energy": raw["Énergie"].fillna(DEFAULT_ENERGY_NAME).astype(str).map(normalize_text).str.strip(),
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
        reindexed["energy"] = reindexed["energy"].fillna(DEFAULT_ENERGY_NAME)
        reindexed["is_imputed"] = is_imputed
        return add_derived_columns(reindexed, tariff)
