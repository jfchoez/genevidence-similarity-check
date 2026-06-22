import type { Metadata } from "next";
import Link from "next/link";
import { Building2, Check, User, Users } from "lucide-react";

import { PublicFooter } from "@/components/PublicFooter";
import { PublicHeader } from "@/components/PublicHeader";


export const metadata: Metadata = {
  title: "Planes",
  description: "Planes Free, Professional e Institutional de Genevidence Similarity Check.",
  alternates: { canonical: "/pricing" }
};


const plans = [
  { icon: User, name: "Free", audience: "Evaluacion inicial", items: ["Creditos iniciales", "Reportes internos", "Descarga PDF"], action: "Crear cuenta", href: "/register" },
  { icon: Users, name: "Professional", audience: "Revisores e investigadores", items: ["Mayor volumen de reportes", "Filtros academicos", "Historial documental"], action: "Acceder", href: "/login" },
  { icon: Building2, name: "Institutional", audience: "Universidades y equipos", items: ["Administracion central", "Estadisticas generales", "Privacidad entre usuarios"], action: "Solicitar acceso", href: "/register" }
];


export default function PricingPage() {
  return (
    <div className="min-h-screen bg-paper">
      <PublicHeader />
      <main>
        <section className="border-b border-line bg-white">
          <div className="mx-auto max-w-7xl px-4 py-14">
            <h1 className="text-3xl font-semibold sm:text-4xl">Planes</h1>
            <p className="mt-4 max-w-2xl text-lg leading-8 text-slate-600">
              Opciones por creditos para revision individual, profesional e institucional.
            </p>
          </div>
        </section>
        <section className="mx-auto grid max-w-7xl gap-4 px-4 py-12 lg:grid-cols-3">
          {plans.map((plan) => (
            <article key={plan.name} className="rounded-md border border-line bg-white p-6 shadow-sm">
              <plan.icon className="text-teal" size={24} />
              <h2 className="mt-4 text-xl font-semibold">{plan.name}</h2>
              <p className="mt-1 text-sm text-slate-600">{plan.audience}</p>
              <ul className="mt-6 space-y-3 text-sm">
                {plan.items.map((item) => (
                  <li key={item} className="flex items-center gap-2"><Check size={16} className="text-teal" /> {item}</li>
                ))}
              </ul>
              <Link className="focus-ring mt-7 block rounded-md border border-teal px-4 py-2 text-center font-medium text-teal" href={plan.href}>
                {plan.action}
              </Link>
            </article>
          ))}
        </section>
      </main>
      <PublicFooter />
    </div>
  );
}
