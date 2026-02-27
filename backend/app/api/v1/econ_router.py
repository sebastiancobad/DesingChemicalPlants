"""
ChemScale — API Router for Module 12: Economic Evaluation & Utilities.

Endpoints:
    POST /api/v1/econ/capex/equipment  — Single equipment CAPEX
    POST /api/v1/econ/capex/project    — Total project CAPEX (Lang)
    POST /api/v1/econ/opex/evaluate    — Annual OPEX breakdown
    GET  /api/v1/econ/cost-indices     — Historical CEPCI values
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter

from app.kernel.modules.economics.cost_engine import (
    equipment_capex,
    evaluate_opex,
    project_capex,
)
from app.schemas.common import CalculationMeta, ValueWithUnit
from app.schemas.economics import (
    CapitalCostSummary,
    CostBreakdown,
    DirectCosts,
    EquipmentCapexRequest,
    EquipmentCapexResponse,
    IndirectCosts,
    LaborCost,
    OpexBreakdown,
    OpexRequest,
    OpexResponse,
    ProjectCapexRequest,
    ProjectCapexResponse,
    SensitivityResult,
    SixTenthsCheck,
    UtilityCostBreakdown,
)

router = APIRouter(prefix="/api/v1/econ", tags=["Economic Evaluation"])


@router.post("/capex/equipment", response_model=EquipmentCapexResponse)
async def calc_equipment_capex(req: EquipmentCapexRequest) -> EquipmentCapexResponse:
    """Estimate bare-module cost for a single piece of equipment."""
    sp = req.sizing_parameters

    # Determine the capacity value based on equipment type
    capacity = 0.0
    if sp.heat_transfer_area:
        from app.core.units import EngineeringValue
        capacity = EngineeringValue(sp.heat_transfer_area.value, sp.heat_transfer_area.unit).to_si().value
    elif sp.power:
        from app.core.units import EngineeringValue
        capacity = EngineeringValue(sp.power.value, sp.power.unit).to_si().value / 1e3  # kW
    elif sp.volume:
        from app.core.units import EngineeringValue
        capacity = EngineeringValue(sp.volume.value, sp.volume.unit).to_si().value

    # Design pressure in barg
    dp_barg = 10.0
    if sp.design_pressure:
        from app.core.units import EngineeringValue
        dp_pa = EngineeringValue(sp.design_pressure.value, sp.design_pressure.unit).to_si().value
        dp_barg = (dp_pa - 101325.0) / 1e5

    shell_mat = (sp.shell_material or "CS").split("-")[0][:2] if sp.shell_material else "CS"
    tube_mat = (sp.tube_material or "CS").split("-")[0][:2] if sp.tube_material else "CS"

    result = equipment_capex(
        equipment_type=req.equipment_type,
        capacity=capacity,
        design_pressure_barg=dp_barg,
        shell_material=shell_mat,
        tube_material=tube_mat,
        base_cepci=req.cost_basis.base_cepci,
        target_cepci=req.cost_basis.target_cepci,
        location_factor=req.cost_basis.location_factor,
        base_cost_override=req.overrides.base_cost_usd,
        material_factor_override=req.overrides.material_factor,
        pressure_factor_override=req.overrides.pressure_factor,
    )

    calc_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()

    six_tenths = None
    if result.six_tenths_cost is not None:
        six_tenths = SixTenthsCheck(
            reference_capacity=ValueWithUnit(value=capacity, unit="m²"),
            reference_cost=ValueWithUnit(value=round(result.base_cost_usd, 0), unit="USD"),
            exponent=result.six_tenths_exponent or 0.6,
            scaled_cost=ValueWithUnit(value=round(result.six_tenths_cost, 0), unit="USD"),
            note=result.six_tenths_note,
        )

    return EquipmentCapexResponse(
        equipment_tag=req.equipment_tag,
        equipment_type=req.equipment_type,
        cost_breakdown=CostBreakdown(
            base_cost=ValueWithUnit(value=round(result.base_cost_usd, 0), unit="USD"),
            material_factor_Fm=result.material_factor,
            pressure_factor_Fp=round(result.pressure_factor, 3),
            bare_module_factor_Fbm=result.bare_module_factor,
            bare_module_cost_base_year=ValueWithUnit(
                value=round(result.bare_module_cost_base_year, 0), unit="USD"
            ),
            cepci_escalation_factor=round(result.cepci_escalation, 3),
            bare_module_cost_target_year=ValueWithUnit(
                value=round(result.bare_module_cost_target_year, 0), unit="USD"
            ),
            location_adjusted=ValueWithUnit(
                value=round(result.location_adjusted, 0), unit="USD"
            ),
        ),
        six_tenths_check=six_tenths,
        method_references=result.references,
        meta=CalculationMeta(
            calculation_id=calc_id,
            timestamp=now,
            standards_references=result.references,
        ),
    )


@router.post("/capex/project", response_model=ProjectCapexResponse)
async def calc_project_capex(req: ProjectCapexRequest) -> ProjectCapexResponse:
    """Total project capital cost using Lang / detailed factors."""
    equip_costs = [e.bare_module_cost for e in req.equipment_list]

    lang = req.lang_method.lang_factor
    factors = req.lang_method.factors.model_dump() if req.lang_method.use_detailed_factors else None

    land_val = req.grassroots_extras.land.value if req.grassroots_extras.land else 0
    offsite_val = req.grassroots_extras.offsite_facilities.value if req.grassroots_extras.offsite_facilities else 0

    result = project_capex(
        equipment_costs=equip_costs,
        lang_factor=lang,
        factors=factors,
        land=land_val,
        offsite_facilities=offsite_val,
    )

    calc_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()

    dc = result.direct_costs
    ic = result.indirect_costs

    return ProjectCapexResponse(
        project_name=req.project_name,
        total_bare_module_cost=ValueWithUnit(
            value=round(result.total_bare_module, 0), unit=req.currency
        ),
        capital_cost_summary=CapitalCostSummary(
            direct_costs=DirectCosts(
                purchased_equipment=dc.get("purchased_equipment", 0),
                installation=dc.get("installation", 0),
                instrumentation=dc.get("instrumentation", 0),
                piping=dc.get("piping", 0),
                electrical=dc.get("electrical", 0),
                subtotal_direct=dc.get("subtotal_direct", sum(dc.values())),
            ),
            indirect_costs=IndirectCosts(
                buildings=ic.get("buildings", 0),
                yard_improvements=ic.get("yard_improvements", 0),
                service_facilities=ic.get("service_facilities", 0),
                engineering_supervision=ic.get("engineering_supervision", 0),
                construction=ic.get("construction", 0),
                legal_fees=ic.get("legal_fees", 0),
                contractor_fee=ic.get("contractor_fee", 0),
                contingency=ic.get("contingency", 0),
                subtotal_indirect=ic.get("subtotal_indirect", sum(ic.values())),
            ),
            fixed_capital_investment=round(result.fixed_capital_investment, 0),
            working_capital=round(result.working_capital, 0),
            land=result.land,
            offsite_facilities=result.offsite_facilities,
            total_capital_investment=ValueWithUnit(
                value=round(result.total_capital_investment, 0), unit=req.currency
            ),
        ),
        effective_lang_factor=round(result.effective_lang_factor, 2),
        sensitivity=SensitivityResult(
            capex_minus_20pct=round(result.total_capital_investment * 0.8, 0),
            capex_plus_20pct=round(result.total_capital_investment * 1.2, 0),
            contingency_range="Class 4 estimate (±30%) per AACE 18R-97",
        ),
        meta=CalculationMeta(
            calculation_id=calc_id,
            timestamp=now,
            standards_references=result.references,
        ),
    )


@router.post("/opex/evaluate", response_model=OpexResponse)
async def calc_opex(req: OpexRequest) -> OpexResponse:
    """Annual operating expenditure evaluation."""
    # Prepare raw materials in SI-friendly form
    raw_mats = []
    for rm in req.raw_materials:
        raw_mats.append({
            "rate_si": rm.consumption_rate.value,
            "unit_cost_per_si": rm.unit_cost.value,
        })

    # Utilities
    utils: dict[str, dict] = {}
    for name in ["steam_hp", "steam_mp", "steam_lp", "cooling_water", "electricity", "fuel_gas"]:
        spec = getattr(req.utilities, name, None)
        if spec:
            utils[name] = {
                "demand_si": spec.demand.value,
                "unit_cost_per_si": spec.unit_cost.value,
            }

    result = evaluate_opex(
        annual_hours=req.annual_operating_hours,
        raw_materials=raw_mats,
        utilities=utils,
        operators_per_shift=req.labor.operators_per_shift,
        shifts_per_day=req.labor.shifts_per_day,
        annual_salary=req.labor.annual_salary_usd,
        overhead_factor=req.labor.overhead_factor,
        fci=req.maintenance.fci_usd,
        maintenance_pct=req.maintenance.percentage,
        insurance_tax_pct=req.insurance_and_taxes.percentage,
        depreciable_capital=req.depreciation.depreciable_capital,
        salvage_value=req.depreciation.salvage_value,
        useful_life_years=req.depreciation.useful_life_years,
    )

    calc_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()

    # Build utility breakdown
    uc = result.utility_costs
    util_breakdown = UtilityCostBreakdown(
        steam_hp=ValueWithUnit(value=round(uc.get("steam_hp", 0), 0), unit=f"{req.currency}/yr") if "steam_hp" in uc else None,
        steam_mp=ValueWithUnit(value=round(uc.get("steam_mp", 0), 0), unit=f"{req.currency}/yr") if "steam_mp" in uc else None,
        steam_lp=ValueWithUnit(value=round(uc.get("steam_lp", 0), 0), unit=f"{req.currency}/yr") if "steam_lp" in uc else None,
        cooling_water=ValueWithUnit(value=round(uc.get("cooling_water", 0), 0), unit=f"{req.currency}/yr") if "cooling_water" in uc else None,
        electricity=ValueWithUnit(value=round(uc.get("electricity", 0), 0), unit=f"{req.currency}/yr") if "electricity" in uc else None,
        fuel_gas=ValueWithUnit(value=round(uc.get("fuel_gas", 0), 0), unit=f"{req.currency}/yr") if "fuel_gas" in uc else None,
        subtotal_util=ValueWithUnit(value=round(result.total_utility_cost, 0), unit=f"{req.currency}/yr"),
    )

    return OpexResponse(
        annual_operating_hours=req.annual_operating_hours,
        opex_breakdown=OpexBreakdown(
            raw_materials=ValueWithUnit(
                value=round(result.raw_materials_cost, 0), unit=f"{req.currency}/yr"
            ),
            utilities=util_breakdown,
            labor=LaborCost(
                operating_labor=ValueWithUnit(
                    value=round(result.operating_labor, 0), unit=f"{req.currency}/yr"
                ),
                with_overhead=ValueWithUnit(
                    value=round(result.labor_with_overhead, 0), unit=f"{req.currency}/yr"
                ),
            ),
            maintenance=ValueWithUnit(
                value=round(result.maintenance, 0), unit=f"{req.currency}/yr"
            ),
            insurance_and_taxes=ValueWithUnit(
                value=round(result.insurance_taxes, 0), unit=f"{req.currency}/yr"
            ),
            depreciation=ValueWithUnit(
                value=round(result.depreciation, 0), unit=f"{req.currency}/yr"
            ),
            total_opex=ValueWithUnit(
                value=round(result.total_opex, 0), unit=f"{req.currency}/yr"
            ),
        ),
        meta=CalculationMeta(
            calculation_id=calc_id,
            timestamp=now,
            standards_references=result.references,
        ),
    )


@router.get("/cost-indices")
async def cost_indices() -> list[dict]:
    """Historical CEPCI and Nelson-Farrar cost indices."""
    return [
        {"year": 2000, "cepci": 394.1, "nelson_farrar": 1542},
        {"year": 2005, "cepci": 468.2, "nelson_farrar": 1918},
        {"year": 2010, "cepci": 550.8, "nelson_farrar": 2269},
        {"year": 2015, "cepci": 556.8, "nelson_farrar": 2352},
        {"year": 2020, "cepci": 596.2, "nelson_farrar": 2478},
        {"year": 2024, "cepci": 790.1, "nelson_farrar": 3102},
        {"year": 2026, "cepci": 823.5, "nelson_farrar": 3250, "note": "estimated"},
    ]
