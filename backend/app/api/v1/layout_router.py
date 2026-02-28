"""
ChemScale — API Router for Plant Layout Module.

Endpoints:
    POST /api/v1/layout/check        — Check equipment spacing
    GET  /api/v1/layout/equipment-types — List equipment types
    GET  /api/v1/layout/spacing-table — Full spacing reference
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Optional

from app.kernel.modules.layout.spacing import (
    check_layout,
    EQUIPMENT_RISK,
    SPACING_TABLE,
)

router = APIRouter(prefix="/api/v1/layout", tags=["Plant Layout"])


class EquipmentItem(BaseModel):
    tag: str = Field(..., description="Equipment tag, e.g. 'E-101'")
    type: str = Field(..., description="Equipment type, e.g. 'heat_exchanger'")


class ProposedDistance(BaseModel):
    from_tag: str
    to_tag: str
    distance_m: float


class LayoutCheckRequest(BaseModel):
    equipment_list: list[EquipmentItem]
    proposed_distances: Optional[list[ProposedDistance]] = None


@router.post("/check")
async def layout_check(req: LayoutCheckRequest) -> dict:
    equip_list = [{"tag": e.tag, "type": e.type} for e in req.equipment_list]
    proposed = None
    if req.proposed_distances:
        proposed = [
            {"from_tag": d.from_tag, "to_tag": d.to_tag, "distance_m": d.distance_m}
            for d in req.proposed_distances
        ]

    result = check_layout(equip_list, proposed)

    return {
        "spacing_checks": [
            {
                "equipment_a": s.equipment_a,
                "equipment_b": s.equipment_b,
                "minimum_distance_m": s.minimum_distance_m,
                "risk_level_a": s.risk_level_a,
                "risk_level_b": s.risk_level_b,
                "governing_standard": s.governing_standard,
                "notes": s.notes,
            }
            for s in result.spacing_checks
        ],
        "total_violations": result.total_violations,
        "plot_area_estimate_m2": result.plot_area_estimate_m2,
        "plot_dimensions_m": result.plot_dimensions_m,
        "equipment_list": result.equipment_list,
        "warnings": result.warnings,
        "standards_refs": result.standards_refs,
        "meta": {
            "calculation_id": str(uuid.uuid4()),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    }


@router.get("/equipment-types")
async def equipment_types() -> dict:
    return EQUIPMENT_RISK


@router.get("/spacing-table")
async def spacing_table() -> list[dict]:
    return [
        {"from": a, "to": b, "min_distance_m": d}
        for (a, b), d in SPACING_TABLE.items()
    ]
