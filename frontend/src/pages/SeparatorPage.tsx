import { useState } from "react";
import { Play, Loader2, AlertTriangle, CheckCircle2 } from "lucide-react";
import ModuleLayout from "../components/ModuleLayout";
import CalcField from "../components/CalcField";
import SelectField from "../components/SelectField";
import ResultCard from "../components/ResultCard";

interface SepResult {
  orientation: string;
  vessel_diameter_m: number;
  vessel_length_m: number;
  l_over_d_ratio: number;
  settling_velocity_ms: number;
  droplet_diameter_um: number;
  gas_velocity_ms: number;
  gas_velocity_max_ms: number;
  k_factor: number;
  liquid_residence_time_s: number;
  liquid_volume_m3: number;
  vessel_volume_m3: number;
  liquid_level_pct: number;
  mist_eliminator: string;
  wall_thickness_mm: number;
  vessel_weight_kg: number;
  warnings: string[];
  standards_refs: string[];
}

const DEFAULTS = {
  gas_flow: "0.5",
  liquid_flow: "0.005",
  rho_gas: "25",
  rho_liquid: "750",
  mu_gas: "0.000012",
  operating_pressure: "2000000",
  operating_temperature: "323",
  orientation: "vertical",
  residence_time: "180",
  droplet_diameter: "150",
  has_mist_eliminator: "true",
  l_over_d: "3.0",
  corrosion_allowance: "0.003",
};

export default function SeparatorPage() {
  const [inputs, setInputs] = useState(DEFAULTS);
  const [result, setResult] = useState<SepResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const set = (k: string) => (v: string) => setInputs({ ...inputs, [k]: v });

  const handleRun = async () => {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const resp = await fetch("/api/v1/separator/size", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          gas_flow_m3s: parseFloat(inputs.gas_flow),
          liquid_flow_m3s: parseFloat(inputs.liquid_flow),
          rho_gas: parseFloat(inputs.rho_gas),
          rho_liquid: parseFloat(inputs.rho_liquid),
          mu_gas: parseFloat(inputs.mu_gas),
          operating_pressure_pa: parseFloat(inputs.operating_pressure),
          operating_temperature_k: parseFloat(inputs.operating_temperature),
          orientation: inputs.orientation,
          residence_time_s: parseFloat(inputs.residence_time),
          droplet_diameter_um: parseFloat(inputs.droplet_diameter),
          has_mist_eliminator: inputs.has_mist_eliminator === "true",
          l_over_d_target: parseFloat(inputs.l_over_d),
          corrosion_allowance_m: parseFloat(inputs.corrosion_allowance),
        }),
      });
      if (!resp.ok) throw new Error(`API returned ${resp.status}`);
      setResult(await resp.json());
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  };

  return (
    <ModuleLayout
      moduleNumber="04"
      title="Phase Separator"
      subtitle="Two-Phase Gas-Liquid Separator (API 12J / GPSA)"
      accentFrom="#8b5cf6"
      accentTo="#ec4899"
    >
      <div className="space-y-8">
        <section className="rounded-2xl border border-border bg-surface p-6">
          <h2 className="text-sm font-semibold text-text-primary mb-4">Process Conditions</h2>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <CalcField label="Gas Flow (actual)" unit="m³/s" value={inputs.gas_flow} onChange={set("gas_flow")} />
            <CalcField label="Liquid Flow" unit="m³/s" value={inputs.liquid_flow} onChange={set("liquid_flow")} />
            <CalcField label="Gas Density" unit="kg/m³" value={inputs.rho_gas} onChange={set("rho_gas")} />
            <CalcField label="Liquid Density" unit="kg/m³" value={inputs.rho_liquid} onChange={set("rho_liquid")} />
            <CalcField label="Gas Viscosity" unit="Pa·s" value={inputs.mu_gas} onChange={set("mu_gas")} />
            <CalcField label="Oper. Pressure" unit="Pa abs" value={inputs.operating_pressure} onChange={set("operating_pressure")} />
            <CalcField label="Oper. Temp" unit="K" value={inputs.operating_temperature} onChange={set("operating_temperature")} />
          </div>
        </section>

        <section className="rounded-2xl border border-border bg-surface p-6">
          <h2 className="text-sm font-semibold text-text-primary mb-4">Design Parameters</h2>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <SelectField
              label="Orientation"
              value={inputs.orientation}
              onChange={set("orientation")}
              options={[
                { value: "vertical", label: "Vertical" },
                { value: "horizontal", label: "Horizontal" },
              ]}
            />
            <CalcField label="Residence Time" unit="s" value={inputs.residence_time} onChange={set("residence_time")} />
            <CalcField label="Droplet Size" unit="μm" value={inputs.droplet_diameter} onChange={set("droplet_diameter")} />
            <CalcField label="Target L/D" unit="-" value={inputs.l_over_d} onChange={set("l_over_d")} />
            <SelectField
              label="Mist Eliminator"
              value={inputs.has_mist_eliminator}
              onChange={set("has_mist_eliminator")}
              options={[
                { value: "true", label: "Yes (Wire Mesh)" },
                { value: "false", label: "No (Gravity Only)" },
              ]}
            />
            <CalcField label="Corrosion Allow." unit="m" value={inputs.corrosion_allowance} onChange={set("corrosion_allowance")} />
          </div>
        </section>

        <button
          onClick={handleRun}
          disabled={loading}
          className="flex items-center gap-2 px-6 py-2.5 text-sm font-semibold bg-accent text-[#050505] rounded-full hover:bg-accent-dim transition-all duration-300 hover:shadow-[0_0_24px_rgba(0,229,160,0.25)] disabled:opacity-50"
        >
          {loading ? <Loader2 size={16} className="animate-spin" /> : <Play size={14} />}
          {loading ? "Computing..." : "Size Separator"}
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
              title="Vessel Geometry"
              items={[
                { label: "Orientation", value: result.orientation },
                { label: "Diameter", value: `${result.vessel_diameter_m} m` },
                { label: "Length", value: `${result.vessel_length_m} m` },
                { label: "L/D Ratio", value: `${result.l_over_d_ratio}` },
                { label: "Volume", value: `${result.vessel_volume_m3} m³` },
                { label: "Liquid Level", value: `${result.liquid_level_pct}%` },
              ]}
            />
            <ResultCard
              title="Separation Performance"
              items={[
                { label: "K Factor", value: `${result.k_factor}` },
                { label: "Settling Vel.", value: `${result.settling_velocity_ms} m/s` },
                { label: "Gas Velocity", value: `${result.gas_velocity_ms} m/s` },
                { label: "Max Gas Vel.", value: `${result.gas_velocity_max_ms} m/s` },
                { label: "Droplet Size", value: `${result.droplet_diameter_um} μm` },
                { label: "Mist Eliminator", value: result.mist_eliminator },
              ]}
            />
            <ResultCard
              title="Liquid Holdup"
              items={[
                { label: "Residence Time", value: `${result.liquid_residence_time_s} s` },
                { label: "Liquid Volume", value: `${result.liquid_volume_m3} m³` },
              ]}
            />
            <ResultCard
              title="Mechanical"
              items={[
                { label: "Wall Thickness", value: `${result.wall_thickness_mm} mm` },
                { label: "Vessel Weight", value: `${result.vessel_weight_kg} kg` },
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
