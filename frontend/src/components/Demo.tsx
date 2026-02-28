import { useState } from "react";
import { motion } from "framer-motion";
import { useScrollReveal } from "../hooks/useScrollReveal";
import { Play, Loader2, CheckCircle2, AlertTriangle } from "lucide-react";

interface SizeResult {
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
  warnings: string[];
  standards_refs: string[];
}

const DEFAULT_INPUTS = {
  T_h_in: "150",
  T_h_out: "90",
  T_c_in: "30",
  T_c_out: "45",
  m_dot_hot: "13.89",
};

export default function Demo() {
  const { ref, isVisible } = useScrollReveal(0.08);
  const [inputs, setInputs] = useState(DEFAULT_INPUTS);
  const [result, setResult] = useState<SizeResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleRun = async () => {
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const resp = await fetch("/api/v1/hx/quick-size", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          T_h_in: parseFloat(inputs.T_h_in) + 273.15,
          T_h_out: parseFloat(inputs.T_h_out) + 273.15,
          T_c_in: parseFloat(inputs.T_c_in) + 273.15,
          T_c_out: parseFloat(inputs.T_c_out) + 273.15,
          m_dot_hot: parseFloat(inputs.m_dot_hot),
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

  const inputFields = [
    { key: "T_h_in", label: "Hot Inlet", unit: "°C" },
    { key: "T_h_out", label: "Hot Outlet", unit: "°C" },
    { key: "T_c_in", label: "Cold Inlet", unit: "°C" },
    { key: "T_c_out", label: "Cold Outlet", unit: "°C" },
    { key: "m_dot_hot", label: "Hot Flow", unit: "kg/s" },
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
                  Quick-Size Heat Exchanger
                </span>
              </div>
              <span className="text-[11px] font-mono text-text-tertiary">
                POST /api/v1/hx/quick-size
              </span>
            </div>

            <div className="p-6 lg:p-8">
              {/* Input grid */}
              <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 mb-6">
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
                {loading ? "Computing..." : "Run Sizing"}
              </button>

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
                      { label: "Duty", value: `${(result.duty_w / 1e3).toFixed(0)} kW` },
                      { label: "LMTD", value: `${result.lmtd_k.toFixed(1)} K` },
                      { label: "Area", value: `${result.area_provided_m2.toFixed(1)} m²` },
                      { label: "Tubes", value: `${result.tube_count}` },
                      { label: "F-Factor", value: result.correction_factor_F.toFixed(3) },
                      { label: "Shell ID", value: `${(result.shell_id_m * 1000).toFixed(0)} mm` },
                      { label: "Length", value: `${result.tube_length_m.toFixed(2)} m` },
                      { label: "Overdesign", value: `${result.overdesign_pct.toFixed(1)}%` },
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
        </motion.div>
      </div>
    </section>
  );
}
