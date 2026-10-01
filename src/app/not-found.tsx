import Link from "next/link";

export default function NotFound() {
  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-semibold tracking-tight text-ink-900">Page not found</h1>
      <p className="text-ink-700">
        That page doesn&rsquo;t exist. The questionnaire still does.
      </p>
      <div className="flex flex-wrap gap-3">
        <Link
          href="/questions/"
          className="rounded bg-accent px-4 py-2.5 font-medium text-white hover:bg-ink-800"
        >
          Start the questionnaire
        </Link>
        <Link
          href="/"
          className="rounded border border-ink-300 px-4 py-2.5 font-medium text-ink-700 hover:border-ink-500"
        >
          Home
        </Link>
      </div>
    </div>
  );
}
