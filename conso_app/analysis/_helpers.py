from __future__ import annotations

from datetime import date, time
from typing import Optional

import numpy as np
import pandas as pd

from ..models import TariffConfig
from ._constants import DAY_LABEL, DEFAULT_ENERGY_NAME, NIGHT_LABEL


def parse_time_text(value: str) -> time:
    hour, minute = value.split(":")
    return time(int(hour), int(minute))


def normalize_text(value: str) -> str:
    normalized = value
    if "Ã" in normalized or "â" in normalized:
        try:
            normalized = normalized.encode("latin1").decode("utf-8")
        except UnicodeError:
            pass

    replacements = {
        "Ã‰": "É",
        "Ã©": "é",
        "Ã¨": "è",
        "Ãª": "ê",
        "Ã ": "à",
        "Ã§": "ç",
        "Ã¹": "ù",
        "Ã´": "ô",
        "Ã®": "î",
        "â€™": "’",
        "â€¦": "…",
        "â‚¬": "€",
        "â†’": "→",
        "Ă‰": "É",
        "Ă©": "é",
        "Ă¨": "è",
        "Ăª": "ê",
        "Ă ": "à",
        "Ă§": "ç",
        "Ă¹": "ù",
        "Ă´": "ô",
        "Ă®": "î",
    }
    for broken, fixed in replacements.items():
        normalized = normalized.replace(broken, fixed)
    return normalized


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
    out["period_label"] = np.where(out["is_day"], DAY_LABEL, NIGHT_LABEL)

    if "energy" not in out.columns:
        out["energy"] = DEFAULT_ENERGY_NAME
    else:
        out["energy"] = out["energy"].fillna(DEFAULT_ENERGY_NAME).astype(str).map(normalize_text)

    if "is_imputed" not in out.columns:
        out["is_imputed"] = False
    else:
        out["is_imputed"] = out["is_imputed"].fillna(False).astype(bool)

    if "source_kind" not in out.columns:
        out["source_kind"] = "observed"
    else:
        out["source_kind"] = out["source_kind"].fillna("observed").astype(str)
    return out


def filter_consumption(
    df: pd.DataFrame,
    tariff: TariffConfig,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
) -> pd.DataFrame:
    filtered = add_derived_columns(df, tariff)
    if start_date is not None:
        filtered = filtered[filtered.index >= pd.Timestamp(start_date)]
    if end_date is not None:
        filtered = filtered[filtered.index <= pd.Timestamp(end_date) + pd.Timedelta(hours=23, minutes=30)]
    return filtered
