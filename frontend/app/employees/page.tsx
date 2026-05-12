'use client';

import { useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import { getEmployees, getMe } from '../../../utils/api';
import EmployeeCard from '../../../components/EmployeeCard';
import CustomSelect from '../../../components/CustomSelect';

const STATUS_OPTIONS = [
  { value: '', label: 'Все статусы' },
  { value: 'active', label: 'Активен' },
  { value: 'blocked', label: 'Заблокирован' },
  { value: 'fired', label: 'Уволен' },
];

export default function EmployeesPage() {
  const [employees, setEmployees] = useState<any[]>([]);
  const [isAdmin, setIsAdmin] = useState(false);
  const [query, setQuery] = useState('');
  const [department, setDepartment] = useState('');
  const [status, setStatus] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    setLoading(true);
    Promise.all([getEmployees(), getMe()])
      .then(([data, me]) => {
        setEmployees(data);
        if (me) setIsAdmin(me.is_admin);
        setError('');
      })
      .catch(() => setError('Не удалось загрузить список сотрудников.'))
      .finally(() => setLoading(false));
  }, []);

  const filteredEmployees = useMemo(() => {
    return employees.filter((employee) => {
      const fullName = employee.full_name?.toLowerCase() ?? '';
      const departmentName = employee.department?.toLowerCase() ?? '';
      const statusValue = employee.status?.toLowerCase() ?? '';

      const matchesQuery = query ? fullName.includes(query.toLowerCase()) : true;
      const matchesDepartment = department ? departmentName.includes(department.toLowerCase()) : true;
      const matchesStatus = status ? statusValue === status : true;

      return matchesQuery && matchesDepartment && matchesStatus;
    });
  }, [employees, query, department, status]);

  const stats = useMemo(() => ({
    total: employees.length,
    active: employees.filter(e => e.status === 'active').length,
    blocked: employees.filter(e => e.status === 'blocked').length,
    fired: employees.filter(e => e.status === 'fired').length,
  }), [employees]);

  return (
    <main className="min-h-screen bg-background text-slate-100">
      <div className="mx-auto max-w-7xl px-4 py-10 sm:px-6 lg:px-8">

        {/* Header */}
        <header className="mb-8 flex flex-col gap-4 rounded-[2rem] border border-slate-700 bg-slate-950/70 p-8 shadow-2xl shadow-slate-950/30 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p className="text-sm uppercase tracking-[0.3em] text-sky-400">Сотрудники</p>
            <h1 className="mt-3 text-3xl font-semibold text-white">Обзор сотрудников</h1>
            <p className="mt-2 text-slate-400">Список всех сотрудников и их статусов.</p>
          </div>
          {isAdmin && (
            <Link
              href="/employees/new"
              className="inline-flex items-center gap-2 rounded-2xl border border-sky-600 bg-sky-600/10 px-4 py-3 text-sm font-semibold text-sky-300 transition hover:bg-sky-600 hover:text-white"
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
              Новый сотрудник
            </Link>
          )}
        </header>

        {/* Stats */}
        {!loading && !error && (
          <div className="mb-6 grid grid-cols-2 gap-4 sm:grid-cols-4">
            <StatCard label="Всего" value={stats.total} />
            <StatCard label="Активных" value={stats.active} color="text-emerald-400" />
            <StatCard label="Заблокированных" value={stats.blocked} color="text-yellow-400" />
            <StatCard label="Уволенных" value={stats.fired} color="text-rose-400" />
          </div>
        )}

        {/* Filters */}
        <section className="mb-8 space-y-4 rounded-[2rem] border border-slate-700 bg-slate-950/70 p-6 shadow-xl shadow-slate-950/20">
          <div className="grid items-end gap-4 sm:grid-cols-3">
            <div className="flex flex-col">
              <span className="mb-2 text-sm text-slate-300">Поиск по ФИО</span>
              <input
                className="w-full rounded-2xl border border-slate-700 bg-slate-900/90 px-4 py-3 text-slate-100 outline-none focus:border-sky-500 focus:ring-2 focus:ring-sky-500/20"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Например, Иванов"
              />
            </div>
            <div className="flex flex-col">
              <span className="mb-2 text-sm text-slate-300">Отдел</span>
              <input
                className="w-full rounded-2xl border border-slate-700 bg-slate-900/90 px-4 py-3 text-slate-100 outline-none focus:border-sky-500 focus:ring-2 focus:ring-sky-500/20"
                value={department}
                onChange={(e) => setDepartment(e.target.value)}
                placeholder="Например, IT"
              />
            </div>
            <div className="flex flex-col">
              <span className="mb-2 text-sm text-slate-300">Статус</span>
              <CustomSelect value={status} onChange={setStatus} options={STATUS_OPTIONS} />
            </div>
          </div>
        </section>

        {/* List */}
        {loading ? (
          <div className="rounded-[2rem] border border-slate-700 bg-slate-950/70 p-10 text-center text-slate-300">Загрузка сотрудников…</div>
        ) : error ? (
          <div className="rounded-[2rem] border border-rose-500 bg-rose-500/10 p-10 text-center text-rose-200">{error}</div>
        ) : filteredEmployees.length === 0 ? (
          <div className="rounded-[2rem] border border-slate-700 bg-slate-950/70 p-10 text-center text-slate-300">Ничего не найдено по заданным фильтрам.</div>
        ) : (
          <div className="grid gap-6 lg:grid-cols-2">
            {filteredEmployees.map((employee) => (
              <EmployeeCard key={employee.id} employee={employee} />
            ))}
          </div>
        )}
      </div>
    </main>
  );
}

function StatCard({ label, value, color = 'text-white' }: { label: string; value: number; color?: string }) {
  return (
    <div className="rounded-2xl border border-slate-700 bg-slate-950/70 p-5">
      <p className="text-xs text-slate-400">{label}</p>
      <p className={`mt-1 text-2xl font-semibold ${color}`}>{value}</p>
    </div>
  );
}
