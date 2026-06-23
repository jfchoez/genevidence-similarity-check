"use client";

export const API_BASE = (process.env.NEXT_PUBLIC_API_BASE_URL || "").replace(/\/+$/, "");

export function apiUrl(path: string): string {
  if (!API_BASE) {
    throw new Error("NEXT_PUBLIC_API_BASE_URL no esta configurada");
  }
  return `${API_BASE}${path.startsWith("/") ? path : `/${path}`}`;
}

export function apiConnectionErrorMessage(error: unknown): string {
  if (error instanceof Error && error.message.includes("NEXT_PUBLIC_API_BASE_URL")) {
    return "La URL de la API no esta configurada. Revisa NEXT_PUBLIC_API_BASE_URL en Vercel.";
  }
  return "No se pudo conectar con la API. Verifica que el backend este desplegado y que NEXT_PUBLIC_API_BASE_URL apunte a una URL HTTPS activa.";
}

export type User = {
  id: number;
  email: string;
  full_name?: string | null;
  role: string;
  created_at: string;
};

export type DocumentItem = {
  id: number;
  title: string;
  original_filename: string;
  file_type: string;
  status: string;
  word_count: number;
  created_at: string;
  error_message?: string | null;
};

export type DocumentDetail = DocumentItem & {
  sections: { id: number; section_name: string; start_position: number; end_position: number }[];
  reports: { id: number; status: string; global_similarity_score: number; created_at: string }[];
};

export type Credits = {
  user_id: number;
  available_credits: number;
  plan: string;
};

export type ReportMatch = {
  id: number;
  source_kind: string;
  source_document_id?: number | null;
  source_document_label: string;
  target_chunk_id: number;
  source_chunk_id?: number | null;
  external_source_id?: string | null;
  external_source_provider?: string | null;
  external_source_title?: string | null;
  external_source_url?: string | null;
  external_source_doi?: string | null;
  external_source_year?: number | null;
  similarity_score: number;
  jaccard_score: number;
  fuzzy_score: number;
  semantic_similarity?: number | null;
  shared_fingerprint_count: number;
  match_type: string;
  target_section: string;
  source_section: string;
  is_common_method_phrase: boolean;
  common_phrase_labels: string[];
  target_text: string;
  source_text: string;
};

export type Report = {
  id: number;
  document_id: number;
  document_title: string;
  status: string;
  global_similarity_score: number;
  literal_similarity_score: number;
  near_literal_similarity_score: number;
  similarity_excluding_references_score: number;
  section_similarity: Record<string, number>;
  source_summary: {
    source_kind: string;
    source_document_id?: number | null;
    source_document_label: string;
    external_source_id?: string | null;
    external_source_provider?: string | null;
    external_source_url?: string | null;
    match_count: number;
    max_score: number;
    matched_sections: string[];
  }[];
  warnings: string[];
  exclude_references: boolean;
  created_at: string;
  completed_at?: string | null;
  matches: ReportMatch[];
};

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("genevidence_token");
}

export function setAuth(token: string, user: User) {
  localStorage.setItem("genevidence_token", token);
  localStorage.setItem("genevidence_user", JSON.stringify(user));
  const secure = window.location.protocol === "https:" ? "; Secure" : "";
  document.cookie = `genevidence_token=${encodeURIComponent(token)}; Path=/; Max-Age=86400; SameSite=Lax${secure}`;
}

export function getStoredUser(): User | null {
  if (typeof window === "undefined") return null;
  const raw = localStorage.getItem("genevidence_user");
  return raw ? (JSON.parse(raw) as User) : null;
}

export function logout() {
  localStorage.removeItem("genevidence_token");
  localStorage.removeItem("genevidence_user");
  document.cookie = "genevidence_token=; Path=/; Max-Age=0; SameSite=Lax";
  window.location.href = "/login";
}

export async function apiFetch<T>(path: string, init: RequestInit = {}): Promise<T> {
  const token = getToken();
  const headers = new Headers(init.headers);
  if (token) headers.set("Authorization", `Bearer ${token}`);
  if (!(init.body instanceof FormData) && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  const response = await fetch(apiUrl(path), { ...init, cache: init.cache || "no-store", headers });
  if (response.status === 401 && typeof window !== "undefined") {
    logout();
    throw new Error("La sesion expiro");
  }
  if (!response.ok) {
    let message = response.statusText;
    try {
      const payload = await response.json();
      message = payload.detail || message;
    } catch {
      // keep response status text
    }
    throw new Error(message);
  }
  return response.json() as Promise<T>;
}

export async function downloadPdf(reportId: number) {
  const token = getToken();
  const response = await fetch(apiUrl(`/reports/${reportId}/pdf`), {
    headers: token ? { Authorization: `Bearer ${token}` } : {}
  });
  if (!response.ok) throw new Error("No se pudo descargar el PDF");
  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `genevidence_report_${reportId}.pdf`;
  link.click();
  URL.revokeObjectURL(url);
}
