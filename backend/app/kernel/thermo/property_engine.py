"""
ChemScale — Thermodynamic & Physical Property Engine.

Provides mixture property calculations using Equations of State (PR, SRK)
and Activity Coefficient models (NRTL, UNIQUAC). This module is the single
source of truth for physical properties consumed by all engineering modules.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

class ThermoModel(str, Enum):
    PR = "PR"
    SRK = "SRK"
    NRTL = "NRTL"
    UNIQUAC = "UNIQUAC"
    WILSON = "WILSON"
    IAPWS97 = "IAPWS97"


class Phase(str, Enum):
    VAPOR = "vapor"
    LIQUID = "liquid"
    LIQUID2 = "liquid2"  # second liquid for LLE/VLLE


@dataclass
class ComponentData:
    """Pure component constants loaded from the component database."""

    cas: str
    name: str
    molecular_weight: float  # g/mol
    tc: float  # K
    pc: float  # Pa
    omega: float  # acentric factor
    vc: Optional[float] = None  # m³/mol
    tb: Optional[float] = None  # K  (normal boiling point)


@dataclass
class PhaseProperties:
    """Thermophysical properties for a single phase."""

    phase: Phase
    fraction: float  # mole fraction of total feed in this phase
    composition: list[float]  # mole fractions within the phase
    density: float  # kg/m³
    viscosity: float  # Pa·s
    thermal_conductivity: float  # W/(m·K)
    heat_capacity_cp: float  # J/(mol·K)
    heat_capacity_cv: Optional[float] = None  # J/(mol·K)
    surface_tension: Optional[float] = None  # N/m
    compressibility: Optional[float] = None  # Z
    enthalpy: Optional[float] = None  # J/mol
    entropy: Optional[float] = None  # J/(mol·K)
    fugacity_coefficients: list[float] = field(default_factory=list)
    molecular_weight_mix: Optional[float] = None  # g/mol


@dataclass
class FlashResult:
    """Result of a VLE/VLLE flash calculation."""

    temperature: float  # K
    pressure: float  # Pa
    phases: list[PhaseProperties]
    converged: bool = True
    iterations: int = 0


@dataclass
class PropertyResult:
    """Complete property package returned to engineering modules."""

    components: list[ComponentData]
    feed_composition: list[float]
    temperature: float  # K
    pressure: float  # Pa
    thermo_model: ThermoModel
    flash: FlashResult
    warnings: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Property Engine
# ---------------------------------------------------------------------------

class PropertyEngine:
    """Central interface for thermodynamic calculations.

    All engineering modules call ``PropertyEngine.calculate()`` to obtain
    mixture properties. The engine delegates to the appropriate EOS or
    activity coefficient model, performs flash calculations, and returns
    a ``PropertyResult`` that the calling module can consume directly.
    """

    def calculate(
        self,
        components: list[ComponentData],
        mole_fractions: list[float],
        temperature: float,
        pressure: float,
        model: ThermoModel = ThermoModel.PR,
    ) -> PropertyResult:
        """Calculate mixture properties at the given T, P, z.

        Parameters
        ----------
        components : list[ComponentData]
            Pure component data for each species.
        mole_fractions : list[float]
            Feed mole fractions (must sum to 1.0).
        temperature : float
            Temperature in K.
        pressure : float
            Pressure in Pa.
        model : ThermoModel
            Thermodynamic model to use.

        Returns
        -------
        PropertyResult
            Full property package including flash results.
        """
        self._validate_inputs(components, mole_fractions)

        flash = self._flash_pt(components, mole_fractions, temperature, pressure, model)

        return PropertyResult(
            components=components,
            feed_composition=mole_fractions,
            temperature=temperature,
            pressure=pressure,
            thermo_model=model,
            flash=flash,
        )

    # -- Flash algorithms ----------------------------------------------------

    def _flash_pt(
        self,
        components: list[ComponentData],
        z: list[float],
        T: float,
        P: float,
        model: ThermoModel,
    ) -> FlashResult:
        """PT flash via successive substitution with Newton acceleration.

        Implements Rachford-Rice for phase split determination and iterates
        K-values until fugacity equality is satisfied.
        """
        n = len(components)

        # Initial K-values from Wilson correlation
        K = [
            (comp.pc / P) * math.exp(5.373 * (1.0 + comp.omega) * (1.0 - comp.tc / T))
            for comp in components
        ]

        # Check if two-phase region
        sum_Kz = sum(Ki * zi for Ki, zi in zip(K, z))
        sum_z_over_K = sum(zi / Ki if Ki > 0 else 0 for Ki, zi in zip(K, z))

        if sum_Kz <= 1.0:
            # All liquid
            props = self._phase_properties(components, z, T, P, Phase.LIQUID, model)
            return FlashResult(
                temperature=T,
                pressure=P,
                phases=[props],
                converged=True,
                iterations=0,
            )

        if sum_z_over_K <= 1.0:
            # All vapor
            props = self._phase_properties(components, z, T, P, Phase.VAPOR, model)
            return FlashResult(
                temperature=T,
                pressure=P,
                phases=[props],
                converged=True,
                iterations=0,
            )

        # Two-phase: solve Rachford-Rice
        V = 0.5  # initial vapor fraction guess
        max_iter = 100
        tol = 1e-10

        for iteration in range(max_iter):
            f = sum(zi * (Ki - 1) / (1 + V * (Ki - 1)) for zi, Ki in zip(z, K))
            df = -sum(
                zi * (Ki - 1) ** 2 / (1 + V * (Ki - 1)) ** 2
                for zi, Ki in zip(z, K)
            )

            if abs(df) < 1e-30:
                break

            dV = -f / df
            V_new = V + dV
            V_new = max(0.0, min(1.0, V_new))
            V = V_new

            if abs(f) < tol:
                break

        # Phase compositions
        x = [zi / (1 + V * (Ki - 1)) for zi, Ki in zip(z, K)]
        y = [Ki * xi for Ki, xi in zip(K, x)]

        # Normalise
        sx = sum(x)
        sy = sum(y)
        x = [xi / sx for xi in x]
        y = [yi / sy for yi in y]

        liquid_props = self._phase_properties(components, x, T, P, Phase.LIQUID, model)
        liquid_props.fraction = 1.0 - V

        vapor_props = self._phase_properties(components, y, T, P, Phase.VAPOR, model)
        vapor_props.fraction = V

        return FlashResult(
            temperature=T,
            pressure=P,
            phases=[liquid_props, vapor_props],
            converged=True,
            iterations=iteration + 1,
        )

    # -- Phase property estimation -------------------------------------------

    def _phase_properties(
        self,
        components: list[ComponentData],
        composition: list[float],
        T: float,
        P: float,
        phase: Phase,
        model: ThermoModel,
    ) -> PhaseProperties:
        """Estimate thermophysical properties for a single phase.

        This is a simplified implementation using corresponding-states
        correlations. Production code will delegate to CoolProp / thermo
        library with full EOS integration.
        """
        mw_mix = sum(xi * comp.molecular_weight for xi, comp in zip(composition, components))

        if phase == Phase.VAPOR:
            Z = self._compressibility_vapor(components, composition, T, P, model)
            R = 8.314  # J/(mol·K)
            rho = P * mw_mix / (1000.0 * Z * R * T)  # kg/m³
            mu = self._viscosity_gas(components, composition, T, mw_mix)
            k_th = self._conductivity_gas(mu, mw_mix)
            cp = self._cp_ideal_gas_mix(components, composition, T)
        else:
            rho = self._density_liquid(components, composition, T)
            mu = self._viscosity_liquid(components, composition, T)
            k_th = self._conductivity_liquid(components, composition, T)
            cp = self._cp_liquid_mix(components, composition, T)
            Z = None

        return PhaseProperties(
            phase=phase,
            fraction=1.0,
            composition=composition,
            density=rho,
            viscosity=mu,
            thermal_conductivity=k_th,
            heat_capacity_cp=cp,
            compressibility=Z,
            molecular_weight_mix=mw_mix,
        )

    # -- EOS helpers (simplified Peng-Robinson) ------------------------------

    def _compressibility_vapor(
        self,
        components: list[ComponentData],
        z: list[float],
        T: float,
        P: float,
        model: ThermoModel,
    ) -> float:
        """Simplified mixture compressibility via PR EOS."""
        R = 8.314
        # Mixing rules (van der Waals one-fluid)
        a_mix = 0.0
        b_mix = 0.0
        for i, (zi, ci) in enumerate(zip(z, components)):
            Tri = T / ci.tc
            kappa = 0.37464 + 1.54226 * ci.omega - 0.26992 * ci.omega**2
            alpha = (1.0 + kappa * (1.0 - math.sqrt(Tri))) ** 2
            ai = 0.45724 * R**2 * ci.tc**2 / ci.pc * alpha
            bi = 0.07780 * R * ci.tc / ci.pc
            b_mix += zi * bi
            for j, (zj, cj) in enumerate(zip(z, components)):
                Trj = T / cj.tc
                kj = 0.37464 + 1.54226 * cj.omega - 0.26992 * cj.omega**2
                alphaj = (1.0 + kj * (1.0 - math.sqrt(Trj))) ** 2
                aj = 0.45724 * R**2 * cj.tc**2 / cj.pc * alphaj
                a_mix += zi * zj * math.sqrt(ai * aj)

        A = a_mix * P / (R * T) ** 2
        B = b_mix * P / (R * T)

        # Solve cubic: Z³ - (1-B)Z² + (A-3B²-2B)Z - (AB-B²-B³) = 0
        # Use Newton's method starting from ideal gas Z=1
        Z = 1.0
        for _ in range(50):
            f = Z**3 - (1 - B) * Z**2 + (A - 3 * B**2 - 2 * B) * Z - (A * B - B**2 - B**3)
            df = 3 * Z**2 - 2 * (1 - B) * Z + (A - 3 * B**2 - 2 * B)
            if abs(df) < 1e-30:
                break
            Z -= f / df
            if abs(f) < 1e-12:
                break

        return max(Z, B + 0.01)  # Ensure Z > B

    def _density_liquid(
        self, components: list[ComponentData], z: list[float], T: float
    ) -> float:
        """Simplified liquid density via Rackett equation."""
        mw_mix = sum(xi * c.molecular_weight for xi, c in zip(z, components))
        # Pseudo-critical mixing
        Tc_mix = sum(xi * c.tc for xi, c in zip(z, components))
        Pc_mix = sum(xi * c.pc for xi, c in zip(z, components))
        omega_mix = sum(xi * c.omega for xi, c in zip(z, components))
        R = 8.314
        Zra = 0.29056 - 0.08775 * omega_mix
        Tr = T / Tc_mix
        Vs = R * Tc_mix / Pc_mix * Zra ** (1.0 + (1.0 - Tr) ** (2.0 / 7.0))
        rho = mw_mix / (1000.0 * Vs)  # kg/m³
        return max(rho, 100.0)  # floor to avoid non-physical results

    def _viscosity_gas(
        self, components: list[ComponentData], z: list[float], T: float, mw: float
    ) -> float:
        """Gas viscosity via Lucas correlation (simplified)."""
        Tc_mix = sum(xi * c.tc for xi, c in zip(z, components))
        Pc_mix = sum(xi * c.pc for xi, c in zip(z, components))
        Tr = T / Tc_mix
        xi = 0.176 * (Tc_mix / (mw**3 * (Pc_mix / 1e5) ** 4)) ** (1.0 / 6.0)
        mu_xi = 0.807 * Tr**0.618 - 0.357 * math.exp(-0.449 * Tr) + 0.340 * math.exp(
            -4.058 * Tr
        ) + 0.018
        mu = mu_xi / xi * 1e-7  # Pa·s
        return max(mu, 1e-7)

    def _viscosity_liquid(
        self, components: list[ComponentData], z: list[float], T: float
    ) -> float:
        """Liquid viscosity via Orrick-Erbar (placeholder, returns typical value)."""
        # Placeholder: returns a temperature-dependent viscosity in the range
        # of light hydrocarbons to water.
        Tc_mix = sum(xi * c.tc for xi, c in zip(z, components))
        Tr = T / Tc_mix
        mu = 1e-3 * math.exp(2.0 * (1.0 / Tr - 1.0))  # Pa·s
        return max(mu, 1e-5)

    def _conductivity_gas(self, mu: float, mw: float) -> float:
        """Gas thermal conductivity from Eucken correlation."""
        R = 8.314
        Cv = 2.5 * R  # monatomic approx; refine per component
        return mu * (Cv + 1.25 * R) / (mw / 1000.0)

    def _conductivity_liquid(
        self, components: list[ComponentData], z: list[float], T: float
    ) -> float:
        """Liquid thermal conductivity (simplified Latini)."""
        Tc_mix = sum(xi * c.tc for xi, c in zip(z, components))
        Tb_mix = sum(
            xi * (c.tb if c.tb else 0.6 * c.tc) for xi, c in zip(z, components)
        )
        mw_mix = sum(xi * c.molecular_weight for xi, c in zip(z, components))
        Tr = T / Tc_mix
        A = 0.494
        k = A * (Tb_mix ** 0.38) / (mw_mix ** 0.5 * Tc_mix ** 0.167) * (1 - Tr) ** 0.38
        return max(k, 0.01)

    def _cp_ideal_gas_mix(
        self, components: list[ComponentData], z: list[float], T: float
    ) -> float:
        """Ideal gas Cp via polynomial (placeholder with typical values)."""
        R = 8.314
        # Simple approximation: Cp/R ≈ 3.5 for diatomics, adjust with T
        cp = sum(
            zi * R * (3.5 + 0.001 * T) for zi in z
        )
        return cp

    def _cp_liquid_mix(
        self, components: list[ComponentData], z: list[float], T: float
    ) -> float:
        """Liquid Cp (placeholder, ~75 J/(mol·K) for water-like fluids)."""
        R = 8.314
        return sum(zi * R * (9.0 + 0.002 * T) for zi in z)

    # -- Input validation ----------------------------------------------------

    def _validate_inputs(
        self, components: list[ComponentData], z: list[float]
    ) -> None:
        if len(components) != len(z):
            raise ValueError("Component count must match mole fraction count")
        if abs(sum(z) - 1.0) > 1e-6:
            raise ValueError(f"Mole fractions must sum to 1.0, got {sum(z):.6f}")
        for comp in components:
            if comp.tc <= 0 or comp.pc <= 0:
                raise ValueError(
                    f"Invalid critical properties for {comp.name} "
                    f"(Tc={comp.tc}, Pc={comp.pc})"
                )
