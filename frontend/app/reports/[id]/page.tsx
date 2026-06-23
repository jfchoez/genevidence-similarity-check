"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import { Download, Filter, RefreshCw } from "lucide-react";
import { AppShell } from "@/components/AppShell";
import { Report, apiFetch, downloadPdf } from "@/lib/api";

function scoreTone(score: number) {
  if (score <= 15) return "border-emerald-200 bg-emerald-50 text-emerald-800";
  if (score <= 30) return "border-amber-200 bg-amber-50 text-amber-800";
  if (score <= 50) return "border-orange-200 bg-orange-50 text-orange-800";
  return "border-rose-200 bg-rose-50 text-rose-800";
}

function scoreLabel(score: number) {
  if (score <= 15) return "bajo";
  if (score <= 30) return "moderado";
  if (score <= 50) return "alto";
  return "muy alto";
}

export default function ReportPage() {
  const params = useParams<{ id: string }>();
  const [report, setReport] = useState<Report | null>(null);
  const [source, setSource] = useState("");
  const [section, setSection] = useState("");
  const [matchType, setMatchType] = useState("");
  const [minScore, setMinScore] = useState("0");
  const [error, setError] = useState("");
  const [busyPdf, setBusyPdf] = useState(false);

  const query = useMemo(() => {
    const paramsValue = new URLSearchParams();
    if (source) paramsValue.set("source", source);
    if (section) paramsValue.set("section", section);
    if (matchType) paramsValue.set("match_type", matchType);
    if (minScore) paramsValue.set("min_score", minScore);
    return paramsValue.toString();
  }, [source, section, matchType, minScore]);

  function load() {
    apiFetch<Report>(`/reports/${params.id}${query ? `?${query}` : ""}`)
      .then(setReport)
      .catch((err) => setError(err.message));
  }

  useEffect(load, [params.id, query]);

  async function onDownload() {
    setBusyPdf(true);
    try {
      await downloadPdf(Number(params.id));
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudo descargar el PDF");
    } finally {
      setBusyPdf(false);
    }
  }

  if (!report) {
    return (
      <AppShell>
        {error ? <p className="rounded-md bg-rose-50 px-3 py-2 text-sm text-rose-800">{error}</p> : null}
      </AppShell>
    );
  }

  const sections = Object.keys(report.section_similarity);

  return (
    <AppShell>
      <div className="mb-5 flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold">Reporte #{report.id}</h1>
          <p className="mt-1 text-sm text-slate-600">
            <Link className="text-teal" href={`/documents/${report.document_id}`}>
              {report.document_title}
            </Link>
          </p>
        </div>
        <button
          className="focus-ring inline-flex items-center gap-2 rounded-md bg-teal px-4 py-2 text-sm font-medium text-white disabled:bg-slate-400"
          onClick={onDownload}
          disabled={busyPdf}
        >
          <Download size={18} /> PDF
        </button>
      </div>

      {error ? <p className="mb-4 rounded-md bg-rose-50 px-3 py-2 text-sm text-rose-800">{error}</p> : null}

      <div className="grid gap-4 md:grid-cols-4">
        <Metric title="Global" value={report.global_similarity_score} />
        <Metric title="Sin referencias" value={report.similarity_excluding_references_score} />
        <Metric title="Literal" value={report.literal_similarity_score} />
        <Metric title="Casi literal/parcial" value={report.near_literal_similarity_score} />
      </div>

      <section className="mt-5 rounded-md border border-line bg-white p-5 shadow-sm">
        <div className="mb-4 flex items-center gap-2 font-semibold">
          <Filter size={18} /> Filtros
        </div>
        <div className="grid gap-3 md:grid-cols-4">
          <input
            className="focus-ring rounded-md border border-line px-3 py-2 text-sm"
            placeholder="Fuente"
            value={source}
            onChange={(event) => setSource(event.target.value)}
          />
          <select
            className="focus-ring rounded-md border border-line px-3 py-2 text-sm"
            value={section}
            onChange={(event) => setSection(event.target.value)}
          >
            <option value="">Todas las secciones</option>
            {sections.map((item) => (
              <option key={item} value={item}>
                {item}
              </option>
            ))}
          </select>
          <select
            className="focus-ring rounded-md border border-line px-3 py-2 text-sm"
            value={matchType}
            onChange={(event) => setMatchType(event.target.value)}
          >
            <option value="">Todos los tipos</option>
            <option value="exact">literal</option>
            <option value="near_exact">casi literal</option>
            <option value="partial">parcial</option>
            <option value="possible_paraphrase">posible parafrasis</option>
            <option value="frase metodologica comun">frase metodologica comun</option>
          </select>
          <input
            className="focus-ring rounded-md border border-line px-3 py-2 text-sm"
            type="number"
            min="0"
            max="100"
            value={minScore}
            onChange={(event) => setMinScore(event.target.value)}
          />
        </div>
      </section>

      <div className="mt-5 grid gap-4 lg:grid-cols-[1fr_360px]">
        <section className="rounded-md border border-line bg-white p-5 shadow-sm">
          <h2 className="mb-3 text-base font-semibold">Coincidencias</h2>
          <div className="space-y-4">
            {report.matches.map((match) => (
              <article key={match.id} className="rounded-md border border-line p-4">
                <div className="flex flex-wrap items-center gap-2 text-xs">
                  <span className="rounded-md bg-slate-100 px-2 py-1 font-medium">{match.match_type}</span>
                  <span className="rounded-md bg-slate-100 px-2 py-1">{match.target_section}</span>
                  <span className="rounded-md bg-slate-100 px-2 py-1">{match.source_document_label}</span>
                  {match.source_kind === "external_academic" && match.external_source_provider ? (
                    <span className="rounded-md border border-teal/20 bg-teal/10 px-2 py-1 text-teal">
                      {match.external_source_provider}
                    </span>
                  ) : null}
                  <span className="font-semibold">{match.similarity_score.toFixed(2)}</span>
                  {match.is_common_method_phrase ? (
                    <span className="rounded-md border border-amber-200 bg-amber-50 px-2 py-1 text-amber-800">
                      frase metodologica comun
                    </span>
                  ) : null}
                </div>
                <div className="mt-3 grid gap-3 md:grid-cols-2">
                  <div>
                    <h3 className="mb-1 text-sm font-semibold">Fragmento analizado</h3>
                    <p className="text-sm leading-6 text-slate-700">{match.target_text}</p>
                  </div>
                  <div>
                    <div className="mb-1 flex flex-wrap items-center gap-2">
                      <h3 className="text-sm font-semibold">Fuente coincidente</h3>
                      {match.external_source_url ? (
                        <a
                          className="text-xs font-medium text-teal"
                          href={match.external_source_url}
                          target="_blank"
                          rel="noreferrer"
                        >
                          Abrir fuente
                        </a>
                      ) : null}
                    </div>
                    <p className="text-sm leading-6 text-slate-700">{match.source_text}</p>
                  </div>
                </div>
              </article>
            ))}
            {report.matches.length === 0 ? <p className="text-sm text-slate-500">Sin coincidencias con los filtros activos</p> : null}
          </div>
        </section>

        <aside className="space-y-4">
          <section className="rounded-md border border-line bg-white p-5 shadow-sm">
            <h2 className="mb-3 text-base font-semibold">Fuentes principales</h2>
            <div className="space-y-3">
              {report.source_summary.map((sourceItem) => (
                <div
                  key={`${sourceItem.source_kind}-${sourceItem.source_document_id ?? sourceItem.external_source_id}`}
                  className="border-b border-line pb-3 text-sm last:border-b-0"
                >
                  <div className="font-medium">{sourceItem.source_document_label}</div>
                  <div className="text-slate-600">
                    {sourceItem.match_count} coincidencias / {sourceItem.max_score.toFixed(2)}
                  </div>
                  {sourceItem.external_source_url ? (
                    <a className="mt-1 block text-xs text-teal" href={sourceItem.external_source_url} target="_blank" rel="noreferrer">
                      Abrir fuente
                    </a>
                  ) : null}
                </div>
              ))}
            </div>
          </section>
          <section className="rounded-md border border-line bg-white p-5 shadow-sm">
            <h2 className="mb-3 text-base font-semibold">Similitud por seccion</h2>
            <div className="space-y-2">
              {Object.entries(report.section_similarity).map(([name, value]) => (
                <div key={name} className="flex items-center justify-between gap-3 text-sm">
                  <span>{name}</span>
                  <span className="font-medium">{value.toFixed(2)}%</span>
                </div>
              ))}
            </div>
          </section>
          <section className="rounded-md border border-line bg-white p-5 shadow-sm">
            <h2 className="mb-3 text-base font-semibold">Advertencias</h2>
            <div className="space-y-2 text-sm text-slate-700">
              {report.warnings.map((warning) => (
                <p key={warning}>{warning}</p>
              ))}
            </div>
          </section>
          <button className="inline-flex items-center gap-2 text-sm text-teal" onClick={load}>
            <RefreshCw size={16} /> Actualizar
          </button>
        </aside>
      </div>
    </AppShell>
  );
}

function Metric({ title, value }: { title: string; value: number }) {
  return (
    <div className={`rounded-md border p-4 shadow-sm ${scoreTone(value)}`}>
      <div className="text-sm font-medium">{title}</div>
      <div className="mt-2 text-3xl font-semibold">{value.toFixed(2)}%</div>
      <div className="mt-1 text-sm">{scoreLabel(value)}</div>
    </div>
  );
}
