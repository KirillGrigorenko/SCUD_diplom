# CLAUDE

## Цель

Единый Django-проект: HTML-шаблоны (порт 8000) + REST API. Next.js-фронтенд убран — весь UI на Django templates + vanilla JS.

---

## Текущее состояние (май 2026)

### Что реализовано
- Список, детали, создание, редактирование, удаление сотрудников
- Страница сотрудника: фото, статус, паспорт, образование, права доступа, история проходов
- Биометрическая регистрация ладони (загрузка файла → MinIO) на странице редактирования
- Вход по логину/паролю и по биометрии ладони (vein recognition + МИВАР-движок)
- МИВАР (mes/mes_app/engine.py) принимает 6 параметров, возвращает allowed/warning/denied
- AccessHistory всегда пишется, включает camera_source и confidence
- Глобальная история `/history/` с фильтрами и экспортом CSV
- Экспорт CSV истории конкретного сотрудника (`/employee/<pk>/history/export/`)
- Справочник уровней доступа `/access-levels/` (CRUD)
- Назначение/удаление прав доступа (AccessRight) прямо в форме редактирования сотрудника
- Flatpickr на всех date-инпутах, тёмная тема
- Swagger UI с полной документацией всех эндпоинтов: `/api/docs/` (drf-yasg)
- Docker Compose запущен: web (8000), vein-service (8001), db (postgres), pgadmin, minio, redis
- Секция «Учётная запись» (смена логина/пароля) в форме редактирования сотрудника
- Форма создания сотрудника: секции «Образование» и «Права доступа» (паритет с редактированием)
- Toast-уведомления: ошибки и успех показываются по центру поверх интерфейса
- Маски ввода для ИНН (`1234 5678 9012`) и СНИЛС (`123-456-789 00`)
- Разделённое хранилище фото: аватарка (`avatar_{pk}`) и биометрия (`bio_{pk}`) — разные ключи
- Тесты: 43 теста pytest-django на все API-эндпоинты (`app/services/tests/test_api.py`)

### Что ещё НЕ сделано (приоритет сверху вниз)

1. **Биометрическая регистрация** — отлаживается. При нажатии «Зарегистрировать ладонь»
   может показываться ошибка. Логи: `docker compose logs vein-service`.
   api.py перехватывает исключение и возвращает точную причину в JSON.

2. **Адаптивность** — мобильная вёрстка не проверялась.

3. **Диапазонный выбор дат** в фильтрах истории — два отдельных поля `date_from`/`date_to`,
   не объединены в один range-picker Flatpickr.

---

## Архитектура

```
app/
  services/
    models.py          — Employee, Administrator, EmployeeCard, BiometricData,
                         AccessLevel, AccessRight, AccessHistory, Department, Position
    views.py           — HTML-views (login, employee_list/detail/edit/create/delete,
                         history_list, access_level_list, history_export_csv,
                         employee_history_export_csv)
    api.py             — DRF APIViews (login, logout, me, employees, biometric, history)
    urls.py            — HTML-маршруты
    api_urls.py        — /api/* маршруты
    palm_bio.py        — клиент к vein-service (HTTP-запросы, detect_face / get_face_hash)
    face_stub.py       — старая заглушка (НЕ используется, можно удалить)
    mes_client.py      — обёртка над МИВАР (mes/mes_app/engine.py)
    serializers.py     — DRF-сериализаторы
    tests/
      __init__.py
      test_api.py      — 43 теста, pytest-django, SQLite in-memory
    templates/services/
      base.html              — шапка, подвал, flatpickr, toast-система, маски ИНН/СНИЛС
      login.html             — вход по паролю + вкладка «По биометрии» (файл ладони)
      employee_list.html     — список сотрудников с фильтрами
      employee_detail.html   — карточка сотрудника
      employee_edit.html     — редактирование (все поля + биометрия + права доступа)
      employee_create.html   — создание (все поля включая образование и права доступа)
      history_list.html      — глобальная история с фильтрами + CSV
      access_level_list.html — справочник уровней доступа
      _bio_capture.html      — виджет загрузки фото ладони (переиспользуемый, без камеры)
      _position_modal.html   — модал создания должности
    static/css/style.css     — все стили, тёмная тема
    static/img/no-photo.svg  — заглушка фото

vein_service/
  Dockerfile           — python:3.11-slim + torch CPU-only + vein_recognition
  server.py            — Flask-сервер (порт 8001): /embed, /compare, /health

mes/
  mes_app/
    engine.py          — run_engine(data) -> {decision, message, ...}
                         32 правила, 5 групп приоритета

app/conftest.py        — фикстуры pytest (api_client, admin_user, employee, ...)
app/config/settings_test.py — настройки для тестов (SQLite, locmem cache)
pytest.ini             — DJANGO_SETTINGS_MODULE=config.settings_test
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

## Биометрия (вход по ладони)

```
POST /api/auth/login/face/
  username + image + zone + camera_source
  → palm_bio.detect_face() → HTTP POST vein-service:8001/compare → confidence (0–100)
  → mes_client.make_decision(employee, confidence, zone)
      → run_engine({confidence, status, access_level, zone, is_work_time, failed_attempts})
      → allowed / warning / denied
  → AccessHistory.create() (ВСЕГДА)
  → если allowed/warning → Django session создаётся
```

### Vein-service (vein_service/)
- Отдельный Docker-контейнер, Flask на порту 8001
- Клонирует https://github.com/KirillGrigorenko/vein_recognition.git
- Модель: ResNet18 grayscale, 512-мерные L2-нормализованные embeddings
- Файл модели: `/opt/vein_recognition/results/best/huita.pt`
- `POST /embed` — image → base64 embedding (для сохранения в `BiometricData.palm_hash`)
- `POST /compare` — image + stored_hash → `{"confidence": 0–100}`
- `GET /health` — проверка живости
- **ВАЖНО**: torch CPU-only (`--index-url https://download.pytorch.org/whl/cpu`),
  иначе pip скачает ~4 ГБ CUDA-библиотек

### palm_bio.py (app/services/palm_bio.py)
- `detect_face(image_bytes, employee)` → вызывает `/compare`, возвращает int 0–100
- `get_face_hash(image_bytes)` → вызывает `/embed`, возвращает str (base64)
- Переменная окружения `VEIN_SERVICE_URL` (по умолчанию `http://vein-service:8001`)
- При ошибке соединения `detect_face` возвращает 0 (доступ будет denied)

### МИВАР (mes_client.py)
- `access_level` берётся из `AccessRight.access_level.code` сотрудника
- Если прав нет → `'low'`
- `is_work_time`: 09:00–18:00
- `failed_attempts`: последовательные denied в biometric истории

---

## Хранилище фото (MinIO)

Три пространства ключей — не смешивать:

| Ключ | Назначение | Где пишется |
|------|-----------|-------------|
| `avatar_{pk}` | Аватарка сотрудника | views.py employee_edit/create, api.py EmployeeUpdateAPIView/EmployeeCreateAPIView |
| `bio_{pk}` | Фото ладони для биометрии | api.py BiometricRegisterAPIView |
| `employee_{pk}` | Легаси (старый код) | Нигде не пишется — только читается для совместимости |

`employee.photo` хранит ключ аватарки. При сохранении формы редактирования, если `employee.photo == f'employee_{pk}'` (легаси-загрязнение от старой биометрии) и новое фото не загружено — поле очищается до `''`, что отобразит заглушку.

URL получается через `get_minio_url(key)` → `http://{MINIO_PUBLIC_ENDPOINT}/{BUCKET}/{key}.jpg`.
Нет ключа / пустой ключ → `/static/img/no-photo.svg`.

---

## Toast-система (base.html)

Ошибки и успех показываются фиксированным контейнером поверх интерфейса, не инлайново.

```javascript
window.showError('текст')    // красный тост
window.showSuccess('текст')  // зелёный тост
window.showWarning('текст')  // жёлтый тост
window.showToast('текст', 'error'|'success'|'warning')
```

- Контейнер: `#toast-container`, `position:fixed; top:76px; left:50%; transform:translateX(-50%)`
- Автодиссмис через 6 секунд
- DOMContentLoaded автоперехватывает `.form-error` элементы (серверные ошибки Django) и конвертирует в toast
- **ВАЖНО**: JS-контролируемые `.form-error` с `style="display:none"` пропускаются (иначе их текст показывается при каждой загрузке страницы)

---

## Маски ввода (base.html)

Автоинициализируются для `#f-inn` и `#f-snils` через `DOMContentLoaded`.

```javascript
window.applyInnMask(value)   // '123456789012' → '1234 5678 9012'
window.applySnilsMask(value) // '12345678900'  → '123-456-789 00'
```

Перед отправкой формы и перед серверной валидацией — пробелы/дефисы стрипаются:
```javascript
innInput.value = innInput.value.replace(/\s/g, '');
```
Серверная валидация в views.py и api.py: `re.fullmatch(r'\d{12}', inn)`.

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
| `/employee/<pk>/history/export/` | `employee_history_export_csv` | CSV истории сотрудника |
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
- Фото аватарки: ключ MinIO = `avatar_{pk}`, URL через `get_minio_url(key)`. Легаси: `employee_{pk}`
- Фото биометрии: ключ MinIO = `bio_{pk}` — никогда не записывать в `employee.photo`
- Нет фото → `/static/img/no-photo.svg`
- Датапикер — flatpickr (CDN), инициализируется в `base.html` на все `input[type=date]` и `.fp-date`
- Модальные окна — кастомные (`.modal-backdrop` / `.modal-box`), без библиотек
- Удаление всегда через POST-форму + модал подтверждения
- Биометрия — загрузка файла (не камера), виджет `_bio_capture.html` вызывает `bioOnCapture(blob)`
- Ошибки — через `window.showError()`, не инлайново. `.form-error` с `style="display:none"` — только для JS-валидации, toast-система их игнорирует
- Проверки прав: `hasattr(user, 'administrator') or user.is_staff or user.is_superuser`
- Хелпер `is_admin(user)` определён в views.py после списка COUNTRIES

---

## Важные баги исправлённые в процессе

- **Двойное открытие диалога файла** в `_bio_capture.html` — был лишний JS-обработчик
  `btn.addEventListener('click', ...)` при том что `<label>` уже оборачивает `<input>`.
  Удалён. Теперь диалог открывается один раз.

- **403 на /api/biometric/register/** — проверка `hasattr(request.user, 'administrator')`
  не пропускала Django-суперпользователей (у `admin` нет объекта Administrator).
  Исправлено: добавлен `or request.user.is_staff or request.user.is_superuser`.
  То же исправление применено к EmployeeUpdateAPIView, EmployeeCreateAPIView, AllHistoryAPIView.

- **Биометрия перезаписывала аватарку** — старый BiometricRegisterAPIView сохранял фото
  по ключу `employee_{pk}` и записывал его в `employee.photo`. После регистрации биометрии
  аватарка и фото ладони указывали на один файл. Исправлено: биометрия пишет в `bio_{pk}`,
  `employee.photo` не трогает. Новые аватарки пишутся в `avatar_{pk}`.

- **Toast при каждой загрузке страницы редактирования** — `<div id="inn-error" class="form-error" style="display:none">` всегда присутствует в DOM, а автоперехват в base.html не проверял видимость. Исправлено: добавлена проверка `if (el.style.display === 'none') return`.

- **ИНН с пробелами не проходил серверную валидацию** — маска вставляет пробелы (`1234 5678 9012`), но валидация требует `\d{12}`. В submit-обработчике и preview добавлено `.replace(/\s/g, '')` перед отправкой.

- **«Все сотрудники»** ссылка на странице employee_detail.html — скрыта для не-администраторов.

- **Камера убрана** — в login.html и _bio_capture.html заменена на загрузку файла.
  Причина: реальное оборудование недоступно.

---

## Тесты

```bash
cd app && python -m pytest services/tests/ -v
```

- Конфиг: `pytest.ini` (корень проекта), `DJANGO_SETTINGS_MODULE=config.settings_test`
- БД: SQLite in-memory, cache: locmem, sessions: db-backend — нет внешних зависимостей
- Фикстуры: `app/conftest.py` — `api_client`, `admin_user`, `emp_user`, `employee`, `admin_client`, `employee_client`
- 43 теста покрывают: AuthLogin, Logout, Me, EmployeeList/Detail/Create/Update, AllHistory, EmployeeHistory, BiometricStatus, Positions/Departments

---

## Запуск

```bash
docker compose up --build   # первый раз
docker compose up           # последующие
docker compose restart web  # перезапустить только web (после правок Python/шаблонов)
```

Логин администратора: `admin` / `admin123`
