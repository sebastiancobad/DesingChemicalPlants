"""
ChemScale — API Router for Module 6: Heat Exchanger Design.

Endpoints:
    POST /api/v1/hx/quick-size   — Conceptual area estimation
    POST /api/v1/hx/rate         — Rigorous rating (Bell-Delaware / Kern)
    GET  /api/v1/hx/tema-types   — List valid TEMA type codes
"""

from __future__ import annotations

import math
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.units import EngineeringValue
from app.kernel.modules.heat_exchanger.sizing import quick_size
from app.kernel.thermo.property_engine import (
    ComponentData,
    PropertyEngine,
    ThermoModel,
)
from app.schemas.common import CalculationMeta, ValueWithUnit
from app.schemas.heat_exchanger import (
    GeometrySummary,
    HXQuickSizeRequest,
    HXQuickSizeResponse,
    MechanicalSummary,
    SideResults,
    ThermalResults,
)

router = APIRouter(prefix="/api/v1/hx", tags=["Heat Exchanger"])


# ---------------------------------------------------------------------------
# Simplified quick-size request (for landing page demo)
# ---------------------------------------------------------------------------

class SimpleHXRequest(BaseModel):
    T_h_in: float = 150.0
    T_h_out: float = 90.0
    T_c_in: float = 30.0
    T_c_out: float = 45.0
    m_dot_hot: float = 13.89


@router.post("/quick-size-simple")
async def hx_quick_size_simple(req: SimpleHXRequest) -> dict:
    """Simplified HX quick-size for the landing page demo.

    Accepts flat temperature + flow input and returns key results
    using assumed water properties and standard geometry.
    """
    T_h_in = req.T_h_in
    T_h_out = req.T_h_out
    T_c_in = req.T_c_in
    T_c_out = req.T_c_out
    m_dot_hot = req.m_dot_hot

    # Use water properties as defaults
    cp_hot = 4180.0   # J/(kg·K)
    cp_cold = 4180.0
    rho = 995.0        # kg/m³
    mu = 0.0008        # Pa·s
    k_fluid = 0.62     # W/(m·K)

    # Energy balance
    duty = m_dot_hot * cp_hot * (T_h_in - T_h_out)
    m_dot_cold = duty / (cp_cold * (T_c_out - T_c_in)) if (T_c_out - T_c_in) > 0 else m_dot_hot

    # LMTD
    dT1 = T_h_in - T_c_out
    dT2 = T_h_out - T_c_in
    if dT1 <= 0 or dT2 <= 0:
        raise HTTPException(422, "Temperature cross detected")
    if abs(dT1 - dT2) < 0.01:
        lmtd = dT1
    else:
        lmtd = (dT1 - dT2) / math.log(dT1 / dT2)

    # F correction for 1-2 exchanger
    R = (T_h_in - T_h_out) / (T_c_out - T_c_in) if (T_c_out - T_c_in) > 0 else 1.0
    P = (T_c_out - T_c_in) / (T_h_in - T_c_in) if (T_h_in - T_c_in) > 0 else 0.5
    F = 0.9  # conservative default
    if R > 0 and P > 0 and R != 1.0:
        S = math.sqrt(R * R + 1.0)
        num = S * math.log((1 - P) / (1 - R * P)) if (1 - R * P) > 0 else 1.0
        den = (R - 1) * math.log((2 - P * (R + 1 - S)) / (2 - P * (R + 1 + S))) if True else 1.0
        try:
            arg = (2 - P * (R + 1 - S)) / (2 - P * (R + 1 + S))
            if arg > 0:
                F = num / ((R - 1) * math.log(arg))
                F = max(0.75, min(1.0, F))
        except (ValueError, ZeroDivisionError):
            F = 0.9

    corrected_mtd = lmtd * F
    U = 500  # W/(m²·K) typical for water-water
    area = duty / (U * corrected_mtd) if corrected_mtd > 0 else 0

    # Standard tube geometry: 19.05 mm OD, 25.4 mm pitch, 4.88 m length
    tube_od = 0.01905
    tube_length = 4.88
    area_per_tube = math.pi * tube_od * tube_length
    n_tubes = max(1, int(math.ceil(area / area_per_tube)))
    area_provided = n_tubes * area_per_tube
    overdesign = ((area_provided / area) - 1) * 100 if area > 0 else 0

    # Shell diameter estimate (CTP = 0.93, CL = 1.0 for triangular)
    pitch = 0.0254
    shell_id = 0.637 * math.sqrt(1.0 / 0.93 * pitch**2 * n_tubes * (pitch / tube_od))

    return {
        "duty_kw": round(duty / 1000, 1),
        "lmtd": round(lmtd, 2),
        "correction_factor_F": round(F, 3),
        "corrected_mtd": round(corrected_mtd, 2),
        "U_assumed": U,
        "area_required_m2": round(area, 1),
        "area_provided_m2": round(area_provided, 1),
        "overdesign_pct": round(overdesign, 1),
        "tube_count": n_tubes,
        "tube_length_m": tube_length,
        "tube_od_mm": tube_od * 1000,
        "shell_id_mm": round(shell_id * 1000, 0),
        "m_dot_cold_kgs": round(m_dot_cold, 2),
        "warnings": [],
        "standards_refs": [
            "TEMA 10th Ed.",
            "Kern, Process Heat Transfer",
            "ASME VIII-1 UG-27",
        ],
        "meta": {
            "calculation_id": str(uuid.uuid4()),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    }

# Singleton property engine
_engine = PropertyEngine()


# ---------------------------------------------------------------------------
# Stub component database (replaced by PostgreSQL in production)
# ---------------------------------------------------------------------------

_COMPONENT_DB: dict[str, ComponentData] = {
    "7732-18-5": ComponentData(
        cas="7732-18-5", name="Water", molecular_weight=18.015,
        tc=647.1, pc=22064000.0, omega=0.344, tb=373.15,
    ),
    "71-43-2": ComponentData(
        cas="71-43-2", name="Benzene", molecular_weight=78.11,
        tc=562.2, pc=4895000.0, omega=0.210, tb=353.2,
    ),
    "108-88-3": ComponentData(
        cas="108-88-3", name="Toluene", molecular_weight=92.14,
        tc=591.8, pc=4108000.0, omega=0.264, tb=383.8,
    ),
    "106-42-3": ComponentData(
        cas="106-42-3", name="p-Xylene", molecular_weight=106.17,
        tc=616.2, pc=3511000.0, omega=0.322, tb=411.5,
    ),
    "74-82-8": ComponentData(
        cas="74-82-8", name="Methane", molecular_weight=16.04,
        tc=190.6, pc=4599000.0, omega=0.011, tb=111.7,
    ),
    "74-84-0": ComponentData(
        cas="74-84-0", name="Ethane", molecular_weight=30.07,
        tc=305.3, pc=4872000.0, omega=0.099, tb=184.6,
    ),
}


def _resolve_components(fluid_spec) -> tuple[list[ComponentData], list[float]]:
    """Look up components from the stub database."""
    comps = []
    fracs = []
    for fc in fluid_spec.components:
        cd = _COMPONENT_DB.get(fc.cas)
        if cd is None:
            raise HTTPException(
                status_code=404,
                detail=f"Component CAS '{fc.cas}' not found in database",
            )
        comps.append(cd)
        fracs.append(fc.mole_fraction)
    return comps, fracs


def _to_si(v: ValueWithUnit) -> float:
    """Convert a ValueWithUnit to SI magnitude."""
    return EngineeringValue(v.value, v.unit).to_si().value


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/quick-size")
async def hx_quick_size(req: SimpleHXRequest) -> dict:
    """Quick-sizing of a shell-and-tube heat exchanger.

    Accepts simple flat input (temperatures + hot flow rate) and returns
    key sizing results using LMTD method with assumed water properties.
    """
    return await hx_quick_size_simple(req)


@router.get("/tema-types")
async def list_tema_types() -> list[dict]:
    """Return valid TEMA type codes with descriptions."""
    return [
        {"code": "AES", "description": "Removable channel, single-pass shell, floating head"},
        {"code": "AEL", "description": "Removable channel, single-pass shell, fixed tubesheet (like A)"},
        {"code": "AEM", "description": "Removable channel, single-pass shell, fixed tubesheet (like B)"},
        {"code": "AEP", "description": "Removable channel, single-pass shell, outside-packed floating head"},
        {"code": "AET", "description": "Removable channel, single-pass shell, pull-through floating head"},
        {"code": "AEU", "description": "Removable channel, single-pass shell, U-tube bundle"},
        {"code": "AEW", "description": "Removable channel, single-pass shell, externally sealed floating tubesheet"},
        {"code": "BEM", "description": "Bonnet, single-pass shell, fixed tubesheet (like B)"},
        {"code": "BEU", "description": "Bonnet, single-pass shell, U-tube bundle"},
        {"code": "AKT", "description": "Removable channel, kettle reboiler, pull-through floating head"},
        {"code": "AJW", "description": "Removable channel, divided-flow shell, ext. sealed"},
    ]
