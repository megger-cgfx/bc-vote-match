import type { Metadata } from "next";
import Link from "next/link";

import { Markdown } from "@/components/Markdown";
import { DOC_FILES, getDoc } from "@/lib/content";
import { SITE, pageOg } from "@/lib/site";

export const metadata: Metadata = {
  title: "About & disclaimer",
  description:
    "Who runs BC Vote Match, why it exists, what it does not claim, and how to submit a correction.",
  alternates: { canonical: "/about/" },
  openGraph: pageOg(`About · ${SITE.name}`, "/about/"),
};

export default function AboutPage() {
  return (
    <div className="space-y-8">
      {/* Public about copy — sourced from docs/content/ABOUT.md at build time. */}
      <Markdown source={getDoc(DOC_FILES.about)} />

      {/* Full disclaimer — docs/content/DISCLAIMER.md, demoted under the page H1. */}
      <section className="space-y-4">
        <Markdown source={getDoc(DOC_FILES.disclaimer)} demote={1} />
      </section>

      <section className="space-y-3">
        <h2 id="independence" className="text-lg font-semibold text-ink-900">
          Independence
        </h2>
        <p className="text-sm text-ink-700">{SITE.independenceDisclaimer}</p>
        <p className="text-sm text-ink-700">
          BC Vote Match is not affiliated with, endorsed by, or connected to Vote Compass or Vox Pop
          Labs. Vote Compass and Vox Pop Labs are trademarks of their respective owners, named here
          only to clarify that we are not them.
        </p>
      </section>

      <p className="text-sm text-ink-600">
        What we collect (almost nothing) is described in the{" "}
        <Link className="text-accent underline underline-offset-2" href="/privacy/">
          privacy notice
        </Link>
        . For official information about registering, voting, and your district, use{" "}
        <a
          className="text-accent underline underline-offset-2"
          href="https://elections.bc.ca"
          rel="noopener noreferrer"
          target="_blank"
        >
          Elections BC
        </a>
        .
      </p>
    </div>
  );
}
