import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";

export const metadata: Metadata = {
  title: "Inbox Copilot",
  description: "Human-in-the-loop AI assistant for email triage",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="bg-gray-50 text-gray-900 min-h-screen">
        <nav className="bg-white border-b border-gray-200">
          <div className="max-w-7xl mx-auto px-6 py-3 flex items-center gap-6">
            <Link href="/" className="font-bold text-lg">
              📥 Inbox Copilot
            </Link>
            <Link href="/" className="text-gray-600 hover:text-black">
              Inbox
            </Link>
            <Link href="/audit" className="text-gray-600 hover:text-black">
              Audit
            </Link>
            <Link href="/dashboard" className="text-gray-600 hover:text-black">
              Dashboard
            </Link>
          </div>
        </nav>
        <main className="max-w-7xl mx-auto px-6 py-8">{children}</main>
      </body>
    </html>
  );
}