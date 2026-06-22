export function StatusBadge({ value }: { value: string }) {
  const styles: Record<string, string> = {
    indexed: "bg-emerald-50 text-emerald-800 border-emerald-200",
    completed: "bg-emerald-50 text-emerald-800 border-emerald-200",
    processing: "bg-amber-50 text-amber-800 border-amber-200",
    pending: "bg-amber-50 text-amber-800 border-amber-200",
    failed: "bg-rose-50 text-rose-800 border-rose-200",
    uploaded: "bg-slate-50 text-slate-700 border-slate-200"
  };

  return (
    <span className={`rounded-md border px-2 py-1 text-xs font-medium ${styles[value] || styles.uploaded}`}>
      {value}
    </span>
  );
}
