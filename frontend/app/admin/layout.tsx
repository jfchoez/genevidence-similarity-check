import { privateMetadata } from "@/lib/private-metadata";


export const metadata = privateMetadata;


export default function AdminLayout({ children }: { children: React.ReactNode }) {
  return children;
}
