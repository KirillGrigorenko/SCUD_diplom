'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { getEmployee, getMe, logout } from '../../../../utils/api';
import StatusPill from '../../../../components/StatusPill';

export default function EmployeeDetailPage() {
  const params = useParams();
  const rawId = params?.id;
  const id = Array.isArray(rawId) ? rawId[0] : rawId;

  const [employee, setEmployee] = useState<any | null>(null);
  const [isAdmin, setIsAdmin] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!id) return;
    setLoading(true);
    Promise.all([getEmployee(id), getMe()])
      .then(([emp, me]) => {
        if (emp) setEmployee(emp);
        if (me) setIsAdmin(me.is_admin);
      })
      .catch(() => setError('Не удалось загрузить данные сотрудника.'))
      .finally(() => setLoading(false));
  }, [id]);

  if (!id) return null;

  return (
    <main className="min-h-screen bg-background text-slate-100">
      <div className="mx-auto max-w-6xl px-4 py-10 sm:px-6 lg:px-8">
        <div className="mb-8 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p className="text-sm uppercase tracking-[0.3em] text-sky-400">Детали сотрудника</p>
            <h1 className="mt-3 text-3xl font-semibold text-white">Карточка сотрудника</h1>
          </div>
          <div className="flex flex-wrap gap-3">
            {isAdmin && employee && (
              <Link
                href={`/employees/${id}/edit`}
                className="inline-flex items-center rounded-2xl border border-sky-600 bg-sky-600/10 px-4 py-3 text-sm font-semibold text-sky-300 transition hover:bg-sky-600 hover:text-white"
              >
                Редактировать
              </Link>
            )}
            <Link
              href="/employees"
              className="inline-flex items-center rounded-2xl border border-slate-700 bg-slate-900/80 px-4 py-3 text-sm font-semibold text-slate-100 transition hover:border-slate-500"
            >
              Назад к списку
            </Link>
            <button
              type="button"
              onClick={() => logout()}
              className="inline-flex items-center rounded-2xl border border-slate-700 bg-slate-900/80 px-4 py-3 text-sm font-semibold text-slate-100 transition hover:border-slate-500"
            >
              Выйти
            </button>
          </div>
        </div>

        {loading ? (
          <div className="rounded-[2rem] border border-slate-700 bg-slate-950/70 p-10 text-center text-slate-300">
            Загрузка данных…
          </div>
        ) : error ? (
          <div className="rounded-[2rem] border border-rose-500 bg-rose-500/10 p-10 text-center text-rose-200">
            {error}
          </div>
        ) : employee ? (
          <div className="grid gap-8 lg:grid-cols-[360px_1fr]">
            <section className="rounded-[2rem] border border-slate-700 bg-slate-950/70 p-6 shadow-xl shadow-slate-950/20">
              <div className="space-y-5 text-center">
                <img
                  src={employee.photo_url}
                  alt={employee.full_name}
                  className="mx-auto h-48 w-48 rounded-[2rem] object-cover ring-1 ring-slate-700"
                />
                <div>
                  <h2 className="text-2xl font-semibold text-white">{employee.full_name}</h2>
                  <p className="mt-2 text-sm text-slate-400">Нанят: {employee.hire_date}</p>
                </div>
                <StatusPill status={employee.status} />
              </div>
            </section>

            <section className="rounded-[2rem] border border-slate-700 bg-slate-950/70 p-6 shadow-xl shadow-slate-950/20">
              <h2 className="text-xl font-semibold text-white">Основная информация</h2>
              <div className="mt-6 grid gap-4 sm:grid-cols-2">
                <InfoCard label="Фамилия" value={employee.last_name} />
                <InfoCard label="Имя" value={employee.first_name} />
                <InfoCard label="Отчество" value={employee.middle_name || '—'} />
                <InfoCard label="Статус" value={employee.status} />
                {employee.position && <InfoCard label="Должность" value={employee.position} />}
                {employee.department && <InfoCard label="Отдел" value={employee.department} />}
              </div>

              {employee.employee_card && (
                <>
                  <h2 className="mt-8 text-xl font-semibold text-white">Паспортные данные</h2>
                  <div className="mt-4 grid gap-4 sm:grid-cols-2">
                    {employee.employee_card.passport_series && (
                      <InfoCard
                        label="Серия и номер паспорта"
                        value={`${employee.employee_card.passport_series} ${employee.employee_card.passport_number}`}
                      />
                    )}
                    {employee.employee_card.citizenship && (
                      <InfoCard label="Гражданство" value={employee.employee_card.citizenship} />
                    )}
                    {employee.employee_card.snils && (
                      <InfoCard label="СНИЛС" value={employee.employee_card.snils} />
                    )}
                    {employee.employee_card.inn && (
                      <InfoCard label="ИНН" value={employee.employee_card.inn} />
                    )}
                    {employee.employee_card.address && (
                      <InfoCard label="Адрес" value={employee.employee_card.address} full />
                    )}
                  </div>
                </>
              )}
            </section>
          </div>
        ) : (
          <div className="rounded-[2rem] border border-slate-700 bg-slate-950/70 p-10 text-center text-slate-300">
            Сотрудник не найден.
          </div>
        )}
      </div>
    </main>
  );
}

function InfoCard({ label, value, full }: { label: string; value: string; full?: boolean }) {
  return (
    <div className={`rounded-3xl bg-slate-900/80 p-5${full ? ' col-span-full' : ''}`}>
      <p className="text-sm text-slate-400">{label}</p>
      <p className="mt-2 text-base font-medium text-white">{value}</p>
    </div>
  );
}
