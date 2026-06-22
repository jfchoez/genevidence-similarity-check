"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { FileSearch, RefreshCw } from "lucide-react";
import { AppShell } from "@/components/AppShell";
import { StatusBadge } from "@/components/StatusBadge";
import { DocumentDetail, Report, apiFetch } from "@/lib/api";

export default function DocumentPage() {
  const router = useRouter();
  const params = useParams<{ id: string }>();
  const [document, setDocument] = useState<DocumentDetail | null>(null);
  const [excludeReferences, setExcludeReferences] = useState(true);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  function load() {
    apiFetch<DocumentDetail>(`/documents/${params.id}`).then(setDocument).catch((err) => setError(err.message));
  }

  useEffect(load, [params.id]);

  async function generateReport() {
    setBusy(true);
    setError("");
    try {
      const report = await apiFetch<Report>(`/reports/${params.id}/generate?exclude_references=${excludeReferences}`, {
        method: "POST"
      });
      router.push(`/reports/${report.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudo generar el reporte");
    } finally {
      setBusy(false);
    }
  }

  if (!document) {
    return (
      <AppShell>
        <button className="inline-flex items-center gap-2 text-sm text-teal" onClick={load}>
          <RefreshCw size={16} /> Actualizar
        </button>
      </AppShell>
    );
  }

  return (
    <AppShell>
      <div className="mb-5 flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold">{document.title}</h1>
          <div className="mt-2 flex flex-wrap items-center gap-3 text-sm text-slate-600">
            <StatusBadge value={document.status} />
            <span>{document.word_count} palabras</span>
            <span>{document.original_filename}</span>
          </div>
        </div>
        <button className="rounded-md border border-line px-3 py-2 text-sm hover:bg-white" onClick={load}>
          <RefreshCw size={16} />
        </button>
      </div>

      {document.error_message ? (
        <p className="mb-4 rounded-md bg-rose-50 px-3 py-2 text-sm text-rose-800">{document.error_message}</p>
      ) : null}
      {error ? <p className="mb-4 rounded-md bg-rose-50 px-3 py-2 text-sm text-rose-800">{error}</p> : null}

      <div className="grid gap-4 lg:grid-cols-[1fr_360px]">
        <section className="rounded-md border border-line bg-white p-5 shadow-sm">
          <h2 className="mb-3 text-base font-semibold">Secciones detectadas</h2>
          <div className="flex flex-wrap gap-2">
            {document.sections.map((section) => (
              <span key={section.id} className="rounded-md border border-line px-3 py-1 text-sm">
                {section.section_name}
              </span>
            ))}
          </div>
        </section>
        <aside className="rounded-md border border-line bg-white p-5 shadow-sm">
          <h2 className="text-base font-semibold">Reporte</h2>
          <label className="mt-4 flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={excludeReferences}
              onChange={(event) => setExcludeReferences(event.target.checked)}
            />
            Excluir referencias
          </label>
          <button
            className="focus-ring mt-4 inline-flex w-full items-center justify-center gap-2 rounded-md bg-teal px-4 py-2 text-sm font-medium text-white disabled:bg-slate-400"
            disabled={document.status !== "indexed" || busy}
            onClick={generateReport}
          >
            <FileSearch size={18} /> {busy ? "Generando" : "Generar reporte"}
          </button>
        </aside>
      </div>

      <section className="mt-5 rounded-md border border-line bg-white shadow-sm">
        <div className="border-b border-line px-5 py-3 font-semibold">Reportes previos</div>
        {document.reports.map((report) => (
          <Link
            key={report.id}
            href={`/reports/${report.id}`}
            className="flex items-center justify-between border-b border-line px-5 py-3 text-sm last:border-b-0 hover:bg-slate-50"
          >
            <span>Reporte #{report.id}</span>
            <span className="font-medium">{report.global_similarity_score.toFixed(2)}%</span>
          </Link>
        ))}
      </section>
    </AppShell>
  );
}
