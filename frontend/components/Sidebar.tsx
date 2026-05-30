import Link from 'next/link';

const links = [
  { href: '/', label: 'Home' },
  { href: '/chat', label: 'Chat' },
  { href: '/agents', label: 'Agents' },
  { href: '/upload', label: 'Upload' },
  { href: '/search', label: 'Search' },
  { href: '/incidents', label: 'Incidents' },
  { href: '/prs', label: 'PRs' },
];

export function Sidebar() {
  return (
    <aside className="w-56 shrink-0 border-r border-white/10 p-5">
      <div className="font-bold text-xl mb-6">AgentForgeOps</div>
      <nav className="space-y-1">
        {links.map((l) => (
          <Link
            key={l.href}
            href={l.href}
            className="block rounded-md px-3 py-2 hover:bg-white/5"
          >
            {l.label}
          </Link>
        ))}
      </nav>
    </aside>
  );
}
