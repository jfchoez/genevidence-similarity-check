import type { Metadata } from "next";


export const metadata: Metadata = {
  title: "Crear cuenta",
  description: "Registro de usuario en Genevidence Similarity Check.",
  alternates: { canonical: "/register" }
};


export default function RegisterLayout({ children }: { children: React.ReactNode }) {
  return children;
}
