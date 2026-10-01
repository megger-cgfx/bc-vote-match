"use client";

import { useState } from "react";

/**
 * Share controls. The share image itself is static (`/og.png`) because this is a
 * fully static export — there is no server to render a per-user card. Instead the
 * *link* carries the user's answers in the query string, so the recipient lands on
 * the same result. Nothing is posted anywhere.
 */
export function ShareCard({ url, summary }: { url: string; summary: string }) {
  const [copied, setCopied] = useState(false);
  const [status, setStatus] = useState("");

  const shareText = `${summary} — ${url}`;

  async function onShare() {
    setStatus("");
    try {
      if (typeof navigator !== "undefined" && navigator.share) {
        await navigator.share({ title: "BC Vote Match", text: summary, url });
        setStatus("Shared.");
        return;
      }
      await copy();
    } catch (err) {
      if ((err as Error)?.name === "AbortError") return;
      setStatus("Sharing was blocked by the browser — use Copy link.");
    }
  }

  async function copy() {
    try {
      await navigator.clipboard.writeText(shareText);
      setCopied(true);
      setStatus("Link copied.");
      window.setTimeout(() => setCopied(false), 2500);
    } catch {
      setStatus("Could not reach the clipboard — select the link below and copy it manually.");
    }
  }

  return (
    <section aria-labelledby="share-heading" className="rounded-lg border border-ink-200 bg-white p-4 sm:p-5">
      <h2 id="share-heading" className="text-base font-semibold text-ink-900">
        Share your result
      </h2>
      <p className="mt-1 text-sm text-ink-600">
        The link contains your answers so it opens on the same match. Nothing is uploaded.
      </p>
      <div className="mt-3 flex flex-wrap gap-2">
        <button
          type="button"
          onClick={onShare}
          className="rounded bg-accent px-4 py-2 text-sm font-medium text-white hover:bg-ink-800"
        >
          Share
        </button>
        <button
          type="button"
          onClick={copy}
          className="rounded border border-ink-300 px-4 py-2 text-sm text-ink-700 hover:border-ink-500"
        >
          {copied ? "Copied ✓" : "Copy link"}
        </button>
        <a
          href={url}
          className="rounded border border-ink-300 px-4 py-2 text-sm text-ink-700 hover:border-ink-500"
        >
          Open result link
        </a>
        <a
          href="/og.png"
          download="bc-vote-match.png"
          className="rounded border border-ink-300 px-4 py-2 text-sm text-ink-700 hover:border-ink-500"
        >
          Download share image
        </a>
      </div>
      <p className="mt-2 break-all font-mono text-xs text-ink-500">{url}</p>
      <p aria-live="polite" className="mt-1 text-xs text-ink-600">
        {status}
      </p>
    </section>
  );
}
