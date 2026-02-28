import { useState } from "react";
import { Play, Loader2, AlertTriangle, CheckCircle2 } from "lucide-react";
import ModuleLayout from "../components/ModuleLayout";
import CalcField from "../components/CalcField";
import ResultCard from "../components/ResultCard";

interface PumpResult {
  flow_rate_m3h: number;
  total_dynamic_head_m: number;
  static_head_m: number;
  friction_head_m: number;
  velocity_head_m: number;
  pressure_head_m: number;
  hydraulic_power_kw: number;
  efficiency_pct: number;
  brake_power_kw: number;
  motor_power_kw: number;
  npsh_available_m: number;
  npsh_required_m: number;
  npsh_margin_m: number;
  npsh_ok: boolean;
  specific_speed: number;
  pump_type_suggestion: string;
  suction_velocity_ms: number;
  discharge_velocity_ms: number;
  warnings: string[];
  standards_refs: string[];
}

const DEFAULTS = {
  flow_rate: "50",
  density: "995",
  viscosity: "0.001",
  suction_pressure: "101325",
  discharge_pressure: "500000",
  static_head: "10",
  friction_loss: "5",
  suction_pipe_id: "0.1",
  discharge_pipe_id: "0.075",
  vapor_pressure: "2340",
  suction_elevation: "2",
  pump_elevation: "0",
  speed: "3550",
  motor_efficiency: "93",
};

export default function PumpPage() {
  const [inputs, setInputs] = useState(DEFAULTS);
  const [result, setResult] = useState<PumpResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const set = (k: string) => (v: string) => setInputs({ ...inputs, [k]: v });

  const handleRun = async () => {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const resp = await fetch("/api/v1/pump/size", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          flow_rate_m3h: parseFloat(inputs.flow_rate),
          density_kgm3: parseFloat(inputs.density),
          viscosity_pas: parseFloat(inputs.viscosity),
          suction_pressure_pa: parseFloat(inputs.suction_pressure),
          discharge_pressure_pa: parseFloat(inputs.discharge_pressure),
          static_head_m: parseFloat(inputs.static_head),
          friction_loss_m: parseFloat(inputs.friction_loss),
          suction_pipe_id_m: parseFloat(inputs.suction_pipe_id),
          discharge_pipe_id_m: parseFloat(inputs.discharge_pipe_id),
          vapor_pressure_pa: parseFloat(inputs.vapor_pressure),
          suction_vessel_elevation_m: parseFloat(inputs.suction_elevation),
          pump_elevation_m: parseFloat(inputs.pump_elevation),
          speed_rpm: parseFloat(inputs.speed),
          motor_efficiency_pct: parseFloat(inputs.motor_efficiency),
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
      moduleNumber="03"
      title="Pump Sizing"
      subtitle="Centrifugal Pump — Head, Power, NPSH (API 610)"
      accentFrom="#f59e0b"
      accentTo="#ef4444"
    >
      <div className="space-y-8">
        <section className="rounded-2xl border border-border bg-surface p-6">
          <h2 className="text-sm font-semibold text-text-primary mb-4">Flow & Fluid</h2>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <CalcField label="Flow Rate" unit="m³/h" value={inputs.flow_rate} onChange={set("flow_rate")} />
            <CalcField label="Density" unit="kg/m³" value={inputs.density} onChange={set("density")} />
            <CalcField label="Viscosity" unit="Pa·s" value={inputs.viscosity} onChange={set("viscosity")} />
            <CalcField label="Vapor Pressure" unit="Pa" value={inputs.vapor_pressure} onChange={set("vapor_pressure")} />
          </div>
        </section>

        <section className="rounded-2xl border border-border bg-surface p-6">
          <h2 className="text-sm font-semibold text-text-primary mb-4">System Conditions</h2>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <CalcField label="Suction P" unit="Pa abs" value={inputs.suction_pressure} onChange={set("suction_pressure")} />
            <CalcField label="Discharge P" unit="Pa abs" value={inputs.discharge_pressure} onChange={set("discharge_pressure")} />
            <CalcField label="Static Head" unit="m" value={inputs.static_head} onChange={set("static_head")} />
            <CalcField label="Friction Loss" unit="m head" value={inputs.friction_loss} onChange={set("friction_loss")} />
          </div>
        </section>

        <section className="rounded-2xl border border-border bg-surface p-6">
          <h2 className="text-sm font-semibold text-text-primary mb-4">Piping & Mechanical</h2>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <CalcField label="Suction Pipe ID" unit="m" value={inputs.suction_pipe_id} onChange={set("suction_pipe_id")} />
            <CalcField label="Discharge Pipe ID" unit="m" value={inputs.discharge_pipe_id} onChange={set("discharge_pipe_id")} />
            <CalcField label="Suction Vessel Elev" unit="m" value={inputs.suction_elevation} onChange={set("suction_elevation")} />
            <CalcField label="Pump Elev" unit="m" value={inputs.pump_elevation} onChange={set("pump_elevation")} />
            <CalcField label="Speed" unit="RPM" value={inputs.speed} onChange={set("speed")} />
            <CalcField label="Motor Efficiency" unit="%" value={inputs.motor_efficiency} onChange={set("motor_efficiency")} />
          </div>
        </section>

        <button
          onClick={handleRun}
          disabled={loading}
          className="flex items-center gap-2 px-6 py-2.5 text-sm font-semibold bg-accent text-[#050505] rounded-full hover:bg-accent-dim transition-all duration-300 hover:shadow-[0_0_24px_rgba(0,229,160,0.25)] disabled:opacity-50"
        >
          {loading ? <Loader2 size={16} className="animate-spin" /> : <Play size={14} />}
          {loading ? "Computing..." : "Size Pump"}
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
              title="Head Analysis"
              items={[
                { label: "Total Dynamic Head", value: `${result.total_dynamic_head_m} m` },
                { label: "Static Head", value: `${result.static_head_m} m` },
                { label: "Friction Head", value: `${result.friction_head_m} m` },
                { label: "Velocity Head", value: `${result.velocity_head_m} m` },
                { label: "Pressure Head", value: `${result.pressure_head_m} m` },
              ]}
            />
            <ResultCard
              title="Power & Efficiency"
              items={[
                { label: "Hydraulic Power", value: `${result.hydraulic_power_kw} kW` },
                { label: "Pump Efficiency", value: `${result.efficiency_pct}%` },
                { label: "Brake Power", value: `${result.brake_power_kw} kW` },
                { label: "Motor Power", value: `${result.motor_power_kw} kW` },
                { label: "Pump Type", value: result.pump_type_suggestion },
                { label: "Specific Speed", value: `${result.specific_speed}` },
              ]}
            />
            <ResultCard
              title="NPSH Analysis"
              items={[
                { label: "NPSH Available", value: `${result.npsh_available_m} m` },
                { label: "NPSH Required", value: `${result.npsh_required_m} m` },
                { label: "NPSH Margin", value: `${result.npsh_margin_m} m` },
                { label: "Cavitation Risk", value: result.npsh_ok ? "Low" : "HIGH" },
                { label: "Suction Velocity", value: `${result.suction_velocity_ms} m/s` },
                { label: "Discharge Velocity", value: `${result.discharge_velocity_ms} m/s` },
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
