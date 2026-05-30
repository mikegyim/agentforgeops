export default function PRsPage() {
  return (
    <div className="max-w-3xl space-y-3">
      <h2 className="text-2xl font-semibold">Pull requests</h2>
      <p className="opacity-80 text-sm">
        AI reviews land here once a GitHub webhook is connected and a PR is opened
        against a configured repository. See <code>github-actions/ai-pr-review.yml</code>{' '}
        for the workflow that calls the backend.
      </p>
      <div className="rounded-xl bg-[var(--panel)] p-5 text-sm opacity-80">
        No PRs yet. Configure <code>GITHUB_TOKEN</code> and{' '}
        <code>GITHUB_WEBHOOK_SECRET</code> in the backend env.
      </div>
    </div>
  );
}
