import type { Metadata } from "next";
import Link from "next/link";
import {
  ArrowRight,
  BookOpenCheck,
  FileDown,
  Fingerprint,
  PanelsTopLeft,
  ScanSearch,
  Users,
  type LucideIcon
} from "lucide-react";

import { PublicFooter } from "@/components/PublicFooter";
import { PublicHeader } from "@/components/PublicHeader";


export const metadata: Metadata = {
  title: "Caracteristicas",
  description: "Funciones de revision textual, reportes academicos y control de acceso de Genevidence Similarity Check.",
  alternates: { canonical: "/features" }
};


type Feature = {
  icon: LucideIcon;
  title: string;
  text: string;
};


const features: Feature[] = [
  { icon: Fingerprint, title: "Coincidencia textual", text: "Fingerprinting winnowing, Jaccard y RapidFuzz para recuperar coincidencias literales y parciales." },
  { icon: PanelsTopLeft, title: "Secciones academicas", text: "Clasificacion por resumen, introduccion, metodologia, resultados, discusion y referencias." },
  { icon: ScanSearch, title: "Parafrasis experimental", text: "Capa opcional de embeddings multilingues para senales de revision semantica." },
  { icon: BookOpenCheck, title: "Criterio academico", text: "Advertencias interpretativas y frases metodologicas comunes sin declaraciones automaticas de plagio." },
  { icon: FileDown, title: "Reporte PDF", text: "Resumen ejecutivo, fuentes, similitud por seccion y detalle de fragmentos revisables." },
  { icon: Users, title: "Acceso multiusuario", text: "Roles, creditos, privacidad documental y panel administrativo institucional." }
];


export default function FeaturesPage() {
  return (
    <div className="min-h-screen bg-paper">
      <PublicHeader />
      <main>
        <section className="border-b border-line bg-white">
          <div className="mx-auto max-w-7xl px-4 py-14">
            <h1 className="text-3xl font-semibold sm:text-4xl">Caracteristicas</h1>
            <p className="mt-4 max-w-2xl text-lg leading-8 text-slate-600">
              Herramientas para localizar, clasificar y revisar similitudes en documentos cientificos.
            </p>
          </div>
        </section>
        <section className="mx-auto grid max-w-7xl gap-px bg-line md:grid-cols-2 lg:grid-cols-3">
          {features.map(({ icon: Icon, title, text }) => (
            <article key={title} className="bg-paper p-6">
              <Icon className="text-teal" size={22} />
              <h2 className="mt-4 text-lg font-semibold">{title}</h2>
              <p className="mt-2 leading-7 text-slate-600">{text}</p>
            </article>
          ))}
        </section>
        <section className="border-y border-line bg-white">
          <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-4 px-4 py-10">
            <div>
              <h2 className="text-xl font-semibold">Comienza con una revision interna</h2>
              <p className="mt-1 text-slate-600">Crea una cuenta y carga tus primeros documentos.</p>
            </div>
            <Link className="focus-ring inline-flex items-center gap-2 rounded-md bg-teal px-4 py-2 font-medium text-white" href="/register">
              Crear cuenta <ArrowRight size={18} />
            </Link>
          </div>
        </section>
      </main>
      <PublicFooter />
    </div>
  );
}
