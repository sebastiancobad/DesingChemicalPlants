"""
Unit tests for Heat Exchanger calculation kernel.

Validates LMTD, F-factor, tube count estimation, and quick-sizing
against hand-calculated reference values.
"""

from __future__ import annotations

import math

import pytest

from app.kernel.modules.heat_exchanger.sizing import (
    correction_factor_1_2,
    estimate_tube_count,
    lmtd_counterflow,
    quick_size,
    shell_min_thickness,
)


class TestLMTD:
    def test_counterflow_basic(self):
        """LMTD for a simple water-water case."""
        lmtd = lmtd_counterflow(
            T_h_in=423.15, T_h_out=363.15,  # 150°C → 90°C
            T_c_in=303.15, T_c_out=318.15,  # 30°C → 45°C
        )
        # Expected: (105 - 45) / ln(105/45) ≈ 71.7 K
        assert 70.0 < lmtd < 80.0

    def test_equal_delta_t(self):
        """When ΔT1 ≈ ΔT2, LMTD should return arithmetic mean."""
        lmtd = lmtd_counterflow(T_h_in=400, T_h_out=350, T_c_in=300, T_c_out=350)
        assert abs(lmtd - 50.0) < 1.0

    def test_temperature_cross_raises(self):
        """Temperature cross should raise ValueError."""
        with pytest.raises(ValueError, match="cross"):
            lmtd_counterflow(T_h_in=350, T_h_out=300, T_c_in=310, T_c_out=360)


class TestCorrectionFactor:
    def test_f_factor_typical(self):
        """F for R=4.0, P=0.125 should be close to 1.0 (near counterflow)."""
        R = 4.0
        P = 0.125
        F = correction_factor_1_2(R, P)
        assert 0.85 < F <= 1.0

    def test_f_factor_r_equals_1(self):
        """Special case R = 1."""
        F = correction_factor_1_2(R=1.0, P=0.3)
        assert 0.5 < F <= 1.0


class TestTubeCount:
    def test_typical_shell(self):
        """A 489mm shell with 19.05mm tubes on 25.4mm pitch, 2 passes."""
        Nt = estimate_tube_count(
            shell_id_m=0.489,
            tube_od_m=0.01905,
            tube_pitch_m=0.0254,
            num_passes=2,
            layout="triangular_30",
        )
        # Typical range: 150-250 for this shell
        assert 100 < Nt < 350


class TestShellThickness:
    def test_asme_ug27(self):
        """Shell thickness for 489mm ID at 10 barg."""
        t = shell_min_thickness(
            inner_diameter=0.489,
            design_pressure=1e6,  # ~10 barg
            allowable_stress=138e6,  # SA-516-70
            corrosion_allowance=0.003,
        )
        # Expected: ~6-8 mm
        assert 0.005 < t < 0.012


class TestQuickSize:
    def test_water_water_case(self):
        """Quick-size a simple water-water exchanger."""
        result = quick_size(
            T_h_in=423.15, T_h_out=363.15,
            T_c_in=303.15, T_c_out=318.15,
            m_dot_hot=50000 / 3600,
            m_dot_cold=None,
            rho_hot=920.0, mu_hot=0.0002, cp_hot=4200.0, k_hot=0.67,
            rho_cold=995.0, mu_cold=0.0008, cp_cold=4180.0, k_cold=0.62,
        )

        # Duty should be ~3500 kW
        assert 3000e3 < result.duty_w < 4000e3

        # Area should be reasonable
        assert 20 < result.area_provided_m2 < 200

        # Should have standards references
        assert len(result.standards_refs) > 0
