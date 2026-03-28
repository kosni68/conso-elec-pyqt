from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence

import numpy as np
from matplotlib.axes import Axes
from matplotlib.patches import Rectangle

from .formatting import format_kwh


@dataclass(frozen=True, slots=True)
class HoverMatch:
    index: int
    pixel_distance: float


def find_nearest_line_point(
    axis: Axes,
    event_xdata: float | None,
    event_ydata: float | None,
    x_values: Sequence[float],
    y_values: Sequence[float],
    *,
    max_distance_px: float = 20.0,
) -> HoverMatch | None:
    if event_xdata is None or event_ydata is None or len(x_values) == 0:
        return None

    points = np.column_stack((np.asarray(x_values, dtype=float), np.asarray(y_values, dtype=float)))
    event_point = axis.transData.transform((event_xdata, event_ydata))
    point_pixels = axis.transData.transform(points)
    distances = np.linalg.norm(point_pixels - event_point, axis=1)
    index = int(np.argmin(distances))
    distance = float(distances[index])
    if distance > max_distance_px:
        return None
    return HoverMatch(index=index, pixel_distance=distance)


def find_nearest_x_index(
    axis: Axes,
    event_xdata: float | None,
    x_values: Sequence[float],
    *,
    max_distance_px: float = 24.0,
) -> int | None:
    if event_xdata is None or len(x_values) == 0:
        return None

    x_array = np.asarray(x_values, dtype=float)
    y_reference = float(np.mean(axis.get_ylim()))
    event_pixel_x = axis.transData.transform((event_xdata, y_reference))[0]
    point_pixels_x = axis.transData.transform(np.column_stack((x_array, np.full_like(x_array, y_reference))))[:, 0]
    distances = np.abs(point_pixels_x - event_pixel_x)
    index = int(np.argmin(distances))
    if float(distances[index]) > max_distance_px:
        return None
    return index


def find_bar_index(
    event_xdata: float | None,
    event_ydata: float | None,
    bars: Iterable[Rectangle],
) -> int | None:
    if event_xdata is None or event_ydata is None:
        return None

    for index, bar in enumerate(bars):
        if not bar.get_visible():
            continue
        x0 = bar.get_x()
        x1 = x0 + bar.get_width()
        y0 = bar.get_y()
        y1 = y0 + bar.get_height()
        min_x, max_x = sorted((x0, x1))
        min_y, max_y = sorted((y0, y1))
        if min_x <= event_xdata <= max_x and min_y <= event_ydata <= max_y:
            return index
    return None


def format_daily_tooltip(timestamp_label: str, value_kwh: float) -> str:
    return "\n".join([timestamp_label, f"Consommation: {format_kwh(value_kwh)}"])


def format_month_total_tooltip(period_label: str, value_kwh: float) -> str:
    return "\n".join([period_label, f"Total mensuel: {format_kwh(value_kwh)}"])


def format_hourly_profile_tooltip(hour_label: str, value_kwh: float) -> str:
    return "\n".join([hour_label, f"Profil moyen: {format_kwh(value_kwh)}"])


def format_simulation_tooltip(
    period_label: str,
    baseline_kwh: float | None,
    grid_kwh: float | None,
    pv_kwh: float | None,
    curtailed_kwh: float | None = None,
) -> str:
    lines = [period_label]
    if baseline_kwh is not None:
        lines.append(f"Charge: {format_kwh(baseline_kwh)}")
    if grid_kwh is not None:
        lines.append(f"Réseau après simulation: {format_kwh(grid_kwh)}")
    if pv_kwh is not None:
        lines.append(f"Production PV: {format_kwh(pv_kwh)}")
    if curtailed_kwh is not None:
        lines.append(f"Surplus perdu: {format_kwh(-curtailed_kwh)}")
    if baseline_kwh is not None and grid_kwh is not None:
        lines.append(f"Réduction réseau: {format_kwh(max(0.0, baseline_kwh - grid_kwh))}")
    return "\n".join(lines)
