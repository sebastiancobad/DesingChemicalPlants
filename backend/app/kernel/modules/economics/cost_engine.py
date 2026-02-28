"""
ChemScale — Economic Evaluation Calculation Kernel.

Implements equipment CAPEX (Guthrie bare-module, six-tenths rule),
project CAPEX (detailed Lang factors), and OPEX evaluation.

References:
    - Turton, R., Analysis, Synthesis and Design of Chemical Processes, 5th Ed.
    - Guthrie, K.M., Chem. Eng., Mar 1969
    - Peters, Timmerhaus & West, Plant Design and Economics, 5th Ed.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Optional

from app.core.standards import standards_ref


# ---------------------------------------------------------------------------
# Cost correlation data (Turton et al., 5th Ed., Appendix A)
#
# log10(Cp°) = K1 + K2 * log10(A) + K3 * (log10(A))²
# where Cp° is purchased cost in base year USD and A is the capacity parameter.
# ---------------------------------------------------------------------------

@dataclass
class CostCorrelation:
    """Bare-module cost correlation coefficients."""

    equipment_type: str
    K1: float
    K2: float
    K3: float
    capacity_unit: str  # e.g., 'm²' for HX area
    capacity_min: float
    capacity_max: float
    base_year: int = 2001
    base_cepci: float = 397.0
    fbm_base: float = 3.17  # bare module factor for CS/CS at base pressure


COST_CORRELATIONS: dict[str, CostCorrelation] = {
    "shell_and_tube_hx": CostCorrelation(
        equipment_type="shell_and_tube_hx",
        K1=4.3247, K2=-0.3030, K3=0.1634,
        capacity_unit="m²", capacity_min=10.0, capacity_max=1000.0,
        fbm_base=3.17,
    ),
    "centrifugal_pump": CostCorrelation(
        equipment_type="centrifugal_pump",
        K1=3.3892, K2=0.0536, K3=0.1538,
        capacity_unit="kW", capacity_min=1.0, capacity_max=300.0,
        fbm_base=3.30,
    ),
    "pressure_vessel_vertical": CostCorrelation(
        equipment_type="pressure_vessel_vertical",
        K1=3.4974, K2=0.4485, K3=0.1074,
        capacity_unit="kg", capacity_min=100.0, capacity_max=50000.0,
        fbm_base=4.16,
    ),
    "pressure_vessel_horizontal": CostCorrelation(
        equipment_type="pressure_vessel_horizontal",
        K1=3.5565, K2=0.3776, K3=0.0905,
        capacity_unit="kg", capacity_min=100.0, capacity_max=50000.0,
        fbm_base=3.05,
    ),
    "tray_column": CostCorrelation(
        equipment_type="tray_column",
        K1=3.4974, K2=0.4485, K3=0.1074,
        capacity_unit="kg", capacity_min=500.0, capacity_max=100000.0,
        fbm_base=4.16,
    ),
    "compressor_centrifugal": CostCorrelation(
        equipment_type="compressor_centrifugal",
        K1=2.2897, K2=1.3604, K3=-0.1027,
        capacity_unit="kW", capacity_min=450.0, capacity_max=3000.0,
        fbm_base=2.15,
    ),
    "fired_heater": CostCorrelation(
        equipment_type="fired_heater",
        K1=1.2110, K2=1.0000, K3=0.0,
        capacity_unit="kW", capacity_min=1000.0, capacity_max=100000.0,
        fbm_base=2.19,
    ),
    "air_cooler": CostCorrelation(
        equipment_type="air_cooler",
        K1=4.0336, K2=0.2341, K3=0.0497,
        capacity_unit="m²", capacity_min=10.0, capacity_max=10000.0,
        fbm_base=2.17,
    ),
}


# Material factors (Fm) — Turton Table A.3
MATERIAL_FACTORS: dict[str, dict[str, float]] = {
    "shell_and_tube_hx": {
        "CS/CS": 1.00,
        "CS/CuAlloy": 1.35,
        "CS/SS316": 1.81,
        "CS/Monel": 2.73,
        "CS/Titanium": 4.63,
        "SS316/SS316": 2.73,
        "Monel/Monel": 3.65,
        "Titanium/Titanium": 7.89,
    },
}


# Pressure factors (Fp) — interpolated from Turton Table A.4
# For HX: log10(Fp) = C1 + C2*log10(P) + C3*(log10(P))²  (P in barg)
@dataclass
class PressureFactorCoeffs:
    C1: float = 0.0
    C2: float = 0.0
    C3: float = 0.0
    p_min_barg: float = 5.0
    p_max_barg: float = 140.0


PRESSURE_FACTOR_COEFFS: dict[str, PressureFactorCoeffs] = {
    "shell_and_tube_hx": PressureFactorCoeffs(
        C1=-0.00164, C2=-0.00627, C3=0.0123,
    ),
}


# ---------------------------------------------------------------------------
# Equipment CAPEX
# ---------------------------------------------------------------------------

@dataclass
class EquipmentCapexResult:
    base_cost_usd: float
    material_factor: float
    pressure_factor: float
    bare_module_factor: float
    bare_module_cost_base_year: float
    cepci_escalation: float
    bare_module_cost_target_year: float
    location_adjusted: float

    six_tenths_cost: Optional[float] = None
    six_tenths_exponent: Optional[float] = None
    six_tenths_note: str = ""

    references: list[str] = field(default_factory=list)


@standards_ref(
    "Turton, R., Analysis, Synthesis and Design of Chemical Processes, 5th Ed., Ch. 7",
    "Guthrie, K.M., Chem. Eng., Mar 1969",
)
def equipment_capex(
    equipment_type: str,
    capacity: float,
    design_pressure_barg: float = 10.0,
    shell_material: str = "CS",
    tube_material: str = "CS",
    base_cepci: float = 397.0,
    target_cepci: float = 823.5,
    location_factor: float = 1.0,
    base_cost_override: Optional[float] = None,
    material_factor_override: Optional[float] = None,
    pressure_factor_override: Optional[float] = None,
) -> EquipmentCapexResult:
    """Calculate bare-module equipment cost using Guthrie method.

    Parameters
    ----------
    equipment_type : str
        Key into COST_CORRELATIONS.
    capacity : float
        Sizing parameter in the unit specified by the correlation.
    design_pressure_barg : float
        Design pressure in barg.
    shell_material, tube_material : str
        Material designations for factor lookup.
    base_cepci, target_cepci : float
        CEPCI values for cost escalation.
    location_factor : float
        Geographic location adjustment factor.
    """
    refs = list(equipment_capex.__standards_refs__)

    corr = COST_CORRELATIONS.get(equipment_type)
    if corr is None:
        raise ValueError(
            f"No cost correlation for '{equipment_type}'. "
            f"Available: {list(COST_CORRELATIONS.keys())}"
        )

    # --- Base purchased cost ---
    if base_cost_override is not None:
        Cp0 = base_cost_override
    else:
        logA = math.log10(max(capacity, corr.capacity_min))
        logCp = corr.K1 + corr.K2 * logA + corr.K3 * logA**2
        Cp0 = 10.0**logCp

    # --- Material factor ---
    mat_key = f"{shell_material}/{tube_material}"
    if material_factor_override is not None:
        Fm = material_factor_override
    else:
        mat_table = MATERIAL_FACTORS.get(equipment_type, {})
        Fm = mat_table.get(mat_key, 1.0)

    # --- Pressure factor ---
    if pressure_factor_override is not None:
        Fp = pressure_factor_override
    else:
        pf_coeffs = PRESSURE_FACTOR_COEFFS.get(equipment_type)
        if pf_coeffs and design_pressure_barg > pf_coeffs.p_min_barg:
            logP = math.log10(max(design_pressure_barg, 1.0))
            logFp = pf_coeffs.C1 + pf_coeffs.C2 * logP + pf_coeffs.C3 * logP**2
            Fp = 10.0**logFp
            Fp = max(Fp, 1.0)
        else:
            Fp = 1.0

    # --- Bare module cost (Turton Eq. 7.7) ---
    # C_BM = Cp° * (B1 + B2·Fm·Fp)  — simplified as Cp° * Fbm when Fm=Fp=1
    # For non-CS or elevated pressure: C_BM = Cp° * (Fbm + Fm·Fp - 1)
    Fbm = corr.fbm_base
    Cbm_base = Cp0 * (Fbm + Fm * Fp - 1.0)

    # --- CEPCI escalation ---
    escalation = target_cepci / base_cepci
    Cbm_target = Cbm_base * escalation

    # --- Location adjustment ---
    Cbm_loc = Cbm_target * location_factor

    # --- Six-tenths rule cross-check ---
    six_tenths_cost = None
    six_tenths_exp = 0.6
    six_tenths_note = ""

    # Standard exponents per equipment type
    exponent_map = {
        "shell_and_tube_hx": 0.59,
        "centrifugal_pump": 0.55,
        "pressure_vessel_vertical": 0.62,
        "pressure_vessel_horizontal": 0.62,
        "compressor_centrifugal": 0.67,
    }
    exp = exponent_map.get(equipment_type, 0.6)

    # Reference point: capacity at midpoint of correlation range
    ref_cap = math.sqrt(corr.capacity_min * corr.capacity_max)
    logA_ref = math.log10(ref_cap)
    logCp_ref = corr.K1 + corr.K2 * logA_ref + corr.K3 * logA_ref**2
    Cp_ref = 10.0**logCp_ref

    six_tenths_cost = Cp_ref * (capacity / ref_cap) ** exp * escalation * location_factor
    deviation = abs(six_tenths_cost - Cbm_loc) / Cbm_loc * 100 if Cbm_loc > 0 else 0
    six_tenths_note = f"Within {deviation:.1f}% of Guthrie correlation"

    return EquipmentCapexResult(
        base_cost_usd=Cp0,
        material_factor=Fm,
        pressure_factor=Fp,
        bare_module_factor=Fbm,
        bare_module_cost_base_year=Cbm_base,
        cepci_escalation=escalation,
        bare_module_cost_target_year=Cbm_target,
        location_adjusted=Cbm_loc,
        six_tenths_cost=six_tenths_cost,
        six_tenths_exponent=exp,
        six_tenths_note=six_tenths_note,
        references=refs,
    )


# ---------------------------------------------------------------------------
# Project CAPEX (Lang / Detailed Factors)
# ---------------------------------------------------------------------------

@dataclass
class ProjectCapexResult:
    total_bare_module: float
    direct_costs: dict[str, float]
    indirect_costs: dict[str, float]
    fixed_capital_investment: float
    working_capital: float
    land: float
    offsite_facilities: float
    total_capital_investment: float
    effective_lang_factor: float
    references: list[str] = field(default_factory=list)


@standards_ref(
    "Peters, Timmerhaus & West, Plant Design and Economics, 5th Ed., Ch. 6",
    "Lang, H.J., Chem. Eng., Jun 1947",
)
def project_capex(
    equipment_costs: list[float],
    lang_factor: Optional[float] = None,
    factors: Optional[dict[str, float]] = None,
    land: float = 0.0,
    offsite_facilities: float = 0.0,
    working_capital_pct: float = 0.15,
) -> ProjectCapexResult:
    """Total project capital cost estimation.

    If ``lang_factor`` is provided, the total installed cost is simply
    ``sum(equipment) * lang_factor``. Otherwise, detailed factors are
    applied component by component per Peters & Timmerhaus.
    """
    refs = list(project_capex.__standards_refs__)
    total_equip = sum(equipment_costs)

    if lang_factor is not None:
        # Simplified Lang method
        tci = total_equip * lang_factor + land + offsite_facilities
        wc = tci * working_capital_pct
        return ProjectCapexResult(
            total_bare_module=total_equip,
            direct_costs={"purchased_equipment": total_equip},
            indirect_costs={},
            fixed_capital_investment=tci - land - offsite_facilities,
            working_capital=wc,
            land=land,
            offsite_facilities=offsite_facilities,
            total_capital_investment=tci + wc,
            effective_lang_factor=lang_factor,
            references=refs,
        )

    # Detailed factor method
    f = factors or {}

    direct = {
        "purchased_equipment": total_equip,
        "installation": total_equip * f.get("installation", 0.47),
        "instrumentation": total_equip * f.get("instrumentation", 0.36),
        "piping": total_equip * f.get("piping", 0.68),
        "electrical": total_equip * f.get("electrical", 0.11),
    }
    direct["subtotal_direct"] = sum(direct.values())

    indirect = {
        "buildings": total_equip * f.get("buildings", 0.18),
        "yard_improvements": total_equip * f.get("yard_improvements", 0.10),
        "service_facilities": total_equip * f.get("service_facilities", 0.70),
        "engineering_supervision": total_equip * f.get("engineering_supervision", 0.33),
        "construction": total_equip * f.get("construction", 0.41),
        "legal_fees": total_equip * f.get("legal_fees", 0.04),
        "contractor_fee": total_equip * f.get("contractor_fee", 0.22),
        "contingency": total_equip * f.get("contingency", 0.44),
    }
    indirect["subtotal_indirect"] = sum(indirect.values())

    fci = direct["subtotal_direct"] + indirect["subtotal_indirect"]
    wc = fci * working_capital_pct
    tci = fci + wc + land + offsite_facilities

    effective_lang = tci / total_equip if total_equip > 0 else 0

    return ProjectCapexResult(
        total_bare_module=total_equip,
        direct_costs=direct,
        indirect_costs=indirect,
        fixed_capital_investment=fci,
        working_capital=wc,
        land=land,
        offsite_facilities=offsite_facilities,
        total_capital_investment=tci,
        effective_lang_factor=effective_lang,
        references=refs,
    )


# ---------------------------------------------------------------------------
# OPEX Evaluation
# ---------------------------------------------------------------------------

@dataclass
class OpexResult:
    raw_materials_cost: float  # USD/yr
    utility_costs: dict[str, float]  # USD/yr per utility
    total_utility_cost: float
    operating_labor: float
    labor_with_overhead: float
    maintenance: float
    insurance_taxes: float
    depreciation: float
    total_opex: float
    references: list[str] = field(default_factory=list)


@standards_ref(
    "Peters, Timmerhaus & West, Plant Design and Economics, 5th Ed., Ch. 8",
)
def evaluate_opex(
    annual_hours: int,
    raw_materials: list[dict],
    utilities: dict[str, dict],
    operators_per_shift: int,
    shifts_per_day: int,
    annual_salary: float,
    overhead_factor: float,
    fci: float,
    maintenance_pct: float,
    insurance_tax_pct: float,
    depreciable_capital: float,
    salvage_value: float,
    useful_life_years: int,
) -> OpexResult:
    """Annual operating expenditure breakdown."""
    refs = list(evaluate_opex.__standards_refs__)

    # Raw materials
    rm_cost = 0.0
    for rm in raw_materials:
        rate = rm["rate_si"]  # converted to SI base unit per second
        unit_cost = rm["unit_cost_per_si"]
        rm_cost += rate * unit_cost * annual_hours * 3600

    # Utilities
    util_costs: dict[str, float] = {}
    for name, spec in utilities.items():
        if spec is None:
            continue
        demand = spec.get("demand_si", 0)  # base SI unit per second
        price = spec.get("unit_cost_per_si", 0)
        annual = demand * price * annual_hours * 3600
        util_costs[name] = annual

    total_util = sum(util_costs.values())

    # Labor
    total_operators = operators_per_shift * shifts_per_day
    op_labor = total_operators * annual_salary
    labor_overhead = op_labor * overhead_factor

    # Maintenance
    maint = fci * maintenance_pct

    # Insurance & taxes
    ins_tax = fci * insurance_tax_pct

    # Depreciation (straight-line)
    depr = (depreciable_capital - salvage_value) / max(useful_life_years, 1)

    total = rm_cost + total_util + labor_overhead + maint + ins_tax + depr

    return OpexResult(
        raw_materials_cost=rm_cost,
        utility_costs=util_costs,
        total_utility_cost=total_util,
        operating_labor=op_labor,
        labor_with_overhead=labor_overhead,
        maintenance=maint,
        insurance_taxes=ins_tax,
        depreciation=depr,
        total_opex=total,
        references=refs,
    )
