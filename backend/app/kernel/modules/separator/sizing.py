"""
ChemScale — Phase Separator / Knockout Drum Calculation Kernel.

Implements two-phase (liquid-vapor) and three-phase (oil-water-gas)
separator sizing per API 12J, GPSA Engineering Data Book, and
Stokes' law settling calculations.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Optional

from app.core.standards import standards_ref


@dataclass
class SeparatorResult:
    orientation: str
    vessel_diameter_m: float
    vessel_length_m: float
    l_over_d_ratio: float
    settling_velocity_ms: float
    droplet_diameter_um: float
    gas_velocity_ms: float
    gas_velocity_max_ms: float
    k_factor: float
    liquid_residence_time_s: float
    liquid_volume_m3: float
    vessel_volume_m3: float
    liquid_level_pct: float
    mist_eliminator: str
    wall_thickness_mm: float
    vessel_weight_kg: float
    warnings: list[str] = field(default_factory=list)
    standards_refs: list[str] = field(default_factory=list)


@standards_ref(
    "API 12J, Oil and Gas Separators, 8th Ed.",
    "GPSA Engineering Data Book, 14th Ed., Ch. 7",
)
def souders_brown_k(
    pressure_pa: float,
    has_mist_eliminator: bool = True,
    separator_type: str = "vertical",
) -> float:
    """Souders-Brown K factor for separator sizing.

    K depends on operating pressure and whether a mist eliminator is used.
    """
    # Base K values (m/s) at various pressures
    p_barg = (pressure_pa - 101325.0) / 1e5

    if separator_type == "vertical":
        if has_mist_eliminator:
            K = 0.107 - 0.0023 * max(p_barg - 7, 0)
        else:
            K = 0.048 - 0.001 * max(p_barg - 7, 0)
    else:
        if has_mist_eliminator:
            K = 0.12 - 0.002 * max(p_barg - 7, 0)
        else:
            K = 0.06 - 0.001 * max(p_barg - 7, 0)

    return max(K, 0.02)


@standards_ref("Stokes' Law for droplet settling")
def stokes_settling_velocity(
    droplet_diameter_m: float,
    rho_liquid: float,
    rho_gas: float,
    mu_gas: float,
) -> float:
    """Terminal settling velocity of a droplet in gas phase (Stokes regime)."""
    g = 9.81
    v_t = g * (rho_liquid - rho_gas) * droplet_diameter_m**2 / (18 * mu_gas)
    return v_t


@standards_ref(
    "API 12J, 8th Ed.",
    "GPSA Engineering Data Book, 14th Ed.",
    "Arnold & Stewart, Surface Production Operations, Vol 1",
)
def size_separator(
    gas_flow_m3s: float,
    liquid_flow_m3s: float,
    rho_gas: float,
    rho_liquid: float,
    mu_gas: float,
    operating_pressure_pa: float,
    operating_temperature_k: float,
    orientation: str = "vertical",
    residence_time_s: float = 180.0,
    droplet_diameter_um: float = 150.0,
    has_mist_eliminator: bool = True,
    l_over_d_target: float = 3.0,
    design_pressure_pa: float | None = None,
    allowable_stress_pa: float = 138e6,
    corrosion_allowance_m: float = 0.003,
) -> SeparatorResult:
    """Size a two-phase (gas-liquid) separator vessel."""
    warnings: list[str] = []
    refs = list(size_separator.__standards_refs__)

    if design_pressure_pa is None:
        design_pressure_pa = operating_pressure_pa * 1.1 + 172000  # API rule of thumb

    # Souders-Brown K factor
    K = souders_brown_k(operating_pressure_pa, has_mist_eliminator, orientation)
    refs.extend(souders_brown_k.__standards_refs__)

    # Maximum allowable gas velocity
    v_gas_max = K * math.sqrt((rho_liquid - rho_gas) / rho_gas) if rho_gas > 0 else 0.1

    # Stokes settling velocity
    d_drop = droplet_diameter_um * 1e-6
    v_settle = stokes_settling_velocity(d_drop, rho_liquid, rho_gas, mu_gas)
    refs.extend(stokes_settling_velocity.__standards_refs__)

    # Use the lesser of Souders-Brown and Stokes
    v_design = min(v_gas_max, v_settle) * 0.75  # 75% of max for safety

    if orientation == "vertical":
        # Gas velocity determines diameter
        A_gas = gas_flow_m3s / v_design if v_design > 0 else 1.0
        D = math.sqrt(4 * A_gas / math.pi)
        D = max(D, 0.3)  # min 300mm

        # Liquid holdup volume
        V_liquid = liquid_flow_m3s * residence_time_s
        # Liquid occupies bottom portion
        h_liquid = V_liquid / (math.pi / 4 * D**2) if D > 0 else 0
        # Total length: liquid section + gas disengagement + mist eliminator
        L_gas = 1.5 * D  # gas disengagement height
        L_mist = 0.3 if has_mist_eliminator else 0
        L = h_liquid + L_gas + L_mist + 0.3  # 0.3m for nozzles
        L = max(L, l_over_d_target * D)
    else:
        # Horizontal separator
        V_liquid = liquid_flow_m3s * residence_time_s
        # Target L/D
        # Total volume: liquid + gas space (liquid typically 50-70% full)
        liquid_fill = 0.5
        V_total = V_liquid / liquid_fill
        D = (4 * V_total / (math.pi * l_over_d_target))**(1.0/3.0)
        D = max(D, 0.3)
        L = l_over_d_target * D

        # Check gas velocity in the gas space
        A_gas_avail = (1 - liquid_fill) * math.pi / 4 * D**2
        v_gas_actual = gas_flow_m3s / A_gas_avail if A_gas_avail > 0 else 999

        if v_gas_actual > v_gas_max:
            # Need larger diameter
            A_gas_needed = gas_flow_m3s / (v_gas_max * 0.75)
            A_total = A_gas_needed / (1 - liquid_fill)
            D = math.sqrt(4 * A_total / math.pi)
            L = l_over_d_target * D

    # Round up to standard sizes (100mm increments)
    D = math.ceil(D * 10) / 10.0
    L = math.ceil(L * 10) / 10.0

    l_over_d = L / D if D > 0 else 0
    v_gas_actual = gas_flow_m3s / (math.pi / 4 * D**2 * (0.5 if orientation == "horizontal" else 1.0))
    V_vessel = math.pi / 4 * D**2 * L
    V_liq_actual = liquid_flow_m3s * residence_time_s
    liquid_level = V_liq_actual / V_vessel * 100 if V_vessel > 0 else 0

    # L/D check
    if l_over_d < 1.5:
        warnings.append(f"L/D = {l_over_d:.1f} is below typical minimum (1.5)")
    elif l_over_d > 6.0:
        warnings.append(f"L/D = {l_over_d:.1f} exceeds typical maximum (6.0) — consider horizontal orientation")

    # Mist eliminator recommendation
    mist_eliminator = "Wire mesh (York-style)" if has_mist_eliminator else "None — gravity settling only"

    # Wall thickness (ASME VIII-1 UG-27)
    R = D / 2.0
    S = allowable_stress_pa
    E = 0.85
    P = design_pressure_pa
    t_calc = P * R / (S * E - 0.6 * P)
    t_min = (t_calc + corrosion_allowance_m) * 1000  # mm
    t_min = max(t_min, 6.0)  # minimum 6mm

    # Weight estimate
    rho_steel = 7850
    t_m = t_min / 1000
    shell_weight = math.pi * D * t_m * L * rho_steel
    head_weight = 2 * math.pi / 4 * D**2 * t_m * rho_steel * 1.5  # 2:1 ellipsoidal heads
    total_weight = shell_weight + head_weight

    return SeparatorResult(
        orientation=orientation,
        vessel_diameter_m=D,
        vessel_length_m=L,
        l_over_d_ratio=round(l_over_d, 1),
        settling_velocity_ms=round(v_settle, 4),
        droplet_diameter_um=droplet_diameter_um,
        gas_velocity_ms=round(v_gas_actual, 2),
        gas_velocity_max_ms=round(v_gas_max, 2),
        k_factor=round(K, 4),
        liquid_residence_time_s=residence_time_s,
        liquid_volume_m3=round(V_liq_actual, 3),
        vessel_volume_m3=round(V_vessel, 3),
        liquid_level_pct=round(liquid_level, 1),
        mist_eliminator=mist_eliminator,
        wall_thickness_mm=round(t_min, 1),
        vessel_weight_kg=round(total_weight, 0),
        warnings=warnings,
        standards_refs=refs,
    )
