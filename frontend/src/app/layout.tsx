import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "The Lenny Growth Assistant | Grounded RAG & Ship 30 Engine",
  description:
    "Enterprise-grade RAG and Ship 30 for 30 Content Engine grounded in Lenny's Podcast transcripts for product managers and growth leaders.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="bg-slate-950 text-slate-100 min-h-screen antialiased">
        {children}
      </body>
    </html>
  );
}
