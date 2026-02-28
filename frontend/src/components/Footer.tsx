export default function Footer() {
  return (
    <footer className="relative border-t border-border bg-surface">
      <div className="max-w-7xl mx-auto px-6 lg:px-10 py-16">
        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-10 lg:gap-8 mb-16">
          {/* Brand */}
          <div className="sm:col-span-2 lg:col-span-1">
            <div className="flex items-center gap-2 mb-4">
              <svg viewBox="0 0 32 32" className="w-5 h-5" fill="none">
                <path
                  d="M16 2L28 9v14l-12 7L4 23V9l12-7z"
                  stroke="currentColor"
                  strokeWidth="1.5"
                  className="text-accent"
                />
                <circle cx="16" cy="16" r="2" className="fill-accent" />
              </svg>
              <span className="text-sm font-semibold text-text-primary">
                Chem<span className="text-accent">Scale</span>
              </span>
            </div>
            <p className="text-[13px] text-text-tertiary leading-relaxed max-w-xs">
              Engineering-grade chemical plant design with full traceability
              to published standards.
            </p>
          </div>

          {/* Modules */}
          <div>
            <h4 className="text-[11px] font-semibold uppercase tracking-[0.15em] text-text-tertiary mb-4">
              Modules
            </h4>
            <ul className="space-y-2.5">
              {[
                "Heat Exchangers",
                "Economic Evaluation",
                "Thermo Properties",
                "Process Simulation",
              ].map((item) => (
                <li key={item}>
                  <a
                    href="#modules"
                    className="text-[13px] text-text-secondary hover:text-text-primary transition-colors duration-200"
                  >
                    {item}
                  </a>
                </li>
              ))}
            </ul>
          </div>

          {/* Standards */}
          <div>
            <h4 className="text-[11px] font-semibold uppercase tracking-[0.15em] text-text-tertiary mb-4">
              Standards
            </h4>
            <ul className="space-y-2.5">
              {["TEMA 10th Ed.", "ASME VIII-1", "API 660", "Turton 5th Ed."].map(
                (item) => (
                  <li key={item}>
                    <a
                      href="#standards"
                      className="text-[13px] text-text-secondary hover:text-text-primary transition-colors duration-200"
                    >
                      {item}
                    </a>
                  </li>
                )
              )}
            </ul>
          </div>

          {/* Resources */}
          <div>
            <h4 className="text-[11px] font-semibold uppercase tracking-[0.15em] text-text-tertiary mb-4">
              Resources
            </h4>
            <ul className="space-y-2.5">
              {["API Documentation", "Architecture", "Contributing", "License"].map(
                (item) => (
                  <li key={item}>
                    <a
                      href="#"
                      className="text-[13px] text-text-secondary hover:text-text-primary transition-colors duration-200"
                    >
                      {item}
                    </a>
                  </li>
                )
              )}
            </ul>
          </div>
        </div>

        {/* Bottom bar */}
        <div className="flex flex-col sm:flex-row items-center justify-between gap-4 pt-8 border-t border-border">
          <p className="text-[12px] text-text-tertiary">
            &copy; {new Date().getFullYear()} ChemScale. All rights reserved.
          </p>
          <div className="flex items-center gap-6">
            {["Privacy", "Terms", "Status"].map((item) => (
              <a
                key={item}
                href="#"
                className="text-[12px] text-text-tertiary hover:text-text-secondary transition-colors duration-200"
              >
                {item}
              </a>
            ))}
          </div>
        </div>
      </div>
    </footer>
  );
}
