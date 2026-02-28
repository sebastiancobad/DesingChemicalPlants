"""
ChemScale — Piping Calculation Kernel.

Implements pipe sizing, pressure drop (Darcy-Weisbach), velocity checks,
and equivalent length calculations per ASME B31.3 and Crane TP-410.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Optional

from app.core.standards import standards_ref


# Standard pipe schedule data (NPS in inches -> OD mm, wall thickness mm)
PIPE_SCHEDULES: dict[str, dict[str, tuple[float, float]]] = {
    "SCH 40": {
        "0.5":  (21.3,  2.77),
        "0.75": (26.7,  2.87),
        "1":    (33.4,  3.38),
        "1.5":  (48.3,  3.68),
        "2":    (60.3,  3.91),
        "3":    (88.9,  5.49),
        "4":    (114.3, 6.02),
        "6":    (168.3, 7.11),
        "8":    (219.1, 8.18),
        "10":   (273.1, 9.27),
        "12":   (323.9, 10.31),
        "14":   (355.6, 11.13),
        "16":   (406.4, 12.70),
        "18":   (457.2, 14.27),
        "20":   (508.0, 15.09),
        "24":   (610.0, 17.48),
    },
    "SCH 80": {
        "0.5":  (21.3,  3.73),
        "0.75": (26.7,  3.91),
        "1":    (33.4,  4.55),
        "1.5":  (48.3,  5.08),
        "2":    (60.3,  5.54),
        "3":    (88.9,  7.62),
        "4":    (114.3, 8.56),
        "6":    (168.3, 10.97),
        "8":    (219.1, 12.70),
        "10":   (273.1, 15.09),
        "12":   (323.9, 17.48),
    },
    "SCH 160": {
        "2":    (60.3,  8.74),
        "3":    (88.9,  11.13),
        "4":    (114.3, 13.49),
        "6":    (168.3, 18.26),
        "8":    (219.1, 23.01),
        "10":   (273.1, 28.58),
        "12":   (323.9, 33.32),
    },
}

# K-values for fittings (Crane TP-410)
FITTING_K_VALUES: dict[str, float] = {
    "90_elbow_std":     0.75,
    "90_elbow_long":    0.45,
    "45_elbow":         0.35,
    "tee_thru":         0.40,
    "tee_branch":       1.50,
    "gate_valve":       0.17,
    "globe_valve":      6.00,
    "check_valve_swing": 2.00,
    "ball_valve":       0.05,
    "butterfly_valve":  0.25,
    "reducer":          0.50,
    "expander":         1.00,
    "entrance_sharp":   0.50,
    "entrance_rounded": 0.04,
    "exit":             1.00,
}


@dataclass
class PipeSizeResult:
    nps: str
    schedule: str
    outer_diameter_mm: float
    wall_thickness_mm: float
    inner_diameter_mm: float
    flow_area_m2: float
    velocity_ms: float
    reynolds: float
    friction_factor: float
    pressure_drop_pa_per_m: float
    total_pressure_drop_pa: float
    pipe_length_m: float
    equivalent_length_fittings_m: float
    total_equivalent_length_m: float
    velocity_ok: bool
    velocity_message: str
    warnings: list[str] = field(default_factory=list)
    standards_refs: list[str] = field(default_factory=list)


@standards_ref("Crane TP-410, Flow of Fluids Through Valves, Fittings, and Pipe")
def colebrook_friction_factor(Re: float, roughness: float, diameter: float) -> float:
    """Solve Colebrook-White equation for Darcy friction factor.

    Uses Swamee-Jain explicit approximation for initial guess,
    then one Newton iteration for accuracy.
    """
    if Re < 2300:
        return 64.0 / max(Re, 1.0)

    e_d = roughness / diameter

    # Swamee-Jain approximation
    f = 0.25 / (math.log10(e_d / 3.7 + 5.74 / Re**0.9))**2

    # One Newton-Raphson iteration on Colebrook
    sqrt_f = math.sqrt(f)
    rhs = -2.0 * math.log10(e_d / 3.7 + 2.51 / (Re * sqrt_f))
    lhs = 1.0 / sqrt_f
    deriv = -0.5 / (f * sqrt_f)
    correction = (lhs - rhs) / (deriv + 2.51 * 0.5 / (Re * f * sqrt_f * math.log(10)))
    f = max(f - correction * 0.5, 0.001)

    return f


@standards_ref(
    "ASME B31.3 Process Piping",
    "Crane TP-410",
    "API RP 14E (erosional velocity)",
)
def size_pipe(
    mass_flow_kgs: float,
    density_kgm3: float,
    viscosity_pas: float,
    pipe_length_m: float = 100.0,
    elevation_change_m: float = 0.0,
    roughness_m: float = 0.000046,  # commercial steel
    schedule: str = "SCH 40",
    nps: str | None = None,
    fittings: dict[str, int] | None = None,
    fluid_phase: str = "liquid",
    max_velocity_ms: float | None = None,
) -> PipeSizeResult:
    """Size a pipe and calculate pressure drop using Darcy-Weisbach.

    If nps is not provided, auto-selects the smallest pipe that keeps
    velocity within recommended limits.
    """
    warnings: list[str] = []
    refs = list(size_pipe.__standards_refs__)

    sched_data = PIPE_SCHEDULES.get(schedule)
    if sched_data is None:
        raise ValueError(f"Unknown schedule '{schedule}'. Available: {list(PIPE_SCHEDULES.keys())}")

    vol_flow = mass_flow_kgs / density_kgm3  # m³/s

    # Velocity limits
    if max_velocity_ms is None:
        if fluid_phase == "gas":
            max_velocity_ms = 30.0
        else:
            max_velocity_ms = 3.0

    # Auto-select NPS if not specified
    if nps is None:
        for candidate_nps in sorted(sched_data.keys(), key=lambda x: float(x)):
            od_mm, wt_mm = sched_data[candidate_nps]
            id_mm = od_mm - 2 * wt_mm
            id_m = id_mm / 1000.0
            area = math.pi / 4 * id_m**2
            vel = vol_flow / area
            if vel <= max_velocity_ms:
                nps = candidate_nps
                break
        if nps is None:
            nps = max(sched_data.keys(), key=lambda x: float(x))
            warnings.append("Largest available NPS selected; velocity may still exceed limit")

    if nps not in sched_data:
        raise ValueError(f"NPS '{nps}' not available in {schedule}")

    od_mm, wt_mm = sched_data[nps]
    id_mm = od_mm - 2 * wt_mm
    id_m = id_mm / 1000.0
    area = math.pi / 4 * id_m**2
    velocity = vol_flow / area

    Re = density_kgm3 * velocity * id_m / viscosity_pas

    f_darcy = colebrook_friction_factor(Re, roughness_m, id_m)
    refs.extend(colebrook_friction_factor.__standards_refs__)

    # Equivalent length of fittings
    eq_length_fittings = 0.0
    if fittings:
        for fitting_type, count in fittings.items():
            K = FITTING_K_VALUES.get(fitting_type, 0.0)
            # L_eq = K * D / f
            eq_length_fittings += count * K * id_m / f_darcy if f_darcy > 0 else 0

    total_eq_length = pipe_length_m + eq_length_fittings

    # Pressure drop: ΔP = f * (L/D) * ρv²/2 + ρgh
    dp_friction = f_darcy * (total_eq_length / id_m) * density_kgm3 * velocity**2 / 2.0
    dp_elevation = density_kgm3 * 9.81 * elevation_change_m
    dp_total = dp_friction + dp_elevation
    dp_per_m = dp_friction / total_eq_length if total_eq_length > 0 else 0

    # Velocity check
    velocity_ok = velocity <= max_velocity_ms
    if velocity > max_velocity_ms:
        velocity_message = f"Velocity {velocity:.2f} m/s exceeds limit {max_velocity_ms:.1f} m/s — consider larger pipe"
        warnings.append(velocity_message)
    elif velocity < 0.5 and fluid_phase == "liquid":
        velocity_message = f"Velocity {velocity:.2f} m/s is low — settling/fouling risk"
        warnings.append(velocity_message)
    else:
        velocity_message = f"Velocity {velocity:.2f} m/s is within acceptable range"

    # Erosional velocity check (API RP 14E)
    v_erosional = 122.0 / math.sqrt(density_kgm3) if density_kgm3 > 0 else 999
    if velocity > v_erosional:
        warnings.append(f"Velocity exceeds erosional limit ({v_erosional:.1f} m/s per API RP 14E)")

    return PipeSizeResult(
        nps=nps,
        schedule=schedule,
        outer_diameter_mm=od_mm,
        wall_thickness_mm=wt_mm,
        inner_diameter_mm=id_mm,
        flow_area_m2=area,
        velocity_ms=velocity,
        reynolds=Re,
        friction_factor=f_darcy,
        pressure_drop_pa_per_m=dp_per_m,
        total_pressure_drop_pa=dp_total,
        pipe_length_m=pipe_length_m,
        equivalent_length_fittings_m=eq_length_fittings,
        total_equivalent_length_m=total_eq_length,
        velocity_ok=velocity_ok,
        velocity_message=velocity_message,
        warnings=warnings,
        standards_refs=refs,
    )
