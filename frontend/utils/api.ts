const API = process.env.NEXT_PUBLIC_API_BASE_URL ?? '/api';

function handleUnauthorized() {
  if (typeof window !== 'undefined') {
    window.location.href = '/login';
  }
}

export async function login(values: { username: string; password: string; remember_me: boolean }) {
  try {
    const response = await fetch(`${API}/auth/login/`, {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(values),
    });

    if (!response.ok) {
      const json = await response.json().catch(() => null);
      return { success: false, message: json?.detail ?? 'Ошибка при входе' };
    }
    return { success: true };
  } catch {
    return { success: false, message: 'Сервер недоступен' };
  }
}

export async function logout() {
  try {
    await fetch(`${API}/auth/logout/`, {
      method: 'POST',
      credentials: 'include',
    });
  } finally {
    window.location.href = '/login';
  }
}

export async function getMe(): Promise<{ id: number; username: string; is_admin: boolean; employee_id: number | null } | null> {
  const response = await fetch(`${API}/auth/me/`, { credentials: 'include' });
  if (response.status === 401) { handleUnauthorized(); return null; }
  if (!response.ok) return null;
  return response.json();
}

export async function getEmployees(): Promise<any[]> {
  const response = await fetch(`${API}/employees/`, { credentials: 'include' });
  if (response.status === 401) { handleUnauthorized(); return []; }
  if (!response.ok) throw new Error('Не удалось получить сотрудников');
  return response.json();
}

export async function getEmployee(id: string | string[]): Promise<any> {
  const resolvedId = Array.isArray(id) ? id[0] : id;
  const response = await fetch(`${API}/employees/${resolvedId}/`, { credentials: 'include' });
  if (response.status === 401) { handleUnauthorized(); return null; }
  if (!response.ok) throw new Error('Не удалось получить данные сотрудника');
  return response.json();
}

export async function updateEmployee(id: string, formData: FormData): Promise<{ data?: any; error?: string }> {
  const response = await fetch(`${API}/employees/${id}/update/`, {
    method: 'PATCH',
    credentials: 'include',
    body: formData,
  });
  if (response.status === 401) { handleUnauthorized(); return { error: 'Не авторизован' }; }
  const json = await response.json().catch(() => null);
  if (!response.ok) return { error: json?.error ?? 'Ошибка сохранения' };
  return { data: json };
}

export async function createEmployee(formData: FormData): Promise<{ data?: any; error?: string }> {
  const response = await fetch(`${API}/employees/create/`, {
    method: 'POST',
    credentials: 'include',
    body: formData,
  });
  if (response.status === 401) { handleUnauthorized(); return { error: 'Не авторизован' }; }
  const json = await response.json().catch(() => null);
  if (!response.ok) return { error: json?.error ?? 'Ошибка создания' };
  return { data: json };
}

export async function getAllHistory(params?: {
  employee?: string;
  result?: string;
  date_from?: string;
  date_to?: string;
}): Promise<any[]> {
  const qs = new URLSearchParams();
  if (params?.employee) qs.set('employee', params.employee);
  if (params?.result) qs.set('result', params.result);
  if (params?.date_from) qs.set('date_from', params.date_from);
  if (params?.date_to) qs.set('date_to', params.date_to);
  const url = `${API}/history/${qs.toString() ? '?' + qs.toString() : ''}`;
  const response = await fetch(url, { credentials: 'include' });
  if (response.status === 401) { handleUnauthorized(); return []; }
  if (!response.ok) return [];
  return response.json();
}

export async function getHistory(id: string): Promise<any[]> {
  const response = await fetch(`${API}/employees/${id}/history/`, { credentials: 'include' });
  if (response.status === 401) { handleUnauthorized(); return []; }
  if (!response.ok) return [];
  return response.json();
}

export async function getPositions(): Promise<any[]> {
  const response = await fetch(`${API}/positions/`, { credentials: 'include' });
  if (!response.ok) return [];
  return response.json();
}

export async function getDepartments(): Promise<any[]> {
  const response = await fetch(`${API}/departments/`, { credentials: 'include' });
  if (!response.ok) return [];
  return response.json();
}

export async function loginWithFace(
  imageBlob: Blob,
  username: string,
  zone: string = 'main',
  cameraSource: 'laptop' | 'external' = 'laptop',
): Promise<{ decision: 'allowed' | 'warning' | 'denied'; message: string; confidence?: number; error?: string }> {
  const form = new FormData();
  form.append('image', imageBlob, 'face.jpg');
  form.append('username', username);
  form.append('zone', zone);
  form.append('camera_source', cameraSource);
  try {
    const response = await fetch(`${API}/auth/login/face/`, {
      method: 'POST',
      credentials: 'include',
      body: form,
    });
    const json = await response.json().catch(() => null);
    if (response.status === 404) return { decision: 'denied', message: json?.error ?? 'Сотрудник не найден' };
    if (response.status === 403) return { decision: 'denied', message: json?.message ?? 'Доступ запрещён', confidence: json?.confidence };
    if (!response.ok) return { decision: 'denied', message: json?.error ?? 'Ошибка сервера' };
    return { decision: json.decision, message: json.message, confidence: json.confidence };
  } catch {
    return { decision: 'denied', message: 'Сервер недоступен' };
  }
}

export async function registerBiometric(
  employeeId: number,
  imageBlob: Blob,
): Promise<{ success: boolean; registeredAt?: string; error?: string }> {
  const form = new FormData();
  form.append('employee_id', String(employeeId));
  form.append('image', imageBlob, 'face.jpg');
  const response = await fetch(`${API}/biometric/register/`, {
    method: 'POST',
    credentials: 'include',
    body: form,
  });
  const json = await response.json().catch(() => null);
  if (!response.ok) return { success: false, error: json?.error ?? 'Ошибка регистрации' };
  return { success: true, registeredAt: json.registered_at };
}

export async function getBiometricStatus(
  employeeId: number,
): Promise<{ registered: boolean; registered_at: string | null } | null> {
  const response = await fetch(`${API}/biometric/${employeeId}/status/`, { credentials: 'include' });
  if (!response.ok) return null;
  return response.json();
}
