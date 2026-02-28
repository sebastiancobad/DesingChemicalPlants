"""
ChemScale — API Router for Material Selection Module.

Endpoints:
    POST /api/v1/materials/assess     — Assess material for service
    GET  /api/v1/materials/list       — List available materials
    GET  /api/v1/materials/environments — List service environments
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Optional

from app.kernel.modules.materials.selection import (
    assess_material,
    MATERIAL_DB,
    CORROSION_RATES,
)

router = APIRouter(prefix="/api/v1/materials", tags=["Material Selection"])


class MaterialAssessRequest(BaseModel):
    material_designation: str = Field(..., description="ASME designation, e.g. 'SA-516-70'")
    environment: str = Field("clean_water", description="Service environment")
    design_temperature_c: float = Field(100.0, description="Design temperature in °C")
    design_life_years: int = Field(20, description="Design life in years")
    is_sour_service: bool = Field(False, description="NACE MR0175 sour service?")
    h2_partial_pressure_bar: float = Field(0.0, description="Hydrogen partial pressure in bar")


@router.post("/assess")
async def material_assess(req: MaterialAssessRequest) -> dict:
    result = assess_material(
        material_designation=req.material_designation,
        environment=req.environment,
        design_temperature_c=req.design_temperature_c,
        design_life_years=req.design_life_years,
        is_sour_service=req.is_sour_service,
        h2_partial_pressure_bar=req.h2_partial_pressure_bar,
    )
    mat = result.material
    return {
        "material": {
            "name": mat.name,
            "designation": mat.designation,
            "category": mat.category,
            "density_kgm3": mat.density_kgm3,
            "yield_strength_mpa": mat.yield_strength_mpa,
            "tensile_strength_mpa": mat.tensile_strength_mpa,
            "allowable_stress_mpa": mat.allowable_stress_mpa,
            "max_temperature_c": mat.max_temperature_c,
            "min_temperature_c": mat.min_temperature_c,
            "thermal_conductivity_wpmk": mat.thermal_conductivity_wpmk,
            "elastic_modulus_gpa": mat.elastic_modulus_gpa,
            "corrosion_allowance_mm": mat.corrosion_allowance_mm,
            "cost_factor": mat.cost_factor,
            "weldability": mat.weldability,
            "notes": mat.notes,
        },
        "environment": result.environment,
        "corrosion_rate_mmyr": result.corrosion_rate_mmyr,
        "design_life_years": result.design_life_years,
        "required_corrosion_allowance_mm": result.required_corrosion_allowance_mm,
        "temperature_ok": result.temperature_ok,
        "sour_service_ok": result.sour_service_ok,
        "sour_service_notes": result.sour_service_notes,
        "cost_relative": result.cost_relative,
        "recommended": result.recommended,
        "recommendation_notes": result.recommendation_notes,
        "alternatives": result.alternatives,
        "warnings": result.warnings,
        "standards_refs": result.standards_refs,
        "meta": {
            "calculation_id": str(uuid.uuid4()),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    }


@router.get("/list")
async def list_materials() -> list[dict]:
    return [
        {
            "designation": m.designation,
            "name": m.name,
            "category": m.category,
            "max_temp_c": m.max_temperature_c,
            "min_temp_c": m.min_temperature_c,
            "allowable_stress_mpa": m.allowable_stress_mpa,
            "cost_factor": m.cost_factor,
        }
        for m in MATERIAL_DB.values()
    ]


@router.get("/environments")
async def list_environments() -> list[str]:
    envs: set[str] = set()
    for rates in CORROSION_RATES.values():
        envs.update(rates.keys())
    return sorted(envs)
