from __future__ import annotations

import os
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

pytest.importorskip("PyQt6")

from PyQt6.QtCore import QTime
from PyQt6.QtWidgets import QApplication

from conso_app.ui import ConsumptionMainWindow


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REAL_CSV_PATH = PROJECT_ROOT / "112486686-DUBOIS-NICOLAS heure.csv"


@pytest.fixture()
def qapp() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_main_window_loads_csv_and_refreshes(qapp: QApplication) -> None:
    window = ConsumptionMainWindow(initial_csv_path=REAL_CSV_PATH)
    qapp.processEvents()

    assert window.raw_df is not None
    assert window.analysis_summary is not None
    assert window.simulation_result is not None
    assert window.kpi_labels["total"].text() != "—"

    window.day_start_edit.setTime(QTime(8, 0))
    window.day_end_edit.setTime(QTime(20, 0))
    window.refresh_analysis()
    qapp.processEvents()

    assert window.filter_labels["range"].text() != "—"
    assert window.simulation_labels["savings"].text() != "—"
    assert window.base_rate_filter_spin.value() == pytest.approx(window.base_rate_sim_spin.value())

    window.close()
