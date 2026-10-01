import type { Metadata } from "next";

import { QuizRedirect } from "./quiz-redirect";

/**
 * `/quiz` is a legacy alias for the questionnaire. `/questions/` is the one
 * canonical route (it is what the sitemap, the home page and every share link
 * reference); this page only exists so old /quiz links keep working on a static
 * export, which has no server to issue a real 301.
 */
export const metadata: Metadata = {
  title: "Questionnaire",
  alternates: { canonical: "/questions/" },
  robots: { index: false, follow: true },
};

export default function QuizAliasPage() {
  return <QuizRedirect />;
}
