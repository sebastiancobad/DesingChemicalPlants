"""
ChemScale — Plant Layout & Spacing Calculation Kernel.

Implements minimum spacing rules between equipment per NFPA 30,
API 2510, and company engineering standards.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from app.core.standards import standards_ref


# Equipment categories and their fire/explosion risk levels
EQUIPMENT_RISK: dict[str, str] = {
    "fired_heater": "high",
    "furnace": "high",
    "flare_stack": "high",
    "cooling_tower": "moderate",
    "compressor": "moderate",
    "pump": "moderate",
    "heat_exchanger": "low",
    "pressure_vessel": "moderate",
    "column": "moderate",
    "reactor": "high",
    "storage_tank_atmospheric": "moderate",
    "storage_tank_pressurized": "high",
    "control_room": "occupied",
    "substation": "occupied",
    "loading_area": "high",
    "pipe_rack": "low",
}


# Minimum spacing table (meters) — from–to pairs
# Based on major EPC company standards and NFPA 30
SPACING_TABLE: dict[tuple[str, str], float] = {
    # Fired heaters to everything
    ("fired_heater", "pressure_vessel"): 15.0,
    ("fired_heater", "column"): 15.0,
    ("fired_heater", "compressor"): 15.0,
    ("fired_heater", "pump"): 15.0,
    ("fired_heater", "heat_exchanger"): 15.0,
    ("fired_heater", "storage_tank_atmospheric"): 30.0,
    ("fired_heater", "storage_tank_pressurized"): 60.0,
    ("fired_heater", "control_room"): 30.0,
    ("fired_heater", "cooling_tower"): 30.0,
    ("fired_heater", "loading_area"): 30.0,
    ("fired_heater", "pipe_rack"): 9.0,
    ("fired_heater", "reactor"): 15.0,
    ("fired_heater", "fired_heater"): 9.0,
    ("fired_heater", "flare_stack"): 60.0,
    # Compressors
    ("compressor", "pressure_vessel"): 9.0,
    ("compressor", "column"): 9.0,
    ("compressor", "pump"): 5.0,
    ("compressor", "heat_exchanger"): 5.0,
    ("compressor", "storage_tank_atmospheric"): 15.0,
    ("compressor", "storage_tank_pressurized"): 30.0,
    ("compressor", "control_room"): 15.0,
    ("compressor", "cooling_tower"): 15.0,
    ("compressor", "pipe_rack"): 5.0,
    ("compressor", "compressor"): 3.0,
    # Pumps
    ("pump", "pressure_vessel"): 5.0,
    ("pump", "column"): 5.0,
    ("pump", "heat_exchanger"): 3.0,
    ("pump", "storage_tank_atmospheric"): 9.0,
    ("pump", "storage_tank_pressurized"): 15.0,
    ("pump", "control_room"): 15.0,
    ("pump", "pipe_rack"): 3.0,
    ("pump", "pump"): 2.0,
    # Columns
    ("column", "column"): 5.0,
    ("column", "pressure_vessel"): 5.0,
    ("column", "heat_exchanger"): 3.0,
    ("column", "storage_tank_atmospheric"): 15.0,
    ("column", "storage_tank_pressurized"): 30.0,
    ("column", "control_room"): 15.0,
    ("column", "pipe_rack"): 5.0,
    # Pressure vessels
    ("pressure_vessel", "pressure_vessel"): 3.0,
    ("pressure_vessel", "heat_exchanger"): 3.0,
    ("pressure_vessel", "storage_tank_atmospheric"): 15.0,
    ("pressure_vessel", "storage_tank_pressurized"): 15.0,
    ("pressure_vessel", "control_room"): 15.0,
    ("pressure_vessel", "pipe_rack"): 3.0,
    # Heat exchangers
    ("heat_exchanger", "heat_exchanger"): 2.0,
    ("heat_exchanger", "storage_tank_atmospheric"): 15.0,
    ("heat_exchanger", "storage_tank_pressurized"): 15.0,
    ("heat_exchanger", "control_room"): 15.0,
    ("heat_exchanger", "pipe_rack"): 3.0,
    # Storage tanks
    ("storage_tank_atmospheric", "storage_tank_atmospheric"): 15.0,
    ("storage_tank_atmospheric", "storage_tank_pressurized"): 30.0,
    ("storage_tank_atmospheric", "control_room"): 30.0,
    ("storage_tank_atmospheric", "pipe_rack"): 9.0,
    ("storage_tank_pressurized", "storage_tank_pressurized"): 15.0,
    ("storage_tank_pressurized", "control_room"): 60.0,
    ("storage_tank_pressurized", "pipe_rack"): 15.0,
    # Flare stack
    ("flare_stack", "control_room"): 90.0,
    ("flare_stack", "storage_tank_atmospheric"): 60.0,
    ("flare_stack", "storage_tank_pressurized"): 60.0,
    ("flare_stack", "compressor"): 60.0,
    ("flare_stack", "pump"): 60.0,
    ("flare_stack", "pressure_vessel"): 60.0,
    ("flare_stack", "column"): 60.0,
    ("flare_stack", "heat_exchanger"): 60.0,
    ("flare_stack", "cooling_tower"): 60.0,
    ("flare_stack", "pipe_rack"): 30.0,
    ("flare_stack", "loading_area"): 60.0,
    ("flare_stack", "flare_stack"): 30.0,
    # Control room
    ("control_room", "control_room"): 0.0,
    ("control_room", "pipe_rack"): 9.0,
    # Pipe rack
    ("pipe_rack", "pipe_rack"): 6.0,
    # Cooling tower
    ("cooling_tower", "control_room"): 15.0,
    ("cooling_tower", "storage_tank_atmospheric"): 15.0,
    ("cooling_tower", "storage_tank_pressurized"): 30.0,
    ("cooling_tower", "cooling_tower"): 9.0,
    ("cooling_tower", "pipe_rack"): 5.0,
    # Loading area
    ("loading_area", "control_room"): 30.0,
    ("loading_area", "storage_tank_atmospheric"): 15.0,
    ("loading_area", "storage_tank_pressurized"): 30.0,
    ("loading_area", "loading_area"): 9.0,
    ("loading_area", "pipe_rack"): 9.0,
    # Reactor
    ("reactor", "reactor"): 9.0,
    ("reactor", "column"): 9.0,
    ("reactor", "pressure_vessel"): 9.0,
    ("reactor", "compressor"): 15.0,
    ("reactor", "pump"): 9.0,
    ("reactor", "heat_exchanger"): 5.0,
    ("reactor", "storage_tank_atmospheric"): 30.0,
    ("reactor", "storage_tank_pressurized"): 30.0,
    ("reactor", "control_room"): 30.0,
    ("reactor", "pipe_rack"): 5.0,
    ("reactor", "flare_stack"): 60.0,
}


@dataclass
class SpacingResult:
    equipment_a: str
    equipment_b: str
    minimum_distance_m: float
    risk_level_a: str
    risk_level_b: str
    governing_standard: str
    notes: str


@dataclass
class LayoutResult:
    spacing_checks: list[SpacingResult]
    total_violations: int
    plot_area_estimate_m2: float
    plot_dimensions_m: tuple[float, float]
    equipment_list: list[str]
    warnings: list[str] = field(default_factory=list)
    standards_refs: list[str] = field(default_factory=list)


def _get_spacing(equip_a: str, equip_b: str) -> float:
    """Look up minimum spacing (symmetric lookup)."""
    d = SPACING_TABLE.get((equip_a, equip_b))
    if d is not None:
        return d
    d = SPACING_TABLE.get((equip_b, equip_a))
    if d is not None:
        return d
    # Default: use risk-based estimate
    risk_a = EQUIPMENT_RISK.get(equip_a, "moderate")
    risk_b = EQUIPMENT_RISK.get(equip_b, "moderate")
    risk_map = {"low": 3.0, "moderate": 9.0, "high": 15.0, "occupied": 15.0}
    return max(risk_map.get(risk_a, 9.0), risk_map.get(risk_b, 9.0))


@standards_ref(
    "NFPA 30 — Flammable and Combustible Liquids Code",
    "API 2510 — Design of LP-Gas Installations",
    "IP Model Code of Safe Practice, Part 19",
)
def check_layout(
    equipment_list: list[dict[str, str]],
    proposed_distances: list[dict] | None = None,
) -> LayoutResult:
    """Check minimum spacing between all equipment pairs.

    Parameters
    ----------
    equipment_list : list of dict
        Each dict has 'tag' (e.g. 'E-101') and 'type' (e.g. 'heat_exchanger').
    proposed_distances : list of dict, optional
        Each dict has 'from_tag', 'to_tag', 'distance_m'.
    """
    warnings: list[str] = []
    refs = list(check_layout.__standards_refs__)

    spacing_checks: list[SpacingResult] = []
    violations = 0

    # Build proposed distance lookup
    dist_lookup: dict[tuple[str, str], float] = {}
    if proposed_distances:
        for d in proposed_distances:
            key = (d["from_tag"], d["to_tag"])
            dist_lookup[key] = d["distance_m"]
            dist_lookup[(d["to_tag"], d["from_tag"])] = d["distance_m"]

    # Check all pairs
    tags = {e["tag"]: e["type"] for e in equipment_list}
    tag_list = list(tags.keys())

    for i in range(len(tag_list)):
        for j in range(i + 1, len(tag_list)):
            tag_a = tag_list[i]
            tag_b = tag_list[j]
            type_a = tags[tag_a]
            type_b = tags[tag_b]

            min_dist = _get_spacing(type_a, type_b)
            risk_a = EQUIPMENT_RISK.get(type_a, "moderate")
            risk_b = EQUIPMENT_RISK.get(type_b, "moderate")

            proposed = dist_lookup.get((tag_a, tag_b))
            if proposed is not None and proposed < min_dist:
                violations += 1
                warnings.append(
                    f"{tag_a} to {tag_b}: {proposed:.1f}m < minimum {min_dist:.1f}m"
                )

            governing = "NFPA 30 / API 2510"
            if "flare" in type_a or "flare" in type_b:
                governing = "API 2510 / Company Standard"
            elif "storage" in type_a or "storage" in type_b:
                governing = "NFPA 30"

            notes = ""
            if risk_a == "high" or risk_b == "high":
                notes = "High-risk equipment — verify with Hazard Analysis"

            spacing_checks.append(SpacingResult(
                equipment_a=f"{tag_a} ({type_a})",
                equipment_b=f"{tag_b} ({type_b})",
                minimum_distance_m=min_dist,
                risk_level_a=risk_a,
                risk_level_b=risk_b,
                governing_standard=governing,
                notes=notes,
            ))

    # Rough plot area estimate
    n = len(equipment_list)
    if n <= 1:
        area = 100.0
    else:
        avg_spacing = sum(s.minimum_distance_m for s in spacing_checks) / max(len(spacing_checks), 1)
        area = (avg_spacing * 1.5)**2 * n * 0.6
    side = area**0.5

    return LayoutResult(
        spacing_checks=spacing_checks,
        total_violations=violations,
        plot_area_estimate_m2=round(area, 0),
        plot_dimensions_m=(round(side, 0), round(side * 1.2, 0)),
        equipment_list=[f"{e['tag']} ({e['type']})" for e in equipment_list],
        warnings=warnings,
        standards_refs=refs,
    )
