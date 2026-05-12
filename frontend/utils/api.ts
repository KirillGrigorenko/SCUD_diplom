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

export async function getEmployees(): Promise<any[]> {
  const response = await fetch(`${API}/employees/`, {
    credentials: 'include',
  });

  if (response.status === 401) {
    handleUnauthorized();
    return [];
  }

  if (!response.ok) {
    throw new Error('Не удалось получить сотрудников');
  }

  return response.json();
}

export async function getEmployee(id: string | string[]): Promise<any> {
  const resolvedId = Array.isArray(id) ? id[0] : id;
  const response = await fetch(`${API}/employees/${resolvedId}/`, {
    credentials: 'include',
  });

  if (response.status === 401) {
    handleUnauthorized();
    return null;
  }

  if (!response.ok) {
    throw new Error('Не удалось получить данные сотрудника');
  }

  return response.json();
}
