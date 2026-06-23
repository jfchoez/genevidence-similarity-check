"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";
import { UserPlus } from "lucide-react";
import { apiConnectionErrorMessage, apiUrl, setAuth } from "@/lib/api";
import { BrandLogo } from "@/components/BrandLogo";

export default function RegisterPage() {
  const router = useRouter();
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  async function submit(event: FormEvent) {
    event.preventDefault();
    setError("");
    let response: Response;
    try {
      response = await fetch(apiUrl("/auth/register"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ full_name: fullName, email, password })
      });
    } catch (requestError) {
      setError(apiConnectionErrorMessage(requestError));
      return;
    }
    if (!response.ok) {
      const payload = await response.json().catch(() => null);
      setError(payload?.detail || "No se pudo crear la cuenta");
      return;
    }
    const payload = await response.json();
    setAuth(payload.access_token, payload.user);
    router.push("/dashboard");
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-paper px-4">
      <form onSubmit={submit} className="w-full max-w-sm rounded-md border border-line bg-white p-6 shadow-sm">
        <BrandLogo className="mx-auto max-w-[320px]" />
        <h1 className="mt-5 text-xl font-semibold">Crear cuenta</h1>
        <div className="mt-5 space-y-4">
          <label className="block text-sm font-medium">
            Nombre
            <input
              className="focus-ring mt-1 w-full rounded-md border border-line px-3 py-2"
              value={fullName}
              onChange={(event) => setFullName(event.target.value)}
            />
          </label>
          <label className="block text-sm font-medium">
            Email
            <input
              className="focus-ring mt-1 w-full rounded-md border border-line px-3 py-2"
              type="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              required
            />
          </label>
          <label className="block text-sm font-medium">
            Password
            <input
              className="focus-ring mt-1 w-full rounded-md border border-line px-3 py-2"
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              minLength={8}
              required
            />
          </label>
        </div>
        {error ? <p className="mt-3 rounded-md bg-rose-50 px-3 py-2 text-sm text-rose-800">{error}</p> : null}
        <button className="focus-ring mt-5 inline-flex w-full items-center justify-center gap-2 rounded-md bg-teal px-4 py-2 font-medium text-white">
          <UserPlus size={18} /> Registrar
        </button>
        <p className="mt-4 text-sm text-slate-600">
          <Link className="font-medium text-teal" href="/login">
            Iniciar sesion
          </Link>
        </p>
      </form>
    </main>
  );
}
