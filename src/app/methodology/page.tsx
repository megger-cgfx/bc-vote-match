import type { Metadata } from "next";
import Link from "next/link";

import { Markdown } from "@/components/Markdown";
import { DOC_FILES, getDoc } from "@/lib/content";
import { getDataset } from "@/lib/data";
import { SITE, pageOg } from "@/lib/site";

export const metadata: Metadata = {
  title: "Method",
  description:
    "How BC Vote Match codes party positions, scores alignment, and protects neutrality — including what it deliberately does not do.",
  alternates: { canonical: "/methodology/" },
  openGraph: pageOg(`Method · ${SITE.name}`, "/methodology/"),
};

export default function MethodologyPage() {
  const { counts } = getDataset();
  return (
    <div className="space-y-8">
      {/* Public method copy — sourced from docs/content/METHODOLOGY.md at build time. */}
      <Markdown source={getDoc(DOC_FILES.methodology)} />

      {/* The neutrality protocol, published in full under an anchor other pages link to. */}
      <section className="space-y-4">
        <Markdown source={getDoc(DOC_FILES.neutrality)} demote={1} />
      </section>

      <p className="text-sm text-ink-600">
        Current dataset: {counts.questions} statements ({counts.frozenQuestions} frozen),{" "}
        {counts.codings} codings, {counts.sources} archived sources.{" "}
        <Link className="text-accent underline underline-offset-2" href="/coding-table/">
          See every code and its source
        </Link>
        .
      </p>

      <p className="rounded-lg border border-ink-200 bg-white p-4 text-xs text-ink-600">
        {SITE.disclaimer} {SITE.independenceDisclaimer}
      </p>
    </div>
  );
}
