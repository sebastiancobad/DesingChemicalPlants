"""
ChemScale — Pump Sizing Calculation Kernel.

Implements centrifugal pump sizing: total dynamic head, hydraulic power,
brake power, NPSH available, and efficiency estimation per Hydraulic Institute
standards and API 610.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Optional

from app.core.standards import standards_ref


@dataclass
class PumpSizeResult:
    flow_rate_m3h: float
    total_dynamic_head_m: float
    static_head_m: float
    friction_head_m: float
    velocity_head_m: float
    pressure_head_m: float
    hydraulic_power_kw: float
    efficiency_pct: float
    brake_power_kw: float
    motor_power_kw: float
    motor_efficiency_pct: float
    npsh_available_m: float
    npsh_required_m: float
    npsh_margin_m: float
    npsh_ok: bool
    specific_speed: float
    pump_type_suggestion: str
    suction_velocity_ms: float
    discharge_velocity_ms: float
    warnings: list[str] = field(default_factory=list)
    standards_refs: list[str] = field(default_factory=list)


@standards_ref("Hydraulic Institute Standards, 14th Ed.")
def estimate_pump_efficiency(flow_m3h: float, head_m: float) -> float:
    """Estimate centrifugal pump efficiency from flow rate.

    Based on Hydraulic Institute typical performance curves.
    """
    if flow_m3h <= 0:
        return 30.0

    # Approximate efficiency curve for centrifugal pumps
    if flow_m3h < 5:
        eta = 35.0
    elif flow_m3h < 20:
        eta = 45.0 + 15.0 * math.log10(flow_m3h / 5.0)
    elif flow_m3h < 100:
        eta = 55.0 + 10.0 * math.log10(flow_m3h / 20.0)
    elif flow_m3h < 500:
        eta = 65.0 + 8.0 * math.log10(flow_m3h / 100.0)
    else:
        eta = 75.0 + 5.0 * math.log10(flow_m3h / 500.0)

    return min(eta, 90.0)


@standards_ref("API 610, 12th Ed. — Centrifugal Pumps for Petroleum")
def estimate_npsh_required(flow_m3h: float, speed_rpm: float = 3550) -> float:
    """Estimate NPSH required from flow and speed.

    Approximate correlation for centrifugal pumps.
    """
    Ns = speed_rpm * math.sqrt(flow_m3h / 3600.0) / (3.0**0.75) if flow_m3h > 0 else 0
    # Rough estimate: NPSHr ≈ 0.3 * (Q/speed)^(2/3) + 1.5
    npsh_r = 1.5 + 0.12 * (flow_m3h)**0.4
    return max(npsh_r, 1.0)


@standards_ref(
    "API 610, 12th Ed.",
    "Hydraulic Institute Standards",
    "Karassik, I.J., Pump Handbook, 4th Ed.",
)
def size_pump(
    flow_rate_m3h: float,
    density_kgm3: float,
    viscosity_pas: float,
    suction_pressure_pa: float,
    discharge_pressure_pa: float,
    static_head_m: float = 0.0,
    friction_loss_m: float = 0.0,
    suction_pipe_id_m: float = 0.1,
    discharge_pipe_id_m: float = 0.075,
    vapor_pressure_pa: float = 2340.0,
    suction_vessel_elevation_m: float = 0.0,
    pump_elevation_m: float = 0.0,
    speed_rpm: float = 3550.0,
    motor_efficiency_pct: float = 93.0,
    safety_factor: float = 1.1,
) -> PumpSizeResult:
    """Size a centrifugal pump: head, power, NPSH, and efficiency."""
    warnings: list[str] = []
    refs = list(size_pump.__standards_refs__)

    g = 9.81
    Q_m3s = flow_rate_m3h / 3600.0

    # Velocities
    A_suction = math.pi / 4 * suction_pipe_id_m**2
    A_discharge = math.pi / 4 * discharge_pipe_id_m**2
    v_suction = Q_m3s / A_suction if A_suction > 0 else 0
    v_discharge = Q_m3s / A_discharge if A_discharge > 0 else 0

    # Head components
    pressure_head = (discharge_pressure_pa - suction_pressure_pa) / (density_kgm3 * g)
    velocity_head = (v_discharge**2 - v_suction**2) / (2 * g)

    total_head = static_head_m + friction_loss_m + pressure_head + velocity_head
    total_head = max(total_head, 0.1)

    # Hydraulic power
    P_hydraulic = density_kgm3 * g * Q_m3s * total_head / 1000.0  # kW

    # Efficiency
    eta_pump = estimate_pump_efficiency(flow_rate_m3h, total_head)
    refs.extend(estimate_pump_efficiency.__standards_refs__)

    # Brake power
    P_brake = P_hydraulic / (eta_pump / 100.0) if eta_pump > 0 else P_hydraulic

    # Motor power (with safety factor and next standard size)
    P_motor = P_brake / (motor_efficiency_pct / 100.0) * safety_factor
    # Round up to next standard motor size
    standard_sizes = [0.37, 0.55, 0.75, 1.1, 1.5, 2.2, 3.0, 4.0, 5.5, 7.5, 11.0, 15.0,
                      18.5, 22.0, 30.0, 37.0, 45.0, 55.0, 75.0, 90.0, 110.0, 132.0,
                      160.0, 200.0, 250.0, 315.0, 355.0, 400.0, 500.0]
    for sz in standard_sizes:
        if sz >= P_motor:
            P_motor = sz
            break

    # NPSH available
    h_suction_static = suction_vessel_elevation_m - pump_elevation_m
    h_friction_suction = friction_loss_m * 0.3  # approximate suction side friction
    npsh_a = (suction_pressure_pa - vapor_pressure_pa) / (density_kgm3 * g) + h_suction_static - h_friction_suction
    npsh_a = max(npsh_a, 0)

    # NPSH required
    npsh_r = estimate_npsh_required(flow_rate_m3h, speed_rpm)
    refs.extend(estimate_npsh_required.__standards_refs__)

    npsh_margin = npsh_a - npsh_r
    npsh_ok = npsh_margin >= 1.0  # Minimum 1m margin recommended

    if not npsh_ok:
        warnings.append(
            f"NPSH margin = {npsh_margin:.2f} m (< 1.0 m) — cavitation risk. "
            "Consider raising suction vessel or reducing suction losses."
        )

    # Specific speed
    N_s = speed_rpm * math.sqrt(Q_m3s) / (total_head**0.75) if total_head > 0 else 0

    # Pump type suggestion based on specific speed
    if N_s < 15:
        pump_type = "Positive displacement (reciprocating)"
    elif N_s < 80:
        pump_type = "Centrifugal — radial flow"
    elif N_s < 160:
        pump_type = "Centrifugal — mixed flow"
    else:
        pump_type = "Centrifugal — axial flow"

    # Velocity warnings
    if v_suction > 2.0:
        warnings.append(f"Suction velocity {v_suction:.2f} m/s exceeds 2.0 m/s — increase suction pipe size")
    if v_discharge > 4.5:
        warnings.append(f"Discharge velocity {v_discharge:.2f} m/s exceeds 4.5 m/s — increase discharge pipe size")

    return PumpSizeResult(
        flow_rate_m3h=flow_rate_m3h,
        total_dynamic_head_m=round(total_head, 2),
        static_head_m=static_head_m,
        friction_head_m=friction_loss_m,
        velocity_head_m=round(velocity_head, 3),
        pressure_head_m=round(pressure_head, 2),
        hydraulic_power_kw=round(P_hydraulic, 2),
        efficiency_pct=round(eta_pump, 1),
        brake_power_kw=round(P_brake, 2),
        motor_power_kw=P_motor,
        motor_efficiency_pct=motor_efficiency_pct,
        npsh_available_m=round(npsh_a, 2),
        npsh_required_m=round(npsh_r, 2),
        npsh_margin_m=round(npsh_margin, 2),
        npsh_ok=npsh_ok,
        specific_speed=round(N_s, 1),
        pump_type_suggestion=pump_type,
        suction_velocity_ms=round(v_suction, 2),
        discharge_velocity_ms=round(v_discharge, 2),
        warnings=warnings,
        standards_refs=refs,
    )
