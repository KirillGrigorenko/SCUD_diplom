'use client';

import { useEffect, useRef, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { getEmployee, getPositions, updateEmployee, getBiometricStatus, registerBiometric } from '../../../../../utils/api';
import FaceCapture, { CameraSource } from '../../../../../components/FaceCapture';

const COUNTRIES = [
  'Россия','Беларусь','Казахстан','Украина','Узбекистан','Таджикистан','Кыргызстан',
  'Азербайджан','Армения','Грузия','Молдова','Туркменистан','Германия','Франция',
  'Италия','Испания','Польша','Чехия','Австрия','Швейцария','Нидерланды','Бельгия',
  'Швеция','Норвегия','Финляндия','Дания','Великобритания','США','Канада','Австралия',
  'Китай','Япония','Индия','Турция','Израиль','ОАЭ','Бразилия','Аргентина','Мексика',
  'Египет','Другое',
];

const inputCls = 'w-full rounded-xl border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-100 outline-none focus:border-sky-500 focus:ring-1 focus:ring-sky-500/30';
const labelCls = 'flex flex-col gap-1';
const labelTextCls = 'text-xs text-slate-400';

export default function EmployeeEditPage() {
  const params = useParams();
  const router = useRouter();
  const id = Array.isArray(params?.id) ? params.id[0] : params?.id;

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [photoPreview, setPhotoPreview] = useState('');
  const [positions, setPositions] = useState<any[]>([]);
  const photoInputRef = useRef<HTMLInputElement>(null);

  // биометрия
  const [bioRegistered, setBioRegistered] = useState(false);
  const [bioRegisteredAt, setBioRegisteredAt] = useState<string | null>(null);
  const [bioCapture, setBioCapture] = useState<{ blob: Blob; source: CameraSource } | null>(null);
  const [bioSaving, setBioSaving] = useState(false);
  const [bioMsg, setBioMsg] = useState('');
  const [bioError, setBioError] = useState('');

  const [form, setForm] = useState({
    last_name: '', first_name: '', middle_name: '',
    hire_date: '', status: 'active',
    position_id: '',
    passport_series: '', passport_number: '', citizenship: '',
    address: '', snils: '', inn: '',
  });

  useEffect(() => {
    if (!id) return;
    Promise.all([getEmployee(id), getPositions(), getBiometricStatus(Number(id))]).then(([emp, pos, bio]) => {
      if (emp) {
        setForm({
          last_name: emp.last_name ?? '',
          first_name: emp.first_name ?? '',
          middle_name: emp.middle_name ?? '',
          hire_date: emp.hire_date ?? '',
          status: emp.status ?? 'active',
          position_id: emp.position_id ? String(emp.position_id) : '',
          passport_series: emp.employee_card?.passport_series ?? '',
          passport_number: emp.employee_card?.passport_number ?? '',
          citizenship: emp.employee_card?.citizenship ?? '',
          address: emp.employee_card?.address ?? '',
          snils: emp.employee_card?.snils ?? '',
          inn: emp.employee_card?.inn ?? '',
        });
        setPhotoPreview(emp.photo_url ?? '');
      }
      if (bio) {
        setBioRegistered(bio.registered);
        setBioRegisteredAt(bio.registered_at);
      }
      setPositions(pos);
      setLoading(false);
    });
  }, [id]);

  async function handleBioRegister() {
    if (!bioCapture || !id) return;
    setBioSaving(true);
    setBioError('');
    setBioMsg('');
    const result = await registerBiometric(Number(id), bioCapture.blob);
    setBioSaving(false);
    if (result.success) {
      setBioRegistered(true);
      setBioRegisteredAt(result.registeredAt ?? null);
      setBioMsg('Биометрия зарегистрирована успешно.');
      setBioCapture(null);
    } else {
      setBioError(result.error ?? 'Ошибка регистрации');
    }
  }

  function set(field: string, value: string) {
    setForm((prev) => ({ ...prev, [field]: value }));
  }

  function handlePhotoChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (ev) => setPhotoPreview(ev.target?.result as string);
    reader.readAsDataURL(file);
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (form.inn && !/^\d{12}$/.test(form.inn)) {
      setError('ИНН должен содержать ровно 12 цифр.');
      return;
    }
    setSaving(true);
    setError('');

    const fd = new FormData();
    Object.entries(form).forEach(([k, v]) => fd.append(k, v));
    const file = photoInputRef.current?.files?.[0];
    if (file) fd.append('photo', file);

    const result = await updateEmployee(id!, fd);
    setSaving(false);
    if (result.error) { setError(result.error); return; }
    router.push(`/employees/${id}`);
  }

  if (loading) {
    return (
      <main className="min-h-screen bg-background text-slate-100 flex items-center justify-center">
        <p className="text-slate-400">Загрузка…</p>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-background text-slate-100">
      <div className="mx-auto max-w-5xl px-4 py-10 sm:px-6 lg:px-8">

        <div className="mb-8 flex items-center justify-between">
          <div>
            <p className="text-xs uppercase tracking-widest text-sky-400">Редактирование</p>
            <h1 className="mt-1 text-2xl font-semibold text-white">{form.last_name} {form.first_name}</h1>
          </div>
          <Link href={`/employees/${id}`} className="rounded-xl border border-slate-700 bg-slate-900/80 px-4 py-2 text-sm font-medium text-slate-200 hover:border-slate-500">
            ← Назад
          </Link>
        </div>

        {error && (
          <div className="mb-6 rounded-xl border border-rose-500/40 bg-rose-500/10 px-4 py-3 text-sm text-rose-300">{error}</div>
        )}

        <form onSubmit={handleSubmit}>
          <div className="grid gap-6 lg:grid-cols-[220px_1fr]">

            {/* Photo sidebar */}
            <div className="rounded-2xl border border-slate-700 bg-slate-950/70 p-5 flex flex-col items-center gap-4">
              <img
                src={photoPreview || 'https://via.placeholder.com/460x520/0b0f1a/ffffff?text=Нет+фото'}
                alt="Фото"
                className="w-40 h-44 rounded-2xl object-cover ring-1 ring-slate-700"
              />
              <button
                type="button"
                onClick={() => photoInputRef.current?.click()}
                className="w-full rounded-xl border border-slate-600 bg-slate-800 px-3 py-2 text-xs font-medium text-slate-200 hover:border-sky-500 hover:text-sky-400 transition"
              >
                Загрузить фото
              </button>
              <input ref={photoInputRef} type="file" accept="image/*" className="hidden" onChange={handlePhotoChange} />
              <p className="text-xs text-slate-500 text-center">JPEG или PNG, до 10 МБ</p>
            </div>

            {/* Fields */}
            <div className="space-y-5">

              {/* Основные данные */}
              <section className="rounded-2xl border border-slate-700 bg-slate-950/70 p-5">
                <h2 className="mb-4 text-sm font-semibold uppercase tracking-widest text-slate-400">Основные данные</h2>
                <div className="grid gap-4 sm:grid-cols-2">
                  <label className={labelCls}>
                    <span className={labelTextCls}>Фамилия</span>
                    <input className={inputCls} value={form.last_name} onChange={e => set('last_name', e.target.value)} required />
                  </label>
                  <label className={labelCls}>
                    <span className={labelTextCls}>Имя</span>
                    <input className={inputCls} value={form.first_name} onChange={e => set('first_name', e.target.value)} required />
                  </label>
                  <label className={labelCls}>
                    <span className={labelTextCls}>Отчество</span>
                    <input className={inputCls} value={form.middle_name} onChange={e => set('middle_name', e.target.value)} />
                  </label>
                  <label className={labelCls}>
                    <span className={labelTextCls}>Дата найма</span>
                    <input className={inputCls} type="date" value={form.hire_date} onChange={e => set('hire_date', e.target.value)} required />
                  </label>
                  <label className={labelCls + ' sm:col-span-2'}>
                    <span className={labelTextCls}>Статус</span>
                    <select className={inputCls} value={form.status} onChange={e => set('status', e.target.value)}>
                      <option value="active">Активен</option>
                      <option value="fired">Уволен</option>
                      <option value="blocked">Заблокирован</option>
                    </select>
                  </label>
                </div>
              </section>

              {/* Должность */}
              <section className="rounded-2xl border border-slate-700 bg-slate-950/70 p-5">
                <h2 className="mb-4 text-sm font-semibold uppercase tracking-widest text-slate-400">Должность</h2>
                <label className={labelCls}>
                  <span className={labelTextCls}>Должность</span>
                  <select className={inputCls} value={form.position_id} onChange={e => set('position_id', e.target.value)}>
                    <option value="">— Не выбрана —</option>
                    {positions.map(p => (
                      <option key={p.pk} value={String(p.pk)}>{p.label}</option>
                    ))}
                  </select>
                </label>
              </section>

              {/* Паспортные данные */}
              <section className="rounded-2xl border border-slate-700 bg-slate-950/70 p-5">
                <h2 className="mb-4 text-sm font-semibold uppercase tracking-widest text-slate-400">Паспортные данные</h2>
                <div className="grid gap-4 sm:grid-cols-2">
                  <label className={labelCls}>
                    <span className={labelTextCls}>Серия паспорта</span>
                    <input className={inputCls} value={form.passport_series} onChange={e => set('passport_series', e.target.value)} />
                  </label>
                  <label className={labelCls}>
                    <span className={labelTextCls}>Номер паспорта</span>
                    <input className={inputCls} value={form.passport_number} onChange={e => set('passport_number', e.target.value)} />
                  </label>
                  <label className={labelCls}>
                    <span className={labelTextCls}>Гражданство</span>
                    <select className={inputCls} value={form.citizenship} onChange={e => set('citizenship', e.target.value)}>
                      <option value="">— Не выбрано —</option>
                      {COUNTRIES.map(c => <option key={c} value={c}>{c}</option>)}
                    </select>
                  </label>
                  <label className={labelCls}>
                    <span className={labelTextCls}>СНИЛС</span>
                    <input className={inputCls} value={form.snils} onChange={e => set('snils', e.target.value)} />
                  </label>
                  <label className={labelCls}>
                    <span className={labelTextCls}>ИНН (12 цифр)</span>
                    <input
                      className={inputCls + (form.inn && !/^\d{12}$/.test(form.inn) ? ' border-rose-500' : '')}
                      value={form.inn}
                      onChange={e => set('inn', e.target.value)}
                      maxLength={12}
                    />
                    {form.inn && !/^\d{12}$/.test(form.inn) && (
                      <span className="text-xs text-rose-400">Введите ровно 12 цифр</span>
                    )}
                  </label>
                  <label className={labelCls + ' sm:col-span-2'}>
                    <span className={labelTextCls}>Адрес прописки</span>
                    <input className={inputCls} value={form.address} onChange={e => set('address', e.target.value)} />
                  </label>
                </div>
              </section>

              {/* Биометрия */}
              <section className="rounded-2xl border border-slate-700 bg-slate-950/70 p-5">
                <h2 className="mb-4 text-sm font-semibold uppercase tracking-widest text-slate-400">Биометрия (лицо)</h2>

                <div className="mb-4 flex items-center gap-3">
                  <span className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-medium ${
                    bioRegistered ? 'bg-emerald-500/15 text-emerald-400' : 'bg-slate-700 text-slate-400'
                  }`}>
                    <span className={`h-2 w-2 rounded-full ${bioRegistered ? 'bg-emerald-400' : 'bg-slate-500'}`} />
                    {bioRegistered ? 'Зарегистрировано' : 'Не зарегистрировано'}
                  </span>
                  {bioRegisteredAt && (
                    <span className="text-xs text-slate-500">
                      {new Date(bioRegisteredAt).toLocaleDateString('ru-RU')}
                    </span>
                  )}
                </div>

                {bioMsg && (
                  <p className="mb-3 text-xs text-emerald-400">{bioMsg}</p>
                )}
                {bioError && (
                  <p className="mb-3 text-xs text-rose-400">{bioError}</p>
                )}

                <FaceCapture
                  disabled={bioSaving}
                  onCapture={(blob, source) => setBioCapture({ blob, source })}
                  onError={(msg) => setBioError(msg)}
                />

                {bioCapture && (
                  <button
                    type="button"
                    onClick={handleBioRegister}
                    disabled={bioSaving}
                    className="mt-3 w-full rounded-xl bg-emerald-600 px-4 py-2 text-sm font-semibold text-white hover:bg-emerald-500 disabled:opacity-50 transition"
                  >
                    {bioSaving ? 'Регистрируем…' : bioRegistered ? 'Перерегистрировать лицо' : 'Зарегистрировать лицо'}
                  </button>
                )}
              </section>

              <div className="flex justify-end gap-3">
                <Link href={`/employees/${id}`} className="rounded-xl border border-slate-700 bg-slate-900/80 px-5 py-2.5 text-sm font-medium text-slate-200 hover:border-slate-500">
                  Отмена
                </Link>
                <button
                  type="submit"
                  disabled={saving}
                  className="rounded-xl bg-sky-600 px-5 py-2.5 text-sm font-semibold text-white hover:bg-sky-500 disabled:opacity-50 transition"
                >
                  {saving ? 'Сохранение…' : 'Сохранить изменения'}
                </button>
              </div>
            </div>
          </div>
        </form>
      </div>
    </main>
  );
}
