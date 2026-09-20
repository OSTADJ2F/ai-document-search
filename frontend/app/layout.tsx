import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Locus — Document Intelligence",
  description: "Search and question your private documents with verifiable citations.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}

