from __future__ import annotations

import sys
from pathlib import Path

from PyQt6.QtWidgets import QApplication

from conso_app.ui import ConsumptionMainWindow


def _default_csv_path() -> Path | None:
    csv_files = sorted(Path.cwd().glob("*.csv"))
    return csv_files[0] if csv_files else None


def main() -> int:
    csv_path = Path(sys.argv[1]) if len(sys.argv) > 1 else _default_csv_path()
    app = QApplication(sys.argv)
    window = ConsumptionMainWindow(initial_csv_path=csv_path)
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
