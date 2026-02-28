import { useState } from "react";
import { Play, Loader2, AlertTriangle, CheckCircle2 } from "lucide-react";
import ModuleLayout from "../components/ModuleLayout";
import CalcField from "../components/CalcField";
import SelectField from "../components/SelectField";
import ResultCard from "../components/ResultCard";

interface CapexResult {
  equipment_tag: string;
  equipment_type: string;
  cost_breakdown: {
    base_cost: { value: number };
    material_factor_Fm: number;
    pressure_factor_Fp: number;
    bare_module_factor_Fbm: number;
    bare_module_cost_base_year: { value: number };
    cepci_escalation_factor: number;
    bare_module_cost_target_year: { value: number };
    location_adjusted: { value: number };
  };
  six_tenths_check?: {
    scaled_cost: { value: number };
    exponent: number;
    note: string;
  };
  method_references: string[];
}

const DEFAULTS = {
  equipment_type: "shell_and_tube_hx",
  capacity: "100",
  design_pressure: "10",
  shell_material: "CS",
  tube_material: "CS",
  base_cepci: "397",
  target_cepci: "823.5",
  location_factor: "1.0",
  tag: "E-101",
};

const EQUIPMENT_TYPES = [
  { value: "shell_and_tube_hx", label: "Shell & Tube HX" },
  { value: "centrifugal_pump", label: "Centrifugal Pump" },
  { value: "pressure_vessel_vertical", label: "Pressure Vessel (Vertical)" },
  { value: "pressure_vessel_horizontal", label: "Pressure Vessel (Horizontal)" },
  { value: "tray_column", label: "Tray Column" },
  { value: "compressor_centrifugal", label: "Centrifugal Compressor" },
  { value: "fired_heater", label: "Fired Heater" },
  { value: "air_cooler", label: "Air Cooler" },
];

const CAPACITY_UNITS: Record<string, string> = {
  shell_and_tube_hx: "m²",
  centrifugal_pump: "kW",
  pressure_vessel_vertical: "kg",
  pressure_vessel_horizontal: "kg",
  tray_column: "kg",
  compressor_centrifugal: "kW",
  fired_heater: "kW",
  air_cooler: "m²",
};

export default function EconomicsPage() {
  const [inputs, setInputs] = useState(DEFAULTS);
  const [result, setResult] = useState<CapexResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const set = (k: string) => (v: string) => setInputs({ ...inputs, [k]: v });

  const capacityUnit = CAPACITY_UNITS[inputs.equipment_type] || "m²";

  const handleRun = async () => {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const sizingParams: Record<string, unknown> = {
        design_pressure: { value: parseFloat(inputs.design_pressure), unit: "barg" },
        shell_material: inputs.shell_material,
        tube_material: inputs.tube_material,
      };

      if (["shell_and_tube_hx", "air_cooler"].includes(inputs.equipment_type)) {
        sizingParams.heat_transfer_area = { value: parseFloat(inputs.capacity), unit: "m²" };
      } else if (["centrifugal_pump", "compressor_centrifugal", "fired_heater"].includes(inputs.equipment_type)) {
        sizingParams.power = { value: parseFloat(inputs.capacity), unit: "kW" };
      } else {
        sizingParams.volume = { value: parseFloat(inputs.capacity), unit: "kg" };
      }

      const resp = await fetch("/api/v1/econ/capex/equipment", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          equipment_tag: inputs.tag,
          equipment_type: inputs.equipment_type,
          sizing_parameters: sizingParams,
          cost_basis: {
            base_cepci: parseFloat(inputs.base_cepci),
            target_cepci: parseFloat(inputs.target_cepci),
            location_factor: parseFloat(inputs.location_factor),
          },
          overrides: {},
        }),
      });
      if (!resp.ok) {
        const errData = await resp.json().catch(() => null);
        throw new Error(errData?.detail || `API returned ${resp.status}`);
      }
      setResult(await resp.json());
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  };

  const fmt = (n: number) => `$${n.toLocaleString("en-US", { maximumFractionDigits: 0 })}`;

  return (
    <ModuleLayout
      moduleNumber="07"
      title="Economic Evaluation"
      subtitle="Equipment CAPEX — Guthrie Bare-Module Method (Turton 5th Ed.)"
      accentFrom="#7b61ff"
      accentTo="#c084fc"
    >
      <div className="space-y-8">
        <section className="rounded-2xl border border-border bg-surface p-6">
          <h2 className="text-sm font-semibold text-text-primary mb-4">Equipment Specification</h2>
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
            <SelectField label="Equipment Type" value={inputs.equipment_type} onChange={set("equipment_type")} options={EQUIPMENT_TYPES} />
            <CalcField label={`Capacity (${capacityUnit})`} unit={capacityUnit} value={inputs.capacity} onChange={set("capacity")} />
            <CalcField label="Design Pressure" unit="barg" value={inputs.design_pressure} onChange={set("design_pressure")} />
            <CalcField label="Equipment Tag" unit="" value={inputs.tag} onChange={set("tag")} type="text" />
            <CalcField label="Shell Material" unit="" value={inputs.shell_material} onChange={set("shell_material")} type="text" />
            <CalcField label="Tube Material" unit="" value={inputs.tube_material} onChange={set("tube_material")} type="text" />
          </div>
        </section>

        <section className="rounded-2xl border border-border bg-surface p-6">
          <h2 className="text-sm font-semibold text-text-primary mb-4">Cost Basis</h2>
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
            <CalcField label="Base CEPCI" unit="" value={inputs.base_cepci} onChange={set("base_cepci")} />
            <CalcField label="Target CEPCI" unit="" value={inputs.target_cepci} onChange={set("target_cepci")} />
            <CalcField label="Location Factor" unit="" value={inputs.location_factor} onChange={set("location_factor")} />
          </div>
        </section>

        <button
          onClick={handleRun}
          disabled={loading}
          className="flex items-center gap-2 px-6 py-2.5 text-sm font-semibold bg-accent text-[#050505] rounded-full hover:bg-accent-dim transition-all duration-300 hover:shadow-[0_0_24px_rgba(0,229,160,0.25)] disabled:opacity-50"
        >
          {loading ? <Loader2 size={16} className="animate-spin" /> : <Play size={14} />}
          {loading ? "Estimating..." : "Estimate CAPEX"}
        </button>

        {error && (
          <div className="flex items-start gap-2 text-sm text-red-400 bg-red-400/10 border border-red-400/20 rounded-lg px-4 py-3">
            <AlertTriangle size={16} className="mt-0.5 flex-shrink-0" />
            {error}
          </div>
        )}

        {result && (
          <div className="space-y-4">
            <div className="rounded-xl border border-accent/30 bg-accent/5 p-4">
              <div className="text-[11px] text-text-tertiary uppercase tracking-wider">
                Total Bare-Module Cost ({inputs.tag})
              </div>
              <div className="text-3xl font-bold font-mono text-accent mt-1">
                {fmt(result.cost_breakdown.location_adjusted.value)}
              </div>
              <div className="text-[12px] text-text-secondary mt-1">
                {result.equipment_type.replace(/_/g, " ")} — CEPCI {inputs.target_cepci}
              </div>
            </div>

            <ResultCard
              title="Cost Breakdown"
              items={[
                { label: "Base Cost (Cp°)", value: fmt(result.cost_breakdown.base_cost.value) },
                { label: "Material Factor (Fm)", value: `${result.cost_breakdown.material_factor_Fm}` },
                { label: "Pressure Factor (Fp)", value: `${result.cost_breakdown.pressure_factor_Fp}` },
                { label: "Bare Module (Fbm)", value: `${result.cost_breakdown.bare_module_factor_Fbm}` },
                { label: "Cost (base year)", value: fmt(result.cost_breakdown.bare_module_cost_base_year.value) },
                { label: "CEPCI Escalation", value: `${result.cost_breakdown.cepci_escalation_factor}x` },
                { label: "Cost (target year)", value: fmt(result.cost_breakdown.bare_module_cost_target_year.value) },
                { label: "Location Adjusted", value: fmt(result.cost_breakdown.location_adjusted.value) },
              ]}
            />

            {result.six_tenths_check && (
              <ResultCard
                title="Six-Tenths Rule Cross-Check"
                items={[
                  { label: "Scaled Cost", value: fmt(result.six_tenths_check.scaled_cost.value) },
                  { label: "Exponent", value: `${result.six_tenths_check.exponent}` },
                  { label: "Note", value: result.six_tenths_check.note },
                ]}
              />
            )}

            {result.method_references.length > 0 && (
              <div className="flex flex-wrap gap-2">
                {result.method_references.map((r, i) => (
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
