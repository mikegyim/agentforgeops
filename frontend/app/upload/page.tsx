'use client';
import { useState } from 'react';

export default function UploadPage() {
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const submit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const form = new FormData(e.currentTarget);
    setLoading(true);
    try {
      const r = await fetch('/api/upload', { method: 'POST', body: form });
      setResult(await r.json());
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-3xl space-y-4">
      <h2 className="text-2xl font-semibold">Upload & index</h2>
      <p className="opacity-80 text-sm">
        Index architecture docs, terraform/k8s manifests, CI/CD configs, runbooks,
        service ownership docs.
      </p>
      <form onSubmit={submit} className="space-y-3">
        <input
          type="file"
          name="files"
          multiple
          className="block w-full text-sm file:rounded-lg file:border-0 file:bg-[var(--accent)] file:text-black file:px-4 file:py-2"
        />
        <button
          disabled={loading}
          className="rounded-lg px-4 py-2 bg-[var(--accent)] text-black font-semibold disabled:opacity-50"
        >
          {loading ? 'Indexing…' : 'Upload'}
        </button>
      </form>
      {result && (
        <pre className="rounded-xl bg-[var(--panel)] p-4 text-xs overflow-auto">
          {JSON.stringify(result, null, 2)}
        </pre>
      )}
    </div>
  );
}
