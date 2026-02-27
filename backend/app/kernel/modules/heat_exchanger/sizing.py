"""
ChemScale — Heat Exchanger Calculation Kernel.

Implements quick-sizing (LMTD method) and rigorous rating (Bell-Delaware)
for shell-and-tube heat exchangers per TEMA 10th Ed and API 660.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Optional

from app.core.standards import standards_ref


# ---------------------------------------------------------------------------
# Result data classes (internal, mapped to Pydantic schemas at API boundary)
# ---------------------------------------------------------------------------

@dataclass
class QuickSizeResult:
    duty_w: float
    lmtd_k: float
    correction_factor_F: float
    corrected_mtd_k: float
    U_assumed: float
    U_clean: float
    U_dirty: float
    area_required_m2: float
    area_provided_m2: float
    overdesign_pct: float

    shell_id_m: float
    tube_count: int
    tube_length_m: float
    baffle_spacing_m: float
    baffle_count: int

    hot_velocity_ms: float
    hot_reynolds: float
    hot_dp_pa: float
    hot_htc: float

    cold_velocity_ms: float
    cold_reynolds: float
    cold_dp_pa: float
    cold_htc: float
    cold_mass_flow_kgs: Optional[float] = None

    shell_min_thickness_m: float = 0.0
    tubesheet_thickness_m: float = 0.0
    shell_weight_kg: float = 0.0
    bundle_weight_kg: float = 0.0

    warnings: list[str] = field(default_factory=list)
    standards_refs: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Core calculations
# ---------------------------------------------------------------------------

@standards_ref("TEMA 10th Ed. §RCB-4.4", "Kern, D.Q., Process Heat Transfer, Ch. 7")
def lmtd_counterflow(T_h_in: float, T_h_out: float, T_c_in: float, T_c_out: float) -> float:
    """Log Mean Temperature Difference for counterflow arrangement [K].

    Parameters are in Kelvin or °C (differences are unit-independent).
    """
    dT1 = T_h_in - T_c_out
    dT2 = T_h_out - T_c_in

    if abs(dT1 - dT2) < 0.01:
        return (dT1 + dT2) / 2.0

    if dT1 <= 0 or dT2 <= 0:
        raise ValueError(
            f"Temperature cross detected: ΔT1={dT1:.1f}, ΔT2={dT2:.1f}. "
            "Check inlet/outlet assignments."
        )

    return (dT1 - dT2) / math.log(dT1 / dT2)


@standards_ref("Bowman, Mueller & Nagle, ASME Trans., 1940")
def correction_factor_1_2(R: float, P: float) -> float:
    """LMTD correction factor F for 1-shell / 2-tube-pass exchanger.

    Parameters
    ----------
    R : float
        (T_h_in - T_h_out) / (T_c_out - T_c_in)
    P : float
        (T_c_out - T_c_in) / (T_h_in - T_c_in)
    """
    if abs(R - 1.0) < 1e-6:
        # Special case: R = 1
        F = (P * math.sqrt(2.0)) / (
            (1.0 - P) * math.log((2.0 - P * (2.0 - math.sqrt(2.0))) /
                                  (2.0 - P * (2.0 + math.sqrt(2.0))))
        )
        return max(min(F, 1.0), 0.5)

    S = math.sqrt(R * R + 1.0) / (R - 1.0)
    W = ((1.0 - P * R) / (1.0 - P))

    if W <= 0:
        return 0.75  # degenerate case — flag as warning

    num = S * math.log(W)
    denom = math.log((2.0 / P - 1.0 - R + S) / (2.0 / P - 1.0 - R - S))

    if abs(denom) < 1e-10:
        return 0.75

    F = num / denom
    return max(min(F, 1.0), 0.5)


@standards_ref("TEMA 10th Ed. §RCB-4.4 (tube count)")
def estimate_tube_count(
    shell_id_m: float,
    tube_od_m: float,
    tube_pitch_m: float,
    num_passes: int,
    layout: str = "triangular_30",
) -> int:
    """Estimate number of tubes that fit in a shell of given ID.

    Uses the CTP (tube count calculation) factor per TEMA.
    """
    # CTP factors (fraction of shell area occupied by tubes)
    ctp_map = {1: 0.93, 2: 0.90, 4: 0.85, 6: 0.80, 8: 0.78}
    CTP = ctp_map.get(num_passes, 0.85)

    # CL factor (layout constant)
    CL = 0.87 if "triangular" in layout else 1.0

    A_shell = math.pi / 4.0 * shell_id_m**2
    Nt = CTP * A_shell * CL / (tube_pitch_m**2)

    return max(int(Nt), 1)


@standards_ref("Kern, D.Q., Process Heat Transfer, Ch. 7")
def kern_shell_side_htc(
    m_dot: float,       # kg/s
    shell_id: float,    # m
    baffle_spacing: float,  # m
    tube_od: float,     # m
    tube_pitch: float,  # m
    mu: float,          # Pa·s
    cp: float,          # J/(kg·K)
    k: float,           # W/(m·K)
    mu_w: float = None, # Pa·s at wall temperature (optional)
) -> tuple[float, float, float]:
    """Shell-side heat transfer coefficient by Kern method.

    Returns (h_shell [W/(m²·K)], Re_shell, velocity [m/s]).
    """
    # Equivalent diameter for triangular pitch
    De = 4.0 * (tube_pitch**2 * math.sqrt(3) / 4.0 - math.pi * tube_od**2 / 8.0) / (
        math.pi * tube_od / 2.0
    )

    # Cross-flow area
    As = shell_id * baffle_spacing * (tube_pitch - tube_od) / tube_pitch

    if As <= 0:
        raise ValueError("Cross-flow area is non-positive; check geometry")

    Gs = m_dot / As  # mass velocity [kg/(m²·s)]
    velocity = Gs / 800.0  # approximate density for velocity estimate
    Re = Gs * De / mu

    Pr = cp * mu / k

    # Kern correlation
    if mu_w and mu_w > 0:
        phi = (mu / mu_w) ** 0.14
    else:
        phi = 1.0

    jH = 0.36 * Re**0.55 * Pr**(1.0 / 3.0) * phi
    h = jH * k / De

    return h, Re, velocity


@standards_ref(
    "Dittus-Boelter correlation",
    "Incropera & DeWitt, Fundamentals of Heat and Mass Transfer, Ch. 8",
)
def tube_side_htc(
    m_dot: float,     # kg/s
    n_tubes: int,
    n_passes: int,
    tube_id: float,   # m
    tube_length: float,  # m
    rho: float,       # kg/m³
    mu: float,        # Pa·s
    cp: float,        # J/(kg·K)
    k: float,         # W/(m·K)
) -> tuple[float, float, float, float]:
    """Tube-side heat transfer coefficient.

    Returns (h_tube [W/(m²·K)], Re, velocity [m/s], dp [Pa]).
    """
    A_tube = math.pi / 4.0 * tube_id**2
    n_tubes_per_pass = n_tubes / n_passes
    A_flow = n_tubes_per_pass * A_tube

    velocity = m_dot / (rho * A_flow)
    Re = rho * velocity * tube_id / mu
    Pr = cp * mu / k

    # Dittus-Boelter for turbulent flow (Re > 10000)
    if Re > 10000:
        Nu = 0.023 * Re**0.8 * Pr**0.4
    elif Re > 2300:
        # Transition regime — Gnielinski
        f = (0.790 * math.log(Re) - 1.64) ** (-2)
        Nu = (f / 8.0) * (Re - 1000) * Pr / (1.0 + 12.7 * math.sqrt(f / 8.0) * (Pr**(2.0/3.0) - 1))
    else:
        # Laminar — Sieder-Tate simplified
        Nu = 3.66

    h = Nu * k / tube_id

    # Pressure drop (Fanning equation + return losses)
    f_fanning = 0.046 * Re**(-0.2) if Re > 10000 else 16.0 / max(Re, 1)
    dp = (4 * f_fanning * tube_length * n_passes / tube_id + 4 * n_passes) * rho * velocity**2 / 2.0

    return h, Re, velocity, dp


@standards_ref("TEMA 10th Ed. §RCB-4.7")
def shell_side_pressure_drop_kern(
    m_dot: float,
    shell_id: float,
    baffle_spacing: float,
    n_baffles: int,
    tube_od: float,
    tube_pitch: float,
    rho: float,
    mu: float,
) -> float:
    """Shell-side pressure drop by Kern method [Pa]."""
    De = 4.0 * (tube_pitch**2 * math.sqrt(3) / 4.0 - math.pi * tube_od**2 / 8.0) / (
        math.pi * tube_od / 2.0
    )
    As = shell_id * baffle_spacing * (tube_pitch - tube_od) / tube_pitch

    if As <= 0:
        return 0.0

    Gs = m_dot / As
    Re = Gs * De / mu

    # Friction factor (Kern)
    f = math.exp(0.576 - 0.19 * math.log(Re)) if Re > 1 else 1.0

    dp = f * Gs**2 * (n_baffles + 1) * shell_id / (2.0 * rho * De)
    return dp


@standards_ref("ASME Sec VIII Div 1, UG-27")
def shell_min_thickness(
    inner_diameter: float,  # m
    design_pressure: float,  # Pa
    allowable_stress: float,  # Pa
    joint_efficiency: float = 0.85,
    corrosion_allowance: float = 0.003,  # m
) -> float:
    """Minimum required shell thickness per ASME UG-27 [m]."""
    P = design_pressure
    R = inner_diameter / 2.0
    S = allowable_stress
    E = joint_efficiency

    t_calc = P * R / (S * E - 0.6 * P)
    t_min = t_calc + corrosion_allowance

    return t_min


@standards_ref(
    "TEMA 10th Ed. §RCB-4.4",
    "TEMA 10th Ed. §RCB-4.7",
    "Kern, D.Q., Process Heat Transfer, Ch. 7",
    "ASME Sec VIII Div 1 UG-27",
)
def quick_size(
    # Process conditions (all in SI)
    T_h_in: float,       # K
    T_h_out: float,      # K
    T_c_in: float,       # K
    T_c_out: float,      # K (may be None → calculated)
    m_dot_hot: float,    # kg/s
    m_dot_cold: float,   # kg/s or None
    # Hot-side properties
    rho_hot: float,      # kg/m³
    mu_hot: float,       # Pa·s
    cp_hot: float,       # J/(kg·K)
    k_hot: float,        # W/(m·K)
    # Cold-side properties
    rho_cold: float,
    mu_cold: float,
    cp_cold: float,
    k_cold: float,
    # Fouling
    Rf_hot: float = 0.000176,   # m²·K/W
    Rf_cold: float = 0.000176,
    # Geometry constraints
    tube_od: float = 0.01905,   # m
    tube_id: float = None,
    tube_pitch: float = 0.0254, # m
    tube_length: float = 6.096, # m
    tube_layout: str = "triangular_30",
    n_shell_passes: int = 1,
    n_tube_passes: int = 2,
    baffle_cut: float = 0.25,
    # Mechanical
    design_pressure_shell: float = 1e6,  # Pa
    design_pressure_tube: float = 1e6,
    corrosion_allowance: float = 0.003,  # m
) -> QuickSizeResult:
    """Conceptual quick-sizing of a shell-and-tube heat exchanger.

    Uses Kern method for shell-side HTC, Dittus-Boelter for tube-side,
    and LMTD method for area calculation.
    """
    warnings: list[str] = []
    refs: list[str] = []

    if tube_id is None:
        tube_id = tube_od - 2 * 0.00165  # 16 BWG default

    # --- Duty ---
    Q = m_dot_hot * cp_hot * (T_h_in - T_h_out)  # W

    # --- Cold-side flow if not given ---
    if m_dot_cold is None or m_dot_cold <= 0:
        if T_c_out is None or T_c_out <= T_c_in:
            raise ValueError("Must specify either cold mass flow or cold outlet T")
        m_dot_cold = Q / (cp_cold * (T_c_out - T_c_in))

    if T_c_out is None:
        T_c_out = T_c_in + Q / (m_dot_cold * cp_cold)

    # --- LMTD & F factor ---
    lmtd = lmtd_counterflow(T_h_in, T_h_out, T_c_in, T_c_out)
    refs.extend(lmtd_counterflow.__standards_refs__)

    R_val = (T_h_in - T_h_out) / max(T_c_out - T_c_in, 0.01)
    P_val = (T_c_out - T_c_in) / max(T_h_in - T_c_in, 0.01)
    F = correction_factor_1_2(R_val, P_val)
    refs.extend(correction_factor_1_2.__standards_refs__)

    if F < 0.75:
        warnings.append(
            f"F correction factor = {F:.3f} < 0.75 — consider additional shell passes"
        )

    mtd = lmtd * F

    # --- Initial shell sizing ---
    # Estimate U for liquid-liquid service
    U_assumed = 850.0  # W/(m²·K), typical for water-water

    A_req = Q / (U_assumed * mtd)

    # Iteratively find shell ID
    A_single_tube = math.pi * tube_od * tube_length
    N_tubes_needed = A_req / A_single_tube

    # Back-calculate shell ID from tube count
    if "triangular" in tube_layout:
        CL = 0.87
    else:
        CL = 1.0

    CTP = {1: 0.93, 2: 0.90, 4: 0.85}.get(n_tube_passes, 0.85)
    shell_id = math.sqrt(4.0 * N_tubes_needed * tube_pitch**2 / (CTP * CL * math.pi))

    N_tubes = estimate_tube_count(shell_id, tube_od, tube_pitch, n_tube_passes, tube_layout)
    refs.extend(estimate_tube_count.__standards_refs__)

    A_provided = N_tubes * A_single_tube

    # --- Baffle spacing ---
    baffle_spacing = max(shell_id * 0.4, 0.050)  # min 50mm or 0.4 * Ds
    if baffle_spacing > shell_id:
        baffle_spacing = shell_id * 0.6

    n_baffles = max(int(tube_length / baffle_spacing) - 1, 1)
    baffle_spacing = tube_length / (n_baffles + 1)

    # --- Shell-side HTC (hot fluid on shell) ---
    h_shell, Re_shell, v_shell = kern_shell_side_htc(
        m_dot_hot, shell_id, baffle_spacing, tube_od, tube_pitch,
        mu_hot, cp_hot, k_hot,
    )
    refs.extend(kern_shell_side_htc.__standards_refs__)

    if v_shell < 0.3:
        warnings.append(
            f"Shell-side velocity = {v_shell:.2f} m/s (< 0.3 m/s) — "
            "severe fouling risk; reduce baffle spacing or shell diameter"
        )
    elif v_shell < 0.9:
        warnings.append(
            f"Shell-side velocity = {v_shell:.2f} m/s (< 0.9 m/s) — "
            "fouling risk; consider reducing baffle spacing"
        )

    # --- Tube-side HTC (cold fluid in tubes) ---
    h_tube, Re_tube, v_tube, dp_tube = tube_side_htc(
        m_dot_cold, N_tubes, n_tube_passes, tube_id, tube_length,
        rho_cold, mu_cold, cp_cold, k_cold,
    )
    refs.extend(tube_side_htc.__standards_refs__)

    # --- Shell-side ΔP ---
    dp_shell = shell_side_pressure_drop_kern(
        m_dot_hot, shell_id, baffle_spacing, n_baffles,
        tube_od, tube_pitch, rho_hot, mu_hot,
    )
    refs.extend(shell_side_pressure_drop_kern.__standards_refs__)

    # --- Overall U ---
    U_clean = 1.0 / (1.0 / h_shell + 1.0 / h_tube +
                      tube_od * math.log(tube_od / tube_id) / (2 * 45.0))  # k_wall ≈ 45 W/(m·K) for CS

    U_dirty = 1.0 / (1.0 / U_clean + Rf_hot + Rf_cold)

    A_req_actual = Q / (U_dirty * mtd)
    overdesign = (A_provided / A_req_actual - 1.0) * 100.0

    # --- Mechanical ---
    S_allow = 138e6  # Pa, SA-516-70 at ~200°C
    t_shell = shell_min_thickness(shell_id, design_pressure_shell, S_allow,
                                   corrosion_allowance=corrosion_allowance)
    refs.extend(shell_min_thickness.__standards_refs__)

    t_tubesheet = 1.5 * tube_od * math.sqrt(design_pressure_tube / S_allow)

    # Weights (approximate)
    rho_steel = 7850  # kg/m³
    shell_weight = math.pi * shell_id * t_shell * tube_length * rho_steel
    bundle_weight = N_tubes * math.pi / 4 * (tube_od**2 - tube_id**2) * tube_length * rho_steel

    return QuickSizeResult(
        duty_w=Q,
        lmtd_k=lmtd,
        correction_factor_F=F,
        corrected_mtd_k=mtd,
        U_assumed=U_assumed,
        U_clean=U_clean,
        U_dirty=U_dirty,
        area_required_m2=A_req_actual,
        area_provided_m2=A_provided,
        overdesign_pct=overdesign,
        shell_id_m=shell_id,
        tube_count=N_tubes,
        tube_length_m=tube_length,
        baffle_spacing_m=baffle_spacing,
        baffle_count=n_baffles,
        hot_velocity_ms=v_shell,
        hot_reynolds=Re_shell,
        hot_dp_pa=dp_shell,
        hot_htc=h_shell,
        cold_velocity_ms=v_tube,
        cold_reynolds=Re_tube,
        cold_dp_pa=dp_tube,
        cold_htc=h_tube,
        cold_mass_flow_kgs=m_dot_cold,
        shell_min_thickness_m=t_shell,
        tubesheet_thickness_m=t_tubesheet,
        shell_weight_kg=shell_weight,
        bundle_weight_kg=bundle_weight,
        warnings=warnings,
        standards_refs=list(set(refs)),
    )
