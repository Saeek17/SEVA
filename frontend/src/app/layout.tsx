import type { Metadata } from "next";
import { AppChrome } from "@/components/AppChrome";
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
        <AppChrome>{children}</AppChrome>
      </body>
    </html>
  );
}
