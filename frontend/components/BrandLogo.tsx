import Image from "next/image";


export function BrandLogo({ className = "" }: { className?: string }) {
  return (
    <Image
      src="/genevidence-similarity-check.png"
      alt="GenEvidence Similarity Check"
      width={1858}
      height={350}
      priority
      className={`h-auto w-full ${className}`}
    />
  );
}
