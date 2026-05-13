# CLAUDE

## Цель

Отдельный фронтенд на Next.js + Tailwind для визуальной части проекта `СКУД`, который работает поверх существующего Django API.

---

## Страницы

### `/`
Страница логина.
- Форма:
  - `username`
  - `password`
  - `remember_me`
- Отправка на `POST /api/auth/login/`
- Успех: редирект на `/employees`
- Ошибка: показать сообщение о неверных данных
- Вкладка «По лицу»: режим биометрического входа (см. раздел «Биометрия»)

### `/employees`
Страница списка сотрудников.
- Загружает данные из `GET /api/employees/`
- Показывает:
  - карточки сотрудников
  - статус
  - фото
  - должность / отдел, если API расширен
- Фильтры:
  - поиск по ФИО
  - фильтр по отделу
  - фильтр по статусу
- Поведение:
  - фильтрация на клиенте, потому что текущий API не поддерживает query-параметры
  - пустой результат показывает состояние "ничего не найдено"

### `/employees/[id]`
Страница деталей сотрудника.
- Загружает данные из `GET /api/employees/{id}/`
- Показывает:
  - фото сотрудника
  - ФИО
  - статус
  - дата найма
  - карточку сотрудника с паспортными и контактными данными, если доступны
  - историю доступа, если API расширен
- Если пользователь администратор — кнопка редактирования.
- Если пользователь неадминистратор и пытается посмотреть чужую запись, API должен отказать.
- Если администратор — в разделе биометрии показывать статус регистрации лица + кнопку регистрации.

---

## Биометрия (вход по лицу)

### Архитектура потока

```
Frontend (Next.js)
  └─ захват кадра с камеры
  └─ POST /api/auth/login/face/
        │
Django Backend
  ├─ face_stub.py → confidence (int 0–100, заглушка)
  ├─ mes_client.py → вызов run_engine() из mes/mes_app/engine.py
  │     параметры:
  │       X1 confidence      — от заглушки ИИ
  │       X2 status          — статус сотрудника (active/blocked)
  │       X3 access_level    — уровень доступа (high/medium/low)
  │       X4 zone            — запрашиваемая зона (main/restricted/server)
  │       X5 is_work_time    — рабочее ли время (True/False)
  │       X6 failed_attempts — счётчик неудачных попыток из AccessHistory
  │
  ├─ MES (МИВАР) возвращает: allowed / warning / denied
  ├─ AccessHistory ВСЕГДА записывается (и при allowed, и при denied, и при warning)
  └─ если allowed или warning — создаётся сессия Django
```

### Заглушка ИИ (face_stub.py)
- Функция `detect_face(image_bytes, employee) -> int` возвращает confidence (0–100)
- Пока возвращает случайное значение в заданном диапазоне для демонстрации
- Позже заменяется реальной моделью векторизации лица
- Хэш лица хранится в `BiometricData.face_hash`

### Камеры
- **Ноутбук** (`laptop`) — `getUserMedia` через браузер, доступна сейчас
- **Камера УК** (`external`) — заглушка: блок с сообщением «Камера не подключена», поле `camera_source='external'` в истории
- Выбор камеры на форме логина
- `camera_source` сохраняется в `AccessHistory`

### Режим работы WARNING
- MES вернул `warning` → вход разрешается, но `AccessHistory.result = 'warning'`
- На фронте показывается предупреждение перед редиректом (например: «Уверенность ИИ недостаточна, вход зафиксирован»)

### Регистрация лица (только администратор)
- Эндпоинт `POST /api/biometric/register/`
- Принимает `employee_id` + `image` (фото)
- Запускает face_stub, сохраняет хэш в `BiometricData`
- Устанавливает `BiometricData.face_registered_at`, `status=True`
- Доступно в UI на странице редактирования сотрудника

---

## MES / МИВАР

- Расположен в `mes/` (отдельный Django-проект)
- Движок: `mes/mes_app/engine.py`, функция `run_engine(data) -> dict`
- Django (СКУД) вызывает движок через прямой Python-импорт (не HTTP)
- Модуль `app/services/mes_client.py` является обёрткой над `run_engine`
- 32 правила в 5 группах приоритета: [4 → 5 → 3 → 1 → 2]
  - Группа 4: статус заблокирован → всегда denied
  - Группа 5: failed_attempts ≥ 1 → warning/denied
  - Группа 3: 50 ≤ confidence < 80 → warning; < 50 → denied
  - Группа 1: штатный доступ в рабочее время
  - Группа 2: нерабочее время

---

## Правила

### Архитектура
- Фронтенд отдельный, Next.js + Tailwind.
- Django остаётся бэкендом, отдаёт API.
- Использовать `credentials: include` для запросов, чтобы поддерживать сессионное куки Django.

### Переменные окружения
- `NEXT_PUBLIC_API_BASE_URL` — базовый адрес Django API.
- Пример: `http://localhost:8000/api`

### Tailwind
- Вся вёрстка — через Tailwind-классы.
- Глобальные стили в `app/globals.css`.
- Старый CSS из `app/services/static/css/style.css` не используется в новом фронтенде.

### Авторизация
- Вход через API `POST /api/auth/login/`
- Вход по лицу через `POST /api/auth/login/face/`
- Если запрос на защищённую страницу возвращает `401`, перенаправлять на `/`

### Навигация
- Шапка `Header`:
  - бренд
  - навигация
  - имя пользователя
  - кнопка выхода
- Футер `Footer`:
  - копирайт
  - подсказка системы

### Ошибки и состояние
- Показывать индикатор загрузки при запросе списка и деталей.
- Показывать ошибку при невозможности подключиться к API.
- Показывать сообщение при отсутствии данных.

---

## API

### `POST /api/auth/login/`
- Тело: `username`, `password`, `remember_me`
- Ответы: `200` — успешный вход, `400`/`401` — ошибка

### `POST /api/auth/login/face/`
- Тело (multipart): `username`, `image`, `zone` (default: `main`), `camera_source` (`laptop`|`external`)
- Процесс:
  1. Найти сотрудника по `username`
  2. face_stub → confidence
  3. Определить access_level, is_work_time, failed_attempts
  4. Вызвать MES: `run_engine({...})`
  5. Записать в `AccessHistory` (ВСЕГДА)
  6. Если `allowed` или `warning` → создать сессию Django
- Ответы:
  - `200` `{decision: 'allowed'|'warning', message, redirect}`
  - `403` `{decision: 'denied', message}`
  - `404` `{error: 'Сотрудник не найден'}`

### `POST /api/biometric/register/`
- Права: только администратор
- Тело (multipart): `employee_id`, `image`
- Процесс: face_stub → hash → BiometricData.face_hash, face_registered_at, status=True
- Ответы: `200` `{status: 'registered'}`, `403`, `404`

### `GET /api/biometric/{employee_id}/status/`
- Права: администратор или сам сотрудник
- Ответ: `{registered: bool, registered_at: date|null}`

### `GET /api/employees/`
- Список сотрудников
- Поля: `id`, `full_name`, `hire_date`, `status`, `photo_url`, `position`, `department`, `employee_card`

### `GET /api/employees/{id}/`
- Детали сотрудника
- Поля: `id`, `full_name`, `first_name`, `last_name`, `middle_name`, `hire_date`, `status`, `photo`, `photo_url`
- По необходимости: `employee_card`, `history`, `position`, `department`

---

## Модели (изменения)

### `AccessHistory` — добавить поля:
- `camera_source` = CharField(max_length=20, choices=[('laptop','Ноутбук'),('external','Камера УК')], null=True, blank=True)
- `confidence` = IntegerField(null=True, blank=True) — уверенность ИИ для биометрических попыток
- `RESULT_CHOICES` расширить: добавить `('warning', 'Предупреждение')`

---

## Новые файлы (Backend)

| Файл | Назначение |
|------|-----------|
| `app/services/face_stub.py` | Заглушка ИИ-модели, возвращает confidence |
| `app/services/mes_client.py` | Обёртка над `mes/mes_app/engine.run_engine()` |

---

## Дополнения
- Если потребуется экран редактирования, добавить `PUT/PATCH /api/employees/{id}/` и сериализатор, который сохраняет `EmployeeCard`.
- Если фронтенд работает на другом порте/домене, нужно настроить CORS и куки на Django.
- Когда появится реальная ИИ-модель — заменить только `face_stub.py`, остальная архитектура остаётся.
