import type { Metadata } from "next";
import { Navbar } from "@/components/Navbar";
import "./globals.css";

export const metadata: Metadata = {
  title: "KisanSaathi - Hyperlocal Vernacular Agro-Advisory Engine",
  description:
    "Empowering smallholder farmers with hyperlocal, crop-specific agronomic advice via standard SMS and outbound voice calls in Hindi, Marathi, and English.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="min-h-screen flex flex-col bg-slate-50 text-slate-900">
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
      </body>
    </html>
  );
}
