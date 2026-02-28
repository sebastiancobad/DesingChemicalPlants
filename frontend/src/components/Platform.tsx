import { motion } from "framer-motion";
import { useScrollReveal } from "../hooks/useScrollReveal";
import { Cpu, Shield, Zap, Layers } from "lucide-react";

const FEATURES = [
  {
    icon: Cpu,
    title: "Deterministic Kernel",
    description:
      "Every calculation is reproducible, auditable, and traceable to a published standard. No stochastic shortcuts.",
  },
  {
    icon: Shield,
    title: "Standards-First",
    description:
      "TEMA, ASME, API, and Kern references are embedded directly into the computation graph with automatic citation.",
  },
  {
    icon: Zap,
    title: "Instant Sizing",
    description:
      "From thermal duty to tube count, baffle spacing, and shell thickness in under 100ms. Full quick-size in one API call.",
  },
  {
    icon: Layers,
    title: "Modular Architecture",
    description:
      "Heat exchangers, economics, thermo-physical properties — each module is independent, testable, and extensible.",
  },
];

export default function Platform() {
  const { ref, isVisible } = useScrollReveal(0.1);

  return (
    <section id="platform" className="relative py-32 lg:py-40">
      <div ref={ref} className="max-w-7xl mx-auto px-6 lg:px-10">
        {/* Section header */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={isVisible ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.8, ease: [0.22, 1, 0.36, 1] }}
          className="max-w-3xl mb-20"
        >
          <p className="text-[12px] font-medium tracking-[0.2em] uppercase text-accent mb-4">
            The Platform
          </p>
          <h2 className="text-4xl sm:text-5xl lg:text-6xl font-bold leading-[1.05] tracking-tight text-text-primary mb-6">
            Engineering precision,
            <br />
            <span className="text-text-secondary">not approximation.</span>
          </h2>
          <p className="text-lg text-text-secondary leading-relaxed max-w-xl font-light">
            ChemScale is built for process engineers who demand traceability
            from first principles to final cost estimate.
          </p>
        </motion.div>

        {/* Feature grid */}
        <div className="grid sm:grid-cols-2 gap-px bg-border rounded-2xl overflow-hidden border border-border">
          {FEATURES.map((feat, i) => (
            <motion.div
              key={feat.title}
              initial={{ opacity: 0, y: 20 }}
              animate={isVisible ? { opacity: 1, y: 0 } : {}}
              transition={{
                delay: 0.15 * i,
                duration: 0.7,
                ease: [0.22, 1, 0.36, 1],
              }}
              className="group bg-surface p-8 lg:p-10 hover:bg-surface-hover transition-all duration-500"
            >
              <div className="w-10 h-10 rounded-xl bg-accent/10 flex items-center justify-center mb-5 group-hover:bg-accent/15 transition-colors duration-500">
                <feat.icon size={20} className="text-accent" />
              </div>
              <h3 className="text-lg font-semibold text-text-primary mb-3">
                {feat.title}
              </h3>
              <p className="text-sm text-text-secondary leading-relaxed">
                {feat.description}
              </p>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
