"use client";

/**
 * RidingLookup.tsx — the riding-level surface (M6 + M6b). CLIENT ONLY.
 *
 * It does TWO things honestly:
 *
 *   1. Given a postal code, it lands on the electoral district (data/candidates/
 *      postal-to-riding.json, lazily fetched — geography only, never an API call), and
 *      given a district it lists who is on the ballot there.
 *   2. If the visitor has taken the survey, it shows how each candidate's *party*
 *      scored, using the party-level codings. It does not score individual candidates:
 *      no candidate platform has been coded, and inventing one would break the
 *      neutrality rule in docs/SCHEMA.md. The copy says so out loud.
 *
 * Empty states are explicit everywhere: a party with no coded positions shows "no coded
 * positions", never a fabricated 0% or an invented number. A postal code that is not in
 * the dataset is reported as not found — never resolved to a guessed district.
 *
 * Answers come from this browser's localStorage (src/lib/store.ts). Nothing is sent
 * anywhere; the site is static, so there is no server to send it to.
 */

import { useEffect, useMemo, useState, type FormEvent, type ReactNode } from "react";

import type { Candidate, Coding, Party, Question, Riding } from "@/lib/schema";
import {
  loadPostalIndex,
  lookupPostal,
  normalisePostal,
  type PostalIndex,
  type PostalLookup,
} from "@/lib/postal";
import { alignAllParties, type Alignment, type Answers } from "@/lib/scoring";
import { loadAnswers } from "@/lib/store";

interface Props {
  ridings: Riding[];
  candidates: Candidate[];
  parties: Party[];
  questions: Question[];
  codings: Coding[];
  version: string;
  fetchedAt: string;
}

const STATUS_LABEL: Record<string, string> = {
  nominated: "Confirmed candidate",
  declared: "Declared, not yet confirmed",
};

export function RidingLookup({
  ridings,
  candidates,
  parties,
  questions,
  codings,
  version,
  fetchedAt,
}: Props) {
  const [query, setQuery] = useState("");
  const [selected, setSelected] = useState<string | null>(null);
  const [answers, setAnswers] = useState<Answers>({});

  const [postalInput, setPostalInput] = useState("");
  const [postalBusy, setPostalBusy] = useState(false);
  const [postalError, setPostalError] = useState<string | null>(null);
  const [postalResult, setPostalResult] = useState<PostalLookup | null>(null);
  const [postalIndex, setPostalIndex] = useState<PostalIndex | null>(null);

  // Read the riding from the URL (?r=slug) and the saved answers on first paint.
  useEffect(() => {
    try {
      const params = new URLSearchParams(window.location.search);
      const r = params.get("r");
      if (r && ridings.some((x) => x.slug === r)) setSelected(r);
    } catch {
      /* no URL access — user picks from the list */
    }
    setAnswers(loadAnswers());
  }, [ridings]);

  const partyBySlug = useMemo(
    () => new Map(parties.map((p) => [p.slug, p])),
    [parties],
  );

  const alignments = useMemo(() => {
    const list = alignAllParties(answers, codings, questions, parties.map((p) => p.slug));
    return new Map<string, Alignment>(list.map((a) => [a.partySlug, a]));
  }, [answers, codings, questions, parties]);

  /** How many real (non-null) coded positions each party has — the empty-state switch. */
  const codedByParty = useMemo(() => {
    const m = new Map<string, number>();
    for (const c of codings) {
      if (typeof c.code === "number") m.set(c.party_slug, (m.get(c.party_slug) ?? 0) + 1);
    }
    return m;
  }, [codings]);

  const answered = Object.values(answers).filter((v) => typeof v === "number").length;

  const matches = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return [];
    return ridings
      .filter((r) => r.name.toLowerCase().includes(q))
      .slice(0, 8);
  }, [query, ridings]);

  const selectedRiding = ridings.find((r) => r.slug === selected) ?? null;
  const selectedCandidates = useMemo(
    () =>
      candidates
        .filter((c) => c.riding_slug === selected)
        .sort(
          (a, b) =>
            Number(b.incumbent) - Number(a.incumbent) ||
            a.party_label.localeCompare(b.party_label) ||
            a.name.localeCompare(b.name),
        ),
    [candidates, selected],
  );

  /** District name with graceful fallbacks if a slug has no riding record. */
  const ridingName = (slug: string): string =>
    ridings.find((r) => r.slug === slug)?.name ??
    postalIndex?.ridings?.[slug]?.name ??
    slug;

  async function handlePostal(e: FormEvent) {
    e.preventDefault();
    const raw = postalInput.trim();
    if (!raw) return;
    setPostalBusy(true);
    setPostalError(null);
    try {
      let index = postalIndex;
      if (!index) {
        index = await loadPostalIndex();
        setPostalIndex(index);
      }
      const result = lookupPostal(index, raw);
      setPostalResult(result);
      if (result.kind === "exact") {
        if (ridings.some((r) => r.slug === result.riding)) {
          setSelected(result.riding);
        } else {
          // The lookup maps to a district the riding list does not carry. Say so
          // rather than rendering an empty panel.
          setPostalError(
            `Postal code ${result.code} maps to ${ridingName(result.riding)}, which is ` +
              "not in our district list yet. Search by district name below.",
          );
        }
      }
    } catch {
      setPostalResult(null);
      setPostalError(
        "The postal lookup could not load. Search by district name below — " +
          "everything on this page still works without it.",
      );
    } finally {
      setPostalBusy(false);
    }
  }

  /** Buttons for "your code is ambiguous — pick your district" results. */
  const ridingChoices = (slugs: string[]) => (
    <ul className="flex flex-wrap gap-2">
      {slugs.map((slug) => (
        <li key={slug}>
          <button
            type="button"
            onClick={() => {
              setSelected(slug);
              setPostalResult(null);
              setPostalError(null);
            }}
            className="rounded-lg border border-ink-300 bg-white px-3 py-1.5 text-sm text-ink-900 hover:bg-ink-50"
          >
            {ridingName(slug)}
          </button>
        </li>
      ))}
    </ul>
  );

  function postalPanel(result: PostalLookup) {
    switch (result.kind) {
      case "exact":
        return (
          <p className="text-sm text-ink-700">
            Postal code {result.code} is in{" "}
            <span className="font-medium text-ink-900">{ridingName(result.riding)}</span>.
          </p>
        );
      case "straddling":
        return (
          <div className="space-y-2">
            <p className="text-sm text-ink-700">
              Postal code {result.code} sits on a boundary between districts in our data,
              so we can&rsquo;t pick for you. Which one is yours?
            </p>
            {ridingChoices(result.ridings)}
          </div>
        );
      case "fsa":
        return (
          <div className="space-y-2">
            <p className="text-sm text-ink-700">
              {result.fsa} is a forward sorting area, not a full postal code. It covers{" "}
              {result.ridings.ridings.length} district
              {result.ridings.ridings.length === 1 ? "" : "s"} in our data — pick yours, or
              enter your full code (like {result.fsa} 1A1) for an exact match.
            </p>
            {ridingChoices(result.ridings.ridings)}
          </div>
        );
      case "fsa-hint":
        return (
          <div className="space-y-2">
            <p className="text-sm text-ink-700">
              We couldn&rsquo;t find {result.code} in our postal dataset. Its forward
              sorting area ({result.fsa}) covers these districts — pick yours, or search by
              district name below:
            </p>
            {ridingChoices(result.ridings.ridings)}
          </div>
        );
      case "not-found":
        return (
          <p className="text-sm text-ink-700">
            We couldn&rsquo;t find “{result.input}” in the BC postal codes in our dataset.
            Check the code, or search by district name below.
          </p>
        );
      case "invalid":
        return (
          <p className="text-sm text-ink-700">
            “{result.input}” doesn&rsquo;t look like a Canadian postal code (format A1A
            1A1). Try again, or search by district name below.
          </p>
        );
    }
  }

  /** The right-hand value for one party: a number, or an explicit empty state. */
  function alignmentValue(partySlug: string | null): ReactNode {
    if (!partySlug) return <span className="text-xs text-ink-400">no party positions</span>;
    if ((codedByParty.get(partySlug) ?? 0) === 0) {
      return (
        <span className="text-xs italic text-ink-400">no coded positions yet</span>
      );
    }
    const al = alignments.get(partySlug);
    if (al && al.percent !== null) {
      return <span className="font-mono text-sm text-ink-900">{Math.round(al.percent)}%</span>;
    }
    if (answered === 0) return <span className="text-xs text-ink-400">—</span>;
    return <span className="text-xs text-ink-400">not enough overlap</span>;
  }

  /** Distinct contract parties standing in the selected riding, alignment-ready. */
  const ridingParties = useMemo(() => {
    const seen = new Map<string, { label: string; count: number }>();
    for (const c of selectedCandidates) {
      if (!c.party_slug) continue;
      const cur = seen.get(c.party_slug) ?? {
        label: partyBySlug.get(c.party_slug)?.name ?? c.party_label,
        count: 0,
      };
      cur.count += 1;
      seen.set(c.party_slug, cur);
    }
    return [...seen.entries()]
      .map(([slug, info]) => ({
        slug,
        label: info.label,
        count: info.count,
        percent: alignments.get(slug)?.percent ?? null,
      }))
      .sort((a, b) => (b.percent ?? -1) - (a.percent ?? -1));
  }, [selectedCandidates, partyBySlug, alignments]);

  const hasIndependents = selectedCandidates.some((c) => !c.party_slug);

  if (ridings.length === 0) {
    return (
      <div className="rounded-lg border border-ink-200 bg-white p-4 text-sm text-ink-700">
        The riding-level layer has not been built yet. Run{" "}
        <span className="font-mono">python3 scripts/build-ridings.py all</span> to fetch the
        electoral-district and candidate lists, then rebuild the site.
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <section className="space-y-3">
        <label className="block text-sm font-medium text-ink-900" htmlFor="postal-code">
          Find your riding by postal code
        </label>
        <form className="flex flex-wrap gap-2" onSubmit={handlePostal}>
          <input
            id="postal-code"
            type="text"
            autoComplete="postal-code"
            value={postalInput}
            onChange={(e) => setPostalInput(e.target.value)}
            placeholder="e.g. V8R 3L2"
            className="w-full max-w-xs rounded-lg border border-ink-300 bg-white px-3 py-2 text-sm text-ink-900 shadow-sm"
          />
          <button
            type="submit"
            disabled={postalBusy || !postalInput.trim()}
            className="rounded-lg bg-accent px-4 py-2 text-sm font-medium text-white shadow-sm disabled:opacity-50"
          >
            {postalBusy ? "Looking up…" : "Find my riding"}
          </button>
        </form>
        {postalError ? (
          <p className="text-sm text-ink-700">{postalError}</p>
        ) : null}
        {postalResult ? <div className="space-y-2">{postalPanel(postalResult)}</div> : null}
      </section>

      <section className="space-y-3">
        <label className="block text-sm font-medium text-ink-900" htmlFor="riding-search">
          Find your electoral district
        </label>
        <input
          id="riding-search"
          type="search"
          autoComplete="off"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Start typing a district, e.g. Burnaby, Saanich, Prince George"
          className="w-full rounded-lg border border-ink-300 bg-white px-3 py-2 text-sm text-ink-900 shadow-sm"
        />
        {query.trim() && matches.length > 0 ? (
          <ul className="divide-y divide-ink-100 overflow-hidden rounded-lg border border-ink-200 bg-white">
            {matches.map((r) => (
              <li key={r.slug}>
                <button
                  type="button"
                  onClick={() => {
                    setSelected(r.slug);
                    setQuery("");
                  }}
                  className="block w-full px-3 py-2 text-left text-sm hover:bg-ink-50"
                >
                  <span className="text-ink-900">{r.name}</span>
                  <span className="ml-2 text-xs text-ink-500">{r.region}</span>
                </button>
              </li>
            ))}
          </ul>
        ) : null}
        {query.trim() && matches.length === 0 ? (
          <p className="text-sm text-ink-500">No district matches “{query.trim()}”.</p>
        ) : null}
      </section>

      {selectedRiding ? (
        <section className="space-y-4">
          <header className="space-y-1">
            <h2 className="text-xl font-semibold tracking-tight text-ink-900">
              {selectedRiding.name}
            </h2>
            <p className="text-xs text-ink-500">
              {selectedRiding.region} · {selectedCandidates.length} candidate
              {selectedCandidates.length === 1 ? "" : "s"} on record
            </p>
          </header>

          {answered === 0 ? (
            <p className="rounded-lg border border-ink-200 bg-ink-50 px-3 py-2 text-sm text-ink-700">
              You haven&rsquo;t taken the survey in this browser, so no alignment is shown
              here.{" "}
              <a className="text-accent underline underline-offset-2" href="/questions/">
                Take the survey
              </a>{" "}
              and come back — your answers never leave this device.
            </p>
          ) : (
            <p className="text-xs text-ink-500">
              Alignment is your match with each candidate&rsquo;s <em>party</em>, from the{" "}
              {answered} question{answered === 1 ? "" : "s"} you answered. Individual
              candidates are not coded.
            </p>
          )}

          {selectedCandidates.length === 0 ? (
            <p className="rounded-lg border border-ink-200 bg-white px-3 py-2 text-sm text-ink-700">
              No candidates are on record for this district in the {version} roster
              snapshot. Nominations close 3 October 2026, so this can change — check back
              after the next refresh.
            </p>
          ) : (
            <ul className="space-y-2">
              {selectedCandidates.map((c) => {
                const party = c.party_slug ? partyBySlug.get(c.party_slug) : undefined;
                return (
                  <li
                    key={c.id}
                    className="rounded-lg border border-ink-200 bg-white p-3 sm:flex sm:items-center sm:justify-between sm:gap-4"
                  >
                    <div className="flex items-start gap-3">
                      <span
                        aria-hidden="true"
                        className="mt-1.5 inline-block h-3 w-3 shrink-0 rounded-full"
                        style={{ backgroundColor: party?.color ?? "#4d5461" }}
                      />
                      <div>
                        <p className="text-sm font-medium text-ink-900">
                          {c.name}
                          {c.incumbent ? (
                            <span className="ml-2 rounded bg-ink-100 px-1.5 py-0.5 text-[11px] font-normal text-ink-700">
                              sitting MLA
                            </span>
                          ) : null}
                        </p>
                        <p className="text-xs text-ink-600">
                          {party ? (
                            <a
                              className="underline decoration-dotted underline-offset-2"
                              href={`/parties/#${party.slug}`}
                            >
                              {c.party_label}
                            </a>
                          ) : (
                            c.party_label
                          )}
                          <span className="text-ink-400">
                            {" · "}
                            {STATUS_LABEL[c.status] ?? c.status}
                          </span>
                        </p>
                      </div>
                    </div>
                    <div className="mt-2 text-right sm:mt-0">
                      {alignmentValue(c.party_slug)}
                    </div>
                  </li>
                );
              })}
            </ul>
          )}

          {selectedCandidates.length > 0 ? (
            <div className="space-y-2">
              <h3 className="text-sm font-medium text-ink-900">
                Party alignment in this district
              </h3>
              <p className="text-xs text-ink-500">
                One code per party, provincially. Where a party has no coded positions,
                there is nothing to show — and nothing is invented.
              </p>
              <ul className="divide-y divide-ink-100 overflow-hidden rounded-lg border border-ink-200 bg-white">
                {ridingParties.map((p) => (
                  <li
                    key={p.slug}
                    className="flex items-center justify-between gap-4 px-3 py-2"
                  >
                    <span className="text-sm text-ink-900">
                      {p.label}
                      <span className="ml-2 text-xs text-ink-400">
                        {p.count} candidate{p.count === 1 ? "" : "s"}
                      </span>
                    </span>
                    {alignmentValue(p.slug)}
                  </li>
                ))}
                {hasIndependents ? (
                  <li className="flex items-center justify-between gap-4 px-3 py-2">
                    <span className="text-sm text-ink-900">
                      Independent / other
                      <span className="ml-2 text-xs text-ink-400">
                        {selectedCandidates.filter((c) => !c.party_slug).length} candidate
                        {selectedCandidates.filter((c) => !c.party_slug).length === 1
                          ? ""
                          : "s"}
                      </span>
                    </span>
                    <span className="text-xs italic text-ink-400">
                      no party positions to compare
                    </span>
                  </li>
                ) : null}
              </ul>
            </div>
          ) : null}

          <p className="text-xs text-ink-500">
            Riding roster {version} · built {fetchedAt}. Candidate lists are snapshots:
            nominations close 3 October 2026 at 1 p.m. Pacific, so this list changes. Source
            and archive links are on the{" "}
            <a className="text-accent underline underline-offset-2" href="/methodology/">
              method
            </a>{" "}
            page.
          </p>
        </section>
      ) : (
        <p className="text-sm text-ink-500">
          Enter a postal code or pick a district above to see who is running where you
          vote.
        </p>
      )}
    </div>
  );
}
