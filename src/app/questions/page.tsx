import type { Metadata } from "next";

import { QuestionFlow } from "@/components/QuestionFlow";
import { getDataset } from "@/lib/data";
import { SITE, pageOg } from "@/lib/site";

export const metadata: Metadata = {
  title: "Questionnaire",
  description:
    "Answer the statements and see which BC party your views sit closest to — every party position is sourced.",
  alternates: { canonical: "/questions/" },
  openGraph: pageOg(`Questionnaire · ${SITE.name}`, "/questions/"),
};

export default function QuestionsPage() {
  const { questions, counts } = getDataset();
  return (
    <div className="space-y-6">
      <header className="space-y-2">
        <h1 className="text-2xl font-semibold tracking-tight text-ink-900 sm:text-3xl">
          The statements
        </h1>
        <p className="text-ink-700">
          For each statement, say how much you agree. There is no right answer and no time limit, and
          you can skip anything you have no view on.
        </p>
        <p className="text-sm text-ink-500">
          {counts.questions} statements across six topics. Your answers never leave this device
          unless you choose to share the link on the results page.
        </p>
      </header>

      <QuestionFlow questions={questions} />
    </div>
  );
}
