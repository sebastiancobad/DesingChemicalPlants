import { motion } from "framer-motion";
import { useScrollReveal } from "../hooks/useScrollReveal";
import { BookOpen, CheckCircle2 } from "lucide-react";

const STANDARDS = [
  {
    code: "TEMA 10th Ed.",
    scope: "Tubular Exchanger Manufacturers Association",
    refs: ["RCB-4.4 Tube Count", "RCB-4.6 Baffle Spacing", "T-4.4.2 Tube Pitch"],
  },
  {
    code: "ASME VIII-1",
    scope: "Boiler and Pressure Vessel Code",
    refs: ["UG-27 Cylindrical Shells", "UG-34 Flat Heads", "UG-47 Tubesheet Design"],
  },
  {
    code: "API 660",
    scope: "Shell-and-Tube Heat Exchangers",
    refs: ["Mechanical Design Rules", "Vibration Analysis", "Nozzle Loads"],
  },
  {
    code: "Turton 5th Ed.",
    scope: "Analysis, Synthesis & Design of Chemical Processes",
    refs: ["Ch. 7 Cost Correlations", "Eq. 7.7 Bare Module", "CEPCI Escalation"],
  },
  {
    code: "Kern Method",
    scope: "Process Heat Transfer (D.Q. Kern)",
    refs: ["Ch. 7 Shell-Side HTC", "Equivalent Diameter", "Pressure Drop"],
  },
  {
    code: "Bowman 1940",
    scope: "ASME Transactions",
    refs: ["F-Factor Analytical", "Multi-Pass Correction", "R & P Parameters"],
  },
];

export default function Standards() {
  const { ref, isVisible } = useScrollReveal(0.08);

  return (
    <section id="standards" className="relative py-32 lg:py-40">
      <div ref={ref} className="max-w-7xl mx-auto px-6 lg:px-10">
        <div className="grid lg:grid-cols-[1fr_1.5fr] gap-16 lg:gap-20">
          {/* Left — copy */}
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={isVisible ? { opacity: 1, y: 0 } : {}}
            transition={{ duration: 0.8, ease: [0.22, 1, 0.36, 1] }}
            className="lg:sticky lg:top-32 lg:self-start"
          >
            <p className="text-[12px] font-medium tracking-[0.2em] uppercase text-accent mb-4">
              Standards & References
            </p>
            <h2 className="text-4xl sm:text-5xl font-bold leading-[1.05] tracking-tight text-text-primary mb-6">
              Every number
              <br />
              <span className="text-text-secondary">has a source.</span>
            </h2>
            <p className="text-base text-text-secondary leading-relaxed font-light mb-8">
              Results include embedded standard references so peer reviewers and
              auditors can trace every coefficient, correlation, and safety
              factor back to its published origin.
            </p>
            <div className="flex items-center gap-3 text-sm text-text-secondary">
              <BookOpen size={16} className="text-accent" />
              <span>6 primary standards integrated</span>
            </div>
          </motion.div>

          {/* Right — standards grid */}
          <div className="grid sm:grid-cols-2 gap-4">
            {STANDARDS.map((std, i) => (
              <motion.div
                key={std.code}
                initial={{ opacity: 0, y: 20 }}
                animate={isVisible ? { opacity: 1, y: 0 } : {}}
                transition={{
                  delay: 0.08 * i,
                  duration: 0.7,
                  ease: [0.22, 1, 0.36, 1],
                }}
                className="group bg-surface rounded-xl border border-border p-6 hover:border-white/[0.08] hover:bg-surface-hover transition-all duration-500"
              >
                <h4 className="text-base font-semibold text-text-primary font-mono mb-1">
                  {std.code}
                </h4>
                <p className="text-[12px] text-text-tertiary mb-4">{std.scope}</p>
                <ul className="space-y-2">
                  {std.refs.map((r) => (
                    <li
                      key={r}
                      className="flex items-start gap-2 text-[12px] text-text-secondary"
                    >
                      <CheckCircle2
                        size={13}
                        className="mt-0.5 text-accent/60 flex-shrink-0"
                      />
                      {r}
                    </li>
                  ))}
                </ul>
              </motion.div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
