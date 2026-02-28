import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Menu, X, ChevronDown } from "lucide-react";
import { Link, useLocation } from "react-router-dom";

const NAV_LINKS = [
  { label: "Platform", href: "/#platform" },
  { label: "Standards", href: "/#standards" },
  { label: "Architecture", href: "/#architecture" },
];

const MODULE_LINKS = [
  { label: "Heat Exchanger", href: "/modules/heat-exchanger", number: "01" },
  { label: "Piping & Pipeline", href: "/modules/piping", number: "02" },
  { label: "Pump Sizing", href: "/modules/pump", number: "03" },
  { label: "Phase Separator", href: "/modules/separator", number: "04" },
  { label: "Material Selection", href: "/modules/materials", number: "05" },
  { label: "Plant Layout", href: "/modules/layout", number: "06" },
  { label: "Economic Evaluation", href: "/modules/economics", number: "07" },
];

export default function Navbar() {
  const [scrolled, setScrolled] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [modulesOpen, setModulesOpen] = useState(false);
  const location = useLocation();
  const isLanding = location.pathname === "/";

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 40);
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  return (
    <motion.header
      initial={{ y: -20, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
      className={`fixed top-0 left-0 right-0 z-50 transition-all duration-500 ${
        scrolled
          ? "bg-[#050505]/80 backdrop-blur-xl border-b border-white/[0.04]"
          : "bg-transparent"
      }`}
    >
      <nav className="mx-auto max-w-7xl px-6 lg:px-10 flex items-center justify-between h-16 lg:h-18">
        {/* Logo */}
        <Link to="/" className="flex items-center gap-3 group">
          <div className="relative w-8 h-8 flex items-center justify-center">
            <div className="absolute inset-0 bg-accent/20 rounded-lg blur-md group-hover:bg-accent/30 transition-colors duration-500" />
            <svg viewBox="0 0 32 32" className="relative w-6 h-6" fill="none">
              <path
                d="M16 2L28 9v14l-12 7L4 23V9l12-7z"
                stroke="currentColor"
                strokeWidth="1.5"
                className="text-accent"
              />
              <path
                d="M16 8l8 4.5v9L16 26l-8-4.5v-9L16 8z"
                stroke="currentColor"
                strokeWidth="1"
                className="text-accent/60"
              />
              <circle cx="16" cy="16" r="2" className="fill-accent" />
            </svg>
          </div>
          <span className="text-[15px] font-semibold tracking-tight text-text-primary">
            Chem<span className="text-accent">Scale</span>
          </span>
        </Link>

        {/* Desktop nav */}
        <div className="hidden md:flex items-center gap-1">
          {isLanding &&
            NAV_LINKS.map((link) => (
              <a
                key={link.href}
                href={link.href}
                className="px-4 py-2 text-[13px] text-text-secondary hover:text-text-primary transition-colors duration-300 rounded-lg hover:bg-white/[0.03]"
              >
                {link.label}
              </a>
            ))}

          {/* Modules dropdown */}
          <div
            className="relative"
            onMouseEnter={() => setModulesOpen(true)}
            onMouseLeave={() => setModulesOpen(false)}
          >
            <button className="flex items-center gap-1 px-4 py-2 text-[13px] text-text-secondary hover:text-text-primary transition-colors duration-300 rounded-lg hover:bg-white/[0.03]">
              Modules <ChevronDown size={14} />
            </button>
            <AnimatePresence>
              {modulesOpen && (
                <motion.div
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: 8 }}
                  transition={{ duration: 0.2 }}
                  className="absolute top-full left-0 mt-1 w-64 bg-surface border border-border rounded-xl overflow-hidden shadow-2xl"
                >
                  {MODULE_LINKS.map((mod) => (
                    <Link
                      key={mod.href}
                      to={mod.href}
                      className="flex items-center gap-3 px-4 py-3 text-[13px] text-text-secondary hover:text-text-primary hover:bg-white/[0.03] transition-colors"
                    >
                      <span className="text-[10px] font-mono text-text-tertiary w-5">
                        {mod.number}
                      </span>
                      {mod.label}
                    </Link>
                  ))}
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </div>

        {/* CTA + Mobile toggle */}
        <div className="flex items-center gap-3">
          <Link
            to="/modules/heat-exchanger"
            className="hidden md:inline-flex items-center gap-2 px-5 py-2 text-[13px] font-medium bg-accent text-[#050505] rounded-full hover:bg-accent-dim transition-all duration-300 hover:shadow-[0_0_24px_rgba(0,229,160,0.25)]"
          >
            Launch App
          </Link>
          <button
            onClick={() => setMobileOpen(!mobileOpen)}
            className="md:hidden p-2 text-text-secondary hover:text-text-primary transition-colors"
          >
            {mobileOpen ? <X size={20} /> : <Menu size={20} />}
          </button>
        </div>
      </nav>

      {/* Mobile menu */}
      <AnimatePresence>
        {mobileOpen && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.3 }}
            className="md:hidden overflow-hidden bg-[#050505]/95 backdrop-blur-xl border-b border-white/[0.04]"
          >
            <div className="px-6 py-4 flex flex-col gap-1">
              <div className="text-[10px] font-mono text-text-tertiary uppercase tracking-wider px-4 py-2">
                Modules
              </div>
              {MODULE_LINKS.map((mod) => (
                <Link
                  key={mod.href}
                  to={mod.href}
                  onClick={() => setMobileOpen(false)}
                  className="flex items-center gap-3 px-4 py-3 text-sm text-text-secondary hover:text-text-primary transition-colors rounded-lg hover:bg-white/[0.03]"
                >
                  <span className="text-[10px] font-mono text-text-tertiary w-5">
                    {mod.number}
                  </span>
                  {mod.label}
                </Link>
              ))}
              {isLanding && (
                <>
                  <div className="w-full h-px bg-border my-2" />
                  {NAV_LINKS.map((link) => (
                    <a
                      key={link.href}
                      href={link.href}
                      onClick={() => setMobileOpen(false)}
                      className="px-4 py-3 text-sm text-text-secondary hover:text-text-primary transition-colors rounded-lg hover:bg-white/[0.03]"
                    >
                      {link.label}
                    </a>
                  ))}
                </>
              )}
              <Link
                to="/modules/heat-exchanger"
                onClick={() => setMobileOpen(false)}
                className="mt-2 flex items-center justify-center gap-2 px-5 py-3 text-sm font-medium bg-accent text-[#050505] rounded-full"
              >
                Launch App
              </Link>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.header>
  );
}
