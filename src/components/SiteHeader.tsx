import Link from "next/link";

import { NAV, SITE } from "@/lib/site";

export function SiteHeader() {
  return (
    <header className="border-b border-ink-200 bg-white">
      <div className="mx-auto flex max-w-4xl flex-col gap-3 px-4 py-3 sm:flex-row sm:items-center sm:justify-between sm:px-6">
        <Link href="/" className="flex items-baseline gap-2 text-ink-900">
          <span className="text-lg font-semibold tracking-tight">{SITE.name}</span>
          <span className="hidden text-xs text-ink-500 sm:inline">BC 2026</span>
        </Link>
        <nav aria-label="Main" className="sm:self-auto">
          <ul className="flex flex-wrap gap-x-4 gap-y-1 text-sm">
            {NAV.map((item) => (
              <li key={item.href}>
                <Link
                  href={item.href}
                  className="text-ink-700 underline-offset-4 hover:text-accent hover:underline"
                >
                  {item.label}
                </Link>
              </li>
            ))}
          </ul>
        </nav>
      </div>
    </header>
  );
}
