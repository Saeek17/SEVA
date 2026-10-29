"use client";

import { usePathname } from "next/navigation";
import { Navbar } from "@/components/Navbar";

// The home page is a self-contained app shell (own sidebar + header), so it
// renders full-bleed; every other route keeps the site navbar and footer.
export function AppChrome({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();

  if (pathname === "/" || pathname?.startsWith("/kisan")) {
    return <>{children}</>;
  }

  return (
    <>
      <Navbar />
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6 sm:py-8">
        {children}
      </main>
      <footer className="border-t border-slate-200 bg-white py-6 text-center text-xs text-slate-500">
        <p>
          KisanSaathi • Hyperlocal Agro-Advisory System • Grounded in Agricultural University (SAU) Packages of Practices
        </p>
        <p className="mt-1 text-slate-400">
          Weather: Open-Meteo & NASA POWER • Soil: ISRIC SoilGrids • DLT Certified Telecom Templates
        </p>
      </footer>
    </>
  );
}
