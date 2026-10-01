"use client";

import { useEffect } from "react";

/**
 * Static-export-safe redirect from /quiz/ to the canonical /questions/ route.
 * A `next.config` redirect needs a server; this export has none. The meta-refresh
 * fallback in the markup catches browsers with JS disabled; the link catches
 * everything else (and screen readers).
 */
export function QuizRedirect() {
  useEffect(() => {
    window.location.replace("/questions/");
  }, []);

  return (
    <div className="space-y-3">
      <meta httpEquiv="refresh" content="0;url=/questions/" />
      <p className="text-ink-700">
        The questionnaire has moved to{" "}
        <a className="text-accent underline underline-offset-2" href="/questions/">
          /questions/
        </a>
        . Redirecting you there now.
      </p>
    </div>
  );
}
