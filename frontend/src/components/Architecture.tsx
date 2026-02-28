import { motion } from "framer-motion";
import { useScrollReveal } from "../hooks/useScrollReveal";

const LAYERS = [
  {
    label: "API Layer",
    tech: "FastAPI + Pydantic v2",
    color: "border-[#00e5a0]/30 bg-[#00e5a0]/[0.04]",
    dotColor: "bg-[#00e5a0]",
  },
  {
    label: "Calculation Kernel",
    tech: "Pure Python — deterministic, no I/O",
    color: "border-[#00b4d8]/30 bg-[#00b4d8]/[0.04]",
    dotColor: "bg-[#00b4d8]",
  },
  {
    label: "Thermo Engine",
    tech: "EOS, DIPPR, VLE solvers",
    color: "border-[#7b61ff]/30 bg-[#7b61ff]/[0.04]",
    dotColor: "bg-[#7b61ff]",
  },
  {
    label: "Data Layer",
    tech: "PostgreSQL + SQLAlchemy 2.0",
    color: "border-[#f59e0b]/30 bg-[#f59e0b]/[0.04]",
    dotColor: "bg-[#f59e0b]",
  },
];

const CODE_PREVIEW = `# Quick-size a shell-and-tube heat exchanger
result = quick_size(
    T_h_in=423.15,   # 150 °C
    T_h_out=363.15,   #  90 °C
    T_c_in=303.15,    #  30 °C
    T_c_out=318.15,   #  45 °C
    m_dot_hot=13.89,  # kg/s
    rho_hot=920.0,
    mu_hot=0.0002,
    cp_hot=4200.0,
    k_hot=0.67,
    rho_cold=995.0,
    mu_cold=0.0008,
    cp_cold=4180.0,
    k_cold=0.62,
)

print(f"Duty:  {result.duty_w/1e3:.0f} kW")
print(f"Area:  {result.area_provided_m2:.1f} m²")
print(f"LMTD:  {result.lmtd_k:.1f} K")
print(f"U:     {result.U_dirty:.0f} W/(m²·K)")`;

export default function Architecture() {
  const { ref, isVisible } = useScrollReveal(0.08);

  return (
    <section id="architecture" className="relative py-32 lg:py-40 bg-surface">
      <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-accent/20 to-transparent" />

      <div ref={ref} className="max-w-7xl mx-auto px-6 lg:px-10">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={isVisible ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.8, ease: [0.22, 1, 0.36, 1] }}
          className="text-center mb-20"
        >
          <p className="text-[12px] font-medium tracking-[0.2em] uppercase text-accent mb-4">
            Architecture
          </p>
          <h2 className="text-4xl sm:text-5xl lg:text-6xl font-bold leading-[1.05] tracking-tight text-text-primary">
            Clean layers,
            <br />
            <span className="text-text-secondary">zero side-effects.</span>
          </h2>
        </motion.div>

        <div className="grid lg:grid-cols-2 gap-10">
          {/* Layer stack */}
          <motion.div
            initial={{ opacity: 0, x: -30 }}
            animate={isVisible ? { opacity: 1, x: 0 } : {}}
            transition={{ delay: 0.2, duration: 0.8, ease: [0.22, 1, 0.36, 1] }}
            className="space-y-3"
          >
            {LAYERS.map((layer, i) => (
              <motion.div
                key={layer.label}
                initial={{ opacity: 0, x: -20 }}
                animate={isVisible ? { opacity: 1, x: 0 } : {}}
                transition={{
                  delay: 0.3 + 0.1 * i,
                  duration: 0.6,
                  ease: [0.22, 1, 0.36, 1],
                }}
                className={`flex items-center gap-4 p-5 rounded-xl border ${layer.color} transition-all duration-300 hover:scale-[1.01]`}
              >
                <span className={`w-2.5 h-2.5 rounded-full ${layer.dotColor}`} />
                <div className="flex-1">
                  <div className="text-sm font-semibold text-text-primary">
                    {layer.label}
                  </div>
                  <div className="text-[12px] text-text-secondary mt-0.5">
                    {layer.tech}
                  </div>
                </div>
                <span className="text-[11px] font-mono text-text-tertiary">
                  L{i}
                </span>
              </motion.div>
            ))}

            {/* Connector lines */}
            <div className="flex justify-center py-2">
              <div className="flex flex-col items-center gap-1">
                {[0, 1, 2].map((j) => (
                  <div key={j} className="w-px h-3 bg-border" />
                ))}
                <div className="text-[10px] text-text-tertiary font-mono">
                  dependency injection
                </div>
              </div>
            </div>
          </motion.div>

          {/* Code preview */}
          <motion.div
            initial={{ opacity: 0, x: 30 }}
            animate={isVisible ? { opacity: 1, x: 0 } : {}}
            transition={{ delay: 0.3, duration: 0.8, ease: [0.22, 1, 0.36, 1] }}
            className="relative rounded-2xl border border-border overflow-hidden glow-accent"
          >
            {/* Window chrome */}
            <div className="flex items-center gap-2 px-5 py-3 bg-[#0d0d0d] border-b border-border">
              <div className="flex gap-1.5">
                <span className="w-2.5 h-2.5 rounded-full bg-[#ff5f56]" />
                <span className="w-2.5 h-2.5 rounded-full bg-[#ffbd2e]" />
                <span className="w-2.5 h-2.5 rounded-full bg-[#27c93f]" />
              </div>
              <span className="ml-3 text-[11px] text-text-tertiary font-mono">
                quick_size_example.py
              </span>
            </div>

            {/* Code block */}
            <pre className="p-6 overflow-x-auto text-[12px] leading-relaxed font-mono">
              <code className="text-text-secondary">
                {CODE_PREVIEW.split("\n").map((line, i) => (
                  <div key={i} className="flex">
                    <span className="w-8 flex-shrink-0 text-text-tertiary/50 text-right mr-4 select-none">
                      {i + 1}
                    </span>
                    <span
                      className={
                        line.startsWith("#")
                          ? "text-text-tertiary italic"
                          : line.includes("=")
                          ? "text-text-secondary"
                          : line.includes("print")
                          ? "text-accent/80"
                          : ""
                      }
                    >
                      {line || "\u00A0"}
                    </span>
                  </div>
                ))}
              </code>
            </pre>
          </motion.div>
        </div>
      </div>
    </section>
  );
}
