import type { Metadata } from "next";


export const metadata: Metadata = {
  title: "Iniciar sesion",
  description: "Acceso a Genevidence Similarity Check.",
  alternates: { canonical: "/login" }
};


export default function LoginLayout({ children }: { children: React.ReactNode }) {
  return children;
}
