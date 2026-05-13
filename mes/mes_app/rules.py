# ============================================================
# МИВАРНАЯ БАЗА ЗНАНИЙ — 32 правила в 5 группах
# МЭС СКУД: биометрическая верификация + управление доступом
#
# Входные параметры:
#   X1 — confidence:      уверенность нейросети (0–100)
#   X2 — status:          статус сотрудника ('active' | 'blocked')
#   X3 — access_level:    уровень доступа ('high' | 'medium' | 'low')
#   X4 — zone:            запрашиваемая зона ('main' | 'restricted' | 'server')
#   X5 — is_work_time:    рабочее время (True | False)
#   X6 — failed_attempts: неудачных попыток подряд (0, 1, 2, 3...)
#
# Выходной параметр:
#   Y1 — decision:        'allowed' | 'warning' | 'denied'
# ============================================================

RULES = [

    # =========================================================
    # ГРУППА 1 — Штатный доступ (рабочее время, X1>=80)
    # 9 правил: 3 уровня × 3 зоны в рабочее время
    # =========================================================
    {
        "id": 1,
        "group": 1,
        "name": "Штатный: High в Main",
        "inputs": ["X1", "X2", "X3", "X4", "X5", "X6"],
        "condition": lambda d: (
            d["confidence"] >= 80 and
            d["status"] == "active" and
            d["access_level"] == "high" and
            d["zone"] == "main" and
            d["is_work_time"] and
            d["failed_attempts"] == 0
        ),
        "result": "allowed",
        "message": "Доступ разрешён — главный вход (высокий уровень)",
        "explanation": "Биометрия подтверждена ({conf}%), активный сотрудник, рабочее время, высокий уровень — главный вход открыт",
    },
    {
        "id": 2,
        "group": 1,
        "name": "Штатный: High в Restricted",
        "inputs": ["X1", "X2", "X3", "X4", "X5", "X6"],
        "condition": lambda d: (
            d["confidence"] >= 80 and
            d["status"] == "active" and
            d["access_level"] == "high" and
            d["zone"] == "restricted" and
            d["is_work_time"] and
            d["failed_attempts"] == 0
        ),
        "result": "allowed",
        "message": "Доступ разрешён — ограниченная зона (высокий уровень)",
        "explanation": "Биометрия подтверждена ({conf}%), высокий уровень доступа — ограниченная зона открыта",
    },
    {
        "id": 3,
        "group": 1,
        "name": "Штатный: High в Server",
        "inputs": ["X1", "X2", "X3", "X4", "X5", "X6"],
        "condition": lambda d: (
            d["confidence"] >= 80 and
            d["status"] == "active" and
            d["access_level"] == "high" and
            d["zone"] == "server" and
            d["is_work_time"] and
            d["failed_attempts"] == 0
        ),
        "result": "allowed",
        "message": "Доступ разрешён — серверная комната (высокий уровень)",
        "explanation": "Биометрия подтверждена ({conf}%), высокий уровень доступа — серверная комната открыта",
    },
    {
        "id": 4,
        "group": 1,
        "name": "Штатный: Medium в Main",
        "inputs": ["X1", "X2", "X3", "X4", "X5", "X6"],
        "condition": lambda d: (
            d["confidence"] >= 80 and
            d["status"] == "active" and
            d["access_level"] == "medium" and
            d["zone"] == "main" and
            d["is_work_time"] and
            d["failed_attempts"] == 0
        ),
        "result": "allowed",
        "message": "Доступ разрешён — главный вход (средний уровень)",
        "explanation": "Биометрия подтверждена ({conf}%), средний уровень — главный вход открыт",
    },
    {
        "id": 5,
        "group": 1,
        "name": "Штатный: Medium в Restricted",
        "inputs": ["X1", "X2", "X3", "X4", "X5", "X6"],
        "condition": lambda d: (
            d["confidence"] >= 80 and
            d["status"] == "active" and
            d["access_level"] == "medium" and
            d["zone"] == "restricted" and
            d["is_work_time"] and
            d["failed_attempts"] == 0
        ),
        "result": "allowed",
        "message": "Доступ разрешён — ограниченная зона (средний уровень)",
        "explanation": "Биометрия подтверждена ({conf}%), средний уровень — ограниченная зона открыта",
    },
    {
        "id": 6,
        "group": 1,
        "name": "Отказ: Medium в Server",
        "inputs": ["X1", "X2", "X3", "X4", "X5", "X6"],
        "condition": lambda d: (
            d["confidence"] >= 80 and
            d["status"] == "active" and
            d["access_level"] == "medium" and
            d["zone"] == "server" and
            d["is_work_time"] and
            d["failed_attempts"] == 0
        ),
        "result": "denied",
        "message": "Доступ запрещён — недостаточно прав для серверной комнаты",
        "explanation": "Биометрия подтверждена ({conf}%), но средний уровень доступа не даёт прав на серверную комнату",
    },
    {
        "id": 7,
        "group": 1,
        "name": "Штатный: Low в Main",
        "inputs": ["X1", "X2", "X3", "X4", "X5", "X6"],
        "condition": lambda d: (
            d["confidence"] >= 80 and
            d["status"] == "active" and
            d["access_level"] == "low" and
            d["zone"] == "main" and
            d["is_work_time"] and
            d["failed_attempts"] == 0
        ),
        "result": "allowed",
        "message": "Доступ разрешён — главный вход (низкий уровень)",
        "explanation": "Биометрия подтверждена ({conf}%), низкий уровень — только главный вход в рабочее время",
    },
    {
        "id": 8,
        "group": 1,
        "name": "Отказ: Low в Restricted",
        "inputs": ["X1", "X2", "X3", "X4", "X5", "X6"],
        "condition": lambda d: (
            d["confidence"] >= 80 and
            d["status"] == "active" and
            d["access_level"] == "low" and
            d["zone"] == "restricted" and
            d["is_work_time"] and
            d["failed_attempts"] == 0
        ),
        "result": "denied",
        "message": "Доступ запрещён — недостаточно прав для ограниченной зоны",
        "explanation": "Биометрия подтверждена ({conf}%), но низкий уровень доступа не даёт прав на ограниченную зону",
    },
    {
        "id": 9,
        "group": 1,
        "name": "Отказ: Low в Server",
        "inputs": ["X1", "X2", "X3", "X4", "X5", "X6"],
        "condition": lambda d: (
            d["confidence"] >= 80 and
            d["status"] == "active" and
            d["access_level"] == "low" and
            d["zone"] == "server" and
            d["is_work_time"] and
            d["failed_attempts"] == 0
        ),
        "result": "denied",
        "message": "Доступ запрещён — недостаточно прав для серверной комнаты",
        "explanation": "Биометрия подтверждена ({conf}%), но низкий уровень доступа не даёт прав на серверную комнату",
    },

    # =========================================================
    # ГРУППА 2 — Доступ в нерабочее время (X1>=80, X5=false)
    # 9 правил: жёсткие ограничения вне рабочего времени
    # =========================================================
    {
        "id": 10,
        "group": 2,
        "name": "Внеурочно: High в Main",
        "inputs": ["X1", "X2", "X3", "X4", "X5", "X6"],
        "condition": lambda d: (
            d["confidence"] >= 80 and
            d["status"] == "active" and
            d["access_level"] == "high" and
            d["zone"] == "main" and
            not d["is_work_time"] and
            d["failed_attempts"] == 0
        ),
        "result": "warning",
        "message": "Предупреждение — доступ вне рабочего времени (главный вход, высокий уровень)",
        "explanation": "Биометрия подтверждена ({conf}%), высокий уровень — доступ вне расписания зафиксирован",
    },
    {
        "id": 11,
        "group": 2,
        "name": "Внеурочно: High в Restricted",
        "inputs": ["X1", "X2", "X3", "X4", "X5", "X6"],
        "condition": lambda d: (
            d["confidence"] >= 80 and
            d["status"] == "active" and
            d["access_level"] == "high" and
            d["zone"] == "restricted" and
            not d["is_work_time"] and
            d["failed_attempts"] == 0
        ),
        "result": "warning",
        "message": "Предупреждение — доступ вне рабочего времени (ограниченная зона, высокий уровень)",
        "explanation": "Биометрия подтверждена ({conf}%), высокий уровень — доступ к ограниченной зоне вне расписания зафиксирован",
    },
    {
        "id": 12,
        "group": 2,
        "name": "Внеурочно: High в Server",
        "inputs": ["X1", "X2", "X3", "X4", "X5", "X6"],
        "condition": lambda d: (
            d["confidence"] >= 80 and
            d["status"] == "active" and
            d["access_level"] == "high" and
            d["zone"] == "server" and
            not d["is_work_time"] and
            d["failed_attempts"] == 0
        ),
        "result": "warning",
        "message": "Предупреждение — доступ вне рабочего времени (серверная комната, высокий уровень)",
        "explanation": "Биометрия подтверждена ({conf}%), высокий уровень — доступ в серверную вне расписания зафиксирован",
    },
    {
        "id": 13,
        "group": 2,
        "name": "Внеурочно: Medium в Main",
        "inputs": ["X1", "X2", "X3", "X4", "X5", "X6"],
        "condition": lambda d: (
            d["confidence"] >= 80 and
            d["status"] == "active" and
            d["access_level"] == "medium" and
            d["zone"] == "main" and
            not d["is_work_time"] and
            d["failed_attempts"] == 0
        ),
        "result": "warning",
        "message": "Предупреждение — доступ вне рабочего времени (главный вход, средний уровень)",
        "explanation": "Биометрия подтверждена ({conf}%), средний уровень — доступ вне расписания зафиксирован",
    },
    {
        "id": 14,
        "group": 2,
        "name": "Внеурочно: Medium в Restricted",
        "inputs": ["X1", "X2", "X3", "X4", "X5", "X6"],
        "condition": lambda d: (
            d["confidence"] >= 80 and
            d["status"] == "active" and
            d["access_level"] == "medium" and
            d["zone"] == "restricted" and
            not d["is_work_time"] and
            d["failed_attempts"] == 0
        ),
        "result": "denied",
        "message": "Доступ запрещён — ограниченная зона закрыта вне рабочего времени (средний уровень)",
        "explanation": "Биометрия подтверждена ({conf}%), но средний уровень не даёт прав на ограниченную зону вне расписания",
    },
    {
        "id": 15,
        "group": 2,
        "name": "Внеурочно: Medium в Server",
        "inputs": ["X1", "X2", "X3", "X4", "X5", "X6"],
        "condition": lambda d: (
            d["confidence"] >= 80 and
            d["status"] == "active" and
            d["access_level"] == "medium" and
            d["zone"] == "server" and
            not d["is_work_time"] and
            d["failed_attempts"] == 0
        ),
        "result": "denied",
        "message": "Доступ запрещён — серверная комната закрыта вне рабочего времени (средний уровень)",
        "explanation": "Биометрия подтверждена ({conf}%), серверная комната недоступна для среднего уровня вне расписания",
    },
    {
        "id": 16,
        "group": 2,
        "name": "Внеурочно: Low в Main",
        "inputs": ["X1", "X2", "X3", "X4", "X5", "X6"],
        "condition": lambda d: (
            d["confidence"] >= 80 and
            d["status"] == "active" and
            d["access_level"] == "low" and
            d["zone"] == "main" and
            not d["is_work_time"] and
            d["failed_attempts"] == 0
        ),
        "result": "denied",
        "message": "Доступ запрещён — низкий уровень, нерабочее время",
        "explanation": "Биометрия подтверждена ({conf}%), но низкий уровень доступа разрешён только в рабочее время",
    },
    {
        "id": 17,
        "group": 2,
        "name": "Внеурочно: Low в Restricted",
        "inputs": ["X1", "X2", "X3", "X4", "X5", "X6"],
        "condition": lambda d: (
            d["confidence"] >= 80 and
            d["status"] == "active" and
            d["access_level"] == "low" and
            d["zone"] == "restricted" and
            not d["is_work_time"] and
            d["failed_attempts"] == 0
        ),
        "result": "denied",
        "message": "Доступ запрещён — недостаточно прав, нерабочее время",
        "explanation": "Биометрия подтверждена ({conf}%), низкий уровень не даёт прав на ограниченную зону вне расписания",
    },
    {
        "id": 18,
        "group": 2,
        "name": "Внеурочно: Low в Server",
        "inputs": ["X1", "X2", "X3", "X4", "X5", "X6"],
        "condition": lambda d: (
            d["confidence"] >= 80 and
            d["status"] == "active" and
            d["access_level"] == "low" and
            d["zone"] == "server" and
            not d["is_work_time"] and
            d["failed_attempts"] == 0
        ),
        "result": "denied",
        "message": "Доступ запрещён — недостаточно прав, нерабочее время",
        "explanation": "Биометрия подтверждена ({conf}%), низкий уровень не даёт прав на серверную комнату вне расписания",
    },

    # =========================================================
    # ГРУППА 3 — Обработка сомнений ИИ (50% <= X1 < 80%)
    # 7 правил: пониженная уверенность нейросети
    # =========================================================
    {
        "id": 19,
        "group": 3,
        "name": "Сомнение ИИ: High → Server",
        "inputs": ["X1", "X2", "X3", "X4", "X5", "X6"],
        "condition": lambda d: (
            50 <= d["confidence"] < 80 and
            d["status"] == "active" and
            d["access_level"] == "high" and
            d["zone"] == "server" and
            d["is_work_time"] and
            d["failed_attempts"] == 0
        ),
        "result": "warning",
        "message": "Требуется подтверждение — низкая уверенность биометрии (серверная комната)",
        "explanation": "Уверенность нейросети {conf}% — требуется дополнительная верификация для серверной комнаты",
    },
    {
        "id": 20,
        "group": 3,
        "name": "Сомнение ИИ: High → Restricted",
        "inputs": ["X1", "X2", "X3", "X4", "X5", "X6"],
        "condition": lambda d: (
            50 <= d["confidence"] < 80 and
            d["status"] == "active" and
            d["access_level"] == "high" and
            d["zone"] == "restricted" and
            d["is_work_time"] and
            d["failed_attempts"] == 0
        ),
        "result": "warning",
        "message": "Требуется подтверждение — низкая уверенность биометрии (ограниченная зона)",
        "explanation": "Уверенность нейросети {conf}% — требуется дополнительная верификация для ограниченной зоны",
    },
    {
        "id": 21,
        "group": 3,
        "name": "Сомнение ИИ: High → Main",
        "inputs": ["X1", "X2", "X3", "X4", "X5", "X6"],
        "condition": lambda d: (
            50 <= d["confidence"] < 80 and
            d["status"] == "active" and
            d["access_level"] == "high" and
            d["zone"] == "main" and
            d["is_work_time"] and
            d["failed_attempts"] == 0
        ),
        "result": "warning",
        "message": "Требуется подтверждение — низкая уверенность биометрии (главный вход)",
        "explanation": "Уверенность нейросети {conf}% — требуется дополнительная верификация для прохода",
    },
    {
        "id": 22,
        "group": 3,
        "name": "Сомнение ИИ: Medium → Restricted",
        "inputs": ["X1", "X2", "X3", "X4", "X5", "X6"],
        "condition": lambda d: (
            50 <= d["confidence"] < 80 and
            d["status"] == "active" and
            d["access_level"] == "medium" and
            d["zone"] == "restricted" and
            d["is_work_time"] and
            d["failed_attempts"] == 0
        ),
        "result": "warning",
        "message": "Требуется подтверждение — низкая уверенность биометрии (ограниченная зона)",
        "explanation": "Уверенность нейросети {conf}% — для ограниченной зоны нужна дополнительная верификация",
    },
    {
        "id": 23,
        "group": 3,
        "name": "Сомнение ИИ: Medium → Main",
        "inputs": ["X1", "X2", "X3", "X4", "X5", "X6"],
        "condition": lambda d: (
            50 <= d["confidence"] < 80 and
            d["status"] == "active" and
            d["access_level"] == "medium" and
            d["zone"] == "main" and
            d["is_work_time"] and
            d["failed_attempts"] == 0
        ),
        "result": "warning",
        "message": "Требуется подтверждение — низкая уверенность биометрии",
        "explanation": "Уверенность нейросети {conf}% — требуется дополнительная верификация для прохода",
    },
    {
        "id": 24,
        "group": 3,
        "name": "Сомнение ИИ: Low → Main",
        "inputs": ["X1", "X2", "X3", "X4", "X5", "X6"],
        "condition": lambda d: (
            50 <= d["confidence"] < 80 and
            d["status"] == "active" and
            d["access_level"] == "low" and
            d["zone"] == "main" and
            d["is_work_time"] and
            d["failed_attempts"] == 0
        ),
        "result": "warning",
        "message": "Требуется подтверждение — низкая уверенность биометрии",
        "explanation": "Уверенность нейросети {conf}% — требуется дополнительная верификация для прохода",
    },
    {
        "id": 25,
        "group": 3,
        "name": "Низкая уверенность ИИ",
        "inputs": ["X1"],
        "condition": lambda d: (
            d["confidence"] < 50
        ),
        "result": "denied",
        "message": "Доступ запрещён — личность не установлена",
        "explanation": "Уверенность нейросети {conf}% — слишком низкая для идентификации личности",
    },

    # =========================================================
    # ГРУППА 4 — Проверка статуса учётной записи (X2=blocked)
    # 3 правила: абсолютный запрет для заблокированных
    # =========================================================
    {
        "id": 26,
        "group": 4,
        "name": "Блокировка: Доступ в Main",
        "inputs": ["X2", "X4"],
        "condition": lambda d: (
            d["status"] == "blocked" and
            d["zone"] == "main"
        ),
        "result": "denied",
        "message": "Доступ запрещён — учётная запись заблокирована",
        "explanation": "Учётная запись сотрудника заблокирована в системе — вход в любую зону запрещён",
    },
    {
        "id": 27,
        "group": 4,
        "name": "Блокировка: Доступ в Restricted",
        "inputs": ["X2", "X4"],
        "condition": lambda d: (
            d["status"] == "blocked" and
            d["zone"] == "restricted"
        ),
        "result": "denied",
        "message": "Доступ запрещён — учётная запись заблокирована",
        "explanation": "Учётная запись сотрудника заблокирована в системе — вход в любую зону запрещён",
    },
    {
        "id": 28,
        "group": 4,
        "name": "Блокировка: Доступ в Server",
        "inputs": ["X2", "X4"],
        "condition": lambda d: (
            d["status"] == "blocked" and
            d["zone"] == "server"
        ),
        "result": "denied",
        "message": "Доступ запрещён — учётная запись заблокирована",
        "explanation": "Учётная запись сотрудника заблокирована в системе — вход в любую зону запрещён",
    },

    # =========================================================
    # ГРУППА 5 — Защита от подбора (X6 — счётчик ошибок)
    # 4 правила: предупреждения и блокировка при ошибках
    # =========================================================
    {
        "id": 29,
        "group": 5,
        "name": "Защита: 1 ошибка распознавания",
        "inputs": ["X6"],
        "condition": lambda d: (
            d["failed_attempts"] == 1
        ),
        "result": "warning",
        "message": "Предупреждение — зафиксирована 1 неудачная попытка",
        "explanation": "Зафиксирована 1 неудачная попытка аутентификации — система в режиме повышенного внимания",
    },
    {
        "id": 30,
        "group": 5,
        "name": "Защита: 2 ошибки распознавания",
        "inputs": ["X6"],
        "condition": lambda d: (
            d["failed_attempts"] == 2
        ),
        "result": "warning",
        "message": "Предупреждение — зафиксированы 2 неудачные попытки",
        "explanation": "Зафиксированы 2 неудачные попытки аутентификации — требуется контроль безопасности",
    },
    {
        "id": 31,
        "group": 5,
        "name": "Блокировка: 3 и более ошибок",
        "inputs": ["X6"],
        "condition": lambda d: (
            d["failed_attempts"] >= 3
        ),
        "result": "denied",
        "message": "Доступ заблокирован — превышено число попыток",
        "explanation": "Зафиксировано {attempts} неудачных попыток подряд — временная блокировка активирована",
    },
    {
        "id": 32,
        "group": 5,
        "name": "Попытка входа заблокированного",
        "inputs": ["X2", "X6"],
        "condition": lambda d: (
            d["status"] == "blocked" and
            d["failed_attempts"] > 0
        ),
        "result": "denied",
        "message": "Доступ запрещён — заблокированный аккаунт с историей ошибок",
        "explanation": "Заблокированный сотрудник совершил попытки входа ({attempts} ошибок) — инцидент безопасности",
    },
]

# Названия групп для отображения
GROUP_NAMES = {
    1: "Штатный доступ (рабочее время)",
    2: "Доступ в нерабочее время",
    3: "Обработка сомнений ИИ",
    4: "Проверка статуса учётной записи",
    5: "Защита от подбора",
}