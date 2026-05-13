'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { getMe, logout } from '@/utils/api';

type Me = { username: string; is_admin: boolean; employee_id: number | null };

export default function Topbar() {
  const pathname = usePathname();
  const [me, setMe] = useState<Me | null>(null);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    getMe()
      .then((data) => { if (data) setMe(data); })
      .catch(() => {})
      .finally(() => setReady(true));
  }, []);

  const isAdmin = me?.is_admin ?? false;

  const navLinks = [
    { href: '/employees', label: 'Сотрудники' },
    { href: '/history', label: 'История' },
  ];

  return (
    <header className="sticky top-0 z-50 border-b border-slate-800 bg-slate-950/90 backdrop-blur-md">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-3 sm:px-6 lg:px-8">

        <div className="flex items-center gap-6">
          <Link href="/employees" className="flex items-center gap-2 font-semibold tracking-wide text-white">
            <svg className="h-5 w-5 text-sky-400" viewBox="0 0 24 24" fill="none">
              <path d="M12 2L3 7v10c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V7l-9-5z" fill="currentColor"/>
              <path d="M9 12l2 2 4-4" stroke="#0f172a" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
            СКУД
          </Link>

          <nav className="hidden items-center gap-1 sm:flex">
            {ready ? navLinks.map((link) => {
              const active = pathname === link.href || pathname.startsWith(link.href + '/');
              return (
                <Link
                  key={link.href}
                  href={link.href}
                  className={`rounded-lg px-3 py-1.5 text-sm font-medium transition-colors ${
                    active ? 'bg-slate-800 text-white' : 'text-slate-400 hover:bg-slate-800/60 hover:text-slate-200'
                  }`}
                >
                  {link.label}
                </Link>
              );
            }) : (
              <span className="h-5 w-32 animate-pulse rounded bg-slate-800" />
            )}
          </nav>
        </div>

        <div className="flex items-center gap-3">
          {me && <span className="hidden text-sm text-slate-400 sm:block">{me.username}</span>}
          <button
            type="button"
            onClick={() => logout()}
            className="rounded-lg border border-slate-700 bg-slate-900 px-3 py-1.5 text-sm font-medium text-slate-300 transition-colors hover:border-slate-500 hover:text-white"
          >
            Выйти
          </button>
        </div>
      </div>
    </header>
  );
}
