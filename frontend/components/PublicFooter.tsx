import Link from "next/link";


export function PublicFooter() {
  return (
    <footer className="border-t border-line bg-white">
      <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-3 px-4 py-6 text-sm text-slate-600">
        <span>Genevidence Similarity Check</span>
        <div className="flex gap-4">
          <Link href="/features">Caracteristicas</Link>
          <Link href="/pricing">Planes</Link>
          <Link href="/login">Acceso</Link>
        </div>
      </div>
    </footer>
  );
}
