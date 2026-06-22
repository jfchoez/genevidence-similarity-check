"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { LogOut, Shield, UploadCloud, WalletCards } from "lucide-react";
import { Credits, apiFetch, getStoredUser, logout } from "@/lib/api";
import { BrandLogo } from "@/components/BrandLogo";

export function AppShell({ children }: { children: React.ReactNode }) {
  const [credits, setCredits] = useState<Credits | null>(null);
  const user = getStoredUser();

  useEffect(() => {
    apiFetch<Credits>("/billing/credits").then(setCredits).catch(() => undefined);
  }, []);

  return (
    <div className="min-h-screen bg-paper">
      <header className="border-b border-line bg-white">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-3">
          <Link href="/dashboard" className="block w-full max-w-[280px]" aria-label="GenEvidence Similarity Check">
            <BrandLogo />
          </Link>
          <nav className="flex items-center gap-2 text-sm">
            <Link className="rounded-md px-3 py-2 hover:bg-slate-100" href="/dashboard">
              Documentos
            </Link>
            <Link className="rounded-md px-3 py-2 hover:bg-slate-100" href="/documents/upload">
              <span className="inline-flex items-center gap-1">
                <UploadCloud size={16} /> Subir
              </span>
            </Link>
            {user?.role === "admin" ? (
              <Link className="rounded-md px-3 py-2 hover:bg-slate-100" href="/admin">
                <span className="inline-flex items-center gap-1">
                  <Shield size={16} /> Admin
                </span>
              </Link>
            ) : null}
            {credits ? (
              <span className="inline-flex items-center gap-1 rounded-md border border-line px-3 py-2">
                <WalletCards size={16} /> {credits.available_credits}
              </span>
            ) : null}
            <button className="rounded-md px-3 py-2 hover:bg-slate-100" onClick={logout} title="Cerrar sesion">
              <LogOut size={16} />
            </button>
          </nav>
        </div>
      </header>
      <main className="mx-auto max-w-7xl px-4 py-6">{children}</main>
    </div>
  );
}
