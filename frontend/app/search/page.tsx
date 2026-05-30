'use client';
import { useState } from 'react';

type Hit = { source: string; score: number; text: string };

export default function SearchPage() {
  const [q, setQ] = useState('');
  const [hits, setHits] = useState<Hit[]>([]);

  const run = async () => {
    const r = await fetch('/api/rag/search', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query: q }),
    });
    const d = await r.json();
    setHits(d.hits || []);
  };

  return (
    <div className="max-w-3xl space-y-4">
      <h2 className="text-2xl font-semibold">RAG search</h2>
      <div className="flex gap-2">
        <input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && run()}
          className="flex-1 rounded-lg bg-[var(--panel)] px-4 py-3"
        />
        <button onClick={run} className="rounded-lg px-4 py-3 bg-[var(--accent)] text-black font-semibold">
          Search
        </button>
      </div>
      <ul className="space-y-2">
        {hits.map((h, i) => (
          <li key={i} className="rounded-lg bg-[var(--panel)] p-3 text-sm">
            <div className="opacity-70">{h.source} — {h.score.toFixed(3)}</div>
            <div className="mt-1">{h.text.slice(0, 600)}</div>
          </li>
        ))}
      </ul>
    </div>
  );
}
