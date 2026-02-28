"""
ChemScale — Central Unit Conversion Service.

All internal calculations operate in SI base units. This module handles
conversion at the system boundary (input ingestion and output formatting).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class EngineeringValue:
    """A numeric value paired with its unit of measure."""

    value: float
    unit: str

    def to_si(self) -> "EngineeringValue":
        """Convert to the canonical SI unit for this quantity."""
        factor, offset, si_unit = _CONVERSION_TABLE.get(
            self.unit, (1.0, 0.0, self.unit)
        )
        return EngineeringValue(
            value=self.value * factor + offset,
            unit=si_unit,
        )

    def from_si(self, target_unit: str) -> "EngineeringValue":
        """Convert from SI to a target unit."""
        factor, offset, _ = _CONVERSION_TABLE.get(
            target_unit, (1.0, 0.0, target_unit)
        )
        return EngineeringValue(
            value=(self.value - offset) / factor,
            unit=target_unit,
        )


# ---------------------------------------------------------------------------
# Conversion table: unit_string -> (multiply, offset, si_unit)
#
# value_SI = value_input * multiply + offset
# ---------------------------------------------------------------------------
_CONVERSION_TABLE: dict[str, tuple[float, float, str]] = {
    # --- Temperature ---
    "K":   (1.0, 0.0, "K"),
    "°C":  (1.0, 273.15, "K"),
    "°F":  (5.0 / 9.0, 255.3722, "K"),
    "R":   (5.0 / 9.0, 0.0, "K"),
    # --- Pressure ---
    "Pa":    (1.0, 0.0, "Pa"),
    "kPa":   (1e3, 0.0, "Pa"),
    "kPa_g": (1e3, 101325.0, "Pa"),  # gauge to absolute
    "MPa":   (1e6, 0.0, "Pa"),
    "bar":   (1e5, 0.0, "Pa"),
    "barg":  (1e5, 101325.0, "Pa"),
    "psi":   (6894.757, 0.0, "Pa"),
    "psig":  (6894.757, 101325.0, "Pa"),
    "atm":   (101325.0, 0.0, "Pa"),
    "mmHg":  (133.322, 0.0, "Pa"),
    # --- Length ---
    "m":    (1.0, 0.0, "m"),
    "mm":   (1e-3, 0.0, "m"),
    "cm":   (1e-2, 0.0, "m"),
    "in":   (0.0254, 0.0, "m"),
    "ft":   (0.3048, 0.0, "m"),
    # --- Mass ---
    "kg":   (1.0, 0.0, "kg"),
    "g":    (1e-3, 0.0, "kg"),
    "lb":   (0.453592, 0.0, "kg"),
    "tonne": (1e3, 0.0, "kg"),
    # --- Mass flow ---
    "kg/h":  (1.0 / 3600.0, 0.0, "kg/s"),
    "kg/s":  (1.0, 0.0, "kg/s"),
    "lb/h":  (0.453592 / 3600.0, 0.0, "kg/s"),
    "tonne/h": (1e3 / 3600.0, 0.0, "kg/s"),
    # --- Volumetric flow ---
    "m³/h":  (1.0 / 3600.0, 0.0, "m³/s"),
    "m³/s":  (1.0, 0.0, "m³/s"),
    "bbl/day": (0.158987 / 86400.0, 0.0, "m³/s"),
    # --- Area ---
    "m²":   (1.0, 0.0, "m²"),
    "ft²":  (0.092903, 0.0, "m²"),
    # --- Power / Duty ---
    "W":     (1.0, 0.0, "W"),
    "kW":    (1e3, 0.0, "W"),
    "MW":    (1e6, 0.0, "W"),
    "BTU/h": (0.293071, 0.0, "W"),
    "hp":    (745.7, 0.0, "W"),
    # --- Heat transfer coefficient ---
    "W/(m²·K)":     (1.0, 0.0, "W/(m²·K)"),
    "BTU/(h·ft²·°F)": (5.678, 0.0, "W/(m²·K)"),
    # --- Fouling resistance ---
    "m²·K/W":       (1.0, 0.0, "m²·K/W"),
    "h·ft²·°F/BTU": (0.17611, 0.0, "m²·K/W"),
    # --- Velocity ---
    "m/s":  (1.0, 0.0, "m/s"),
    "ft/s": (0.3048, 0.0, "m/s"),
    # --- Viscosity ---
    "Pa·s":  (1.0, 0.0, "Pa·s"),
    "cP":    (1e-3, 0.0, "Pa·s"),
    "mPa·s": (1e-3, 0.0, "Pa·s"),
    # --- Density ---
    "kg/m³":  (1.0, 0.0, "kg/m³"),
    "lb/ft³": (16.0185, 0.0, "kg/m³"),
    # --- Thermal conductivity ---
    "W/(m·K)":       (1.0, 0.0, "W/(m·K)"),
    "BTU/(h·ft·°F)": (1.7307, 0.0, "W/(m·K)"),
    # --- Energy ---
    "J":     (1.0, 0.0, "J"),
    "kJ":    (1e3, 0.0, "J"),
    "MJ":    (1e6, 0.0, "J"),
    "BTU":   (1055.06, 0.0, "J"),
    "kcal":  (4184.0, 0.0, "J"),
}


def convert(value: float, from_unit: str, to_unit: str) -> float:
    """Convert a scalar value between two units."""
    si = EngineeringValue(value, from_unit).to_si()
    return si.from_si(to_unit).value
