from __future__ import annotations

from PyQt6.QtWidgets import QDateEdit, QDoubleSpinBox, QTimeEdit


class _NoWheelMixin:
    def wheelEvent(self, event) -> None:  # noqa: N802 - Qt naming convention
        event.ignore()


class NoWheelDoubleSpinBox(_NoWheelMixin, QDoubleSpinBox):
    pass


class NoWheelDateEdit(_NoWheelMixin, QDateEdit):
    pass


class NoWheelTimeEdit(_NoWheelMixin, QTimeEdit):
    pass
