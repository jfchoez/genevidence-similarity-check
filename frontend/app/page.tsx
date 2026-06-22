import type { Metadata } from "next";
import Image from "next/image";
import Link from "next/link";
import { ArrowRight, FileSearch, Layers3, ShieldCheck } from "lucide-react";

import { PublicFooter } from "@/components/PublicFooter";
import { PublicHeader } from "@/components/PublicHeader";
import { APP_NAME, SITE_DESCRIPTION } from "@/lib/site";


export const metadata: Metadata = {
  title: APP_NAME,
  description: SITE_DESCRIPTION,
  alternates: { canonical: "/" }
};


export default function HomePage() {
  return (
    <div className="min-h-screen bg-paper">
      <PublicHeader />
      <main>
        <section className="relative isolate overflow-hidden border-b border-line bg-white">
          <Image
            src="/genevidence-similarity-check.png"
            alt=""
            width={2000}
            height={358}
            priority
            aria-hidden="true"
            className="pointer-events-none absolute inset-x-0 top-1/2 -z-10 w-full -translate-y-1/2 object-contain opacity-[0.035]"
          />
          <div className="mx-auto flex min-h-[68vh] max-w-5xl flex-col items-center justify-center px-4 py-16 text-center">
            <h1 className="max-w-4xl text-4xl font-semibold leading-tight text-ink sm:text-5xl">
              Genevidence Similarity Check
            </h1>
            <p className="mt-6 max-w-2xl text-lg leading-8 text-slate-600">
              Revision de similitud documental para textos academicos y cientificos, con coincidencias trazables y criterio humano.
            </p>
            <div className="mt-8 flex flex-wrap justify-center gap-3">
              <Link className="focus-ring inline-flex items-center gap-2 rounded-md bg-teal px-5 py-3 font-medium text-white" href="/register">
                Crear cuenta <ArrowRight size={18} />
              </Link>
              <Link className="focus-ring rounded-md border border-line bg-white px-5 py-3 font-medium text-ink" href="/features">
                Ver caracteristicas
              </Link>
            </div>
          </div>
        </section>

        <section className="border-b border-line bg-paper">
          <div className="mx-auto grid max-w-7xl gap-8 px-4 py-14 md:grid-cols-3">
            <Feature icon={<FileSearch size={22} />} title="Revision documentada" text="Fragmentos, fuentes y scores organizados para evaluacion academica." />
            <Feature icon={<Layers3 size={22} />} title="Analisis por seccion" text="Resultados clasificados por resumen, metodologia, resultados, discusion y referencias." />
            <Feature icon={<ShieldCheck size={22} />} title="Privacidad por usuario" text="Acceso autenticado y fuentes internas anonimizadas cuando corresponde." />
          </div>
        </section>
      </main>
      <PublicFooter />
    </div>
  );
}


function Feature({ icon, title, text }: { icon: React.ReactNode; title: string; text: string }) {
  return (
    <div className="border-l-2 border-teal pl-4">
      <div className="text-teal">{icon}</div>
      <h2 className="mt-3 text-lg font-semibold">{title}</h2>
      <p className="mt-2 leading-7 text-slate-600">{text}</p>
    </div>
  );
}
