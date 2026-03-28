from __future__ import annotations


def fr_number(value: float, decimals: int = 2) -> str:
    formatted = f"{value:,.{decimals}f}"
    return formatted.replace(",", " ").replace(".", ",")


def format_kwh(value: float) -> str:
    return f"{fr_number(value, 2)} kWh"


def format_currency(value: float) -> str:
    return f"{fr_number(value, 2)} €"


def format_percent(value: float) -> str:
    return f"{fr_number(value * 100.0, 1)} %"
