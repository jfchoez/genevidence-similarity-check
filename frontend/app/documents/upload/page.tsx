"use client";

import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";
import { UploadCloud } from "lucide-react";
import { AppShell } from "@/components/AppShell";
import { apiFetch } from "@/lib/api";

export default function UploadPage() {
  const router = useRouter();
  const [file, setFile] = useState<File | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(event: FormEvent) {
    event.preventDefault();
    if (!file) return;
    setBusy(true);
    setError("");
    const formData = new FormData();
    formData.set("file", file);
    try {
      const document = await apiFetch<{ id: number }>("/documents/upload", { method: "POST", body: formData });
      router.push(`/documents/${document.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudo subir el documento");
    } finally {
      setBusy(false);
    }
  }

  return (
    <AppShell>
      <h1 className="mb-5 text-2xl font-semibold">Subir documento</h1>
      <form onSubmit={submit} className="max-w-2xl rounded-md border border-line bg-white p-6 shadow-sm">
        <label className="flex min-h-44 cursor-pointer flex-col items-center justify-center rounded-md border border-dashed border-slate-300 bg-slate-50 px-6 text-center hover:border-teal">
          <UploadCloud className="mb-3 text-teal" size={32} />
          <span className="font-medium">{file ? file.name : "Seleccionar PDF o DOCX"}</span>
          <input
            className="sr-only"
            type="file"
            accept=".pdf,.docx"
            onChange={(event) => setFile(event.target.files?.[0] || null)}
          />
        </label>
        {error ? <p className="mt-3 rounded-md bg-rose-50 px-3 py-2 text-sm text-rose-800">{error}</p> : null}
        <button
          className="focus-ring mt-5 inline-flex items-center gap-2 rounded-md bg-teal px-4 py-2 text-sm font-medium text-white disabled:bg-slate-400"
          disabled={!file || busy}
        >
          <UploadCloud size={18} /> {busy ? "Subiendo" : "Subir"}
        </button>
      </form>
    </AppShell>
  );
}
