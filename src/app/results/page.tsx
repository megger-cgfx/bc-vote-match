import type { Metadata } from "next";

import { ResultsView } from "@/components/ResultsView";
import { getDataset } from "@/lib/data";
import { SITE, pageOg } from "@/lib/site";

export const metadata: Metadata = {
  title: "Results",
  description:
    "Your alignment with each BC party, the two-dimensional compass, and the source behind every party position.",
  alternates: { canonical: "/results/" },
  openGraph: pageOg(`Results · ${SITE.name}`, "/results/"),
  robots: { index: false, follow: true },
};

export default function ResultsPage() {
  const { parties, questions, codings, sources } = getDataset();
  return (
    <ResultsView
      parties={parties}
      questions={questions}
      codings={codings}
      sources={sources}
    />
  );
}
