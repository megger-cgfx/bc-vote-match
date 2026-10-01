import type { Metadata } from "next";
import Link from "next/link";

import { Markdown } from "@/components/Markdown";
import { DOC_FILES, getDoc } from "@/lib/content";
import { SITE, pageOg } from "@/lib/site";

export const metadata: Metadata = {
  title: "Privacy",
  description:
    "What BC Vote Match does and does not collect: no accounts, no personal information, and your answers never leave your browser.",
  alternates: { canonical: "/privacy/" },
  openGraph: pageOg(`Privacy · ${SITE.name}`, "/privacy/"),
};

export default function PrivacyPage() {
  return (
    <div className="space-y-8">
      {/* Public privacy copy — sourced from docs/content/PRIVACY.md at build time. */}
      <Markdown source={getDoc(DOC_FILES.privacy)} />

      <p className="text-sm text-ink-600">
        See also the{" "}
        <Link className="text-accent underline underline-offset-2" href="/about/#disclaimer">
          disclaimer
        </Link>{" "}
        and{" "}
        <Link className="text-accent underline underline-offset-2" href="/about/">
          about page
        </Link>
        . {SITE.independenceDisclaimer}
      </p>
    </div>
  );
}
