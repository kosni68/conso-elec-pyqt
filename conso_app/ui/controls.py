from __future__ import annotations

from datetime import date
from pathlib import Path

from PyQt6.QtCore import QDate, QSignalBlocker, Qt, QTime, pyqtSignal
from PyQt6.QtWidgets import (
    QDateEdit,
    QDoubleSpinBox,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTimeEdit,
    QVBoxLayout,
    QWidget,
)

from ..analysis import AnalysisSummary
from ..models import DEFAULT_BASE_RATE_EUR_KWH, TariffConfig
from ..theme import BORDER_COLOR, CARD_BACKGROUND, TEXT_MUTED, TEXT_PRIMARY
from .formatting import format_currency, format_kwh, format_percent

EMPTY_VALUE = "—"


class FileSelectionBar(QWidget):
    browse_requested = pyqtSignal()
    reload_requested = pyqtSignal(str)

    def __init__(self) -> None:
        super().__init__()
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        label = QLabel("Fichier CSV")
        label.setStyleSheet(f"font-weight: 600; color: {TEXT_PRIMARY};")

        self.file_path_edit = QLineEdit()
        self.file_path_edit.setPlaceholderText("Choisir un export CSV Linky ou équivalent")
        self.file_path_edit.returnPressed.connect(self._emit_reload_requested)

        browse_button = QPushButton("Parcourir…")
        browse_button.clicked.connect(self.browse_requested.emit)
        reload_button = QPushButton("Recharger")
        reload_button.clicked.connect(self._emit_reload_requested)

        layout.addWidget(label)
        layout.addWidget(self.file_path_edit, stretch=1)
        layout.addWidget(browse_button)
        layout.addWidget(reload_button)

    def current_path_text(self) -> str:
        return self.file_path_edit.text().strip()

    def set_file_path(self, path: Path | str) -> None:
        self.file_path_edit.setText(str(path))

    def _emit_reload_requested(self) -> None:
        self.reload_requested.emit(self.current_path_text())


class KpiPanel(QWidget):
    def __init__(self) -> None:
        super().__init__()
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        self.value_labels: dict[str, QLabel] = {}
        cards = [
            ("total", "Consommation filtrée"),
            ("average", "Moyenne / jour"),
            ("cost", "Coût base estimé"),
            ("day", "Part jour"),
            ("night", "Part nuit"),
        ]
        for key, title in cards:
            frame = QFrame()
            frame.setFrameShape(QFrame.Shape.StyledPanel)
            frame.setStyleSheet(
                f"QFrame {{ background: {CARD_BACKGROUND}; border: 1px solid {BORDER_COLOR}; border-radius: 10px; }}"
            )
            frame_layout = QVBoxLayout(frame)
            frame_layout.setContentsMargins(14, 12, 14, 12)
            frame_layout.setSpacing(4)

            title_label = QLabel(title)
            title_label.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 12px;")
            value_label = QLabel(EMPTY_VALUE)
            value_label.setStyleSheet(f"font-size: 22px; font-weight: 700; color: {TEXT_PRIMARY};")
            self.value_labels[key] = value_label

            frame_layout.addWidget(title_label)
            frame_layout.addWidget(value_label)
            layout.addWidget(frame)

    def update_summary(self, summary: AnalysisSummary) -> None:
        self.value_labels["total"].setText(format_kwh(summary.total_kwh))
        self.value_labels["average"].setText(format_kwh(summary.average_daily_kwh))
        self.value_labels["cost"].setText(format_currency(summary.cost_eur))
        self.value_labels["day"].setText(format_percent(summary.day_kwh / summary.total_kwh if summary.total_kwh else 0.0))
        self.value_labels["night"].setText(
            format_percent(summary.night_kwh / summary.total_kwh if summary.total_kwh else 0.0)
        )


class FilterPanel(QWidget):
    apply_requested = pyqtSignal()
    reset_requested = pyqtSignal()
    base_rate_changed = pyqtSignal(float)

    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        controls_box = QGroupBox("Paramètres d'analyse")
        controls_layout = QGridLayout(controls_box)
        controls_layout.setHorizontalSpacing(14)
        controls_layout.setVerticalSpacing(10)

        self.start_date_edit = QDateEdit(calendarPopup=True)
        self.end_date_edit = QDateEdit(calendarPopup=True)
        self.start_date_edit.setDisplayFormat("dd/MM/yyyy")
        self.end_date_edit.setDisplayFormat("dd/MM/yyyy")
        self.day_start_edit = QTimeEdit(QTime(7, 0))
        self.day_end_edit = QTimeEdit(QTime(22, 0))
        self.day_start_edit.setDisplayFormat("HH:mm")
        self.day_end_edit.setDisplayFormat("HH:mm")
        self.base_rate_spin = self._make_spinbox(0.0, 5.0, 4, DEFAULT_BASE_RATE_EUR_KWH, suffix=" €/kWh")
        self.base_rate_spin.valueChanged.connect(self.base_rate_changed.emit)

        apply_button = QPushButton("Appliquer les filtres")
        apply_button.clicked.connect(self.apply_requested.emit)
        reset_button = QPushButton("Réinitialiser")
        reset_button.clicked.connect(self.reset_requested.emit)

        controls_layout.addWidget(QLabel("Date de début"), 0, 0)
        controls_layout.addWidget(self.start_date_edit, 0, 1)
        controls_layout.addWidget(QLabel("Date de fin"), 0, 2)
        controls_layout.addWidget(self.end_date_edit, 0, 3)
        controls_layout.addWidget(QLabel("Début jour"), 1, 0)
        controls_layout.addWidget(self.day_start_edit, 1, 1)
        controls_layout.addWidget(QLabel("Fin jour"), 1, 2)
        controls_layout.addWidget(self.day_end_edit, 1, 3)
        controls_layout.addWidget(QLabel("Tarif base"), 2, 0)
        controls_layout.addWidget(self.base_rate_spin, 2, 1)
        controls_layout.addWidget(apply_button, 2, 2)
        controls_layout.addWidget(reset_button, 2, 3)

        summary_box = QGroupBox("Synthèse du filtre")
        summary_layout = QGridLayout(summary_box)
        summary_layout.setHorizontalSpacing(20)
        summary_layout.setVerticalSpacing(8)

        self.summary_labels: dict[str, QLabel] = {}
        info_rows = [
            ("range", "Période affichée"),
            ("days", "Nombre de jours"),
            ("intervals", "Pas de 30 min"),
            ("imputed", "Pas reconstitués"),
        ]
        for row_index, (key, title) in enumerate(info_rows):
            title_label = QLabel(title)
            title_label.setStyleSheet(f"color: {TEXT_MUTED};")
            value_label = QLabel(EMPTY_VALUE)
            value_label.setStyleSheet("font-weight: 600;")
            self.summary_labels[key] = value_label
            summary_layout.addWidget(title_label, row_index, 0)
            summary_layout.addWidget(value_label, row_index, 1)

        self.note_label = QLabel(
            "Le filtre jour/nuit est analytique : il découpe les consommations mais n'applique pas de tarif HP/HC."
        )
        self.note_label.setWordWrap(True)
        self.note_label.setStyleSheet(f"color: {TEXT_MUTED};")

        layout.addWidget(controls_box)
        layout.addWidget(summary_box)
        layout.addWidget(self.note_label)
        layout.addStretch(1)

    def set_date_bounds(self, min_date: date, max_date: date, *, reset_selection: bool) -> None:
        min_qdate = QDate(min_date.year, min_date.month, min_date.day)
        max_qdate = QDate(max_date.year, max_date.month, max_date.day)
        for widget in (self.start_date_edit, self.end_date_edit):
            widget.setDateRange(min_qdate, max_qdate)
        if reset_selection:
            self.start_date_edit.setDate(min_qdate)
            self.end_date_edit.setDate(max_qdate)

    def reset_controls(self, min_date: date, max_date: date) -> None:
        self.set_date_bounds(min_date, max_date, reset_selection=True)
        self.day_start_edit.setTime(QTime(7, 0))
        self.day_end_edit.setTime(QTime(22, 0))
        self.set_base_rate(DEFAULT_BASE_RATE_EUR_KWH)
        self.base_rate_changed.emit(self.base_rate_spin.value())

    def current_tariff(self) -> TariffConfig:
        return TariffConfig(
            mode="base",
            base_rate_eur_kwh=self.base_rate_spin.value(),
            day_start=self.day_start_edit.time().toPyTime(),
            day_end=self.day_end_edit.time().toPyTime(),
        )

    def selected_dates(self) -> tuple[date, date]:
        return self.start_date_edit.date().toPyDate(), self.end_date_edit.date().toPyDate()

    def set_base_rate(self, value: float) -> None:
        with QSignalBlocker(self.base_rate_spin):
            self.base_rate_spin.setValue(value)

    def update_summary(self, summary: AnalysisSummary) -> None:
        if summary.filtered_df.empty:
            self.clear_summary()
            return

        start = summary.filtered_df.index.min().strftime("%d/%m/%Y")
        end = summary.filtered_df.index.max().strftime("%d/%m/%Y")
        self.summary_labels["range"].setText(f"{start} → {end}")
        self.summary_labels["days"].setText(str(summary.daily_totals.shape[0]))
        self.summary_labels["intervals"].setText(str(summary.filtered_df.shape[0]))
        self.summary_labels["imputed"].setText(str(int(summary.filtered_df["is_imputed"].sum())))

    def clear_summary(self) -> None:
        for label in self.summary_labels.values():
            label.setText(EMPTY_VALUE)

    @staticmethod
    def _make_spinbox(
        minimum: float,
        maximum: float,
        decimals: int,
        value: float,
        suffix: str = "",
    ) -> QDoubleSpinBox:
        widget = QDoubleSpinBox()
        widget.setRange(minimum, maximum)
        widget.setDecimals(decimals)
        widget.setValue(value)
        widget.setSuffix(suffix)
        widget.setAlignment(Qt.AlignmentFlag.AlignRight)
        widget.setSingleStep(0.1 if decimals else 1.0)
        return widget
