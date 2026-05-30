'use client';
import { useState } from 'react';

type Source = { id: number; name: string; score: number; snippet: string };

export default function ChatPage() {
  const [msg, setMsg] = useState('');
  const [answer, setAnswer] = useState<string>('');
  const [sources, setSources] = useState<Source[]>([]);
  const [loading, setLoading] = useState(false);

  const send = async () => {
    if (!msg.trim()) return;
    setLoading(true);
    try {
      const r = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: msg }),
      });
      const data = await r.json();
      setAnswer(data.answer || '');
      setSources(data.sources || []);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-3xl space-y-4">
      <h2 className="text-2xl font-semibold">Grounded chat</h2>
      <div className="flex gap-2">
        <input
          value={msg}
          onChange={(e) => setMsg(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && send()}
          placeholder="Ask about your indexed runbooks, code, manifests…"
          className="flex-1 rounded-lg bg-[var(--panel)] px-4 py-3 outline-none"
        />
        <button
          onClick={send}
          disabled={loading}
          className="rounded-lg px-4 py-3 bg-[var(--accent)] text-black font-semibold disabled:opacity-50"
        >
          {loading ? '…' : 'Send'}
        </button>
      </div>

      {answer && (
        <div className="rounded-xl bg-[var(--panel)] p-5 whitespace-pre-wrap">{answer}</div>
      )}

      {sources.length > 0 && (
        <div>
          <h3 className="font-semibold mt-4 mb-2">Sources</h3>
          <ul className="space-y-2">
            {sources.map((s) => (
              <li key={s.id} className="rounded-lg bg-[var(--panel)] p-3 text-sm">
                <div className="opacity-70">[#{s.id}] {s.name} — score {s.score.toFixed(3)}</div>
                <div className="mt-1">{s.snippet}</div>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
