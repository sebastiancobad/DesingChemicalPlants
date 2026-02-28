import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Menu, X } from "lucide-react";

const NAV_LINKS = [
  { label: "Platform", href: "#platform" },
  { label: "Modules", href: "#modules" },
  { label: "Standards", href: "#standards" },
  { label: "Architecture", href: "#architecture" },
];

export default function Navbar() {
  const [scrolled, setScrolled] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);

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
        <a href="#" className="flex items-center gap-3 group">
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
        </a>

        {/* Desktop nav */}
        <div className="hidden md:flex items-center gap-1">
          {NAV_LINKS.map((link) => (
            <a
              key={link.href}
              href={link.href}
              className="px-4 py-2 text-[13px] text-text-secondary hover:text-text-primary transition-colors duration-300 rounded-lg hover:bg-white/[0.03]"
            >
              {link.label}
            </a>
          ))}
        </div>

        {/* CTA + Mobile toggle */}
        <div className="flex items-center gap-3">
          <a
            href="#demo"
            className="hidden md:inline-flex items-center gap-2 px-5 py-2 text-[13px] font-medium bg-accent text-[#050505] rounded-full hover:bg-accent-dim transition-all duration-300 hover:shadow-[0_0_24px_rgba(0,229,160,0.25)]"
          >
            Launch App
          </a>
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
              <a
                href="#demo"
                onClick={() => setMobileOpen(false)}
                className="mt-2 flex items-center justify-center gap-2 px-5 py-3 text-sm font-medium bg-accent text-[#050505] rounded-full"
              >
                Launch App
              </a>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.header>
  );
}
