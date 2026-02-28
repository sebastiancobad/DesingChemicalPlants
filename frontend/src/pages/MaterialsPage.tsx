import { useState } from "react";
import { Loader2, AlertTriangle, CheckCircle2, Shield } from "lucide-react";
import ModuleLayout from "../components/ModuleLayout";
import SelectField from "../components/SelectField";
import CalcField from "../components/CalcField";
import ResultCard from "../components/ResultCard";

interface MatResult {
  material: {
    name: string;
    designation: string;
    category: string;
    density_kgm3: number;
    yield_strength_mpa: number;
    tensile_strength_mpa: number;
    allowable_stress_mpa: number;
    max_temperature_c: number;
    min_temperature_c: number;
    thermal_conductivity_wpmk: number;
    elastic_modulus_gpa: number;
    corrosion_allowance_mm: number;
    cost_factor: number;
    weldability: string;
    notes: string;
  };
  environment: string;
  corrosion_rate_mmyr: number;
  design_life_years: number;
  required_corrosion_allowance_mm: number;
  temperature_ok: boolean;
  sour_service_ok: boolean;
  sour_service_notes: string;
  cost_relative: number;
  recommended: boolean;
  recommendation_notes: string;
  alternatives: string[];
  warnings: string[];
  standards_refs: string[];
}

const DEFAULTS = {
  material: "SA-516-70",
  environment: "clean_water",
  design_temperature: "100",
  design_life: "20",
  is_sour: "false",
  h2_pressure: "0",
};

const MATERIALS = [
  { value: "SA-516-70", label: "SA-516-70 (Carbon Steel)" },
  { value: "SA-516-60", label: "SA-516-60 (Carbon Steel)" },
  { value: "SA-240-304", label: "SA-240-304 (SS 304)" },
  { value: "SA-240-316L", label: "SA-240-316L (SS 316L)" },
  { value: "SA-240-2205", label: "SA-240-2205 (Duplex SS)" },
  { value: "SB-265-Gr2", label: "SB-265-Gr2 (Titanium)" },
  { value: "SB-462-N08825", label: "SB-462-N08825 (Alloy 825)" },
  { value: "SA-387-Gr11", label: "SA-387-Gr11 (1.25Cr-0.5Mo)" },
];

const ENVIRONMENTS = [
  { value: "clean_water", label: "Clean Water" },
  { value: "seawater", label: "Seawater" },
  { value: "mild_acid", label: "Mild Acid" },
  { value: "strong_acid", label: "Strong Acid" },
  { value: "caustic_soda", label: "Caustic Soda" },
  { value: "sour_gas", label: "Sour Gas (H2S)" },
  { value: "hydrogen", label: "Hydrogen Service" },
  { value: "steam", label: "Steam" },
  { value: "atmospheric", label: "Atmospheric" },
  { value: "amine", label: "Amine Service" },
];

export default function MaterialsPage() {
  const [inputs, setInputs] = useState(DEFAULTS);
  const [result, setResult] = useState<MatResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const set = (k: string) => (v: string) => setInputs({ ...inputs, [k]: v });

  const handleRun = async () => {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const resp = await fetch("/api/v1/materials/assess", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          material_designation: inputs.material,
          environment: inputs.environment,
          design_temperature_c: parseFloat(inputs.design_temperature),
          design_life_years: parseInt(inputs.design_life),
          is_sour_service: inputs.is_sour === "true",
          h2_partial_pressure_bar: parseFloat(inputs.h2_pressure),
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
      moduleNumber="05"
      title="Material Selection"
      subtitle="Corrosion Assessment & NACE MR0175 Compliance"
      accentFrom="#10b981"
      accentTo="#34d399"
    >
      <div className="space-y-8">
        <section className="rounded-2xl border border-border bg-surface p-6">
          <h2 className="text-sm font-semibold text-text-primary mb-4">Service Conditions</h2>
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
            <SelectField label="Material" value={inputs.material} onChange={set("material")} options={MATERIALS} />
            <SelectField label="Environment" value={inputs.environment} onChange={set("environment")} options={ENVIRONMENTS} />
            <CalcField label="Design Temperature" unit="°C" value={inputs.design_temperature} onChange={set("design_temperature")} />
            <CalcField label="Design Life" unit="years" value={inputs.design_life} onChange={set("design_life")} />
            <SelectField
              label="Sour Service (NACE)"
              value={inputs.is_sour}
              onChange={set("is_sour")}
              options={[
                { value: "false", label: "No" },
                { value: "true", label: "Yes" },
              ]}
            />
            <CalcField label="H₂ Partial Press." unit="bar" value={inputs.h2_pressure} onChange={set("h2_pressure")} />
          </div>
        </section>

        <button
          onClick={handleRun}
          disabled={loading}
          className="flex items-center gap-2 px-6 py-2.5 text-sm font-semibold bg-accent text-[#050505] rounded-full hover:bg-accent-dim transition-all duration-300 hover:shadow-[0_0_24px_rgba(0,229,160,0.25)] disabled:opacity-50"
        >
          {loading ? <Loader2 size={16} className="animate-spin" /> : <Shield size={14} />}
          {loading ? "Assessing..." : "Assess Material"}
        </button>

        {error && (
          <div className="flex items-start gap-2 text-sm text-red-400 bg-red-400/10 border border-red-400/20 rounded-lg px-4 py-3">
            <AlertTriangle size={16} className="mt-0.5 flex-shrink-0" />
            {error}
          </div>
        )}

        {result && (
          <div className="space-y-4">
            {/* Recommendation banner */}
            <div className={`rounded-xl border p-4 flex items-center gap-3 ${
              result.recommended
                ? "border-green-500/30 bg-green-500/5"
                : "border-red-500/30 bg-red-500/5"
            }`}>
              <div className={`w-3 h-3 rounded-full ${result.recommended ? "bg-green-500" : "bg-red-500"}`} />
              <div>
                <div className={`text-sm font-semibold ${result.recommended ? "text-green-400" : "text-red-400"}`}>
                  {result.recommended ? "SUITABLE" : "REVIEW NEEDED"}
                </div>
                <div className="text-[12px] text-text-secondary">{result.recommendation_notes}</div>
              </div>
            </div>

            <ResultCard
              title="Material Properties"
              items={[
                { label: "Name", value: result.material.name },
                { label: "Category", value: result.material.category },
                { label: "Yield Strength", value: `${result.material.yield_strength_mpa} MPa` },
                { label: "Tensile Strength", value: `${result.material.tensile_strength_mpa} MPa` },
                { label: "Allowable Stress", value: `${result.material.allowable_stress_mpa} MPa` },
                { label: "Density", value: `${result.material.density_kgm3} kg/m³` },
                { label: "Thermal Cond.", value: `${result.material.thermal_conductivity_wpmk} W/(m·K)` },
                { label: "Elastic Modulus", value: `${result.material.elastic_modulus_gpa} GPa` },
                { label: "Weldability", value: result.material.weldability },
              ]}
            />

            <ResultCard
              title="Corrosion Assessment"
              items={[
                { label: "Environment", value: result.environment.replace(/_/g, " ") },
                { label: "Corrosion Rate", value: `${result.corrosion_rate_mmyr} mm/yr` },
                { label: "Design Life", value: `${result.design_life_years} yr` },
                { label: "Required CA", value: `${result.required_corrosion_allowance_mm} mm` },
                { label: "Std CA", value: `${result.material.corrosion_allowance_mm} mm` },
                { label: "Temp Range", value: `${result.material.min_temperature_c} to ${result.material.max_temperature_c} °C` },
                { label: "Temp OK", value: result.temperature_ok ? "Yes" : "No" },
                { label: "Cost Factor", value: `${result.cost_relative}x CS` },
              ]}
            />

            <ResultCard
              title="Sour Service (NACE MR0175)"
              items={[
                { label: "Compliant", value: result.sour_service_ok ? "Yes" : "No" },
                { label: "Notes", value: result.sour_service_notes },
              ]}
            />

            {result.alternatives.length > 0 && (
              <div className="rounded-xl border border-border bg-surface p-4">
                <h3 className="text-[13px] font-semibold text-text-primary mb-3">
                  Alternative Materials (Lower Corrosion Rate)
                </h3>
                <ul className="space-y-2">
                  {result.alternatives.map((alt, i) => (
                    <li key={i} className="text-[12px] text-text-secondary flex items-center gap-2">
                      <span className="w-1.5 h-1.5 rounded-full bg-accent/50" />
                      {alt}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            <div className="rounded-xl border border-border bg-surface-elevated p-4">
              <p className="text-[11px] text-text-tertiary italic">{result.material.notes}</p>
            </div>

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
