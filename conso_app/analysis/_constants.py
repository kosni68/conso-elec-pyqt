from __future__ import annotations

CSV_DELIMITER = ";"
CSV_DATE_FORMAT = "%d/%m/%Y %H:%M:%S"
HALF_HOUR_FREQUENCY = "30min"
INTERVAL_HOURS = 0.5
HALF_HOUR_SLOTS_PER_DAY = 48
DEFAULT_ENERGY_NAME = "Électricité"
DAY_LABEL = "Jour"
NIGHT_LABEL = "Nuit"

MONTHLY_PV_WEIGHTS = {
    1: 0.03,
    2: 0.05,
    3: 0.08,
    4: 0.11,
    5: 0.13,
    6: 0.14,
    7: 0.14,
    8: 0.12,
    9: 0.09,
    10: 0.06,
    11: 0.03,
    12: 0.02,
}

MONTHLY_SOLAR_WINDOWS = {
    1: ("08:00", "17:00"),
    2: ("07:30", "18:00"),
    3: ("07:00", "19:00"),
    4: ("06:30", "20:00"),
    5: ("06:00", "20:30"),
    6: ("05:30", "21:00"),
    7: ("06:00", "20:30"),
    8: ("06:30", "20:00"),
    9: ("07:00", "19:30"),
    10: ("07:30", "18:30"),
    11: ("08:00", "17:00"),
    12: ("08:30", "16:30"),
}
