import { motion } from "framer-motion";
import { ArrowRight, Hexagon } from "lucide-react";

const EASE: [number, number, number, number] = [0.22, 1, 0.36, 1];

const FADE_UP = {
  hidden: { opacity: 0, y: 30 },
  visible: (i: number) => ({
    opacity: 1,
    y: 0,
    transition: { delay: 0.15 * i, duration: 0.8, ease: EASE },
  }),
};

export default function Hero() {
  return (
    <section className="relative min-h-screen flex items-center justify-center overflow-hidden">
      {/* Background layers */}
      <div className="absolute inset-0 grid-pattern" />

      {/* Radial gradient orb */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[900px] h-[900px] rounded-full bg-gradient-radial from-accent/[0.06] via-transparent to-transparent blur-3xl pointer-events-none" />

      {/* Floating hexagons */}
      <motion.div
        animate={{ y: [0, -20, 0], rotate: [0, 5, 0] }}
        transition={{ duration: 12, repeat: Infinity, ease: "easeInOut" }}
        className="absolute top-32 right-[15%] text-accent/10"
      >
        <Hexagon size={120} strokeWidth={0.5} />
      </motion.div>
      <motion.div
        animate={{ y: [0, 15, 0], rotate: [0, -3, 0] }}
        transition={{ duration: 10, repeat: Infinity, ease: "easeInOut", delay: 2 }}
        className="absolute bottom-40 left-[10%] text-accent/[0.07]"
      >
        <Hexagon size={80} strokeWidth={0.5} />
      </motion.div>

      {/* Content */}
      <div className="relative z-10 max-w-5xl mx-auto px-6 text-center pt-28 pb-20">
        {/* Badge */}
        <motion.div
          custom={0}
          variants={FADE_UP}
          initial="hidden"
          animate="visible"
          className="inline-flex items-center gap-2 px-4 py-1.5 mb-8 rounded-full border border-accent/20 bg-accent/[0.05]"
        >
          <span className="w-1.5 h-1.5 rounded-full bg-accent animate-pulse" />
          <span className="text-[12px] font-medium tracking-wider uppercase text-accent">
            Engineering-Grade Accuracy
          </span>
        </motion.div>

        {/* Headline */}
        <motion.h1
          custom={1}
          variants={FADE_UP}
          initial="hidden"
          animate="visible"
          className="text-5xl sm:text-6xl lg:text-[80px] font-bold leading-[0.95] tracking-tight mb-6"
        >
          <span className="block text-text-primary">Design Chemical</span>
          <span className="block gradient-text mt-2">Plants at Scale</span>
        </motion.h1>

        {/* Subtitle */}
        <motion.p
          custom={2}
          variants={FADE_UP}
          initial="hidden"
          animate="visible"
          className="max-w-2xl mx-auto text-lg sm:text-xl text-text-secondary leading-relaxed mb-12 font-light"
        >
          TEMA-certified heat exchanger sizing, rigorous cost estimation, and
          ASME-compliant mechanical design — all in one deterministic kernel.
        </motion.p>

        {/* CTAs */}
        <motion.div
          custom={3}
          variants={FADE_UP}
          initial="hidden"
          animate="visible"
          className="flex flex-col sm:flex-row items-center justify-center gap-4"
        >
          <a
            href="#demo"
            className="group flex items-center gap-2 px-8 py-3.5 text-sm font-semibold bg-accent text-[#050505] rounded-full hover:bg-accent-dim transition-all duration-300 hover:shadow-[0_0_32px_rgba(0,229,160,0.3)]"
          >
            Start Designing
            <ArrowRight
              size={16}
              className="group-hover:translate-x-1 transition-transform duration-300"
            />
          </a>
          <a
            href="#platform"
            className="flex items-center gap-2 px-8 py-3.5 text-sm font-medium text-text-secondary border border-border rounded-full hover:border-text-tertiary hover:text-text-primary transition-all duration-300"
          >
            Explore Platform
          </a>
        </motion.div>

        {/* Stats bar */}
        <motion.div
          custom={4}
          variants={FADE_UP}
          initial="hidden"
          animate="visible"
          className="mt-20 grid grid-cols-2 sm:grid-cols-4 gap-px bg-border rounded-2xl overflow-hidden border border-border"
        >
          {[
            { value: "TEMA 10th", label: "Edition Compliant" },
            { value: "API 660", label: "Shell & Tube Standard" },
            { value: "ASME VIII", label: "Pressure Vessel Code" },
            { value: "Turton 5th", label: "Cost Correlations" },
          ].map((stat) => (
            <div
              key={stat.label}
              className="bg-surface px-6 py-5 text-center hover:bg-surface-hover transition-colors duration-300"
            >
              <div className="text-xl sm:text-2xl font-semibold text-text-primary font-mono">
                {stat.value}
              </div>
              <div className="text-[11px] text-text-tertiary uppercase tracking-widest mt-1">
                {stat.label}
              </div>
            </div>
          ))}
        </motion.div>
      </div>

      {/* Bottom fade */}
      <div className="absolute bottom-0 left-0 right-0 h-32 bg-gradient-to-t from-[#050505] to-transparent pointer-events-none" />
    </section>
  );
}
