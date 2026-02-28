import { motion } from "framer-motion";
import { useScrollReveal } from "../hooks/useScrollReveal";
import { Link } from "react-router-dom";
import {
  Thermometer,
  DollarSign,
  Pipette,
  Gauge,
  Filter,
  Shield,
  LayoutGrid,
} from "lucide-react";

const MODULES = [
  {
    number: "01",
    icon: Thermometer,
    title: "Heat Exchanger Design",
    subtitle: "Shell & Tube — TEMA E/J/X",
    href: "/modules/heat-exchanger",
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
    icon: Pipette,
    title: "Piping & Pipeline",
    subtitle: "Pipe Sizing & Pressure Drop",
    href: "/modules/piping",
    details: [
      "Auto NPS selection (SCH 40/80/160)",
      "Darcy-Weisbach pressure drop",
      "Colebrook-White friction factor",
      "Fitting equivalent lengths (Crane TP-410)",
      "Erosional velocity check (API RP 14E)",
    ],
    accent: "from-[#3b82f6] to-[#06b6d4]",
  },
  {
    number: "03",
    icon: Gauge,
    title: "Pump Sizing",
    subtitle: "Centrifugal Pump — API 610",
    href: "/modules/pump",
    details: [
      "Total dynamic head calculation",
      "Hydraulic & brake power",
      "NPSH available vs required",
      "Pump efficiency estimation (HI)",
      "Motor sizing to standard frames",
    ],
    accent: "from-[#f59e0b] to-[#ef4444]",
  },
  {
    number: "04",
    icon: Filter,
    title: "Phase Separator",
    subtitle: "Gas-Liquid Knockout Drum",
    href: "/modules/separator",
    details: [
      "Souders-Brown K factor (API 12J)",
      "Stokes' law droplet settling",
      "Vertical & horizontal sizing",
      "Mist eliminator selection",
      "ASME VIII-1 wall thickness",
    ],
    accent: "from-[#8b5cf6] to-[#ec4899]",
  },
  {
    number: "05",
    icon: Shield,
    title: "Material Selection",
    subtitle: "Corrosion & NACE MR0175",
    href: "/modules/materials",
    details: [
      "8 ASME materials (CS to Titanium)",
      "Corrosion rate lookup (10 environments)",
      "NACE MR0175 sour service compliance",
      "API 941 hydrogen attack check",
      "Alternative material suggestions",
    ],
    accent: "from-[#10b981] to-[#34d399]",
  },
  {
    number: "06",
    icon: LayoutGrid,
    title: "Plant Layout",
    subtitle: "Equipment Spacing Rules",
    href: "/modules/layout",
    details: [
      "NFPA 30 minimum distances",
      "API 2510 pressurized storage",
      "Fire risk classification",
      "Plot area estimation",
      "Equipment pair spacing matrix",
    ],
    accent: "from-[#06b6d4] to-[#3b82f6]",
  },
  {
    number: "07",
    icon: DollarSign,
    title: "Economic Evaluation",
    subtitle: "CAPEX — Guthrie Bare-Module",
    href: "/modules/economics",
    details: [
      "Turton 5th Ed. cost correlations",
      "Bare-module method (Fbm + Fm·Fp)",
      "CEPCI escalation (2001-2026)",
      "Six-tenths rule cross-check",
      "8 equipment types supported",
    ],
    accent: "from-[#7b61ff] to-[#c084fc]",
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
            Seven pillars of
            <br />
            <span className="text-text-secondary">process design.</span>
          </h2>
        </motion.div>

        {/* Module cards */}
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-5">
          {MODULES.map((mod, i) => (
            <Link key={mod.number} to={mod.href}>
              <motion.div
                initial={{ opacity: 0, y: 30 }}
                animate={isVisible ? { opacity: 1, y: 0 } : {}}
                transition={{
                  delay: 0.08 * i,
                  duration: 0.7,
                  ease: [0.22, 1, 0.36, 1],
                }}
                className="group relative bg-[#050505] rounded-2xl border border-border overflow-hidden hover:border-white/[0.08] transition-all duration-500 h-full cursor-pointer"
              >
                {/* Top accent line */}
                <div
                  className={`absolute top-0 left-0 right-0 h-px bg-gradient-to-r ${mod.accent} opacity-0 group-hover:opacity-40 transition-opacity duration-500`}
                />

                <div className="p-8">
                  {/* Header row */}
                  <div className="flex items-start justify-between mb-5">
                    <div>
                      <span className="text-[11px] font-mono text-text-tertiary tracking-wider">
                        MODULE {mod.number}
                      </span>
                      <h3 className="text-lg font-semibold text-text-primary mt-1">
                        {mod.title}
                      </h3>
                      <p className="text-[12px] text-text-secondary mt-0.5">
                        {mod.subtitle}
                      </p>
                    </div>
                    <div className="w-9 h-9 rounded-xl bg-white/[0.04] flex items-center justify-center flex-shrink-0 group-hover:bg-white/[0.06] transition-colors">
                      <mod.icon
                        size={16}
                        className="text-text-secondary group-hover:text-text-primary transition-colors"
                      />
                    </div>
                  </div>

                  {/* Details list */}
                  <ul className="space-y-2">
                    {mod.details.map((detail) => (
                      <li
                        key={detail}
                        className="flex items-start gap-2.5 text-[12px] text-text-secondary"
                      >
                        <span className="mt-1.5 w-1 h-1 rounded-full bg-accent/50 flex-shrink-0" />
                        {detail}
                      </li>
                    ))}
                  </ul>

                  {/* Open link */}
                  <div className="mt-5 text-[12px] font-medium text-accent opacity-0 group-hover:opacity-100 transition-opacity duration-300">
                    Open Module →
                  </div>
                </div>
              </motion.div>
            </Link>
          ))}
        </div>
      </div>
    </section>
  );
}
