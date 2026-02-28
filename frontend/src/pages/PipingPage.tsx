import { useState } from "react";
import { Play, Loader2, AlertTriangle, CheckCircle2 } from "lucide-react";
import ModuleLayout from "../components/ModuleLayout";
import CalcField from "../components/CalcField";
import SelectField from "../components/SelectField";
import ResultCard from "../components/ResultCard";

interface PipeResult {
  nps: string;
  schedule: string;
  outer_diameter_mm: number;
  wall_thickness_mm: number;
  inner_diameter_mm: number;
  flow_area_m2: number;
  velocity_ms: number;
  reynolds: number;
  friction_factor: number;
  pressure_drop_pa_per_m: number;
  total_pressure_drop_kpa: number;
  pipe_length_m: number;
  equivalent_length_fittings_m: number;
  total_equivalent_length_m: number;
  velocity_ok: boolean;
  velocity_message: string;
  warnings: string[];
  standards_refs: string[];
}

const DEFAULTS = {
  mass_flow: "5.0",
  density: "995",
  viscosity: "0.001",
  pipe_length: "100",
  elevation: "0",
  roughness: "0.000046",
  schedule: "SCH 40",
  fluid_phase: "liquid",
  elbows_90: "4",
  elbows_45: "2",
  gate_valves: "2",
  globe_valves: "0",
  tee_branch: "1",
};

export default function PipingPage() {
  const [inputs, setInputs] = useState(DEFAULTS);
  const [result, setResult] = useState<PipeResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const set = (k: string) => (v: string) => setInputs({ ...inputs, [k]: v });

  const handleRun = async () => {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const fittings: Record<string, number> = {};
      if (parseInt(inputs.elbows_90) > 0) fittings["90_elbow_std"] = parseInt(inputs.elbows_90);
      if (parseInt(inputs.elbows_45) > 0) fittings["45_elbow"] = parseInt(inputs.elbows_45);
      if (parseInt(inputs.gate_valves) > 0) fittings["gate_valve"] = parseInt(inputs.gate_valves);
      if (parseInt(inputs.globe_valves) > 0) fittings["globe_valve"] = parseInt(inputs.globe_valves);
      if (parseInt(inputs.tee_branch) > 0) fittings["tee_branch"] = parseInt(inputs.tee_branch);

      const resp = await fetch("/api/v1/piping/size", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          mass_flow_kgs: parseFloat(inputs.mass_flow),
          density_kgm3: parseFloat(inputs.density),
          viscosity_pas: parseFloat(inputs.viscosity),
          pipe_length_m: parseFloat(inputs.pipe_length),
          elevation_change_m: parseFloat(inputs.elevation),
          roughness_m: parseFloat(inputs.roughness),
          schedule: inputs.schedule,
          fluid_phase: inputs.fluid_phase,
          fittings: Object.keys(fittings).length > 0 ? fittings : undefined,
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
      moduleNumber="02"
      title="Piping & Pipeline"
      subtitle="Pipe Sizing & Pressure Drop (Darcy-Weisbach)"
      accentFrom="#3b82f6"
      accentTo="#06b6d4"
    >
      <div className="space-y-8">
        <section className="rounded-2xl border border-border bg-surface p-6">
          <h2 className="text-sm font-semibold text-text-primary mb-4">Flow Conditions</h2>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <CalcField label="Mass Flow" unit="kg/s" value={inputs.mass_flow} onChange={set("mass_flow")} />
            <CalcField label="Density" unit="kg/m³" value={inputs.density} onChange={set("density")} />
            <CalcField label="Viscosity" unit="Pa·s" value={inputs.viscosity} onChange={set("viscosity")} />
            <SelectField
              label="Fluid Phase"
              value={inputs.fluid_phase}
              onChange={set("fluid_phase")}
              options={[
                { value: "liquid", label: "Liquid" },
                { value: "gas", label: "Gas" },
              ]}
            />
          </div>
        </section>

        <section className="rounded-2xl border border-border bg-surface p-6">
          <h2 className="text-sm font-semibold text-text-primary mb-4">Pipe Geometry</h2>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <CalcField label="Pipe Length" unit="m" value={inputs.pipe_length} onChange={set("pipe_length")} />
            <CalcField label="Elevation Change" unit="m" value={inputs.elevation} onChange={set("elevation")} />
            <CalcField label="Roughness" unit="m" value={inputs.roughness} onChange={set("roughness")} />
            <SelectField
              label="Schedule"
              value={inputs.schedule}
              onChange={set("schedule")}
              options={[
                { value: "SCH 40", label: "SCH 40" },
                { value: "SCH 80", label: "SCH 80" },
                { value: "SCH 160", label: "SCH 160" },
              ]}
            />
          </div>
        </section>

        <section className="rounded-2xl border border-border bg-surface p-6">
          <h2 className="text-sm font-semibold text-text-primary mb-4">Fittings (Crane TP-410)</h2>
          <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
            <CalcField label="90° Elbows" unit="qty" value={inputs.elbows_90} onChange={set("elbows_90")} />
            <CalcField label="45° Elbows" unit="qty" value={inputs.elbows_45} onChange={set("elbows_45")} />
            <CalcField label="Gate Valves" unit="qty" value={inputs.gate_valves} onChange={set("gate_valves")} />
            <CalcField label="Globe Valves" unit="qty" value={inputs.globe_valves} onChange={set("globe_valves")} />
            <CalcField label="Tee (Branch)" unit="qty" value={inputs.tee_branch} onChange={set("tee_branch")} />
          </div>
        </section>

        <button
          onClick={handleRun}
          disabled={loading}
          className="flex items-center gap-2 px-6 py-2.5 text-sm font-semibold bg-accent text-[#050505] rounded-full hover:bg-accent-dim transition-all duration-300 hover:shadow-[0_0_24px_rgba(0,229,160,0.25)] disabled:opacity-50"
        >
          {loading ? <Loader2 size={16} className="animate-spin" /> : <Play size={14} />}
          {loading ? "Computing..." : "Size Pipe"}
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
              title="Selected Pipe"
              items={[
                { label: "NPS", value: `${result.nps}"` },
                { label: "Schedule", value: result.schedule },
                { label: "OD", value: `${result.outer_diameter_mm} mm` },
                { label: "Wall", value: `${result.wall_thickness_mm} mm` },
                { label: "ID", value: `${result.inner_diameter_mm} mm` },
                { label: "Flow Area", value: `${(result.flow_area_m2 * 1e4).toFixed(2)} cm²` },
              ]}
            />
            <ResultCard
              title="Hydraulics"
              items={[
                { label: "Velocity", value: `${result.velocity_ms.toFixed(3)} m/s` },
                { label: "Reynolds", value: `${result.reynolds.toFixed(0)}` },
                { label: "Friction Factor", value: `${result.friction_factor.toFixed(6)}` },
                { label: "ΔP/m", value: `${result.pressure_drop_pa_per_m.toFixed(1)} Pa/m` },
                { label: "Total ΔP", value: `${result.total_pressure_drop_kpa.toFixed(2)} kPa` },
                { label: "Velocity Status", value: result.velocity_ok ? "OK" : "EXCEEDS LIMIT" },
              ]}
            />
            <ResultCard
              title="Equivalent Lengths"
              items={[
                { label: "Straight Pipe", value: `${result.pipe_length_m} m` },
                { label: "Fittings Eq. Length", value: `${result.equivalent_length_fittings_m.toFixed(1)} m` },
                { label: "Total Eq. Length", value: `${result.total_equivalent_length_m.toFixed(1)} m` },
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
