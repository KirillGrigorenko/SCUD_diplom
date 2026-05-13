# CLAUDE

## Цель

Единый Django-проект: HTML-шаблоны (порт 8000) + REST API. Next.js-фронтенд убран — весь UI на Django templates + vanilla JS.

---

## Текущее состояние (май 2026)

### Что реализовано
- Список, детали, создание, редактирование, удаление сотрудников
- Страница сотрудника: фото, статус, паспорт, образование, права доступа, история проходов
- Биометрическая регистрация лица (webcam → MinIO) на странице редактирования
- Вход по логину/паролю и по лицу (заглушка ИИ + МИВАР-движок)
- МИВАР (mes/mes_app/engine.py) принимает 6 параметров, возвращает allowed/warning/denied
- AccessHistory всегда пишется, включает camera_source и confidence
- Глобальная история `/history/` с фильтрами и экспортом CSV
- Справочник уровней доступа `/access-levels/` (CRUD)
- Назначение/удаление прав доступа (AccessRight) прямо в форме редактирования сотрудника
- Flatpickr на всех date-инпутах, тёмная тема
- Swagger UI: `/api/docs/`
- Docker Compose: web (8000), db (postgres), pgadmin, minio, redis

### Что ещё НЕ сделано (приоритет сверху вниз)

1. **Вход по лицу реально не работает** — сейчас `face_stub.py` возвращает случайные числа.
   Когда будет готова нейросеть — заменить только `app/services/face_stub.py`,
   функции `detect_face(image_bytes, employee) -> int` и `get_face_hash(image_bytes) -> str`.

2. **Страница входа по лицу** (`/login/` вкладка «По лицу») — работает, но
   не тестировалась глубоко. Проверить весь флоу: allowed / warning / denied.

3. **Страница создания сотрудника** (`/employee/create/`) — базово работает,
   но не имеет секций «Образование» и «Права доступа» (в отличие от редактирования).
   Привести к тому же виду что и форма редактирования.

4. **Страница редактирования** — нет возможности изменить логин/пароль сотрудника.
   Добавить секцию «Учётная запись» с полями username + смена пароля.

5. **История на странице сотрудника** — показывает только 100 последних записей,
   нет кнопки экспорта CSV для конкретного сотрудника.

6. **Биометрия ладони** — модель `BiometricData` имеет `palm_hash` и `palm_registered_at`,
   но UI и API для неё нет. Либо добавить, либо убрать поля из модели.

7. **Адаптивность** — мобильная вёрстка не проверялась.

8. **Тесты** — нет ни одного. Минимум: тесты API (pytest-django).

---

## Архитектура

```
app/
  services/
    models.py          — Employee, Administrator, EmployeeCard, BiometricData,
                         AccessLevel, AccessRight, AccessHistory, Department, Position
    views.py           — HTML-views (login, employee_list/detail/edit/create/delete,
                         history_list, access_level_list, history_export_csv)
    api.py             — DRF APIViews (login, logout, me, employees, biometric, history)
    urls.py            — HTML-маршруты
    api_urls.py        — /api/* маршруты
    face_stub.py       — заглушка ИИ (заменить на реальную модель)
    mes_client.py      — обёртка над МИВАР (mes/mes_app/engine.py)
    serializers.py     — DRF-сериализаторы
    templates/services/
      base.html              — шапка, подвал, flatpickr, custom select JS
      login.html             — вход по паролю + вкладка «По лицу»
      employee_list.html     — список сотрудников с фильтрами
      employee_detail.html   — карточка сотрудника
      employee_edit.html     — редактирование (все поля + биометрия + права доступа)
      employee_create.html   — создание (НУЖНО ДОПОЛНИТЬ секциями образования и прав)
      history_list.html      — глобальная история с фильтрами + CSV
      access_level_list.html — справочник уровней доступа
      _bio_capture.html      — виджет захвата лица с webcam (переиспользуемый)
      _position_modal.html   — модал создания должности
    static/css/style.css     — все стили, тёмная тема
    static/img/no-photo.svg  — заглушка фото

mes/
  mes_app/
    engine.py          — run_engine(data) -> {decision, message, ...}
                         32 правила, 5 групп приоритета
```

---

## Модели данных

### Employee
`user`, `last_name`, `first_name`, `middle_name`, `hire_date`, `fire_date`, `status` (active/fired/blocked), `photo` (ключ MinIO)

### EmployeeCard (1:1 к Employee)
Паспорт: `passport_series`, `passport_number`, `passport_date`, `passport_issued_by`, `citizenship`, `address`, `snils`, `inn`
Должность: `position` (FK), `administrator` (FK)
Образование: `education_year`, `education_name`, `specialty`, `diploma_number`

### AccessLevel
`name`, `code` (high/medium/low — используется МИВАР), `zone`, `description`

### AccessRight
`employee` (FK), `access_level` (FK), `position` (FK, optional), `assigned_at`, `expires_at`

### BiometricData (1:1 к Employee)
`face_hash`, `palm_hash`, `face_registered_at`, `palm_registered_at`, `status`

### AccessHistory
`employee` (FK), `datetime`, `access_point`, `result` (allowed/denied/warning),
`method` (password/biometric), `camera_source` (laptop/external), `confidence`

---

## Биометрия (вход по лицу)

```
POST /api/auth/login/face/
  username + image + zone + camera_source
  → face_stub.detect_face() → confidence (0–100)
  → mes_client.make_decision(employee, confidence, zone)
      → run_engine({confidence, status, access_level, zone, is_work_time, failed_attempts})
      → allowed / warning / denied
  → AccessHistory.create() (ВСЕГДА)
  → если allowed/warning → Django session создаётся
```

### Заглушка ИИ (face_stub.py)
- Биометрия зарегистрирована → confidence 70–95
- Не зарегистрирована → confidence 20–55
- **Заменить** на реальную модель — только этот файл, архитектура не меняется

### МИВАР (mes_client.py)
- `access_level` берётся из `AccessRight.access_level.code` сотрудника
- Если прав нет → `'low'`
- `is_work_time`: 09:00–18:00
- `failed_attempts`: последовательные denied в biometric истории

---

## Уровни доступа (AccessLevel.code)

Движок понимает только три значения:
- `high` — высокий (server + restricted + main)
- `medium` — средний (main + restricted)
- `low` — низкий (только main)

---

## URL-маршруты

| URL | Имя | Описание |
|-----|-----|---------|
| `/` | `employee_list` | Список сотрудников |
| `/login/` | `login` | Вход |
| `/logout/` | `logout` | Выход |
| `/employee/create/` | `employee_create` | Создание |
| `/employee/<pk>/` | `employee_detail` | Детали |
| `/employee/<pk>/edit/` | `employee_edit` | Редактирование |
| `/employee/<pk>/delete/` | `employee_delete` | Удаление (POST) |
| `/access-right/<pk>/delete/` | `access_right_delete` | Удалить право (POST) |
| `/access-levels/` | `access_level_list` | Справочник уровней |
| `/access-levels/<pk>/delete/` | `access_level_delete` | Удалить уровень (POST) |
| `/history/` | `history_list` | Глобальная история |
| `/history/export/` | `history_export_csv` | Экспорт CSV |
| `/api/docs/` | — | Swagger UI |

---

## Правила разработки

- Весь UI — Django templates + vanilla JS, никакого React/Next.js
- Стили — `app/services/static/css/style.css`, тёмная тема, CSS-переменные
- Фото хранятся в MinIO, ключ = `employee_{pk}`, URL через `get_minio_url(key)`
- Нет фото → `/static/img/no-photo.svg`
- Датапикер — flatpickr (CDN), инициализируется в `base.html` на все `input[type=date]` и `.fp-date`
- Модальные окна — кастомные (`.modal-backdrop` / `.modal-box`), без библиотек
- Удаление всегда через POST-форму + модал подтверждения
- Когда появится реальная ИИ-модель — заменить только `face_stub.py`
