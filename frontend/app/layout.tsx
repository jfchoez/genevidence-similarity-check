import type { Metadata } from "next";
import "./globals.css";

import { APP_NAME, SITE_DESCRIPTION, SITE_URL } from "@/lib/site";

export const metadata: Metadata = {
  metadataBase: new URL(SITE_URL),
  title: {
    default: APP_NAME,
    template: `%s | ${APP_NAME}`
  },
  description: SITE_DESCRIPTION,
  applicationName: APP_NAME,
  alternates: {
    canonical: "/"
  },
  openGraph: {
    type: "website",
    locale: "es_MX",
    url: SITE_URL,
    siteName: APP_NAME,
    title: APP_NAME,
    description: SITE_DESCRIPTION,
    images: [
      {
        url: "/genevidence-similarity-check.png",
        width: 2000,
        height: 358,
        alt: APP_NAME
      }
    ]
  },
  twitter: {
    card: "summary_large_image",
    title: APP_NAME,
    description: SITE_DESCRIPTION,
    images: ["/genevidence-similarity-check.png"]
  },
  robots: {
    index: true,
    follow: true
  }
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="es">
      <body>{children}</body>
    </html>
  );
}
