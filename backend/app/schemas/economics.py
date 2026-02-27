"""
ChemScale — Pydantic schemas for Module 12: Economic Evaluation & Utilities.

Covers equipment CAPEX, project CAPEX (Lang factor), OPEX evaluation,
cash-flow analysis, and utility demand calculators.
"""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field

from .common import CalculationMeta, ValueWithUnit


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class CostMethod(str, Enum):
    GUTHRIE_BARE_MODULE = "guthrie_bare_module"
    SIX_TENTHS = "six_tenths"
    VENDOR_QUOTE = "vendor_quote"


class DepreciationMethod(str, Enum):
    STRAIGHT_LINE = "straight_line"
    MACRS = "macrs"
    DECLINING_BALANCE = "declining_balance"


class SteamHeader(str, Enum):
    HP = "HP"
    MP = "MP"
    LP = "LP"


# ---------------------------------------------------------------------------
# Equipment CAPEX
# ---------------------------------------------------------------------------

class CostBasis(BaseModel):
    method: CostMethod = CostMethod.GUTHRIE_BARE_MODULE
    base_year: int = 2020
    base_cepci: float = 596.2
    target_year: int = 2026
    target_cepci: float = 823.5
    location_factor: float = Field(default=1.0, ge=0.5, le=3.0)
    currency: str = "USD"


class EquipmentSizingParams(BaseModel):
    """Size-dependent parameters for cost correlation lookup."""

    heat_transfer_area: Optional[ValueWithUnit] = None
    volume: Optional[ValueWithUnit] = None
    power: Optional[ValueWithUnit] = None
    flow_rate: Optional[ValueWithUnit] = None
    design_pressure: Optional[ValueWithUnit] = None
    shell_material: Optional[str] = None
    tube_material: Optional[str] = None
    tema_type: Optional[str] = None


class CostOverrides(BaseModel):
    """User-supplied overrides for the cost correlation."""

    base_cost_usd: Optional[float] = None
    material_factor: Optional[float] = None
    pressure_factor: Optional[float] = None


class EquipmentCapexRequest(BaseModel):
    project_id: str
    equipment_tag: str
    equipment_type: str
    sizing_parameters: EquipmentSizingParams
    cost_basis: CostBasis = CostBasis()
    overrides: CostOverrides = CostOverrides()


class CostBreakdown(BaseModel):
    base_cost: ValueWithUnit
    material_factor_Fm: float
    pressure_factor_Fp: float
    bare_module_factor_Fbm: float
    bare_module_cost_base_year: ValueWithUnit
    cepci_escalation_factor: float
    bare_module_cost_target_year: ValueWithUnit
    location_adjusted: ValueWithUnit


class SixTenthsCheck(BaseModel):
    reference_capacity: ValueWithUnit
    reference_cost: ValueWithUnit
    exponent: float
    scaled_cost: ValueWithUnit
    note: str


class EquipmentCapexResponse(BaseModel):
    status: str = "success"
    equipment_tag: str
    equipment_type: str
    cost_breakdown: CostBreakdown
    six_tenths_check: Optional[SixTenthsCheck] = None
    method_references: list[str] = Field(default_factory=list)
    meta: CalculationMeta


# ---------------------------------------------------------------------------
# Project CAPEX (Lang Factor)
# ---------------------------------------------------------------------------

class EquipmentCostItem(BaseModel):
    tag: str
    bare_module_cost: float


class DetailedLangFactors(BaseModel):
    installation: float = 0.47
    instrumentation: float = 0.36
    piping: float = 0.68
    electrical: float = 0.11
    buildings: float = 0.18
    yard_improvements: float = 0.10
    service_facilities: float = 0.70
    engineering_supervision: float = 0.33
    construction: float = 0.41
    legal_fees: float = 0.04
    contractor_fee: float = 0.22
    contingency: float = 0.44


class LangMethodSpec(BaseModel):
    lang_factor: Optional[float] = None
    use_detailed_factors: bool = True
    factors: DetailedLangFactors = DetailedLangFactors()


class GrassrootsExtras(BaseModel):
    land: Optional[ValueWithUnit] = None
    offsite_facilities: Optional[ValueWithUnit] = None


class ProjectCapexRequest(BaseModel):
    project_id: str
    project_name: str
    plant_type: str = "fluid_processing"
    equipment_list: list[EquipmentCostItem]
    lang_method: LangMethodSpec = LangMethodSpec()
    grassroots_extras: GrassrootsExtras = GrassrootsExtras()
    currency: str = "USD"
    cost_year: int = 2026


class DirectCosts(BaseModel):
    purchased_equipment: float
    installation: float
    instrumentation: float
    piping: float
    electrical: float
    subtotal_direct: float


class IndirectCosts(BaseModel):
    buildings: float
    yard_improvements: float
    service_facilities: float
    engineering_supervision: float
    construction: float
    legal_fees: float
    contractor_fee: float
    contingency: float
    subtotal_indirect: float


class CapitalCostSummary(BaseModel):
    direct_costs: DirectCosts
    indirect_costs: IndirectCosts
    fixed_capital_investment: float
    working_capital: float
    land: float
    offsite_facilities: float
    total_capital_investment: ValueWithUnit


class SensitivityResult(BaseModel):
    capex_minus_20pct: float
    capex_plus_20pct: float
    contingency_range: str


class ProjectCapexResponse(BaseModel):
    status: str = "success"
    project_name: str
    total_bare_module_cost: ValueWithUnit
    capital_cost_summary: CapitalCostSummary
    effective_lang_factor: float
    sensitivity: SensitivityResult
    meta: CalculationMeta


# ---------------------------------------------------------------------------
# OPEX Evaluation
# ---------------------------------------------------------------------------

class RawMaterial(BaseModel):
    name: str
    consumption_rate: ValueWithUnit
    unit_cost: ValueWithUnit


class UtilityDemand(BaseModel):
    demand: ValueWithUnit
    unit_cost: ValueWithUnit


class UtilitiesSpec(BaseModel):
    steam_hp: Optional[UtilityDemand] = None
    steam_mp: Optional[UtilityDemand] = None
    steam_lp: Optional[UtilityDemand] = None
    cooling_water: Optional[UtilityDemand] = None
    electricity: Optional[UtilityDemand] = None
    fuel_gas: Optional[UtilityDemand] = None


class LaborSpec(BaseModel):
    operators_per_shift: int
    shifts_per_day: int = 4
    annual_salary_usd: float
    overhead_factor: float = 1.6


class MaintenanceSpec(BaseModel):
    method: str = "percentage_of_fci"
    fci_usd: float = 0.0
    percentage: float = 0.06


class InsuranceTaxSpec(BaseModel):
    method: str = "percentage_of_fci"
    percentage: float = 0.03


class DepreciationSpec(BaseModel):
    method: DepreciationMethod = DepreciationMethod.STRAIGHT_LINE
    depreciable_capital: float
    salvage_value: float = 0.0
    useful_life_years: int = 20


class OpexRequest(BaseModel):
    project_id: str
    annual_operating_hours: int = 8400
    raw_materials: list[RawMaterial] = Field(default_factory=list)
    utilities: UtilitiesSpec = UtilitiesSpec()
    labor: LaborSpec
    maintenance: MaintenanceSpec
    insurance_and_taxes: InsuranceTaxSpec = InsuranceTaxSpec()
    depreciation: DepreciationSpec
    currency: str = "USD"


class UtilityCostBreakdown(BaseModel):
    steam_hp: Optional[ValueWithUnit] = None
    steam_mp: Optional[ValueWithUnit] = None
    steam_lp: Optional[ValueWithUnit] = None
    cooling_water: Optional[ValueWithUnit] = None
    electricity: Optional[ValueWithUnit] = None
    fuel_gas: Optional[ValueWithUnit] = None
    subtotal_util: ValueWithUnit


class LaborCost(BaseModel):
    operating_labor: ValueWithUnit
    with_overhead: ValueWithUnit


class OpexBreakdown(BaseModel):
    raw_materials: ValueWithUnit
    utilities: UtilityCostBreakdown
    labor: LaborCost
    maintenance: ValueWithUnit
    insurance_and_taxes: ValueWithUnit
    depreciation: ValueWithUnit
    total_opex: ValueWithUnit


class OpexResponse(BaseModel):
    status: str = "success"
    annual_operating_hours: int
    opex_breakdown: OpexBreakdown
    meta: CalculationMeta


# ---------------------------------------------------------------------------
# Utilities — Steam Demand Calculator
# ---------------------------------------------------------------------------

class SteamConsumer(BaseModel):
    tag: str
    duty_kw: float
    steam_pressure: SteamHeader
    steam_conditions: Optional[dict] = None


class SteamDemandRequest(BaseModel):
    consumers: list[SteamConsumer]
    condensate_return_pct: float = Field(default=85.0, ge=0.0, le=100.0)
    bfw_temperature: ValueWithUnit = ValueWithUnit(value=105.0, unit="°C")


class SteamHeaderSummary(BaseModel):
    header: SteamHeader
    total_duty_kw: float
    latent_heat_kj_kg: float
    mass_flow_kg_h: float
    consumers: list[str]


class SteamDemandResponse(BaseModel):
    status: str = "success"
    steam_summary: list[SteamHeaderSummary]
    total_steam_demand_kg_h: float
    makeup_water_kg_h: float
    bfw_preheat_duty_kw: float
    meta: CalculationMeta
