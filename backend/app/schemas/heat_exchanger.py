"""
ChemScale — Pydantic schemas for Module 6: Heat Exchanger Design.

Covers quick-sizing, rigorous rating, and iterative design endpoints.
"""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field

from .common import CalculationMeta, FluidSpec, ValueWithUnit


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class HXType(str, Enum):
    SHELL_AND_TUBE = "shell_and_tube"
    AIR_COOLER = "air_cooler"
    PLATE = "plate"
    DOUBLE_PIPE = "double_pipe"


class TubeLayout(str, Enum):
    TRIANGULAR_30 = "triangular_30"
    TRIANGULAR_60 = "triangular_60"
    SQUARE_90 = "square_90"
    ROTATED_SQUARE_45 = "rotated_square_45"


class RatingMethod(str, Enum):
    KERN = "kern"
    BELL_DELAWARE = "bell_delaware"


class RatingMode(str, Enum):
    CHECK_RATING = "check_rating"
    SIMULATION = "simulation"


# ---------------------------------------------------------------------------
# Input schemas
# ---------------------------------------------------------------------------

class ProcessSide(BaseModel):
    """One side (hot or cold) of the heat exchanger."""

    fluid: FluidSpec
    inlet_temperature: ValueWithUnit
    outlet_temperature: Optional[ValueWithUnit] = None
    mass_flow_rate: Optional[ValueWithUnit] = None
    inlet_pressure: ValueWithUnit
    fouling_resistance: ValueWithUnit = Field(
        default=ValueWithUnit(value=0.000176, unit="m²·K/W"),
        description="Fouling resistance per TEMA Table RGP-T-2.4",
    )
    max_pressure_drop: Optional[ValueWithUnit] = None


class GeometryConstraints(BaseModel):
    """Geometry parameters for quick-sizing (constraints / defaults)."""

    max_tube_length: ValueWithUnit = ValueWithUnit(value=6.096, unit="m")
    tube_od: ValueWithUnit = ValueWithUnit(value=19.05, unit="mm")
    tube_pitch: ValueWithUnit = ValueWithUnit(value=25.4, unit="mm")
    tube_layout: TubeLayout = TubeLayout.TRIANGULAR_30
    baffle_cut: float = Field(default=0.25, ge=0.15, le=0.45)
    num_shell_passes: int = Field(default=1, ge=1, le=4)
    num_tube_passes: int = Field(default=2, ge=1, le=16)


class FullGeometry(BaseModel):
    """Exact geometry for rigorous rating."""

    shell_id: ValueWithUnit
    tube_count: int
    tube_od: ValueWithUnit
    tube_id: ValueWithUnit
    tube_length: ValueWithUnit
    tube_pitch: ValueWithUnit
    tube_layout: TubeLayout = TubeLayout.TRIANGULAR_30
    baffle_cut: float = Field(default=0.25, ge=0.15, le=0.45)
    baffle_spacing: ValueWithUnit
    num_shell_passes: int = Field(default=1, ge=1, le=4)
    num_tube_passes: int = Field(default=2, ge=1, le=16)
    seal_strips: int = Field(default=1, ge=0)
    tube_to_baffle_clearance: Optional[ValueWithUnit] = None
    shell_to_baffle_clearance: Optional[ValueWithUnit] = None


class DesignConditions(BaseModel):
    """Mechanical design conditions per ASME Sec VIII."""

    shell_design_pressure: ValueWithUnit
    tube_design_pressure: ValueWithUnit
    shell_design_temperature: ValueWithUnit
    tube_design_temperature: ValueWithUnit
    shell_material: str = "SA-516-70"
    tube_material: str = "SA-179"
    corrosion_allowance: ValueWithUnit = ValueWithUnit(value=3.0, unit="mm")


class HXQuickSizeRequest(BaseModel):
    """Input for the conceptual quick-sizing endpoint."""

    project_id: str
    tag: str = Field(..., description="Equipment tag, e.g. 'E-101'")
    hx_type: HXType = HXType.SHELL_AND_TUBE
    tema_type: str = Field(default="AES", max_length=3, min_length=3)

    hot_side: ProcessSide
    cold_side: ProcessSide
    geometry_constraints: GeometryConstraints = GeometryConstraints()
    design_conditions: DesignConditions

    output_units: str = "SI"


class HXRateRequest(BaseModel):
    """Input for the rigorous rating endpoint."""

    project_id: str
    tag: str
    rating_mode: RatingMode = RatingMode.CHECK_RATING
    hx_type: HXType = HXType.SHELL_AND_TUBE
    tema_type: str = Field(default="AES", max_length=3, min_length=3)

    hot_side: ProcessSide
    cold_side: ProcessSide
    geometry: FullGeometry
    method: RatingMethod = RatingMethod.BELL_DELAWARE
    zone_analysis: bool = False
    design_conditions: DesignConditions

    output_units: str = "SI"


# ---------------------------------------------------------------------------
# Output schemas
# ---------------------------------------------------------------------------

class ThermalResults(BaseModel):
    duty: ValueWithUnit
    lmtd: ValueWithUnit
    correction_factor_F: float
    corrected_mtd: ValueWithUnit
    overall_U_assumed: Optional[ValueWithUnit] = None
    overall_U_clean: ValueWithUnit
    overall_U_dirty: ValueWithUnit
    area_required: ValueWithUnit
    area_provided: ValueWithUnit
    overdesign_pct: float


class SideResults(BaseModel):
    mass_flow_rate: Optional[ValueWithUnit] = None
    velocity: ValueWithUnit
    reynolds: float
    pressure_drop: ValueWithUnit
    heat_transfer_coeff: ValueWithUnit


class GeometrySummary(BaseModel):
    shell_id: ValueWithUnit
    tube_count: int
    tube_length: ValueWithUnit
    tube_od: ValueWithUnit
    tube_pitch: ValueWithUnit
    baffle_spacing: ValueWithUnit
    baffle_count: int
    num_shell_passes: int
    num_tube_passes: int


class MechanicalSummary(BaseModel):
    shell_min_thickness: ValueWithUnit
    tube_sheet_thickness: ValueWithUnit
    shell_weight_empty: ValueWithUnit
    bundle_weight: ValueWithUnit


class BellDelawareDetails(BaseModel):
    j_h_ideal: float
    j_c_baffle_cut: float
    j_l_leakage: float
    j_b_bypass: float
    j_s_spacing: float
    j_r_adverse: float
    h_shell_corrected: ValueWithUnit


class ZoneResult(BaseModel):
    zone: int
    zone_type: str
    duty_fraction: float
    t_hot_in: float
    t_hot_out: float
    t_cold_in: float
    t_cold_out: float
    U_zone: float
    area_zone: float


class VibrationCheck(BaseModel):
    natural_frequency_hz: float
    critical_velocity_ms: float
    actual_crossflow_velocity_ms: float
    status: str
    margin_pct: float


class HXQuickSizeResponse(BaseModel):
    status: str = "success"
    tag: str
    tema_type: str

    thermal_results: ThermalResults
    cold_side_results: SideResults
    hot_side_results: SideResults
    geometry_summary: GeometrySummary
    mechanical_summary: MechanicalSummary

    warnings: list[str] = Field(default_factory=list)
    meta: CalculationMeta


class HXRateResponse(HXQuickSizeResponse):
    bell_delaware_details: Optional[BellDelawareDetails] = None
    zone_analysis_results: Optional[list[ZoneResult]] = None
    vibration_check: Optional[VibrationCheck] = None
