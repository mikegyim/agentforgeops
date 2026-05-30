'use client';
import { useEffect, useState } from 'react';

type Agent = { id: string; name: string; description: string };

export default function AgentsPage() {
  const [agents, setAgents] = useState<Agent[]>([]);

  useEffect(() => {
    fetch('/api/agents')
      .then((r) => r.json())
      .then((d) => setAgents(d.agents || []));
  }, []);

  return (
    <div className="max-w-4xl">
      <h2 className="text-2xl font-semibold mb-4">Agents</h2>
      <div className="grid md:grid-cols-2 gap-4">
        {agents.map((a) => (
          <div key={a.id} className="rounded-xl bg-[var(--panel)] p-5">
            <div className="text-lg font-semibold">{a.name}</div>
            <div className="text-sm opacity-80 mt-1">{a.description}</div>
            <div className="text-xs opacity-60 mt-3">POST /api/agents/{a.id}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
