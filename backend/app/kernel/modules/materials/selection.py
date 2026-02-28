"""
ChemScale — Material Selection Kernel.

Provides material properties, corrosion rate data, and compatibility
assessments for process equipment per ASME II, NACE MR0175, and API 571.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from app.core.standards import standards_ref


@dataclass
class MaterialProperties:
    name: str
    designation: str
    category: str
    density_kgm3: float
    yield_strength_mpa: float
    tensile_strength_mpa: float
    allowable_stress_mpa: float  # at design temperature
    max_temperature_c: float
    min_temperature_c: float
    thermal_conductivity_wpmk: float
    thermal_expansion_per_c: float
    elastic_modulus_gpa: float
    corrosion_allowance_mm: float
    cost_factor: float  # relative to CS
    weldability: str
    notes: str


# Material database
MATERIAL_DB: dict[str, MaterialProperties] = {
    "SA-516-70": MaterialProperties(
        name="Carbon Steel SA-516 Gr. 70",
        designation="SA-516-70",
        category="Carbon Steel",
        density_kgm3=7850,
        yield_strength_mpa=260,
        tensile_strength_mpa=485,
        allowable_stress_mpa=138,
        max_temperature_c=450,
        min_temperature_c=-29,
        thermal_conductivity_wpmk=50.0,
        thermal_expansion_per_c=12e-6,
        elastic_modulus_gpa=200,
        corrosion_allowance_mm=3.0,
        cost_factor=1.0,
        weldability="Excellent",
        notes="Most common pressure vessel plate. Suitable for non-corrosive services.",
    ),
    "SA-240-304": MaterialProperties(
        name="Stainless Steel 304 (18Cr-8Ni)",
        designation="SA-240-304",
        category="Austenitic Stainless Steel",
        density_kgm3=7930,
        yield_strength_mpa=205,
        tensile_strength_mpa=515,
        allowable_stress_mpa=115,
        max_temperature_c=815,
        min_temperature_c=-196,
        thermal_conductivity_wpmk=16.3,
        thermal_expansion_per_c=17.3e-6,
        elastic_modulus_gpa=193,
        corrosion_allowance_mm=1.5,
        cost_factor=3.2,
        weldability="Good — use 308L filler",
        notes="General purpose stainless. Susceptible to chloride SCC above 60°C.",
    ),
    "SA-240-316L": MaterialProperties(
        name="Stainless Steel 316L (16Cr-12Ni-2Mo)",
        designation="SA-240-316L",
        category="Austenitic Stainless Steel",
        density_kgm3=7960,
        yield_strength_mpa=170,
        tensile_strength_mpa=485,
        allowable_stress_mpa=110,
        max_temperature_c=815,
        min_temperature_c=-196,
        thermal_conductivity_wpmk=14.6,
        thermal_expansion_per_c=16.0e-6,
        elastic_modulus_gpa=193,
        corrosion_allowance_mm=1.5,
        cost_factor=4.0,
        weldability="Good — use 316L filler",
        notes="Better chloride resistance than 304. Low carbon for weld sensitization resistance.",
    ),
    "SA-240-2205": MaterialProperties(
        name="Duplex Stainless Steel 2205 (22Cr-5Ni-3Mo)",
        designation="SA-240-2205",
        category="Duplex Stainless Steel",
        density_kgm3=7820,
        yield_strength_mpa=450,
        tensile_strength_mpa=620,
        allowable_stress_mpa=170,
        max_temperature_c=315,
        min_temperature_c=-50,
        thermal_conductivity_wpmk=19.0,
        thermal_expansion_per_c=13.0e-6,
        elastic_modulus_gpa=200,
        corrosion_allowance_mm=1.0,
        cost_factor=5.5,
        weldability="Fair — requires controlled heat input",
        notes="Excellent chloride SCC resistance. Used in seawater and sour service.",
    ),
    "SB-265-Gr2": MaterialProperties(
        name="Titanium Grade 2 (Commercially Pure)",
        designation="SB-265-Gr2",
        category="Titanium",
        density_kgm3=4510,
        yield_strength_mpa=275,
        tensile_strength_mpa=345,
        allowable_stress_mpa=86,
        max_temperature_c=315,
        min_temperature_c=-196,
        thermal_conductivity_wpmk=21.9,
        thermal_expansion_per_c=8.6e-6,
        elastic_modulus_gpa=103,
        corrosion_allowance_mm=0.5,
        cost_factor=12.0,
        weldability="Requires inert atmosphere (argon shielding)",
        notes="Excellent seawater and chloride resistance. Light weight. High cost.",
    ),
    "SB-462-N08825": MaterialProperties(
        name="Alloy 825 (Incoloy 825)",
        designation="SB-462-N08825",
        category="Nickel Alloy",
        density_kgm3=8140,
        yield_strength_mpa=240,
        tensile_strength_mpa=586,
        allowable_stress_mpa=140,
        max_temperature_c=540,
        min_temperature_c=-196,
        thermal_conductivity_wpmk=11.1,
        thermal_expansion_per_c=14.0e-6,
        elastic_modulus_gpa=196,
        corrosion_allowance_mm=0.5,
        cost_factor=8.0,
        weldability="Good — use matching filler or Alloy 625",
        notes="Resistant to sulfuric/phosphoric acid, sour gas, and chlorides.",
    ),
    "SA-387-Gr11": MaterialProperties(
        name="Chrome-Moly Steel 1.25Cr-0.5Mo",
        designation="SA-387-Gr11",
        category="Alloy Steel",
        density_kgm3=7850,
        yield_strength_mpa=310,
        tensile_strength_mpa=515,
        allowable_stress_mpa=138,
        max_temperature_c=595,
        min_temperature_c=-29,
        thermal_conductivity_wpmk=37.0,
        thermal_expansion_per_c=12.6e-6,
        elastic_modulus_gpa=200,
        corrosion_allowance_mm=3.0,
        cost_factor=2.0,
        weldability="Requires preheat and PWHT",
        notes="High-temperature hydrogen service. Resists hydrogen attack per Nelson curves.",
    ),
    "SA-516-60": MaterialProperties(
        name="Carbon Steel SA-516 Gr. 60",
        designation="SA-516-60",
        category="Carbon Steel",
        density_kgm3=7850,
        yield_strength_mpa=220,
        tensile_strength_mpa=415,
        allowable_stress_mpa=117,
        max_temperature_c=450,
        min_temperature_c=-29,
        thermal_conductivity_wpmk=50.0,
        thermal_expansion_per_c=12e-6,
        elastic_modulus_gpa=200,
        corrosion_allowance_mm=3.0,
        cost_factor=0.95,
        weldability="Excellent",
        notes="Lower strength than Gr. 70. Used for lower-pressure applications.",
    ),
}


# Corrosion rate lookup (mm/yr) by material and environment
CORROSION_RATES: dict[str, dict[str, float]] = {
    "SA-516-70": {
        "clean_water": 0.1,
        "seawater": 0.3,
        "mild_acid": 1.5,
        "strong_acid": 5.0,
        "caustic_soda": 0.5,
        "sour_gas": 0.3,
        "hydrogen": 0.1,
        "steam": 0.05,
        "atmospheric": 0.08,
        "amine": 0.25,
    },
    "SA-240-304": {
        "clean_water": 0.01,
        "seawater": 0.05,
        "mild_acid": 0.1,
        "strong_acid": 2.0,
        "caustic_soda": 0.02,
        "sour_gas": 0.05,
        "hydrogen": 0.01,
        "steam": 0.01,
        "atmospheric": 0.005,
        "amine": 0.02,
    },
    "SA-240-316L": {
        "clean_water": 0.005,
        "seawater": 0.02,
        "mild_acid": 0.05,
        "strong_acid": 1.0,
        "caustic_soda": 0.01,
        "sour_gas": 0.03,
        "hydrogen": 0.005,
        "steam": 0.005,
        "atmospheric": 0.003,
        "amine": 0.01,
    },
    "SB-265-Gr2": {
        "clean_water": 0.001,
        "seawater": 0.001,
        "mild_acid": 0.01,
        "strong_acid": 0.5,
        "caustic_soda": 0.01,
        "sour_gas": 0.005,
        "hydrogen": 0.001,
        "steam": 0.001,
        "atmospheric": 0.001,
        "amine": 0.005,
    },
}

# NACE MR0175 sour service limits
SOUR_SERVICE_LIMITS: dict[str, dict] = {
    "SA-516-70": {"max_hardness_hrc": 22, "requires_pwht": True, "nace_compliant": True},
    "SA-240-304": {"max_hardness_hrc": 22, "requires_pwht": False, "nace_compliant": True},
    "SA-240-316L": {"max_hardness_hrc": 22, "requires_pwht": False, "nace_compliant": True},
    "SA-240-2205": {"max_hardness_hrc": 28, "requires_pwht": False, "nace_compliant": True},
    "SB-265-Gr2": {"max_hardness_hrc": None, "requires_pwht": False, "nace_compliant": True},
    "SB-462-N08825": {"max_hardness_hrc": 35, "requires_pwht": False, "nace_compliant": True},
    "SA-387-Gr11": {"max_hardness_hrc": 22, "requires_pwht": True, "nace_compliant": True},
}


@dataclass
class MaterialAssessment:
    material: MaterialProperties
    environment: str
    corrosion_rate_mmyr: float
    design_life_years: int
    required_corrosion_allowance_mm: float
    temperature_ok: bool
    sour_service_ok: bool
    sour_service_notes: str
    cost_relative: float
    recommended: bool
    recommendation_notes: str
    alternatives: list[str]
    warnings: list[str] = field(default_factory=list)
    standards_refs: list[str] = field(default_factory=list)


@standards_ref(
    "ASME Sec II Part D — Material Properties",
    "NACE MR0175/ISO 15156 — Sour Service",
    "API 571 — Damage Mechanisms",
)
def assess_material(
    material_designation: str,
    environment: str = "clean_water",
    design_temperature_c: float = 100.0,
    design_life_years: int = 20,
    is_sour_service: bool = False,
    h2_partial_pressure_bar: float = 0.0,
) -> MaterialAssessment:
    """Assess material suitability for a given service environment."""
    warnings: list[str] = []
    refs = list(assess_material.__standards_refs__)

    mat = MATERIAL_DB.get(material_designation)
    if mat is None:
        raise ValueError(
            f"Material '{material_designation}' not found. "
            f"Available: {list(MATERIAL_DB.keys())}"
        )

    # Corrosion rate
    mat_rates = CORROSION_RATES.get(material_designation, {})
    cr = mat_rates.get(environment, 0.5)  # default 0.5 mm/yr if unknown

    required_ca = cr * design_life_years

    # Temperature check
    temp_ok = mat.min_temperature_c <= design_temperature_c <= mat.max_temperature_c
    if not temp_ok:
        warnings.append(
            f"Design temperature {design_temperature_c}°C is outside "
            f"material range [{mat.min_temperature_c}, {mat.max_temperature_c}]°C"
        )

    # Sour service check
    sour_ok = True
    sour_notes = "Not sour service"
    if is_sour_service:
        sour_info = SOUR_SERVICE_LIMITS.get(material_designation, {})
        sour_ok = sour_info.get("nace_compliant", False)
        if sour_ok:
            notes_parts = [f"NACE MR0175 compliant"]
            if sour_info.get("requires_pwht"):
                notes_parts.append("PWHT required")
            if sour_info.get("max_hardness_hrc"):
                notes_parts.append(f"Max hardness {sour_info['max_hardness_hrc']} HRC")
            sour_notes = "; ".join(notes_parts)
        else:
            sour_notes = "NOT suitable for sour service per NACE MR0175"
            warnings.append(sour_notes)

    # Hydrogen attack check (Nelson curves)
    if h2_partial_pressure_bar > 0 and mat.category == "Carbon Steel":
        if design_temperature_c > 260 and h2_partial_pressure_bar > 7:
            warnings.append(
                "Risk of high-temperature hydrogen attack (HTHA) — "
                "consider Cr-Mo steel per API 941 Nelson curves"
            )

    # Recommendation
    recommended = temp_ok and sour_ok and cr < 0.5
    if required_ca > 6.0:
        recommended = False
        warnings.append(f"Required CA = {required_ca:.1f} mm over {design_life_years} yr — excessive")

    # Alternatives
    alternatives = []
    for alt_name, alt_mat in MATERIAL_DB.items():
        if alt_name == material_designation:
            continue
        alt_rates = CORROSION_RATES.get(alt_name, {})
        alt_cr = alt_rates.get(environment, 0.5)
        if alt_cr < cr and alt_mat.min_temperature_c <= design_temperature_c <= alt_mat.max_temperature_c:
            alternatives.append(f"{alt_mat.name} (CR: {alt_cr} mm/yr, cost: {alt_mat.cost_factor}x)")
    alternatives = alternatives[:3]  # top 3

    rec_notes = "Suitable for service" if recommended else "Review alternatives — see warnings"

    return MaterialAssessment(
        material=mat,
        environment=environment,
        corrosion_rate_mmyr=cr,
        design_life_years=design_life_years,
        required_corrosion_allowance_mm=round(required_ca, 1),
        temperature_ok=temp_ok,
        sour_service_ok=sour_ok,
        sour_service_notes=sour_notes,
        cost_relative=mat.cost_factor,
        recommended=recommended,
        recommendation_notes=rec_notes,
        alternatives=alternatives,
        warnings=warnings,
        standards_refs=refs,
    )
