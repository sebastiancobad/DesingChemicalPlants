interface CalcFieldProps {
  label: string;
  unit: string;
  value: string;
  onChange: (v: string) => void;
  type?: string;
  step?: string;
}

export default function CalcField({
  label,
  unit,
  value,
  onChange,
  type = "number",
  step,
}: CalcFieldProps) {
  return (
    <div>
      <label className="block text-[11px] text-text-tertiary uppercase tracking-wider mb-1.5">
        {label}
      </label>
      <div className="relative">
        <input
          type={type}
          step={step}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          className="w-full bg-[#050505] border border-border rounded-lg px-3 py-2.5 text-sm font-mono text-text-primary focus:outline-none focus:border-accent/40 transition-colors pr-12"
        />
        <span className="absolute right-3 top-1/2 -translate-y-1/2 text-[10px] text-text-tertiary">
          {unit}
        </span>
      </div>
    </div>
  );
}
