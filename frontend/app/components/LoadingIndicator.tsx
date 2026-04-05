"use client";

interface Props {
  label: string;
}

export function LoadingIndicator({ label }: Props) {
  return (
    <div className="mb-4 flex items-center gap-3 rounded-[22px] border border-[rgba(44,93,176,0.12)] bg-[linear-gradient(180deg,#f7faff,#edf4ff)] px-4 py-3 text-[#27466f] shadow-[0_14px_28px_rgba(54,113,201,0.08)]">
      <span className="inline-flex min-w-[52px] items-center justify-center gap-1.5 rounded-full px-3 py-2">
        {[0, 1, 2].map((i) => (
          <span
            key={i}
            className="h-2 w-2 rounded-full bg-[#2b63bd]"
            style={{ animation: `typingBounce 1.15s ease-in-out ${i * 0.16}s infinite` }}
          />
        ))}
      </span>
      <div>
        <div className="text-[11px] font-semibold uppercase tracking-[0.2em] text-[#4a6484]">
          Workbench Update
        </div>
        <div className="mt-1 text-sm font-medium">{label}</div>
      </div>
    </div>
  );
}
