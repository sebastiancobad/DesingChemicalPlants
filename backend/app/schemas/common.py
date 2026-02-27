"""
ChemScale — Shared Pydantic schemas used across all modules.
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field, field_validator


class ValueWithUnit(BaseModel):
    """A numeric engineering value with its unit of measure."""

    value: float
    unit: str


class FluidComponent(BaseModel):
    """A single component in a fluid mixture."""

    cas: str = Field(..., description="CAS Registry Number, e.g. '7732-18-5'")
    name: str
    mole_fraction: float = Field(..., ge=0.0, le=1.0)


class FluidSpec(BaseModel):
    """Specification of a process fluid (components + thermo model)."""

    components: list[FluidComponent]
    thermo_model: str = Field(
        default="PR",
        description="Thermodynamic model: PR, SRK, NRTL, UNIQUAC, WILSON, IAPWS97",
    )

    @field_validator("components")
    @classmethod
    def fractions_must_sum_to_one(cls, v: list[FluidComponent]) -> list[FluidComponent]:
        total = sum(c.mole_fraction for c in v)
        if abs(total - 1.0) > 1e-4:
            raise ValueError(f"Mole fractions must sum to 1.0, got {total:.6f}")
        return v


class CalculationMeta(BaseModel):
    """Metadata attached to every calculation response."""

    calculation_id: str
    calc_version: str = "0.1.0"
    timestamp: str
    standards_references: list[str] = Field(default_factory=list)
