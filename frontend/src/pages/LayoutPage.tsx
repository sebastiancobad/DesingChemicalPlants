import { useState } from "react";
import { Play, Loader2, AlertTriangle, CheckCircle2, Plus, Trash2 } from "lucide-react";
import ModuleLayout from "../components/ModuleLayout";
import SelectField from "../components/SelectField";
import ResultCard from "../components/ResultCard";

interface SpacingCheck {
  equipment_a: string;
  equipment_b: string;
  minimum_distance_m: number;
  risk_level_a: string;
  risk_level_b: string;
  governing_standard: string;
  notes: string;
}

interface LayoutResult {
  spacing_checks: SpacingCheck[];
  total_violations: number;
  plot_area_estimate_m2: number;
  plot_dimensions_m: [number, number];
  equipment_list: string[];
  warnings: string[];
  standards_refs: string[];
}

interface Equipment {
  tag: string;
  type: string;
}

const EQUIPMENT_TYPES = [
  { value: "heat_exchanger", label: "Heat Exchanger" },
  { value: "pump", label: "Pump" },
  { value: "compressor", label: "Compressor" },
  { value: "pressure_vessel", label: "Pressure Vessel" },
  { value: "column", label: "Column / Tower" },
  { value: "reactor", label: "Reactor" },
  { value: "fired_heater", label: "Fired Heater / Furnace" },
  { value: "storage_tank_atmospheric", label: "Atmospheric Storage Tank" },
  { value: "storage_tank_pressurized", label: "Pressurized Storage Tank" },
  { value: "cooling_tower", label: "Cooling Tower" },
  { value: "flare_stack", label: "Flare Stack" },
  { value: "control_room", label: "Control Room" },
  { value: "pipe_rack", label: "Pipe Rack" },
  { value: "loading_area", label: "Loading Area" },
];

const DEFAULT_EQUIPMENT: Equipment[] = [
  { tag: "E-101", type: "heat_exchanger" },
  { tag: "P-101", type: "pump" },
  { tag: "V-101", type: "pressure_vessel" },
  { tag: "T-101", type: "column" },
  { tag: "H-101", type: "fired_heater" },
];

export default function LayoutPage() {
  const [equipment, setEquipment] = useState<Equipment[]>(DEFAULT_EQUIPMENT);
  const [result, setResult] = useState<LayoutResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const addEquipment = () => {
    const idx = equipment.length + 1;
    setEquipment([...equipment, { tag: `EQ-${idx}`, type: "pressure_vessel" }]);
  };

  const removeEquipment = (idx: number) => {
    setEquipment(equipment.filter((_, i) => i !== idx));
  };

  const updateEquipment = (idx: number, field: keyof Equipment, value: string) => {
    const updated = [...equipment];
    updated[idx] = { ...updated[idx], [field]: value };
    setEquipment(updated);
  };

  const handleRun = async () => {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const resp = await fetch("/api/v1/layout/check", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ equipment_list: equipment }),
      });
      if (!resp.ok) throw new Error(`API returned ${resp.status}`);
      setResult(await resp.json());
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  };

  const riskColor = (level: string) => {
    switch (level) {
      case "high": return "text-red-400";
      case "moderate": return "text-yellow-400";
      case "low": return "text-green-400";
      case "occupied": return "text-blue-400";
      default: return "text-text-secondary";
    }
  };

  return (
    <ModuleLayout
      moduleNumber="06"
      title="Plant Layout"
      subtitle="Minimum Spacing Rules (NFPA 30 / API 2510)"
      accentFrom="#06b6d4"
      accentTo="#3b82f6"
    >
      <div className="space-y-8">
        <section className="rounded-2xl border border-border bg-surface p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-semibold text-text-primary">Equipment List</h2>
            <button
              onClick={addEquipment}
              className="flex items-center gap-1.5 px-3 py-1.5 text-[12px] font-medium text-accent border border-accent/30 rounded-lg hover:bg-accent/10 transition-colors"
            >
              <Plus size={14} /> Add Equipment
            </button>
          </div>

          <div className="space-y-2">
            {equipment.map((eq, idx) => (
              <div key={idx} className="grid grid-cols-[1fr_2fr_auto] gap-3 items-end">
                <div>
                  <label className="block text-[10px] text-text-tertiary uppercase tracking-wider mb-1">Tag</label>
                  <input
                    type="text"
                    value={eq.tag}
                    onChange={(e) => updateEquipment(idx, "tag", e.target.value)}
                    className="w-full bg-[#050505] border border-border rounded-lg px-3 py-2 text-sm font-mono text-text-primary focus:outline-none focus:border-accent/40"
                  />
                </div>
                <SelectField
                  label="Type"
                  value={eq.type}
                  onChange={(v) => updateEquipment(idx, "type", v)}
                  options={EQUIPMENT_TYPES}
                />
                <button
                  onClick={() => removeEquipment(idx)}
                  className="p-2 text-text-tertiary hover:text-red-400 transition-colors mb-0.5"
                >
                  <Trash2 size={16} />
                </button>
              </div>
            ))}
          </div>
        </section>

        <button
          onClick={handleRun}
          disabled={loading || equipment.length < 2}
          className="flex items-center gap-2 px-6 py-2.5 text-sm font-semibold bg-accent text-[#050505] rounded-full hover:bg-accent-dim transition-all duration-300 hover:shadow-[0_0_24px_rgba(0,229,160,0.25)] disabled:opacity-50"
        >
          {loading ? <Loader2 size={16} className="animate-spin" /> : <Play size={14} />}
          {loading ? "Checking..." : "Check Spacing"}
        </button>

        {error && (
          <div className="flex items-start gap-2 text-sm text-red-400 bg-red-400/10 border border-red-400/20 rounded-lg px-4 py-3">
            <AlertTriangle size={16} className="mt-0.5 flex-shrink-0" />
            {error}
          </div>
        )}

        {result && (
          <div className="space-y-4">
            {/* Summary */}
            <ResultCard
              title="Plot Estimate"
              items={[
                { label: "Plot Area", value: `${result.plot_area_estimate_m2} m²` },
                { label: "Dimensions", value: `${result.plot_dimensions_m[0]} x ${result.plot_dimensions_m[1]} m` },
                { label: "Equipment Count", value: `${result.equipment_list.length}` },
                { label: "Violations", value: `${result.total_violations}` },
              ]}
            />

            {/* Spacing matrix */}
            <div className="rounded-xl border border-border bg-surface overflow-hidden">
              <div className="px-4 py-3 border-b border-border bg-surface-elevated">
                <h3 className="text-[13px] font-semibold text-text-primary">
                  Minimum Spacing Requirements ({result.spacing_checks.length} pairs)
                </h3>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-[12px]">
                  <thead>
                    <tr className="border-b border-border text-text-tertiary uppercase tracking-wider">
                      <th className="text-left px-4 py-2 font-medium">Equipment A</th>
                      <th className="text-left px-4 py-2 font-medium">Equipment B</th>
                      <th className="text-right px-4 py-2 font-medium">Min Distance</th>
                      <th className="text-center px-4 py-2 font-medium">Risk A</th>
                      <th className="text-center px-4 py-2 font-medium">Risk B</th>
                      <th className="text-left px-4 py-2 font-medium">Standard</th>
                    </tr>
                  </thead>
                  <tbody>
                    {result.spacing_checks.map((s, i) => (
                      <tr key={i} className="border-b border-border/50 hover:bg-white/[0.01]">
                        <td className="px-4 py-2 text-text-primary font-mono">{s.equipment_a}</td>
                        <td className="px-4 py-2 text-text-primary font-mono">{s.equipment_b}</td>
                        <td className="px-4 py-2 text-right text-text-primary font-semibold font-mono">
                          {s.minimum_distance_m} m
                        </td>
                        <td className={`px-4 py-2 text-center capitalize ${riskColor(s.risk_level_a)}`}>
                          {s.risk_level_a}
                        </td>
                        <td className={`px-4 py-2 text-center capitalize ${riskColor(s.risk_level_b)}`}>
                          {s.risk_level_b}
                        </td>
                        <td className="px-4 py-2 text-text-secondary">{s.governing_standard}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
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
