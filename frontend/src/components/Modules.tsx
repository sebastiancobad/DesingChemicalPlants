import { motion } from "framer-motion";
import { useScrollReveal } from "../hooks/useScrollReveal";
import { Thermometer, DollarSign, FlaskConical, BarChart3 } from "lucide-react";

const MODULES = [
  {
    number: "01",
    icon: Thermometer,
    title: "Heat Exchanger Design",
    subtitle: "Shell & Tube — TEMA E/J/X",
    details: [
      "LMTD & F-factor (Bowman-Mueller-Nagle)",
      "Kern method shell-side HTC",
      "Dittus-Boelter tube-side HTC",
      "ASME VIII-1 UG-27 shell thickness",
      "Tube count via CTP/CL factors",
    ],
    accent: "from-[#00e5a0] to-[#00b4d8]",
  },
  {
    number: "02",
    icon: DollarSign,
    title: "Economic Evaluation",
    subtitle: "CAPEX, OPEX & Cash Flow",
    details: [
      "Turton 5th Ed. cost correlations",
      "Bare-module method (B1/B2 + Fm·Fp)",
      "CEPCI escalation (1957-2024)",
      "Lang factor & detailed factorial",
      "Straight-line depreciation & OPEX",
    ],
    accent: "from-[#7b61ff] to-[#c084fc]",
  },
  {
    number: "03",
    icon: FlaskConical,
    title: "Thermo-Physical Properties",
    subtitle: "Pure Components & Mixtures",
    details: [
      "Peng-Robinson EOS",
      "DIPPR correlations",
      "Vapor-liquid equilibrium",
      "Transport properties (μ, k, ρ)",
      "Activity coefficient models",
    ],
    accent: "from-[#f59e0b] to-[#ef4444]",
  },
  {
    number: "04",
    icon: BarChart3,
    title: "Process Simulation",
    subtitle: "Steady-State Flowsheeting",
    details: [
      "Sequential modular solver",
      "Recycle stream convergence",
      "Energy & mass balance audit",
      "Equipment performance curves",
      "Sensitivity & optimization",
    ],
    accent: "from-[#06b6d4] to-[#3b82f6]",
  },
];

export default function Modules() {
  const { ref, isVisible } = useScrollReveal(0.08);

  return (
    <section id="modules" className="relative py-32 lg:py-40 bg-surface">
      {/* Top border glow */}
      <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-accent/20 to-transparent" />

      <div ref={ref} className="max-w-7xl mx-auto px-6 lg:px-10">
        {/* Section header */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={isVisible ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.8, ease: [0.22, 1, 0.36, 1] }}
          className="text-center mb-20"
        >
          <p className="text-[12px] font-medium tracking-[0.2em] uppercase text-accent mb-4">
            Calculation Modules
          </p>
          <h2 className="text-4xl sm:text-5xl lg:text-6xl font-bold leading-[1.05] tracking-tight text-text-primary">
            Four pillars of
            <br />
            <span className="text-text-secondary">process design.</span>
          </h2>
        </motion.div>

        {/* Module cards */}
        <div className="grid md:grid-cols-2 gap-5">
          {MODULES.map((mod, i) => (
            <motion.div
              key={mod.number}
              initial={{ opacity: 0, y: 30 }}
              animate={isVisible ? { opacity: 1, y: 0 } : {}}
              transition={{
                delay: 0.12 * i,
                duration: 0.7,
                ease: [0.22, 1, 0.36, 1],
              }}
              className="group relative bg-[#050505] rounded-2xl border border-border overflow-hidden hover:border-white/[0.08] transition-all duration-500"
            >
              {/* Top accent line */}
              <div
                className={`absolute top-0 left-0 right-0 h-px bg-gradient-to-r ${mod.accent} opacity-0 group-hover:opacity-40 transition-opacity duration-500`}
              />

              <div className="p-8 lg:p-10">
                {/* Header row */}
                <div className="flex items-start justify-between mb-6">
                  <div>
                    <span className="text-[11px] font-mono text-text-tertiary tracking-wider">
                      MODULE {mod.number}
                    </span>
                    <h3 className="text-xl font-semibold text-text-primary mt-1">
                      {mod.title}
                    </h3>
                    <p className="text-[13px] text-text-secondary mt-0.5">
                      {mod.subtitle}
                    </p>
                  </div>
                  <div className="w-10 h-10 rounded-xl bg-white/[0.04] flex items-center justify-center flex-shrink-0 group-hover:bg-white/[0.06] transition-colors">
                    <mod.icon size={18} className="text-text-secondary group-hover:text-text-primary transition-colors" />
                  </div>
                </div>

                {/* Details list */}
                <ul className="space-y-2.5">
                  {mod.details.map((detail) => (
                    <li
                      key={detail}
                      className="flex items-start gap-3 text-[13px] text-text-secondary"
                    >
                      <span className="mt-1.5 w-1 h-1 rounded-full bg-accent/50 flex-shrink-0" />
                      {detail}
                    </li>
                  ))}
                </ul>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
