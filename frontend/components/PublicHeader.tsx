import Link from "next/link";
import { LogIn } from "lucide-react";

import { BrandLogo } from "@/components/BrandLogo";


export function PublicHeader() {
  return (
    <header className="border-b border-line bg-white">
      <div className="mx-auto flex max-w-7xl items-center justify-between gap-4 px-4 py-3">
        <Link href="/" className="block w-full max-w-[260px]" aria-label="Genevidence Similarity Check">
          <BrandLogo />
        </Link>
        <nav className="flex items-center gap-1 text-sm" aria-label="Navegacion principal">
          <Link className="rounded-md px-3 py-2 hover:bg-slate-100" href="/features">
            Caracteristicas
          </Link>
          <Link className="rounded-md px-3 py-2 hover:bg-slate-100" href="/pricing">
            Planes
          </Link>
          <Link className="focus-ring inline-flex items-center gap-2 rounded-md bg-ink px-3 py-2 font-medium text-white" href="/login">
            <LogIn size={16} /> Entrar
          </Link>
        </nav>
      </div>
    </header>
  );
}
