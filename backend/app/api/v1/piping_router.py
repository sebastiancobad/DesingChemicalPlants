"""
ChemScale — API Router for Piping Module.

Endpoints:
    POST /api/v1/piping/size         — Pipe sizing and pressure drop
    GET  /api/v1/piping/schedules    — Available pipe schedules
    GET  /api/v1/piping/fittings     — K-values for fittings
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Optional

from app.kernel.modules.piping.sizing import (
    size_pipe,
    PIPE_SCHEDULES,
    FITTING_K_VALUES,
)

router = APIRouter(prefix="/api/v1/piping", tags=["Piping"])


class PipeSizeRequest(BaseModel):
    mass_flow_kgs: float = Field(..., description="Mass flow rate in kg/s")
    density_kgm3: float = Field(..., description="Fluid density in kg/m³")
    viscosity_pas: float = Field(..., description="Dynamic viscosity in Pa·s")
    pipe_length_m: float = Field(100.0, description="Straight pipe length in m")
    elevation_change_m: float = Field(0.0, description="Elevation change in m (positive = uphill)")
    roughness_m: float = Field(0.000046, description="Pipe roughness in m (CS default)")
    schedule: str = Field("SCH 40", description="Pipe schedule")
    nps: Optional[str] = Field(None, description="Nominal pipe size (auto-select if None)")
    fluid_phase: str = Field("liquid", description="Phase: liquid or gas")
    max_velocity_ms: Optional[float] = Field(None, description="Max allowable velocity in m/s")
    fittings: Optional[dict[str, int]] = Field(None, description="Fitting counts, e.g. {'90_elbow_std': 4}")


@router.post("/size")
async def pipe_size(req: PipeSizeRequest) -> dict:
    result = size_pipe(
        mass_flow_kgs=req.mass_flow_kgs,
        density_kgm3=req.density_kgm3,
        viscosity_pas=req.viscosity_pas,
        pipe_length_m=req.pipe_length_m,
        elevation_change_m=req.elevation_change_m,
        roughness_m=req.roughness_m,
        schedule=req.schedule,
        nps=req.nps,
        fittings=req.fittings,
        fluid_phase=req.fluid_phase,
        max_velocity_ms=req.max_velocity_ms,
    )
    return {
        "nps": result.nps,
        "schedule": result.schedule,
        "outer_diameter_mm": result.outer_diameter_mm,
        "wall_thickness_mm": result.wall_thickness_mm,
        "inner_diameter_mm": round(result.inner_diameter_mm, 2),
        "flow_area_m2": round(result.flow_area_m2, 6),
        "velocity_ms": round(result.velocity_ms, 3),
        "reynolds": round(result.reynolds, 0),
        "friction_factor": round(result.friction_factor, 6),
        "pressure_drop_pa_per_m": round(result.pressure_drop_pa_per_m, 2),
        "total_pressure_drop_kpa": round(result.total_pressure_drop_pa / 1000, 2),
        "pipe_length_m": result.pipe_length_m,
        "equivalent_length_fittings_m": round(result.equivalent_length_fittings_m, 1),
        "total_equivalent_length_m": round(result.total_equivalent_length_m, 1),
        "velocity_ok": result.velocity_ok,
        "velocity_message": result.velocity_message,
        "warnings": result.warnings,
        "standards_refs": result.standards_refs,
        "meta": {
            "calculation_id": str(uuid.uuid4()),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    }


@router.get("/schedules")
async def list_schedules() -> dict:
    return {
        sched: {nps: {"od_mm": od, "wt_mm": wt} for nps, (od, wt) in sizes.items()}
        for sched, sizes in PIPE_SCHEDULES.items()
    }


@router.get("/fittings")
async def list_fittings() -> dict:
    return FITTING_K_VALUES
