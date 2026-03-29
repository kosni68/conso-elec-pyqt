from __future__ import annotations

import os
from pathlib import Path

import pytest
from matplotlib.backend_bases import KeyEvent, MouseButton, MouseEvent, PickEvent

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

pytest.importorskip("PyQt6")

from PyQt6.QtCore import QTime
from PyQt6.QtWidgets import QApplication

from conso_app.ui import ConsumptionMainWindow


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REAL_CSV_PATH = PROJECT_ROOT / "112486686.csv"


class DummyWheelEvent:
    def __init__(self) -> None:
        self.ignored = False

    def ignore(self) -> None:
        self.ignored = True


@pytest.fixture()
def qapp() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


@pytest.fixture()
def loaded_window(qapp: QApplication) -> ConsumptionMainWindow:
    window = ConsumptionMainWindow(initial_csv_path=REAL_CSV_PATH)
    qapp.processEvents()
    yield window
    window.close()


def _dispatch_mouse_event(canvas, name: str, axis, x_value: float, y_value: float, **kwargs):
    pixel_x, pixel_y = axis.transData.transform((x_value, y_value))
    event = MouseEvent(name, canvas, pixel_x, pixel_y, **kwargs)
    canvas.callbacks.process(name, event)
    return event


def test_main_window_loads_csv_and_refreshes(loaded_window: ConsumptionMainWindow, qapp: QApplication) -> None:
    window = loaded_window

    assert window.raw_df is not None
    assert window.analysis_summary is not None
    assert window.simulation_result is not None
    assert window.current_file_path == REAL_CSV_PATH
    assert window.kpi_labels["total"].text() != "—"
    assert set(window.overview_toolbar.button_map) == {
        "home",
        "back",
        "forward",
        "zoom_in",
        "zoom_out",
        "move_left",
        "move_right",
        "pan",
        "zoom",
        "reset",
        "save",
    }
    assert set(window.simulation_toolbar.button_map) == {
        "home",
        "back",
        "forward",
        "zoom_in",
        "zoom_out",
        "move_left",
        "move_right",
        "pan",
        "zoom",
        "reset",
        "save",
    }
    assert window.overview_scroll_area.widget() is window.overview_chart
    assert window.simulation_scroll_area.widget() is window.simulation_tab_content
    assert len(window.overview_chart.plot_axes) == 3
    assert len(window.simulation_chart.plot_axes) == 1
    assert window.overview_toolbar.button_map["zoom_in"].isEnabled() is True
    assert window.overview_toolbar.button_map["move_left"].isEnabled() is True
    assert window.simulation_toolbar.button_map["zoom_in"].isEnabled() is False
    assert window.simulation_toolbar.button_map["move_left"].isEnabled() is False
    assert window.simulation_toolbar.button_map["pan"].isEnabled() is False
    assert window.simulation_toolbar.button_map["zoom"].isEnabled() is False
    assert window.simulation_scroll_area.verticalScrollBarPolicy().name == "ScrollBarAsNeeded"
    assert window.ev_enabled_checkbox.isChecked() is False
    assert window.ev_daily_energy_spin.isEnabled() is False

    window.day_start_edit.setTime(QTime(8, 0))
    window.day_end_edit.setTime(QTime(20, 0))
    window.refresh_analysis()
    qapp.processEvents()

    assert window.filter_labels["range"].text() != "—"
    assert window.simulation_labels["savings"].text() != "—"
    assert window.base_rate_filter_spin.value() == pytest.approx(window.base_rate_sim_spin.value())


def test_overview_chart_hover_zoom_and_reset(loaded_window: ConsumptionMainWindow, qapp: QApplication) -> None:
    overview = loaded_window.overview_chart
    axis = overview.plot_axes[0]
    overview.canvas.draw()
    qapp.processEvents()

    x_values = overview._daily_data["x_values"]
    y_values = overview._daily_data["y_values"]
    x_value = x_values[0]
    y_value = y_values[0]
    initial_xlim = axis.get_xlim()

    _dispatch_mouse_event(overview.canvas, "motion_notify_event", axis, x_value, y_value)
    qapp.processEvents()

    annotation = overview.tooltip_annotations[axis]
    assert annotation.get_visible() is True
    assert "Consommation" in annotation.get_text()

    overview.toolbar.button_map["zoom"].click()
    qapp.processEvents()

    zoom_start_x = x_values[5]
    zoom_end_x = x_values[20]
    zoom_start_y = min(y_values)
    zoom_end_y = max(y_values) * 0.8
    _dispatch_mouse_event(
        overview.canvas,
        "button_press_event",
        axis,
        zoom_start_x,
        zoom_start_y,
        button=MouseButton.LEFT,
    )
    _dispatch_mouse_event(
        overview.canvas,
        "motion_notify_event",
        axis,
        zoom_end_x,
        zoom_end_y,
        button=MouseButton.LEFT,
    )
    _dispatch_mouse_event(
        overview.canvas,
        "button_release_event",
        axis,
        zoom_end_x,
        zoom_end_y,
        button=MouseButton.LEFT,
    )
    qapp.processEvents()

    zoomed_xlim = axis.get_xlim()
    zoomed_ylim = axis.get_ylim()
    assert (zoomed_xlim[1] - zoomed_xlim[0]) < (initial_xlim[1] - initial_xlim[0])

    reset_x = (zoomed_xlim[0] + zoomed_xlim[1]) / 2
    reset_y = (zoomed_ylim[0] + zoomed_ylim[1]) / 2
    _dispatch_mouse_event(
        overview.canvas,
        "button_press_event",
        axis,
        reset_x,
        reset_y,
        button=MouseButton.LEFT,
        dblclick=True,
    )
    qapp.processEvents()

    reset_xlim = axis.get_xlim()
    assert reset_xlim == pytest.approx(initial_xlim)


def test_input_fields_ignore_mouse_wheel(loaded_window: ConsumptionMainWindow) -> None:
    window = loaded_window

    initial_filter_rate = window.base_rate_filter_spin.value()
    filter_rate_event = DummyWheelEvent()
    window.base_rate_filter_spin.wheelEvent(filter_rate_event)
    assert filter_rate_event.ignored is True
    assert window.base_rate_filter_spin.value() == pytest.approx(initial_filter_rate)

    initial_start_date = window.start_date_edit.date()
    start_date_event = DummyWheelEvent()
    window.start_date_edit.wheelEvent(start_date_event)
    assert start_date_event.ignored is True
    assert window.start_date_edit.date() == initial_start_date

    initial_day_start = window.day_start_edit.time()
    day_start_event = DummyWheelEvent()
    window.day_start_edit.wheelEvent(day_start_event)
    assert day_start_event.ignored is True
    assert window.day_start_edit.time() == initial_day_start


def test_overview_chart_toolbar_zoom_and_move_buttons(loaded_window: ConsumptionMainWindow, qapp: QApplication) -> None:
    overview = loaded_window.overview_chart
    axis = overview.plot_axes[0]
    overview.canvas.draw()
    qapp.processEvents()

    initial_xlim = axis.get_xlim()
    overview.toolbar.button_map["zoom_in"].click()
    qapp.processEvents()

    zoomed_xlim = axis.get_xlim()
    assert (zoomed_xlim[1] - zoomed_xlim[0]) < (initial_xlim[1] - initial_xlim[0])

    overview.toolbar.button_map["move_right"].click()
    qapp.processEvents()

    moved_right_xlim = axis.get_xlim()
    assert moved_right_xlim[0] > zoomed_xlim[0]

    overview.toolbar.button_map["move_left"].click()
    qapp.processEvents()

    moved_left_xlim = axis.get_xlim()
    assert moved_left_xlim[0] < moved_right_xlim[0]

    overview.toolbar.button_map["zoom_out"].click()
    qapp.processEvents()

    zoomed_out_xlim = axis.get_xlim()
    assert (zoomed_out_xlim[1] - zoomed_out_xlim[0]) > (moved_left_xlim[1] - moved_left_xlim[0])


def test_overview_chart_navigation_is_limited_to_daily_axis(loaded_window: ConsumptionMainWindow, qapp: QApplication) -> None:
    overview = loaded_window.overview_chart
    daily_axis = overview.plot_axes[0]
    monthly_axis = overview.plot_axes[1]
    overview.canvas.draw()
    qapp.processEvents()

    daily_initial_xlim = daily_axis.get_xlim()
    monthly_initial_xlim = monthly_axis.get_xlim()

    _dispatch_mouse_event(
        overview.canvas,
        "scroll_event",
        monthly_axis,
        0.0,
        float(max(monthly_axis.get_ylim()) / 2.0),
        button="up",
        step=1,
    )
    qapp.processEvents()

    assert monthly_axis.get_xlim() == pytest.approx(monthly_initial_xlim)
    assert daily_axis.get_xlim() == pytest.approx(daily_initial_xlim)

    overview.toolbar.button_map["pan"].click()
    qapp.processEvents()

    start_x = overview._daily_data["x_values"][5]
    start_y = overview._daily_data["y_values"][5]
    initial_ylim = daily_axis.get_ylim()
    _dispatch_mouse_event(
        overview.canvas,
        "button_press_event",
        daily_axis,
        start_x,
        start_y,
        button=MouseButton.LEFT,
    )
    _dispatch_mouse_event(
        overview.canvas,
        "motion_notify_event",
        daily_axis,
        start_x + 2.0,
        start_y + 3.0,
        button=MouseButton.LEFT,
    )
    _dispatch_mouse_event(
        overview.canvas,
        "button_release_event",
        daily_axis,
        start_x + 2.0,
        start_y + 3.0,
        button=MouseButton.LEFT,
    )
    qapp.processEvents()

    assert daily_axis.get_xlim() != pytest.approx(daily_initial_xlim)
    assert daily_axis.get_ylim() == pytest.approx(initial_ylim)


def test_escape_leaves_zoom_mode(loaded_window: ConsumptionMainWindow, qapp: QApplication) -> None:
    overview = loaded_window.overview_chart
    overview.toolbar.button_map["zoom"].click()
    qapp.processEvents()

    assert overview.current_mode == "zoom"

    event = KeyEvent("key_press_event", overview.canvas, "escape")
    overview.canvas.callbacks.process("key_press_event", event)
    qapp.processEvents()

    assert overview.current_mode == "inspect"
    assert overview.toolbar.button_map["zoom"].isChecked() is False


def test_simulation_chart_legend_toggle(loaded_window: ConsumptionMainWindow, qapp: QApplication) -> None:
    simulation = loaded_window.simulation_chart
    simulation.canvas.draw()
    qapp.processEvents()

    legend_text = simulation._legend.get_texts()[3]
    pv_line = simulation._pv_line
    assert pv_line is not None and pv_line.get_visible() is True

    mouse_event = MouseEvent("button_press_event", simulation.canvas, 0, 0, button=MouseButton.LEFT)
    pick_event = PickEvent("pick_event", simulation.canvas, mouse_event, legend_text)
    simulation.canvas.callbacks.process("pick_event", pick_event)
    qapp.processEvents()

    assert pv_line.get_visible() is False
    assert legend_text.get_alpha() == pytest.approx(0.45)

    simulation.canvas.callbacks.process("pick_event", pick_event)
    qapp.processEvents()

    assert pv_line.get_visible() is True
    assert legend_text.get_alpha() == pytest.approx(1.0)


def test_simulation_chart_surplus_bars_are_negative_and_hoverable(
    loaded_window: ConsumptionMainWindow,
    qapp: QApplication,
) -> None:
    simulation = loaded_window.simulation_chart
    axis = simulation.plot_axes[0]
    simulation.canvas.draw()
    qapp.processEvents()

    assert "curtailed_kwh" in simulation._monthly_summary.columns
    assert any(value > 0 for value in simulation._monthly_summary["curtailed_kwh"].tolist())
    surplus_index = next(
        index
        for index, value in enumerate(simulation._monthly_summary["curtailed_kwh"].tolist())
        if value > 0
    )
    surplus_bar = simulation._curtailed_bars[surplus_index]

    assert surplus_bar.get_height() < 0
    assert surplus_bar.get_height() == pytest.approx(-simulation._monthly_summary["curtailed_kwh"].iloc[surplus_index])

    x_value = surplus_bar.get_x() + (surplus_bar.get_width() / 2)
    y_value = surplus_bar.get_y() + (surplus_bar.get_height() / 2)
    _dispatch_mouse_event(simulation.canvas, "motion_notify_event", axis, x_value, y_value)
    qapp.processEvents()

    annotation = simulation.tooltip_annotations[axis]
    assert annotation.get_visible() is True
    assert "Surplus perdu" in annotation.get_text()
    assert "-" in annotation.get_text()


def test_simulation_chart_surplus_legend_toggle(loaded_window: ConsumptionMainWindow, qapp: QApplication) -> None:
    simulation = loaded_window.simulation_chart
    simulation.canvas.draw()
    qapp.processEvents()

    legend_text = simulation._legend.get_texts()[2]
    assert any(bar.get_visible() for bar in simulation._curtailed_bars)

    mouse_event = MouseEvent("button_press_event", simulation.canvas, 0, 0, button=MouseButton.LEFT)
    pick_event = PickEvent("pick_event", simulation.canvas, mouse_event, legend_text)
    simulation.canvas.callbacks.process("pick_event", pick_event)
    qapp.processEvents()

    assert all(not bar.get_visible() for bar in simulation._curtailed_bars)
    assert legend_text.get_alpha() == pytest.approx(0.45)

    simulation.canvas.callbacks.process("pick_event", pick_event)
    qapp.processEvents()

    assert all(bar.get_visible() for bar in simulation._curtailed_bars)
    assert legend_text.get_alpha() == pytest.approx(1.0)


def test_simulation_chart_hover_works_with_only_surplus_visible(
    loaded_window: ConsumptionMainWindow,
    qapp: QApplication,
) -> None:
    simulation = loaded_window.simulation_chart
    axis = simulation.plot_axes[0]
    simulation.canvas.draw()
    qapp.processEvents()

    mouse_event = MouseEvent("button_press_event", simulation.canvas, 0, 0, button=MouseButton.LEFT)
    for legend_text in simulation._legend.get_texts()[0:2] + simulation._legend.get_texts()[3:5]:
        pick_event = PickEvent("pick_event", simulation.canvas, mouse_event, legend_text)
        simulation.canvas.callbacks.process("pick_event", pick_event)
    qapp.processEvents()

    assert all(not bar.get_visible() for bar in simulation._baseline_bars)
    assert all(not bar.get_visible() for bar in simulation._grid_bars)
    assert simulation._pv_line is not None and simulation._pv_line.get_visible() is False
    assert any(bar.get_visible() for bar in simulation._curtailed_bars)
    assert any(value > 0 for value in simulation._monthly_summary["curtailed_kwh"].tolist())

    surplus_index = next(
        index
        for index, value in enumerate(simulation._monthly_summary["curtailed_kwh"].tolist())
        if value > 0
    )
    surplus_bar = simulation._curtailed_bars[surplus_index]
    x_value = surplus_bar.get_x() + (surplus_bar.get_width() / 2)
    y_value = surplus_bar.get_y() + (surplus_bar.get_height() / 2)
    _dispatch_mouse_event(simulation.canvas, "motion_notify_event", axis, x_value, y_value)
    qapp.processEvents()

    annotation = simulation.tooltip_annotations[axis]
    assert annotation.get_visible() is True
    assert "Surplus perdu" in annotation.get_text()
    assert "Charge" not in annotation.get_text()
    assert "Production PV" not in annotation.get_text()


def test_ev_controls_and_chart_update_when_ev_is_enabled(
    loaded_window: ConsumptionMainWindow,
    qapp: QApplication,
) -> None:
    window = loaded_window
    window.ev_enabled_checkbox.setChecked(True)
    qapp.processEvents()

    assert window.ev_daily_energy_spin.isEnabled() is True

    window.ev_daily_energy_spin.setValue(12.0)
    window.ev_charge_power_spin.setValue(7.4)
    window.ev_start_time_edit.setTime(QTime(22, 0))
    window.ev_end_time_edit.setTime(QTime(6, 0))
    for button in window.ev_day_buttons:
        button.setChecked(True)

    window.run_simulation()
    qapp.processEvents()

    simulation = window.simulation_chart
    axis = simulation.plot_axes[0]
    simulation.canvas.draw()
    qapp.processEvents()

    assert window.simulation_labels["ev_charge"].text() != "â€”"
    assert "Recharge VE activee" in window.simulation_note_label.text()
    assert "ev_kwh" in simulation._monthly_summary.columns
    assert simulation._monthly_summary["ev_kwh"].sum() > 0
    assert simulation._ev_line is not None and simulation._ev_line.get_visible() is True

    first_index = int(simulation._monthly_summary["ev_kwh"].to_numpy(dtype=float).argmax())
    x_value = float(first_index)
    y_value = float(simulation._monthly_summary["ev_kwh"].iloc[first_index])
    _dispatch_mouse_event(simulation.canvas, "motion_notify_event", axis, x_value, y_value)
    qapp.processEvents()

    annotation = simulation.tooltip_annotations[axis]
    assert annotation.get_visible() is True
    assert "Recharge VE" in annotation.get_text()
