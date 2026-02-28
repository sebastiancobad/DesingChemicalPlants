import { useState } from "react";
import { motion } from "framer-motion";
import { useScrollReveal } from "../hooks/useScrollReveal";
import { Play, Loader2, CheckCircle2, AlertTriangle } from "lucide-react";
import { Link } from "react-router-dom";

interface PipeResult {
  nps: string;
  schedule: string;
  inner_diameter_mm: number;
  velocity_ms: number;
  reynolds: number;
  friction_factor: number;
  total_pressure_drop_kpa: number;
  total_equivalent_length_m: number;
  velocity_ok: boolean;
  velocity_message: string;
  warnings: string[];
  standards_refs: string[];
}

const DEFAULT_INPUTS = {
  mass_flow: "5.0",
  density: "995",
  viscosity: "0.001",
  pipe_length: "100",
  m_dot_hot: "13.89",
};

export default function Demo() {
  const { ref, isVisible } = useScrollReveal(0.08);
  const [inputs, setInputs] = useState(DEFAULT_INPUTS);
  const [result, setResult] = useState<PipeResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleRun = async () => {
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const resp = await fetch("/api/v1/piping/size", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          mass_flow_kgs: parseFloat(inputs.mass_flow),
          density_kgm3: parseFloat(inputs.density),
          viscosity_pas: parseFloat(inputs.viscosity),
          pipe_length_m: parseFloat(inputs.pipe_length),
          fluid_phase: "liquid",
          fittings: { "90_elbow_std": 4, "gate_valve": 2 },
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

  const inputFields = [
    { key: "mass_flow", label: "Mass Flow", unit: "kg/s" },
    { key: "density", label: "Density", unit: "kg/m³" },
    { key: "viscosity", label: "Viscosity", unit: "Pa·s" },
    { key: "pipe_length", label: "Pipe Length", unit: "m" },
  ];

  return (
    <section id="demo" className="relative py-32 lg:py-40">
      <div ref={ref} className="max-w-7xl mx-auto px-6 lg:px-10">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={isVisible ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.8, ease: [0.22, 1, 0.36, 1] }}
          className="text-center mb-16"
        >
          <p className="text-[12px] font-medium tracking-[0.2em] uppercase text-accent mb-4">
            Live Demo
          </p>
          <h2 className="text-4xl sm:text-5xl font-bold leading-[1.05] tracking-tight text-text-primary">
            Try it now.
          </h2>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={isVisible ? { opacity: 1, y: 0 } : {}}
          transition={{ delay: 0.2, duration: 0.8, ease: [0.22, 1, 0.36, 1] }}
          className="max-w-4xl mx-auto"
        >
          <div className="rounded-2xl border border-border bg-surface overflow-hidden glow-accent">
            {/* Header bar */}
            <div className="px-6 py-4 border-b border-border flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-2 h-2 rounded-full bg-accent animate-pulse" />
                <span className="text-[13px] font-medium text-text-primary">
                  Quick Pipe Sizing
                </span>
              </div>
              <span className="text-[11px] font-mono text-text-tertiary">
                POST /api/v1/piping/size
              </span>
            </div>

            <div className="p-6 lg:p-8">
              {/* Input grid */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-6">
                {inputFields.map((f) => (
                  <div key={f.key}>
                    <label className="block text-[11px] text-text-tertiary uppercase tracking-wider mb-1.5">
                      {f.label}
                    </label>
                    <div className="relative">
                      <input
                        type="number"
                        value={inputs[f.key as keyof typeof inputs]}
                        onChange={(e) =>
                          setInputs({ ...inputs, [f.key]: e.target.value })
                        }
                        className="w-full bg-[#050505] border border-border rounded-lg px-3 py-2.5 text-sm font-mono text-text-primary focus:outline-none focus:border-accent/40 transition-colors"
                      />
                      <span className="absolute right-3 top-1/2 -translate-y-1/2 text-[10px] text-text-tertiary">
                        {f.unit}
                      </span>
                    </div>
                  </div>
                ))}
              </div>

              {/* Run button */}
              <div className="flex items-center gap-4">
                <button
                  onClick={handleRun}
                  disabled={loading}
                  className="flex items-center gap-2 px-6 py-2.5 text-sm font-semibold bg-accent text-[#050505] rounded-full hover:bg-accent-dim transition-all duration-300 hover:shadow-[0_0_24px_rgba(0,229,160,0.25)] disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {loading ? (
                    <Loader2 size={16} className="animate-spin" />
                  ) : (
                    <Play size={14} />
                  )}
                  {loading ? "Computing..." : "Size Pipe"}
                </button>
                <Link
                  to="/modules/piping"
                  className="text-[13px] text-accent hover:text-accent-dim transition-colors"
                >
                  Open full module →
                </Link>
              </div>

              {/* Error */}
              {error && (
                <div className="mt-4 flex items-start gap-2 text-sm text-red-400 bg-red-400/10 border border-red-400/20 rounded-lg px-4 py-3">
                  <AlertTriangle size={16} className="mt-0.5 flex-shrink-0" />
                  {error}
                </div>
              )}

              {/* Results */}
              {result && (
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.5 }}
                  className="mt-6 space-y-4"
                >
                  {/* Results grid */}
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-px bg-border rounded-xl overflow-hidden border border-border">
                    {[
                      { label: "NPS", value: `${result.nps}"` },
                      { label: "Schedule", value: result.schedule },
                      { label: "Inner Dia.", value: `${result.inner_diameter_mm} mm` },
                      { label: "Velocity", value: `${result.velocity_ms} m/s` },
                      { label: "Reynolds", value: `${result.reynolds.toLocaleString()}` },
                      { label: "Friction f", value: result.friction_factor.toFixed(5) },
                      { label: "Total ΔP", value: `${result.total_pressure_drop_kpa} kPa` },
                      { label: "Eq. Length", value: `${result.total_equivalent_length_m} m` },
                    ].map((item) => (
                      <div
                        key={item.label}
                        className="bg-[#050505] px-4 py-3"
                      >
                        <div className="text-[10px] text-text-tertiary uppercase tracking-wider">
                          {item.label}
                        </div>
                        <div className="text-base font-semibold font-mono text-text-primary mt-0.5">
                          {item.value}
                        </div>
                      </div>
                    ))}
                  </div>

                  {/* Warnings */}
                  {result.warnings.length > 0 && (
                    <div className="space-y-1.5">
                      {result.warnings.map((w, i) => (
                        <div
                          key={i}
                          className="flex items-start gap-2 text-[12px] text-yellow-400/80 bg-yellow-400/5 border border-yellow-400/10 rounded-lg px-3 py-2"
                        >
                          <AlertTriangle size={13} className="mt-0.5 flex-shrink-0" />
                          {w}
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Standards refs */}
                  {result.standards_refs.length > 0 && (
                    <div className="flex flex-wrap gap-2">
                      {result.standards_refs.map((r, i) => (
                        <span
                          key={i}
                          className="inline-flex items-center gap-1.5 px-2.5 py-1 text-[10px] font-mono text-text-tertiary bg-white/[0.02] border border-border rounded-full"
                        >
                          <CheckCircle2 size={10} className="text-accent/50" />
                          {r}
                        </span>
                      ))}
                    </div>
                  )}
                </motion.div>
              )}
            </div>
          </div>

          {/* Module links grid */}
          <div className="mt-8 grid grid-cols-2 sm:grid-cols-4 gap-3">
            {[
              { label: "Heat Exchanger", href: "/modules/heat-exchanger" },
              { label: "Pump Sizing", href: "/modules/pump" },
              { label: "Phase Separator", href: "/modules/separator" },
              { label: "Materials", href: "/modules/materials" },
              { label: "Plant Layout", href: "/modules/layout" },
              { label: "Economics", href: "/modules/economics" },
              { label: "Piping", href: "/modules/piping" },
            ].map((m) => (
              <Link
                key={m.href}
                to={m.href}
                className="px-4 py-3 text-[13px] text-center text-text-secondary hover:text-text-primary border border-border rounded-xl hover:border-accent/30 hover:bg-white/[0.02] transition-all"
              >
                {m.label}
              </Link>
            ))}
          </div>
        </motion.div>
      </div>
    </section>
  );
}
