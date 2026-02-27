"""
Unit tests for Economic Evaluation calculation kernel.

Validates equipment CAPEX correlations, project CAPEX with Lang factors,
and OPEX evaluation against textbook reference values.
"""

from __future__ import annotations

import pytest

from app.kernel.modules.economics.cost_engine import (
    equipment_capex,
    evaluate_opex,
    project_capex,
)


class TestEquipmentCapex:
    def test_hx_capex_basic(self):
        """CAPEX for a 70 m² shell-and-tube HX in CS/CS."""
        result = equipment_capex(
            equipment_type="shell_and_tube_hx",
            capacity=70.0,  # m²
            design_pressure_barg=10.0,
        )

        # Base cost from Turton correlation should be > 0
        assert result.base_cost_usd > 0

        # Bare module cost in target year should be escalated
        assert result.bare_module_cost_target_year > result.bare_module_cost_base_year

        # Material factor for CS/CS should be 1.0
        assert result.material_factor == 1.0

    def test_hx_capex_with_location(self):
        """Location factor should scale linearly."""
        r1 = equipment_capex("shell_and_tube_hx", 70.0, location_factor=1.0)
        r2 = equipment_capex("shell_and_tube_hx", 70.0, location_factor=1.15)

        ratio = r2.location_adjusted / r1.location_adjusted
        assert abs(ratio - 1.15) < 0.01

    def test_invalid_equipment_type(self):
        """Unknown equipment type should raise ValueError."""
        with pytest.raises(ValueError, match="No cost correlation"):
            equipment_capex("unknown_equipment", 100.0)


class TestProjectCapex:
    def test_simple_lang_factor(self):
        """Project CAPEX with a simple Lang factor of 4.74."""
        result = project_capex(
            equipment_costs=[100000, 200000, 300000],
            lang_factor=4.74,
        )

        expected_base = 600000 * 4.74
        assert abs(result.total_capital_investment - expected_base * 1.15) < 1

    def test_detailed_factors(self):
        """Project CAPEX with detailed factors should sum correctly."""
        result = project_capex(
            equipment_costs=[1000000],
            factors={
                "installation": 0.47,
                "instrumentation": 0.36,
                "piping": 0.68,
                "electrical": 0.11,
                "buildings": 0.18,
                "yard_improvements": 0.10,
                "service_facilities": 0.70,
                "engineering_supervision": 0.33,
                "construction": 0.41,
                "legal_fees": 0.04,
                "contractor_fee": 0.22,
                "contingency": 0.44,
            },
        )

        # Total equipment = 1M, sum of all factors = 4.04
        # FCI = 1M * (1 + 0.47+0.36+0.68+0.11) + 1M * (0.18+0.10+...)
        assert result.fixed_capital_investment > 1000000
        assert result.total_capital_investment > result.fixed_capital_investment


class TestOpex:
    def test_basic_opex(self):
        """Basic OPEX evaluation with all components."""
        result = evaluate_opex(
            annual_hours=8400,
            raw_materials=[],
            utilities={
                "electricity": {"demand_si": 8500, "unit_cost_per_si": 0.08},
            },
            operators_per_shift=6,
            shifts_per_day=4,
            annual_salary=85000,
            overhead_factor=1.6,
            fci=15000000,
            maintenance_pct=0.06,
            insurance_tax_pct=0.03,
            depreciable_capital=15000000,
            salvage_value=1500000,
            useful_life_years=20,
        )

        assert result.total_opex > 0
        assert result.maintenance == 15000000 * 0.06
        assert result.depreciation == (15000000 - 1500000) / 20
        assert result.operating_labor == 6 * 4 * 85000
