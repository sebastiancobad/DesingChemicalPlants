"""
ChemScale — API Router for Pump Sizing Module.

Endpoints:
    POST /api/v1/pump/size   — Centrifugal pump sizing
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Optional

from app.kernel.modules.pump.sizing import size_pump

router = APIRouter(prefix="/api/v1/pump", tags=["Pump Sizing"])


class PumpSizeRequest(BaseModel):
    flow_rate_m3h: float = Field(..., description="Volumetric flow rate in m³/h")
    density_kgm3: float = Field(..., description="Fluid density in kg/m³")
    viscosity_pas: float = Field(..., description="Dynamic viscosity in Pa·s")
    suction_pressure_pa: float = Field(101325.0, description="Suction pressure in Pa (absolute)")
    discharge_pressure_pa: float = Field(500000.0, description="Discharge pressure in Pa (absolute)")
    static_head_m: float = Field(0.0, description="Static head (elevation difference) in m")
    friction_loss_m: float = Field(0.0, description="Friction losses in piping in m of head")
    suction_pipe_id_m: float = Field(0.1, description="Suction pipe ID in m")
    discharge_pipe_id_m: float = Field(0.075, description="Discharge pipe ID in m")
    vapor_pressure_pa: float = Field(2340.0, description="Fluid vapor pressure in Pa at operating T")
    suction_vessel_elevation_m: float = Field(0.0, description="Suction vessel liquid level elevation in m")
    pump_elevation_m: float = Field(0.0, description="Pump centerline elevation in m")
    speed_rpm: float = Field(3550.0, description="Pump speed in RPM")
    motor_efficiency_pct: float = Field(93.0, description="Motor efficiency in %")


@router.post("/size")
async def pump_size(req: PumpSizeRequest) -> dict:
    result = size_pump(
        flow_rate_m3h=req.flow_rate_m3h,
        density_kgm3=req.density_kgm3,
        viscosity_pas=req.viscosity_pas,
        suction_pressure_pa=req.suction_pressure_pa,
        discharge_pressure_pa=req.discharge_pressure_pa,
        static_head_m=req.static_head_m,
        friction_loss_m=req.friction_loss_m,
        suction_pipe_id_m=req.suction_pipe_id_m,
        discharge_pipe_id_m=req.discharge_pipe_id_m,
        vapor_pressure_pa=req.vapor_pressure_pa,
        suction_vessel_elevation_m=req.suction_vessel_elevation_m,
        pump_elevation_m=req.pump_elevation_m,
        speed_rpm=req.speed_rpm,
        motor_efficiency_pct=req.motor_efficiency_pct,
    )
    return {
        "flow_rate_m3h": result.flow_rate_m3h,
        "total_dynamic_head_m": result.total_dynamic_head_m,
        "static_head_m": result.static_head_m,
        "friction_head_m": result.friction_head_m,
        "velocity_head_m": result.velocity_head_m,
        "pressure_head_m": result.pressure_head_m,
        "hydraulic_power_kw": result.hydraulic_power_kw,
        "efficiency_pct": result.efficiency_pct,
        "brake_power_kw": result.brake_power_kw,
        "motor_power_kw": result.motor_power_kw,
        "motor_efficiency_pct": result.motor_efficiency_pct,
        "npsh_available_m": result.npsh_available_m,
        "npsh_required_m": result.npsh_required_m,
        "npsh_margin_m": result.npsh_margin_m,
        "npsh_ok": result.npsh_ok,
        "specific_speed": result.specific_speed,
        "pump_type_suggestion": result.pump_type_suggestion,
        "suction_velocity_ms": result.suction_velocity_ms,
        "discharge_velocity_ms": result.discharge_velocity_ms,
        "warnings": result.warnings,
        "standards_refs": result.standards_refs,
        "meta": {
            "calculation_id": str(uuid.uuid4()),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    }
