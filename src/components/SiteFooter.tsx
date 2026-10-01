import Link from "next/link";

import { SITE } from "@/lib/site";
import type { Dataset } from "@/lib/schema";

export function SiteFooter({ counts }: { counts: Dataset["counts"] }) {
  return (
    <footer className="mt-8 border-t border-ink-200 bg-white">
      <div className="mx-auto max-w-4xl space-y-3 px-4 py-8 text-sm text-ink-600 sm:px-6">
        <p className="text-ink-700">
          <strong className="font-semibold">Independent and non-partisan.</strong>{" "}
          {SITE.independenceDisclaimer}
        </p>
        <p>
          Election day: <time dateTime={SITE.electionDay}>{SITE.electionDay}</time> · Advance
          voting {SITE.advanceVoting}. Confirm your own details with{" "}
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
        <p className="text-xs text-ink-500">
          No accounts, no cookies for tracking, no personal data collected or stored. Answers stay
          in your browser. Content licensed MIT — corrections and pull requests welcome.
        </p>
        <p className="text-xs text-ink-500" data-dataset-counts>
          Dataset: {counts.parties} parties · {counts.questions} statements (
          {counts.frozenQuestions} frozen) · {counts.codings} party codings · {counts.sources}{" "}
          archived sources.
        </p>
        <ul className="flex flex-wrap gap-x-4 gap-y-1 text-xs">
          <li>
            <Link className="text-accent underline underline-offset-2" href="/about/">
              About &amp; disclaimer
            </Link>
          </li>
          <li>
            <Link className="text-accent underline underline-offset-2" href="/privacy/">
              Privacy
            </Link>
          </li>
          <li>
            <Link className="text-accent underline underline-offset-2" href="/methodology/">
              Methodology
            </Link>
          </li>
          <li>
            <Link className="text-accent underline underline-offset-2" href="/coding-table/">
              Full coding table
            </Link>
          </li>
        </ul>
      </div>
    </footer>
  );
}
