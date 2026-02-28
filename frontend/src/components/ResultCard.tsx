interface ResultItem {
  label: string;
  value: string;
}

interface ResultCardProps {
  title: string;
  items: ResultItem[];
}

export default function ResultCard({ title, items }: ResultCardProps) {
  return (
    <div className="rounded-xl border border-border bg-surface overflow-hidden">
      <div className="px-4 py-3 border-b border-border bg-surface-elevated">
        <h3 className="text-[13px] font-semibold text-text-primary">{title}</h3>
      </div>
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-px bg-border">
        {items.map((item) => (
          <div key={item.label} className="bg-[#050505] px-4 py-3">
            <div className="text-[10px] text-text-tertiary uppercase tracking-wider">
              {item.label}
            </div>
            <div className="text-sm font-semibold font-mono text-text-primary mt-0.5">
              {item.value}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
