from __future__ import annotations

from matplotlib.figure import Figure

from conso_app.ui.chart_utils import (
    find_bar_index,
    find_nearest_line_point,
    find_nearest_x_index,
    format_hourly_profile_tooltip,
    format_simulation_tooltip,
)


def test_find_nearest_line_point_returns_closest_index() -> None:
    figure = Figure()
    axis = figure.subplots()
    axis.plot([0.0, 1.0, 2.0], [0.0, 2.0, 0.0])
    figure.canvas.draw()

    match = find_nearest_line_point(axis, 1.0, 2.0, [0.0, 1.0, 2.0], [0.0, 2.0, 0.0])

    assert match is not None
    assert match.index == 1


def test_find_nearest_x_index_returns_index_when_cursor_is_close() -> None:
    figure = Figure()
    axis = figure.subplots()
    axis.plot([0.0, 1.0, 2.0], [1.0, 2.0, 3.0])
    figure.canvas.draw()

    index = find_nearest_x_index(axis, 1.03, [0.0, 1.0, 2.0])

    assert index == 1


def test_find_bar_index_returns_hovered_bar() -> None:
    figure = Figure()
    axis = figure.subplots()
    bars = axis.bar([0.0, 1.0], [2.0, 3.0], width=0.6)

    index = find_bar_index(1.0, 2.5, bars)

    assert index == 1


def test_tooltip_formatters_include_main_metrics() -> None:
    hourly = format_hourly_profile_tooltip("07:00", 1.234)
    simulation = format_simulation_tooltip("Jan 2026", 120.0, 80.0, 60.0, 15.5, 22.0)

    assert "07:00" in hourly
    assert "Profil moyen" in hourly
    assert "Charge" in simulation
    assert "Recharge VE" in simulation
    assert "Surplus perdu" in simulation
    assert "-15,50 kWh" in simulation
    assert "Réseau après simulation" in simulation
    assert "Réduction réseau" in simulation
