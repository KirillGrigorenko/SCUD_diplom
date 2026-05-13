'use client';

import { useEffect, useRef, useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { getPositions, createEmployee } from '@/utils/api';

const COUNTRIES = [
  'Россия','Беларусь','Казахстан','Украина','Узбекистан','Таджикистан','Кыргызстан',
  'Азербайджан','Армения','Грузия','Молдова','Туркменистан','Германия','Франция',
  'Италия','Испания','Польша','Чехия','Австрия','Швейцария','Нидерланды','Бельгия',
  'Швеция','Норвегия','Финляндия','Дания','Великобритания','США','Канада','Австралия',
  'Китай','Япония','Индия','Турция','Израиль','ОАЭ','Бразилия','Аргентина','Мексика',
  'Египет','Другое',
];

const LAST_NAMES = ['Иванов','Смирнов','Кузнецов','Попов','Васильев','Петров','Соколов','Михайлов','Новиков','Федоров','Морозов','Волков','Алексеев','Лебедев','Семенов'];
const FIRST_NAMES = ['Александр','Сергей','Дмитрий','Андрей','Алексей','Максим','Евгений','Иван','Михаил','Артем','Николай','Владимир'];
const MIDDLES = ['Александрович','Сергеевич','Дмитриевич','Андреевич','Алексеевич','Максимович','Иванович','Михайлович'];
const CITIES = ['Москва','Санкт-Петербург','Новосибирск','Екатеринбург','Казань','Нижний Новгород'];
const STREETS = ['Ленина','Пушкина','Гагарина','Мира','Советская','Кирова'];

function rnd<T>(arr: T[]): T { return arr[Math.floor(Math.random() * arr.length)]; }
function rndInt(min: number, max: number) { return Math.floor(Math.random() * (max - min + 1)) + min; }
function digits(n: number) { return Array.from({ length: n }, () => rndInt(0, 9)).join(''); }
function pad(n: number) { return String(n).padStart(2, '0'); }
function randDate() { return `${rndInt(2015, 2024)}-${pad(rndInt(1,12))}-${pad(rndInt(1,28))}`; }
function randSnils() { return `${digits(3)}-${digits(3)}-${digits(3)} ${digits(2)}`; }

const inputCls = 'w-full rounded-xl border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-100 outline-none focus:border-sky-500 focus:ring-1 focus:ring-sky-500/30';
const labelCls = 'flex flex-col gap-1';
const labelTextCls = 'text-xs text-slate-400';

export default function EmployeeNewPage() {
  const router = useRouter();
  const photoInputRef = useRef<HTMLInputElement>(null);

  const [positions, setPositions] = useState<any[]>([]);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [photoPreview, setPhotoPreview] = useState('');

  const [form, setForm] = useState({
    username: '', password: '',
    last_name: '', first_name: '', middle_name: '',
    hire_date: '', status: 'active',
    position_id: '',
    passport_series: '', passport_number: '', citizenship: '',
    address: '', snils: '', inn: '',
  });

  useEffect(() => { getPositions().then(setPositions); }, []);

  function set(field: string, value: string) {
    setForm((prev) => ({ ...prev, [field]: value }));
  }

  function fillRandom() {
    const ln = rnd(LAST_NAMES);
    const fn = rnd(FIRST_NAMES);
    const city = rnd(CITIES);
    const street = rnd(STREETS);
    setForm({
      username: (ln + fn[0]).toLowerCase().replace(/ё/g, 'e') + rndInt(10, 99),
      password: 'Pass' + digits(4) + '!',
      last_name: ln,
      first_name: fn,
      middle_name: rnd(MIDDLES),
      hire_date: randDate(),
      status: rnd(['active','active','active','blocked','fired']),
      position_id: positions.length ? String(positions[rndInt(0, positions.length - 1)].pk) : '',
      passport_series: digits(4),
      passport_number: digits(6),
      citizenship: 'Россия',
      address: `г. ${city}, ул. ${street}, д. ${rndInt(1,120)}, кв. ${rndInt(1,200)}`,
      snils: randSnils(),
      inn: digits(12),
    });
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

    const result = await createEmployee(fd);
    setSaving(false);
    if (result.error) { setError(result.error); return; }
    router.push(`/employees/${result.data.id}`);
  }

  return (
    <main className="min-h-screen bg-background text-slate-100">
      <div className="mx-auto max-w-5xl px-4 py-10 sm:px-6 lg:px-8">

        <div className="mb-8 flex items-center justify-between">
          <div>
            <p className="text-xs uppercase tracking-widest text-sky-400">Создание</p>
            <h1 className="mt-1 text-2xl font-semibold text-white">Новый сотрудник</h1>
          </div>
          <div className="flex gap-3">
            <button
              type="button"
              onClick={fillRandom}
              className="rounded-xl border border-slate-600 bg-slate-800 px-4 py-2 text-sm font-medium text-slate-200 hover:border-sky-500 hover:text-sky-400 transition"
            >
              Случайные данные
            </button>
            <Link href="/employees" className="rounded-xl border border-slate-700 bg-slate-900/80 px-4 py-2 text-sm font-medium text-slate-200 hover:border-slate-500">
              ← Назад
            </Link>
          </div>
        </div>

        {error && (
          <div className="mb-6 rounded-xl border border-rose-500/40 bg-rose-500/10 px-4 py-3 text-sm text-rose-300">{error}</div>
        )}

        <form onSubmit={handleSubmit}>
          <div className="grid gap-6 lg:grid-cols-[220px_1fr]">

            {/* Photo sidebar */}
            <div className="rounded-2xl border border-slate-700 bg-slate-950/70 p-5 flex flex-col items-center gap-4">
              <img
                src={photoPreview || 'https://via.placeholder.com/460x520/0b0f1a/ffffff?text=Фото'}
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

              {/* Учётная запись */}
              <section className="rounded-2xl border border-slate-700 bg-slate-950/70 p-5">
                <h2 className="mb-4 text-sm font-semibold uppercase tracking-widest text-slate-400">Учётная запись</h2>
                <div className="grid gap-4 sm:grid-cols-2">
                  <label className={labelCls}>
                    <span className={labelTextCls}>Логин <span className="text-rose-400">*</span></span>
                    <input className={inputCls} value={form.username} onChange={e => set('username', e.target.value)} required />
                  </label>
                  <label className={labelCls}>
                    <span className={labelTextCls}>Пароль <span className="text-rose-400">*</span></span>
                    <input className={inputCls} type="text" value={form.password} onChange={e => set('password', e.target.value)} required />
                  </label>
                </div>
              </section>

              {/* Основные данные */}
              <section className="rounded-2xl border border-slate-700 bg-slate-950/70 p-5">
                <h2 className="mb-4 text-sm font-semibold uppercase tracking-widest text-slate-400">Основные данные</h2>
                <div className="grid gap-4 sm:grid-cols-2">
                  <label className={labelCls}>
                    <span className={labelTextCls}>Фамилия <span className="text-rose-400">*</span></span>
                    <input className={inputCls} value={form.last_name} onChange={e => set('last_name', e.target.value)} required />
                  </label>
                  <label className={labelCls}>
                    <span className={labelTextCls}>Имя <span className="text-rose-400">*</span></span>
                    <input className={inputCls} value={form.first_name} onChange={e => set('first_name', e.target.value)} required />
                  </label>
                  <label className={labelCls}>
                    <span className={labelTextCls}>Отчество</span>
                    <input className={inputCls} value={form.middle_name} onChange={e => set('middle_name', e.target.value)} />
                  </label>
                  <label className={labelCls}>
                    <span className={labelTextCls}>Дата найма <span className="text-rose-400">*</span></span>
                    <input className={inputCls} type="date" value={form.hire_date} onChange={e => set('hire_date', e.target.value)} required />
                  </label>
                  <label className={labelCls}>
                    <span className={labelTextCls}>Статус</span>
                    <select className={inputCls} value={form.status} onChange={e => set('status', e.target.value)}>
                      <option value="active">Активен</option>
                      <option value="fired">Уволен</option>
                      <option value="blocked">Заблокирован</option>
                    </select>
                  </label>
                  <label className={labelCls}>
                    <span className={labelTextCls}>Должность</span>
                    <select className={inputCls} value={form.position_id} onChange={e => set('position_id', e.target.value)}>
                      <option value="">— Не выбрана —</option>
                      {positions.map(p => (
                        <option key={p.pk} value={String(p.pk)}>{p.label}</option>
                      ))}
                    </select>
                  </label>
                </div>
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

              <div className="flex justify-end gap-3">
                <Link href="/employees" className="rounded-xl border border-slate-700 bg-slate-900/80 px-5 py-2.5 text-sm font-medium text-slate-200 hover:border-slate-500">
                  Отмена
                </Link>
                <button
                  type="submit"
                  disabled={saving}
                  className="rounded-xl bg-sky-600 px-5 py-2.5 text-sm font-semibold text-white hover:bg-sky-500 disabled:opacity-50 transition"
                >
                  {saving ? 'Создание…' : 'Создать сотрудника'}
                </button>
              </div>
            </div>
          </div>
        </form>
      </div>
    </main>
  );
}
