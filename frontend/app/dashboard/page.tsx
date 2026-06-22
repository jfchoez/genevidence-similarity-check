"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { FileText, Plus } from "lucide-react";
import { AppShell } from "@/components/AppShell";
import { StatusBadge } from "@/components/StatusBadge";
import { Credits, DocumentItem, apiFetch, getToken } from "@/lib/api";

export default function DashboardPage() {
  const router = useRouter();
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [credits, setCredits] = useState<Credits | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!getToken()) {
      router.push("/login");
      return;
    }
    Promise.all([apiFetch<DocumentItem[]>("/documents"), apiFetch<Credits>("/billing/credits")])
      .then(([docs, creditData]) => {
        setDocuments(docs);
        setCredits(creditData);
      })
      .catch((err) => setError(err.message));
  }, [router]);

  return (
    <AppShell>
      <div className="mb-5 flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold">Documentos</h1>
          {credits ? <p className="mt-1 text-sm text-slate-600">Plan {credits.plan} / {credits.available_credits} creditos</p> : null}
        </div>
        <Link className="focus-ring inline-flex items-center gap-2 rounded-md bg-teal px-4 py-2 text-sm font-medium text-white" href="/documents/upload">
          <Plus size={18} /> Nuevo documento
        </Link>
      </div>
      {error ? <p className="rounded-md bg-rose-50 px-3 py-2 text-sm text-rose-800">{error}</p> : null}
      <div className="overflow-hidden rounded-md border border-line bg-white shadow-sm">
        <table className="w-full border-collapse text-left text-sm">
          <thead className="bg-slate-100 text-xs uppercase text-slate-600">
            <tr>
              <th className="px-4 py-3">Documento</th>
              <th className="px-4 py-3">Estado</th>
              <th className="px-4 py-3">Palabras</th>
              <th className="px-4 py-3">Fecha</th>
            </tr>
          </thead>
          <tbody>
            {documents.map((document) => (
              <tr key={document.id} className="border-t border-line">
                <td className="px-4 py-3">
                  <Link className="inline-flex items-center gap-2 font-medium text-teal" href={`/documents/${document.id}`}>
                    <FileText size={16} /> {document.title}
                  </Link>
                  <div className="text-xs text-slate-500">{document.original_filename}</div>
                </td>
                <td className="px-4 py-3"><StatusBadge value={document.status} /></td>
                <td className="px-4 py-3">{document.word_count}</td>
                <td className="px-4 py-3">{new Date(document.created_at).toLocaleString()}</td>
              </tr>
            ))}
            {documents.length === 0 ? (
              <tr>
                <td className="px-4 py-8 text-center text-slate-500" colSpan={4}>
                  Sin documentos cargados
                </td>
              </tr>
            ) : null}
          </tbody>
        </table>
      </div>
    </AppShell>
  );
}
