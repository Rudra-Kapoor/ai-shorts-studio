import type { Metadata } from "next";
import "./globals.css";
import Link from "next/link";

export const metadata: Metadata = {
  title: "AI Shorts Studio",
  description: "Turn long videos into viral Shorts — fully automated, fully in the cloud.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <div className="mx-auto max-w-5xl px-4 py-6">
          <header className="mb-8 flex items-center justify-between">
            <Link href="/" className="flex items-center gap-2">
              <span className="text-2xl">🎬</span>
              <span className="text-lg font-semibold tracking-tight">
                AI Shorts <span className="text-brand">Studio</span>
              </span>
            </Link>
            <a
              href="https://github.com"
              className="text-sm text-gray-400 hover:text-gray-200"
            >
              docs
            </a>
          </header>
          {children}
          <footer className="mt-16 border-t border-edge pt-6 text-center text-xs text-gray-500">
            Runs entirely on free cloud tiers · Groq · Gemini · R2 · Vercel · Render
          </footer>
        </div>
      </body>
    </html>
  );
}
