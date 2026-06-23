"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";
import { LogIn } from "lucide-react";
import { apiConnectionErrorMessage, apiUrl, setAuth } from "@/lib/api";
import { BrandLogo } from "@/components/BrandLogo";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  async function submit(event: FormEvent) {
    event.preventDefault();
    setError("");
    const body = new URLSearchParams();
    body.set("username", email);
    body.set("password", password);
    let response: Response;
    try {
      response = await fetch(apiUrl("/auth/login"), {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body
      });
    } catch (requestError) {
      setError(apiConnectionErrorMessage(requestError));
      return;
    }
    if (!response.ok) {
      setError("Credenciales no validas");
      return;
    }
    const payload = await response.json();
    setAuth(payload.access_token, payload.user);
    const nextPath = new URLSearchParams(window.location.search).get("next");
    router.push(nextPath?.startsWith("/") && !nextPath.startsWith("//") ? nextPath : "/dashboard");
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-paper px-4">
      <form onSubmit={submit} className="w-full max-w-sm rounded-md border border-line bg-white p-6 shadow-sm">
        <BrandLogo className="mx-auto max-w-[320px]" />
        <div className="mt-5 space-y-4">
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
              required
            />
          </label>
        </div>
        {error ? <p className="mt-3 rounded-md bg-rose-50 px-3 py-2 text-sm text-rose-800">{error}</p> : null}
        <button className="focus-ring mt-5 inline-flex w-full items-center justify-center gap-2 rounded-md bg-teal px-4 py-2 font-medium text-white">
          <LogIn size={18} /> Entrar
        </button>
        <p className="mt-4 text-sm text-slate-600">
          <Link className="font-medium text-teal" href="/register">
            Crear cuenta
          </Link>
        </p>
      </form>
    </main>
  );
}
