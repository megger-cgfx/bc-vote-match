import type { Metadata } from "next";

import { RidingLookup } from "@/components/RidingLookup";
import { getDataset } from "@/lib/data";
import { SITE, pageOg } from "@/lib/site";

export const metadata: Metadata = {
  title: "Your riding",
  description:
    "Find your BC electoral district and see which candidates are on the ballot there, " +
    "alongside how each candidate's party matches your answers.",
  alternates: { canonical: "/riding/" },
  openGraph: pageOg(`Your riding · ${SITE.name}`, "/riding/"),
};

export default function RidingPage() {
  const { ridings, candidates, parties, questions, codings } = getDataset();
  const version = candidates[0]?.version ?? "v1.1";
  const fetchedAt = candidates[0]?.fetched_at ?? "";

  return (
    <div className="space-y-8">
      <header className="space-y-2">
        <h1 className="text-2xl font-semibold tracking-tight text-ink-900 sm:text-3xl">
          Who is on your ballot
        </h1>
        <p className="text-ink-700">
          BC has {ridings.length || 93} electoral districts. Enter your postal code or
          pick your district to see the candidates standing there. We show you the
          candidates and how each one&rsquo;s party lines up with your answers — we do not
          score candidates individually.
        </p>
        <p className="text-sm text-ink-600">
          Party positions are coded once, provincially. A local candidate of the same party
          therefore shows the same alignment as that party. That is a limitation of a
          party-level method, and it is stated rather than hidden.
        </p>
      </header>

      <RidingLookup
        ridings={ridings}
        candidates={candidates}
        parties={parties}
        questions={questions}
        codings={codings}
        version={version}
        fetchedAt={fetchedAt}
      />
    </div>
  );
}
