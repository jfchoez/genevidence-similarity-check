import type { MetadataRoute } from "next";

import { SITE_URL } from "@/lib/site";


export default function sitemap(): MetadataRoute.Sitemap {
  const routes = ["/", "/features", "/pricing", "/login", "/register"];
  return routes.map((route) => ({
    url: `${SITE_URL}${route}`,
    lastModified: new Date(),
    changeFrequency: route === "/" ? "weekly" : "monthly",
    priority: route === "/" ? 1 : route === "/features" || route === "/pricing" ? 0.8 : 0.5
  }));
}
