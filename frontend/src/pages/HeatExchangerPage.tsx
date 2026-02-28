import { useState } from "react";
import { Play, Loader2, AlertTriangle, CheckCircle2 } from "lucide-react";
import ModuleLayout from "../components/ModuleLayout";
import CalcField from "../components/CalcField";
import ResultCard from "../components/ResultCard";

interface HXResult {
  duty_w: number;
  lmtd_k: number;
  correction_factor_F: number;
  area_provided_m2: number;
  tube_count: number;
  shell_id_m: number;
  tube_length_m: number;
  overdesign_pct: number;
  hot_velocity_ms: number;
  cold_velocity_ms: number;
  hot_reynolds: number;
  cold_reynolds: number;
  hot_dp_pa: number;
  cold_dp_pa: number;
  hot_htc: number;
  cold_htc: number;
  U_clean: number;
  U_dirty: number;
  shell_min_thickness_m: number;
  shell_weight_kg: number;
  bundle_weight_kg: number;
  baffle_spacing_m: number;
  baffle_count: number;
  warnings: string[];
  standards_refs: string[];
}

const DEFAULTS = {
  T_h_in: "150",
  T_h_out: "90",
  T_c_in: "30",
  T_c_out: "45",
  m_dot_hot: "13.89",
  rho_hot: "850",
  mu_hot: "0.0003",
  cp_hot: "2200",
  k_hot: "0.13",
  rho_cold: "995",
  mu_cold: "0.0008",
  cp_cold: "4180",
  k_cold: "0.62",
  Rf_hot: "0.000176",
  Rf_cold: "0.000176",
  tube_od: "19.05",
  tube_pitch: "25.4",
  tube_length: "6.096",
  n_tube_passes: "2",
  design_pressure: "1000",
};

export default function HeatExchangerPage() {
  const [inputs, setInputs] = useState(DEFAULTS);
  const [result, setResult] = useState<HXResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const set = (k: string) => (v: string) => setInputs({ ...inputs, [k]: v });

  const handleRun = async () => {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const i = inputs;
      const resp = await fetch("/api/v1/hx/quick-size", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          project_id: "web",
          tag: "E-101",
          hx_type: "SHELL_AND_TUBE",
          tema_type: "AES",
          hot_side: {
            fluid: {
              components: [{ cas: "7732-18-5", name: "Water", mole_fraction: 1.0 }],
              thermo_model: "PR",
            },
            inlet_temperature: { value: parseFloat(i.T_h_in), unit: "°C" },
            outlet_temperature: { value: parseFloat(i.T_h_out), unit: "°C" },
            inlet_pressure: { value: 500, unit: "kPa" },
            mass_flow_rate: { value: parseFloat(i.m_dot_hot), unit: "kg/s" },
            fouling_resistance: { value: parseFloat(i.Rf_hot), unit: "m²·K/W" },
          },
          cold_side: {
            fluid: {
              components: [{ cas: "7732-18-5", name: "Water", mole_fraction: 1.0 }],
              thermo_model: "PR",
            },
            inlet_temperature: { value: parseFloat(i.T_c_in), unit: "°C" },
            outlet_temperature: { value: parseFloat(i.T_c_out), unit: "°C" },
            inlet_pressure: { value: 500, unit: "kPa" },
            fouling_resistance: { value: parseFloat(i.Rf_cold), unit: "m²·K/W" },
          },
          geometry_constraints: {
            tube_od: { value: parseFloat(i.tube_od), unit: "mm" },
            tube_pitch: { value: parseFloat(i.tube_pitch), unit: "mm" },
            max_tube_length: { value: parseFloat(i.tube_length), unit: "m" },
            tube_layout: "triangular_30",
            num_shell_passes: 1,
            num_tube_passes: parseInt(i.n_tube_passes),
            baffle_cut: 0.25,
          },
          design_conditions: {
            shell_design_pressure: { value: parseFloat(i.design_pressure), unit: "kPa" },
            tube_design_pressure: { value: parseFloat(i.design_pressure), unit: "kPa" },
            shell_design_temperature: { value: 200, unit: "°C" },
            tube_design_temperature: { value: 200, unit: "°C" },
            shell_material: "SA-516-70",
            tube_material: "SA-179",
            corrosion_allowance: { value: 3, unit: "mm" },
          },
        }),
      });
      if (!resp.ok) {
        const errData = await resp.json().catch(() => null);
        throw new Error(errData?.detail || `API returned ${resp.status}`);
      }
      const data = await resp.json();
      setResult({
        duty_w: data.thermal_results.duty.value * 1000,
        lmtd_k: data.thermal_results.lmtd.value,
        correction_factor_F: data.thermal_results.correction_factor_F,
        area_provided_m2: data.thermal_results.area_provided.value,
        tube_count: data.geometry_summary.tube_count,
        shell_id_m: data.geometry_summary.shell_id.value / 1000,
        tube_length_m: data.geometry_summary.tube_length.value,
        overdesign_pct: data.thermal_results.overdesign_pct,
        hot_velocity_ms: data.hot_side_results.velocity.value,
        cold_velocity_ms: data.cold_side_results.velocity.value,
        hot_reynolds: data.hot_side_results.reynolds,
        cold_reynolds: data.cold_side_results.reynolds,
        hot_dp_pa: data.hot_side_results.pressure_drop.value * 1000,
        cold_dp_pa: data.cold_side_results.pressure_drop.value * 1000,
        hot_htc: data.hot_side_results.heat_transfer_coeff.value,
        cold_htc: data.cold_side_results.heat_transfer_coeff.value,
        U_clean: data.thermal_results.overall_U_clean.value,
        U_dirty: data.thermal_results.overall_U_dirty.value,
        shell_min_thickness_m: data.mechanical_summary.shell_min_thickness.value / 1000,
        shell_weight_kg: data.mechanical_summary.shell_weight_empty.value,
        bundle_weight_kg: data.mechanical_summary.bundle_weight.value,
        baffle_spacing_m: data.geometry_summary.baffle_spacing.value / 1000,
        baffle_count: data.geometry_summary.baffle_count,
        warnings: data.warnings || [],
        standards_refs: data.meta?.standards_references || [],
      });
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  };

  return (
    <ModuleLayout
      moduleNumber="01"
      title="Heat Exchanger Design"
      subtitle="Shell & Tube Quick-Sizing (TEMA E)"
      accentFrom="#00e5a0"
      accentTo="#00b4d8"
    >
      <div className="space-y-8">
        {/* Process Conditions */}
        <section className="rounded-2xl border border-border bg-surface p-6">
          <h2 className="text-sm font-semibold text-text-primary mb-4">
            Process Conditions
          </h2>
          <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
            <CalcField label="Hot Inlet T" unit="°C" value={inputs.T_h_in} onChange={set("T_h_in")} />
            <CalcField label="Hot Outlet T" unit="°C" value={inputs.T_h_out} onChange={set("T_h_out")} />
            <CalcField label="Cold Inlet T" unit="°C" value={inputs.T_c_in} onChange={set("T_c_in")} />
            <CalcField label="Cold Outlet T" unit="°C" value={inputs.T_c_out} onChange={set("T_c_out")} />
            <CalcField label="Hot Mass Flow" unit="kg/s" value={inputs.m_dot_hot} onChange={set("m_dot_hot")} />
          </div>
        </section>

        {/* Fluid Properties */}
        <section className="rounded-2xl border border-border bg-surface p-6">
          <h2 className="text-sm font-semibold text-text-primary mb-4">
            Fluid Properties
          </h2>
          <div className="grid grid-cols-2 gap-6">
            <div>
              <h3 className="text-[11px] font-mono text-accent uppercase tracking-wider mb-3">Hot Side</h3>
              <div className="grid grid-cols-2 gap-3">
                <CalcField label="Density" unit="kg/m³" value={inputs.rho_hot} onChange={set("rho_hot")} />
                <CalcField label="Viscosity" unit="Pa·s" value={inputs.mu_hot} onChange={set("mu_hot")} />
                <CalcField label="Cp" unit="J/(kg·K)" value={inputs.cp_hot} onChange={set("cp_hot")} />
                <CalcField label="Conductivity" unit="W/(m·K)" value={inputs.k_hot} onChange={set("k_hot")} />
              </div>
            </div>
            <div>
              <h3 className="text-[11px] font-mono text-accent uppercase tracking-wider mb-3">Cold Side</h3>
              <div className="grid grid-cols-2 gap-3">
                <CalcField label="Density" unit="kg/m³" value={inputs.rho_cold} onChange={set("rho_cold")} />
                <CalcField label="Viscosity" unit="Pa·s" value={inputs.mu_cold} onChange={set("mu_cold")} />
                <CalcField label="Cp" unit="J/(kg·K)" value={inputs.cp_cold} onChange={set("cp_cold")} />
                <CalcField label="Conductivity" unit="W/(m·K)" value={inputs.k_cold} onChange={set("k_cold")} />
              </div>
            </div>
          </div>
        </section>

        {/* Geometry */}
        <section className="rounded-2xl border border-border bg-surface p-6">
          <h2 className="text-sm font-semibold text-text-primary mb-4">
            Geometry & Design
          </h2>
          <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
            <CalcField label="Tube OD" unit="mm" value={inputs.tube_od} onChange={set("tube_od")} />
            <CalcField label="Tube Pitch" unit="mm" value={inputs.tube_pitch} onChange={set("tube_pitch")} />
            <CalcField label="Tube Length" unit="m" value={inputs.tube_length} onChange={set("tube_length")} />
            <CalcField label="Tube Passes" unit="#" value={inputs.n_tube_passes} onChange={set("n_tube_passes")} />
            <CalcField label="Design P" unit="kPa" value={inputs.design_pressure} onChange={set("design_pressure")} />
          </div>
        </section>

        {/* Run */}
        <button
          onClick={handleRun}
          disabled={loading}
          className="flex items-center gap-2 px-6 py-2.5 text-sm font-semibold bg-accent text-[#050505] rounded-full hover:bg-accent-dim transition-all duration-300 hover:shadow-[0_0_24px_rgba(0,229,160,0.25)] disabled:opacity-50"
        >
          {loading ? <Loader2 size={16} className="animate-spin" /> : <Play size={14} />}
          {loading ? "Computing..." : "Run Quick-Size"}
        </button>

        {error && (
          <div className="flex items-start gap-2 text-sm text-red-400 bg-red-400/10 border border-red-400/20 rounded-lg px-4 py-3">
            <AlertTriangle size={16} className="mt-0.5 flex-shrink-0" />
            {error}
          </div>
        )}

        {result && (
          <div className="space-y-4">
            <ResultCard
              title="Thermal Results"
              items={[
                { label: "Duty", value: `${(result.duty_w / 1e3).toFixed(0)} kW` },
                { label: "LMTD", value: `${result.lmtd_k.toFixed(1)} K` },
                { label: "F-Factor", value: result.correction_factor_F.toFixed(3) },
                { label: "Area Provided", value: `${result.area_provided_m2.toFixed(1)} m²` },
                { label: "Overdesign", value: `${result.overdesign_pct.toFixed(1)}%` },
                { label: "U clean", value: `${result.U_clean.toFixed(0)} W/(m²·K)` },
                { label: "U dirty", value: `${result.U_dirty.toFixed(0)} W/(m²·K)` },
              ]}
            />
            <ResultCard
              title="Geometry"
              items={[
                { label: "Shell ID", value: `${(result.shell_id_m * 1000).toFixed(0)} mm` },
                { label: "Tubes", value: `${result.tube_count}` },
                { label: "Tube Length", value: `${result.tube_length_m.toFixed(2)} m` },
                { label: "Baffle Spacing", value: `${(result.baffle_spacing_m * 1000).toFixed(0)} mm` },
                { label: "Baffles", value: `${result.baffle_count}` },
              ]}
            />
            <div className="grid md:grid-cols-2 gap-4">
              <ResultCard
                title="Hot Side (Shell)"
                items={[
                  { label: "Velocity", value: `${result.hot_velocity_ms.toFixed(2)} m/s` },
                  { label: "Reynolds", value: `${result.hot_reynolds.toFixed(0)}` },
                  { label: "Pressure Drop", value: `${(result.hot_dp_pa / 1e3).toFixed(1)} kPa` },
                  { label: "HTC", value: `${result.hot_htc.toFixed(0)} W/(m²·K)` },
                ]}
              />
              <ResultCard
                title="Cold Side (Tube)"
                items={[
                  { label: "Velocity", value: `${result.cold_velocity_ms.toFixed(2)} m/s` },
                  { label: "Reynolds", value: `${result.cold_reynolds.toFixed(0)}` },
                  { label: "Pressure Drop", value: `${(result.cold_dp_pa / 1e3).toFixed(1)} kPa` },
                  { label: "HTC", value: `${result.cold_htc.toFixed(0)} W/(m²·K)` },
                ]}
              />
            </div>
            <ResultCard
              title="Mechanical (ASME VIII-1)"
              items={[
                { label: "Shell Thickness", value: `${(result.shell_min_thickness_m * 1000).toFixed(1)} mm` },
                { label: "Shell Weight", value: `${result.shell_weight_kg.toFixed(0)} kg` },
                { label: "Bundle Weight", value: `${result.bundle_weight_kg.toFixed(0)} kg` },
              ]}
            />

            {result.warnings.length > 0 && (
              <div className="space-y-1.5">
                {result.warnings.map((w, i) => (
                  <div key={i} className="flex items-start gap-2 text-[12px] text-yellow-400/80 bg-yellow-400/5 border border-yellow-400/10 rounded-lg px-3 py-2">
                    <AlertTriangle size={13} className="mt-0.5 flex-shrink-0" />
                    {w}
                  </div>
                ))}
              </div>
            )}

            {result.standards_refs.length > 0 && (
              <div className="flex flex-wrap gap-2">
                {result.standards_refs.map((r, i) => (
                  <span key={i} className="inline-flex items-center gap-1.5 px-2.5 py-1 text-[10px] font-mono text-text-tertiary bg-white/[0.02] border border-border rounded-full">
                    <CheckCircle2 size={10} className="text-accent/50" />
                    {r}
                  </span>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </ModuleLayout>
  );
}
