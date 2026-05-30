'use client';
import { useState } from 'react';

export default function IncidentsPage() {
  const [logs, setLogs] = useState('');
  const [service, setService] = useState('checkout');
  const [out, setOut] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const triage = async () => {
    setLoading(true);
    try {
      const r = await fetch('/api/agents/incident-triage', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ logs, service }),
      });
      setOut(await r.json());
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl space-y-4">
      <h2 className="text-2xl font-semibold">Incident triage</h2>
      <input
        value={service}
        onChange={(e) => setService(e.target.value)}
        className="rounded-lg bg-[var(--panel)] px-3 py-2"
      />
      <textarea
        value={logs}
        onChange={(e) => setLogs(e.target.value)}
        rows={10}
        placeholder="Paste logs here…"
        className="w-full rounded-lg bg-[var(--panel)] p-3 font-mono text-sm"
      />
      <button
        onClick={triage}
        disabled={loading}
        className="rounded-lg px-4 py-2 bg-[var(--accent)] text-black font-semibold disabled:opacity-50"
      >
        {loading ? 'Triaging…' : 'Triage'}
      </button>
      {out && (
        <pre className="rounded-xl bg-[var(--panel)] p-4 text-xs overflow-auto">
          {JSON.stringify(out, null, 2)}
        </pre>
      )}
    </div>
  );
}
