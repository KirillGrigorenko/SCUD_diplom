'use client';

import { FormEvent, useState } from 'react';
import { useRouter } from 'next/navigation';
import { login, loginWithFace, getMe } from '@/utils/api';
import FaceCapture, { CameraSource } from '@/components/FaceCapture';

type Tab = 'password' | 'face';

export default function LoginPage() {
  const router = useRouter();

  // общее
  const [tab, setTab] = useState<Tab>('password');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [warning, setWarning] = useState('');

  // пароль
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [remember, setRemember] = useState(false);

  // лицо
  const [faceUsername, setFaceUsername] = useState('');
  const [capturedBlob, setCapturedBlob] = useState<Blob | null>(null);
  const [capturedSource, setCapturedSource] = useState<CameraSource>('laptop');

  async function handlePasswordSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError('');
    setWarning('');
    setLoading(true);
    const result = await login({ username, password, remember_me: remember });
    setLoading(false);
    if (result.success) {
      await redirect();
    } else {
      setError(result.message ?? 'Неверный логин или пароль');
    }
  }

  async function handleFaceSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError('');
    setWarning('');
    if (!capturedBlob) { setError('Сначала сделайте фото.'); return; }
    if (!faceUsername.trim()) { setError('Укажите логин.'); return; }

    setLoading(true);
    const result = await loginWithFace(capturedBlob, faceUsername.trim(), 'main', capturedSource);
    setLoading(false);

    if (result.decision === 'allowed') {
      await redirect();
    } else if (result.decision === 'warning') {
      setWarning(result.message ?? 'Вход разрешён с предупреждением.');
      // даём пользователю секунду прочитать, затем редиректим
      setTimeout(() => redirect(), 2500);
    } else {
      setError(result.message ?? 'Доступ запрещён');
    }
  }

  async function redirect() {
    const me = await getMe();
    if (me && !me.is_admin && me.employee_id) {
      router.push(`/employees/${me.employee_id}`);
    } else {
      router.push('/employees');
    }
  }

  return (
    <main className="min-h-screen bg-background text-slate-100">
      <div className="mx-auto flex min-h-screen max-w-lg items-center justify-center px-4 py-10">
        <div className="w-full rounded-[2rem] border border-slate-700 bg-slate-950/80 p-8 shadow-2xl shadow-slate-950/30 backdrop-blur-md sm:p-10">

          {/* Заголовок */}
          <div className="mb-6 text-center">
            <p className="text-sm uppercase tracking-[0.3em] text-sky-400">Авторизация</p>
            <h1 className="mt-3 text-3xl font-semibold text-white">Войти в систему</h1>
          </div>

          {/* Переключатель вкладок */}
          <div className="mb-6 flex rounded-xl border border-slate-700 overflow-hidden">
            <button
              type="button"
              onClick={() => { setTab('password'); setError(''); setWarning(''); }}
              className={`flex-1 py-2.5 text-sm font-medium transition-colors ${
                tab === 'password' ? 'bg-sky-600 text-white' : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              По паролю
            </button>
            <button
              type="button"
              onClick={() => { setTab('face'); setError(''); setWarning(''); }}
              className={`flex-1 py-2.5 text-sm font-medium transition-colors ${
                tab === 'face' ? 'bg-sky-600 text-white' : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              По лицу
            </button>
          </div>

          {/* Сообщения */}
          {error && (
            <div className="mb-4 rounded-2xl bg-rose-500/10 px-4 py-3 text-sm text-rose-200 ring-1 ring-rose-500/30">
              {error}
            </div>
          )}
          {warning && (
            <div className="mb-4 rounded-2xl bg-amber-500/10 px-4 py-3 text-sm text-amber-200 ring-1 ring-amber-500/30">
              ⚠ {warning} Перенаправление…
            </div>
          )}

          {/* Вкладка: пароль */}
          {tab === 'password' && (
            <form className="space-y-5" onSubmit={handlePasswordSubmit}>
              <label className="block">
                <span className="text-sm font-medium text-slate-300">Логин</span>
                <input
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  className="mt-2 w-full rounded-2xl border border-slate-700 bg-slate-900/90 px-4 py-3 text-slate-100 outline-none transition focus:border-sky-500 focus:ring-2 focus:ring-sky-500/20"
                  placeholder="Введите логин"
                  required
                  autoComplete="username"
                />
              </label>

              <label className="block">
                <span className="text-sm font-medium text-slate-300">Пароль</span>
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="mt-2 w-full rounded-2xl border border-slate-700 bg-slate-900/90 px-4 py-3 text-slate-100 outline-none transition focus:border-sky-500 focus:ring-2 focus:ring-sky-500/20"
                  placeholder="Введите пароль"
                  required
                  autoComplete="current-password"
                />
              </label>

              <label className="flex items-center gap-3 text-sm text-slate-300">
                <input
                  type="checkbox"
                  checked={remember}
                  onChange={(e) => setRemember(e.target.checked)}
                  className="h-4 w-4 rounded border-slate-600 bg-slate-900 text-sky-500 focus:ring-sky-500"
                />
                Запомнить меня
              </label>

              <button
                type="submit"
                disabled={loading}
                className="inline-flex w-full justify-center rounded-2xl bg-sky-500 px-5 py-3 text-sm font-semibold text-white shadow-lg shadow-sky-500/20 transition hover:bg-sky-400 disabled:opacity-60 disabled:cursor-not-allowed"
              >
                {loading ? 'Входим…' : 'Войти'}
              </button>
            </form>
          )}

          {/* Вкладка: лицо */}
          {tab === 'face' && (
            <form className="space-y-5" onSubmit={handleFaceSubmit}>
              <label className="block">
                <span className="text-sm font-medium text-slate-300">Логин</span>
                <input
                  type="text"
                  value={faceUsername}
                  onChange={(e) => setFaceUsername(e.target.value)}
                  className="mt-2 w-full rounded-2xl border border-slate-700 bg-slate-900/90 px-4 py-3 text-slate-100 outline-none transition focus:border-sky-500 focus:ring-2 focus:ring-sky-500/20"
                  placeholder="Ваш логин"
                  required
                  autoComplete="username"
                />
              </label>

              <div>
                <span className="text-sm font-medium text-slate-300">Камера</span>
                <div className="mt-2">
                  <FaceCapture
                    disabled={loading}
                    onCapture={(blob, source) => {
                      setCapturedBlob(blob);
                      setCapturedSource(source);
                    }}
                    onError={(msg) => setError(msg)}
                  />
                </div>
              </div>

              {capturedBlob && (
                <p className="text-xs text-emerald-400">Фото готово — нажмите «Войти»</p>
              )}

              <button
                type="submit"
                disabled={loading || !capturedBlob}
                className="inline-flex w-full justify-center rounded-2xl bg-sky-500 px-5 py-3 text-sm font-semibold text-white shadow-lg shadow-sky-500/20 transition hover:bg-sky-400 disabled:opacity-60 disabled:cursor-not-allowed"
              >
                {loading ? 'Проверяем…' : 'Войти по лицу'}
              </button>
            </form>
          )}

        </div>
      </div>
    </main>
  );
}
