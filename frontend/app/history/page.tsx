'use client';

import { useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import { getAllHistory } from '../../../utils/api';

const METHOD_LABELS: Record<string, string> = {
  biometric: 'Биометрия',
  password: 'Пароль',
};

const inputCls =
  'w-full rounded-xl border border-slate-700 bg-slate-900/90 px-3 py-2 text-sm text-slate-100 outline-none focus:border-sky-500 focus:ring-1 focus:ring-sky-500/20';

export default function HistoryPage() {
  const [rows, setRows] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const [filterEmployee, setFilterEmployee] = useState('');
  const [filterResult, setFilterResult] = useState('');
  const [filterDateFrom, setFilterDateFrom] = useState('');
  const [filterDateTo, setFilterDateTo] = useState('');

  function load() {
    setLoading(true);
    getAllHistory({
      employee: filterEmployee || undefined,
      result: filterResult || undefined,
      date_from: filterDateFrom || undefined,
      date_to: filterDateTo || undefined,
    })
      .then((data) => { setRows(data); setError(''); })
      .catch(() => setError('Не удалось загрузить историю.'))
      .finally(() => setLoading(false));
  }

  useEffect(() => { load(); }, []);

  const stats = useMemo(() => ({
    total: rows.length,
    allowed: rows.filter((r) => r.result === 'allowed').length,
    denied: rows.filter((r) => r.result === 'denied').length,
  }), [rows]);

  return (
    <main className="min-h-screen bg-background text-slate-100">
      <div className="mx-auto max-w-7xl px-4 py-10 sm:px-6 lg:px-8">

        {/* Header */}
        <header className="mb-8 flex flex-col gap-4 rounded-[2rem] border border-slate-700 bg-slate-950/70 p-8 shadow-2xl sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p className="text-sm uppercase tracking-[0.3em] text-sky-400">Система доступа</p>
            <h1 className="mt-3 text-3xl font-semibold text-white">История всех проходов</h1>
            <p className="mt-2 text-slate-400">Журнал событий контроля доступа.</p>
          </div>
          <div />
        </header>

        {/* Stats */}
        {!loading && !error && (
          <div className="mb-6 grid grid-cols-3 gap-4">
            <div className="rounded-2xl border border-slate-700 bg-slate-950/70 p-5">
              <p className="text-xs text-slate-400">Всего событий</p>
              <p className="mt-1 text-2xl font-semibold text-white">{stats.total}</p>
            </div>
            <div className="rounded-2xl border border-slate-700 bg-slate-950/70 p-5">
              <p className="text-xs text-slate-400">Разрешено</p>
              <p className="mt-1 text-2xl font-semibold text-emerald-400">{stats.allowed}</p>
            </div>
            <div className="rounded-2xl border border-slate-700 bg-slate-950/70 p-5">
              <p className="text-xs text-slate-400">Отказано</p>
              <p className="mt-1 text-2xl font-semibold text-rose-400">{stats.denied}</p>
            </div>
          </div>
        )}

        {/* Filters */}
        <section className="mb-6 rounded-[2rem] border border-slate-700 bg-slate-950/70 p-6">
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <div className="flex flex-col gap-1">
              <span className="text-xs text-slate-400">Сотрудник</span>
              <input
                className={inputCls}
                placeholder="ФИО"
                value={filterEmployee}
                onChange={(e) => setFilterEmployee(e.target.value)}
              />
            </div>
            <div className="flex flex-col gap-1">
              <span className="text-xs text-slate-400">Результат</span>
              <select
                className={inputCls}
                value={filterResult}
                onChange={(e) => setFilterResult(e.target.value)}
              >
                <option value="">Все</option>
                <option value="allowed">Разрешён</option>
                <option value="denied">Отказано</option>
              </select>
            </div>
            <div className="flex flex-col gap-1">
              <span className="text-xs text-slate-400">Дата с</span>
              <input
                className={inputCls}
                type="date"
                value={filterDateFrom}
                onChange={(e) => setFilterDateFrom(e.target.value)}
              />
            </div>
            <div className="flex flex-col gap-1">
              <span className="text-xs text-slate-400">Дата по</span>
              <input
                className={inputCls}
                type="date"
                value={filterDateTo}
                onChange={(e) => setFilterDateTo(e.target.value)}
              />
            </div>
          </div>
          <div className="mt-4 flex gap-3">
            <button
              type="button"
              onClick={load}
              className="rounded-xl bg-sky-600 px-5 py-2 text-sm font-semibold text-white hover:bg-sky-500 transition"
            >
              Применить
            </button>
            <button
              type="button"
              onClick={() => {
                setFilterEmployee('');
                setFilterResult('');
                setFilterDateFrom('');
                setFilterDateTo('');
                getAllHistory().then((data) => { setRows(data); }).catch(() => {});
              }}
              className="rounded-xl border border-slate-700 bg-slate-900 px-5 py-2 text-sm font-medium text-slate-300 hover:border-slate-500 transition"
            >
              Сбросить
            </button>
          </div>
        </section>

        {/* Table */}
        {loading ? (
          <div className="rounded-[2rem] border border-slate-700 bg-slate-950/70 p-10 text-center text-slate-300">
            Загрузка…
          </div>
        ) : error ? (
          <div className="rounded-[2rem] border border-rose-500 bg-rose-500/10 p-10 text-center text-rose-200">
            {error}
          </div>
        ) : rows.length === 0 ? (
          <div className="rounded-[2rem] border border-slate-700 bg-slate-950/70 p-10 text-center text-slate-300">
            Нет событий по выбранным фильтрам.
          </div>
        ) : (
          <div className="rounded-[2rem] border border-slate-700 bg-slate-950/70 shadow-xl overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-slate-700 bg-slate-900/60 text-left text-xs uppercase tracking-wider text-slate-400">
                    <th className="px-5 py-4">Дата и время</th>
                    <th className="px-5 py-4">Сотрудник</th>
                    <th className="px-5 py-4">Точка доступа</th>
                    <th className="px-5 py-4">Метод</th>
                    <th className="px-5 py-4">Результат</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800">
                  {rows.map((h) => (
                    <tr key={h.id} className="hover:bg-slate-900/40 transition-colors">
                      <td className="px-5 py-3.5 text-slate-400 tabular-nums whitespace-nowrap">
                        {new Date(h.datetime).toLocaleString('ru-RU')}
                      </td>
                      <td className="px-5 py-3.5">
                        <Link
                          href={`/employees/${h.employee_id}`}
                          className="font-medium text-slate-100 hover:text-sky-400 transition-colors"
                        >
                          {h.employee_name}
                        </Link>
                      </td>
                      <td className="px-5 py-3.5 text-slate-300">{h.access_point}</td>
                      <td className="px-5 py-3.5 text-slate-400">
                        {METHOD_LABELS[h.method] ?? h.method}
                      </td>
                      <td className="px-5 py-3.5">
                        <span className={`inline-flex rounded-full px-2.5 py-0.5 text-xs font-medium ${
                          h.result === 'allowed'
                            ? 'bg-emerald-500/15 text-emerald-400'
                            : 'bg-rose-500/15 text-rose-400'
                        }`}>
                          {h.result === 'allowed' ? 'Разрешён' : 'Отказано'}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="border-t border-slate-700 px-5 py-3 text-xs text-slate-500">
              Показано {rows.length} записей (максимум 500)
            </div>
          </div>
        )}
      </div>
    </main>
  );
}
