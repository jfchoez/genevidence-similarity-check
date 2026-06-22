"use client";

import { FormEvent, useEffect, useState } from "react";
import { Shield, WalletCards } from "lucide-react";
import { AppShell } from "@/components/AppShell";
import { DocumentItem, Report, User, apiFetch } from "@/lib/api";

type Stats = {
  total_users: number;
  total_documents: number;
  total_reports: number;
  total_credit_consumed: number;
};

export default function AdminPage() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [users, setUsers] = useState<User[]>([]);
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [reports, setReports] = useState<Report[]>([]);
  const [targetUserId, setTargetUserId] = useState("");
  const [credits, setCredits] = useState("5");
  const [message, setMessage] = useState("");

  function load() {
    Promise.all([
      apiFetch<Stats>("/admin/stats"),
      apiFetch<User[]>("/admin/users"),
      apiFetch<DocumentItem[]>("/admin/documents"),
      apiFetch<Report[]>("/admin/reports")
    ]).then(([statsData, userData, documentData, reportData]) => {
      setStats(statsData);
      setUsers(userData);
      setDocuments(documentData);
      setReports(reportData);
    });
  }

  useEffect(load, []);

  async function grant(event: FormEvent) {
    event.preventDefault();
    setMessage("");
    await apiFetch(`/admin/users/${targetUserId}/credits`, {
      method: "POST",
      body: JSON.stringify({ amount: Number(credits), reason: "admin_credit_adjustment" })
    });
    setMessage("Creditos actualizados");
    load();
  }

  return (
    <AppShell>
      <div className="mb-5 flex items-center gap-2">
        <Shield size={22} className="text-teal" />
        <h1 className="text-2xl font-semibold">Panel admin</h1>
      </div>

      <div className="grid gap-4 md:grid-cols-4">
        <Stat label="Usuarios" value={stats?.total_users ?? 0} />
        <Stat label="Documentos" value={stats?.total_documents ?? 0} />
        <Stat label="Reportes" value={stats?.total_reports ?? 0} />
        <Stat label="Creditos consumidos" value={stats?.total_credit_consumed ?? 0} />
      </div>

      <section className="mt-5 rounded-md border border-line bg-white p-5 shadow-sm">
        <h2 className="mb-4 flex items-center gap-2 text-base font-semibold">
          <WalletCards size={18} /> Asignar creditos
        </h2>
        <form onSubmit={grant} className="grid gap-3 md:grid-cols-[1fr_140px_140px]">
          <select
            className="focus-ring rounded-md border border-line px-3 py-2 text-sm"
            value={targetUserId}
            onChange={(event) => setTargetUserId(event.target.value)}
            required
          >
            <option value="">Usuario</option>
            {users.map((user) => (
              <option key={user.id} value={user.id}>
                {user.email}
              </option>
            ))}
          </select>
          <input
            className="focus-ring rounded-md border border-line px-3 py-2 text-sm"
            type="number"
            value={credits}
            onChange={(event) => setCredits(event.target.value)}
          />
          <button className="focus-ring rounded-md bg-teal px-4 py-2 text-sm font-medium text-white">Asignar</button>
        </form>
        {message ? <p className="mt-3 text-sm text-teal">{message}</p> : null}
      </section>

      <div className="mt-5 grid gap-4 lg:grid-cols-2">
        <Table title="Usuarios" headers={["Email", "Rol"]} rows={users.map((user) => [user.email, user.role])} />
        <Table
          title="Documentos"
          headers={["Titulo", "Estado"]}
          rows={documents.map((document) => [document.title, document.status])}
        />
        <Table
          title="Reportes"
          headers={["Documento", "Similitud"]}
          rows={reports.map((report) => [report.document_title, `${report.global_similarity_score.toFixed(2)}%`])}
        />
      </div>
    </AppShell>
  );
}

function Stat({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-md border border-line bg-white p-4 shadow-sm">
      <div className="text-sm text-slate-600">{label}</div>
      <div className="mt-2 text-2xl font-semibold">{value}</div>
    </div>
  );
}

function Table({ title, headers, rows }: { title: string; headers: string[]; rows: string[][] }) {
  return (
    <section className="overflow-hidden rounded-md border border-line bg-white shadow-sm">
      <div className="border-b border-line px-4 py-3 font-semibold">{title}</div>
      <table className="w-full text-left text-sm">
        <thead className="bg-slate-100 text-xs uppercase text-slate-600">
          <tr>
            {headers.map((header) => (
              <th key={header} className="px-4 py-3">
                {header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, rowIndex) => (
            <tr key={rowIndex} className="border-t border-line">
              {row.map((cell, cellIndex) => (
                <td key={cellIndex} className="px-4 py-3">
                  {cell}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}
