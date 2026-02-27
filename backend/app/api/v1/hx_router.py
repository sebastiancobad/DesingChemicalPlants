"""
ChemScale — API Router for Module 6: Heat Exchanger Design.

Endpoints:
    POST /api/v1/hx/quick-size   — Conceptual area estimation
    POST /api/v1/hx/rate         — Rigorous rating (Bell-Delaware / Kern)
    GET  /api/v1/hx/tema-types   — List valid TEMA type codes
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException

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

@router.post("/quick-size", response_model=HXQuickSizeResponse)
async def hx_quick_size(req: HXQuickSizeRequest) -> HXQuickSizeResponse:
    """Conceptual quick-sizing of a shell-and-tube heat exchanger.

    Uses Kern method for shell-side, Dittus-Boelter for tube-side,
    and LMTD method for area estimation.
    """
    # Resolve fluids
    hot_comps, hot_z = _resolve_components(req.hot_side.fluid)
    cold_comps, cold_z = _resolve_components(req.cold_side.fluid)

    model_hot = ThermoModel(req.hot_side.fluid.thermo_model)
    model_cold = ThermoModel(req.cold_side.fluid.thermo_model)

    T_h_in = _to_si(req.hot_side.inlet_temperature)
    T_h_out = _to_si(req.hot_side.outlet_temperature) if req.hot_side.outlet_temperature else None
    T_c_in = _to_si(req.cold_side.inlet_temperature)
    T_c_out = _to_si(req.cold_side.outlet_temperature) if req.cold_side.outlet_temperature else None

    m_hot = _to_si(req.hot_side.mass_flow_rate) if req.hot_side.mass_flow_rate else None
    m_cold = _to_si(req.cold_side.mass_flow_rate) if req.cold_side.mass_flow_rate else None

    if T_h_out is None or m_hot is None:
        raise HTTPException(422, "Hot-side outlet temperature and mass flow are required")

    P_hot = _to_si(req.hot_side.inlet_pressure)
    P_cold = _to_si(req.cold_side.inlet_pressure)

    # Get thermodynamic properties at mean conditions
    T_hot_mean = (T_h_in + T_h_out) / 2.0
    T_cold_mean = (T_c_in + (T_c_out or T_c_in + 15)) / 2.0

    props_hot = _engine.calculate(hot_comps, hot_z, T_hot_mean, P_hot, model_hot)
    props_cold = _engine.calculate(cold_comps, cold_z, T_cold_mean, P_cold, model_cold)

    # Extract liquid-phase properties (assume liquid for sizing)
    hp = props_hot.flash.phases[0]
    cp_ = props_cold.flash.phases[0]

    mw_hot = hp.molecular_weight_mix or 18.015
    mw_cold = cp_.molecular_weight_mix or 18.015

    # Convert molar Cp to mass Cp
    cp_hot_mass = hp.heat_capacity_cp / (mw_hot / 1000.0)
    cp_cold_mass = cp_.heat_capacity_cp / (mw_cold / 1000.0)

    gc = req.geometry_constraints

    result = quick_size(
        T_h_in=T_h_in, T_h_out=T_h_out,
        T_c_in=T_c_in, T_c_out=T_c_out,
        m_dot_hot=m_hot, m_dot_cold=m_cold,
        rho_hot=hp.density, mu_hot=hp.viscosity,
        cp_hot=cp_hot_mass, k_hot=hp.thermal_conductivity,
        rho_cold=cp_.density, mu_cold=cp_.viscosity,
        cp_cold=cp_cold_mass, k_cold=cp_.thermal_conductivity,
        Rf_hot=_to_si(req.hot_side.fouling_resistance),
        Rf_cold=_to_si(req.cold_side.fouling_resistance),
        tube_od=_to_si(gc.tube_od),
        tube_pitch=_to_si(gc.tube_pitch),
        tube_length=_to_si(gc.max_tube_length),
        tube_layout=gc.tube_layout.value,
        n_shell_passes=gc.num_shell_passes,
        n_tube_passes=gc.num_tube_passes,
        baffle_cut=gc.baffle_cut,
        design_pressure_shell=_to_si(req.design_conditions.shell_design_pressure),
        design_pressure_tube=_to_si(req.design_conditions.tube_design_pressure),
        corrosion_allowance=_to_si(req.design_conditions.corrosion_allowance),
    )

    # Build response
    calc_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()

    return HXQuickSizeResponse(
        tag=req.tag,
        tema_type=req.tema_type,
        thermal_results=ThermalResults(
            duty=ValueWithUnit(value=round(result.duty_w / 1e3, 1), unit="kW"),
            lmtd=ValueWithUnit(value=round(result.lmtd_k, 2), unit="K"),
            correction_factor_F=round(result.correction_factor_F, 3),
            corrected_mtd=ValueWithUnit(value=round(result.corrected_mtd_k, 2), unit="K"),
            overall_U_assumed=ValueWithUnit(value=result.U_assumed, unit="W/(m²·K)"),
            overall_U_clean=ValueWithUnit(value=round(result.U_clean, 1), unit="W/(m²·K)"),
            overall_U_dirty=ValueWithUnit(value=round(result.U_dirty, 1), unit="W/(m²·K)"),
            area_required=ValueWithUnit(value=round(result.area_required_m2, 1), unit="m²"),
            area_provided=ValueWithUnit(value=round(result.area_provided_m2, 1), unit="m²"),
            overdesign_pct=round(result.overdesign_pct, 1),
        ),
        hot_side_results=SideResults(
            velocity=ValueWithUnit(value=round(result.hot_velocity_ms, 2), unit="m/s"),
            reynolds=round(result.hot_reynolds, 0),
            pressure_drop=ValueWithUnit(value=round(result.hot_dp_pa / 1e3, 1), unit="kPa"),
            heat_transfer_coeff=ValueWithUnit(value=round(result.hot_htc, 0), unit="W/(m²·K)"),
        ),
        cold_side_results=SideResults(
            mass_flow_rate=(
                ValueWithUnit(value=round(result.cold_mass_flow_kgs * 3600, 1), unit="kg/h")
                if result.cold_mass_flow_kgs else None
            ),
            velocity=ValueWithUnit(value=round(result.cold_velocity_ms, 2), unit="m/s"),
            reynolds=round(result.cold_reynolds, 0),
            pressure_drop=ValueWithUnit(value=round(result.cold_dp_pa / 1e3, 1), unit="kPa"),
            heat_transfer_coeff=ValueWithUnit(value=round(result.cold_htc, 0), unit="W/(m²·K)"),
        ),
        geometry_summary=GeometrySummary(
            shell_id=ValueWithUnit(value=round(result.shell_id_m * 1e3, 0), unit="mm"),
            tube_count=result.tube_count,
            tube_length=ValueWithUnit(value=round(result.tube_length_m, 3), unit="m"),
            tube_od=ValueWithUnit(value=round(gc.tube_od.value, 2), unit=gc.tube_od.unit),
            tube_pitch=ValueWithUnit(value=round(gc.tube_pitch.value, 1), unit=gc.tube_pitch.unit),
            baffle_spacing=ValueWithUnit(value=round(result.baffle_spacing_m * 1e3, 0), unit="mm"),
            baffle_count=result.baffle_count,
            num_shell_passes=gc.num_shell_passes,
            num_tube_passes=gc.num_tube_passes,
        ),
        mechanical_summary=MechanicalSummary(
            shell_min_thickness=ValueWithUnit(
                value=round(result.shell_min_thickness_m * 1e3, 2), unit="mm"
            ),
            tube_sheet_thickness=ValueWithUnit(
                value=round(result.tubesheet_thickness_m * 1e3, 1), unit="mm"
            ),
            shell_weight_empty=ValueWithUnit(value=round(result.shell_weight_kg, 0), unit="kg"),
            bundle_weight=ValueWithUnit(value=round(result.bundle_weight_kg, 0), unit="kg"),
        ),
        warnings=result.warnings,
        meta=CalculationMeta(
            calculation_id=calc_id,
            timestamp=now,
            standards_references=result.standards_refs,
        ),
    )


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
