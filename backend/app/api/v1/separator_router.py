"""
ChemScale — API Router for Phase Separator Module.

Endpoints:
    POST /api/v1/separator/size   — Two-phase separator sizing
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Optional

from app.kernel.modules.separator.sizing import size_separator

router = APIRouter(prefix="/api/v1/separator", tags=["Phase Separator"])


class SeparatorSizeRequest(BaseModel):
    gas_flow_m3s: float = Field(..., description="Gas volumetric flow at operating conditions in m³/s")
    liquid_flow_m3s: float = Field(..., description="Liquid volumetric flow in m³/s")
    rho_gas: float = Field(..., description="Gas density in kg/m³")
    rho_liquid: float = Field(..., description="Liquid density in kg/m³")
    mu_gas: float = Field(..., description="Gas viscosity in Pa·s")
    operating_pressure_pa: float = Field(..., description="Operating pressure in Pa (absolute)")
    operating_temperature_k: float = Field(300.0, description="Operating temperature in K")
    orientation: str = Field("vertical", description="Vessel orientation: vertical or horizontal")
    residence_time_s: float = Field(180.0, description="Liquid residence time in seconds")
    droplet_diameter_um: float = Field(150.0, description="Design droplet diameter in micrometers")
    has_mist_eliminator: bool = Field(True, description="Include wire mesh mist eliminator")
    l_over_d_target: float = Field(3.0, description="Target length-to-diameter ratio")
    design_pressure_pa: Optional[float] = Field(None, description="Design pressure in Pa (auto if None)")
    corrosion_allowance_m: float = Field(0.003, description="Corrosion allowance in m")


@router.post("/size")
async def separator_size(req: SeparatorSizeRequest) -> dict:
    result = size_separator(
        gas_flow_m3s=req.gas_flow_m3s,
        liquid_flow_m3s=req.liquid_flow_m3s,
        rho_gas=req.rho_gas,
        rho_liquid=req.rho_liquid,
        mu_gas=req.mu_gas,
        operating_pressure_pa=req.operating_pressure_pa,
        operating_temperature_k=req.operating_temperature_k,
        orientation=req.orientation,
        residence_time_s=req.residence_time_s,
        droplet_diameter_um=req.droplet_diameter_um,
        has_mist_eliminator=req.has_mist_eliminator,
        l_over_d_target=req.l_over_d_target,
        design_pressure_pa=req.design_pressure_pa,
        corrosion_allowance_m=req.corrosion_allowance_m,
    )
    return {
        "orientation": result.orientation,
        "vessel_diameter_m": result.vessel_diameter_m,
        "vessel_length_m": result.vessel_length_m,
        "l_over_d_ratio": result.l_over_d_ratio,
        "settling_velocity_ms": result.settling_velocity_ms,
        "droplet_diameter_um": result.droplet_diameter_um,
        "gas_velocity_ms": result.gas_velocity_ms,
        "gas_velocity_max_ms": result.gas_velocity_max_ms,
        "k_factor": result.k_factor,
        "liquid_residence_time_s": result.liquid_residence_time_s,
        "liquid_volume_m3": result.liquid_volume_m3,
        "vessel_volume_m3": result.vessel_volume_m3,
        "liquid_level_pct": result.liquid_level_pct,
        "mist_eliminator": result.mist_eliminator,
        "wall_thickness_mm": result.wall_thickness_mm,
        "vessel_weight_kg": result.vessel_weight_kg,
        "warnings": result.warnings,
        "standards_refs": result.standards_refs,
        "meta": {
            "calculation_id": str(uuid.uuid4()),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    }
