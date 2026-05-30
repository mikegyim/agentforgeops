export default function Home() {
  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-3xl font-bold">AgentForgeOps</h1>
        <p className="opacity-80">
          AI-Native DevOps & Software Engineering Platform — RAG, multi-agent
          workflows, PR review, deployment validation, incident triage.
        </p>
      </header>

      <section className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card title="Chat" body="Ask grounded questions against your indexed context." href="/chat" />
        <Card title="Agents" body="Run code review, test gen, deploy validation, triage." href="/agents" />
        <Card title="Upload" body="Index docs, code, runbooks, manifests." href="/upload" />
        <Card title="RAG search" body="Search indexed sources with citations." href="/search" />
        <Card title="Incidents" body="Correlate logs and propose root cause." href="/incidents" />
        <Card title="Pull requests" body="See AI reviews and merge readiness." href="/prs" />
      </section>
    </div>
  );
}

function Card({ title, body, href }: { title: string; body: string; href: string }) {
  return (
    <a
      href={href}
      className="block rounded-xl p-5 bg-[var(--panel)] hover:ring-1 hover:ring-[var(--accent)] transition"
    >
      <div className="text-lg font-semibold">{title}</div>
      <div className="text-sm opacity-80 mt-2">{body}</div>
    </a>
  );
}
