import type { ReactNode } from "react";
import { Link } from "react-router-dom";
import { ArrowLeft } from "lucide-react";

interface ModuleLayoutProps {
  moduleNumber: string;
  title: string;
  subtitle: string;
  accentFrom: string;
  accentTo: string;
  children: ReactNode;
}

export default function ModuleLayout({
  moduleNumber,
  title,
  subtitle,
  accentFrom,
  accentTo,
  children,
}: ModuleLayoutProps) {
  return (
    <div className="min-h-screen bg-[#050505] text-white">
      {/* Header */}
      <header className="border-b border-border bg-surface/80 backdrop-blur-xl sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 lg:px-10 flex items-center h-16 gap-4">
          <Link
            to="/"
            className="flex items-center gap-2 text-text-secondary hover:text-text-primary transition-colors"
          >
            <ArrowLeft size={16} />
            <span className="text-[13px]">Back</span>
          </Link>
          <div className="w-px h-6 bg-border" />
          <div className="flex items-center gap-3">
            <span
              className="text-[10px] font-mono tracking-wider px-2 py-0.5 rounded-md border border-border"
              style={{
                background: `linear-gradient(135deg, ${accentFrom}15, ${accentTo}15)`,
              }}
            >
              MODULE {moduleNumber}
            </span>
            <h1 className="text-[15px] font-semibold text-text-primary">
              {title}
            </h1>
            <span className="hidden sm:inline text-[12px] text-text-tertiary">
              {subtitle}
            </span>
          </div>
        </div>
      </header>

      {/* Content */}
      <main className="max-w-7xl mx-auto px-6 lg:px-10 py-8 lg:py-12">
        {children}
      </main>
    </div>
  );
}
