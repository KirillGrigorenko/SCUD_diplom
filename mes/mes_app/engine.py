# ============================================================
# МИВАРНЫЙ ДВИЖОК ВЫВОДА
# Обрабатывает правила в приоритетном порядке:
#   1. Группа 4 (статус заблокирован) — абсолютный запрет
#   2. Группа 5 (защита от подбора) — счётчик ошибок
#   3. Группа 3 (сомнения ИИ, X1 < 80%) — предупреждения
#   4. Группа 1 (штатный доступ в рабочее время)
#   5. Группа 2 (нерабочее время)
# ============================================================

from .rules import RULES, GROUP_NAMES


PRIORITY_ORDER = [4, 5, 3, 1, 2]


def run_engine(data: dict) -> dict:
    """
    Запускает миварный движок на входных данных.

    Аргументы:
        data (dict): {
            "confidence":      int   (X1, 0–100),
            "status":          str   (X2, 'active'|'blocked'),
            "access_level":    str   (X3, 'high'|'medium'|'low'),
            "zone":            str   (X4, 'main'|'restricted'|'server'),
            "is_work_time":    bool  (X5),
            "failed_attempts": int   (X6, 0, 1, 2, 3...),
        }

    Возвращает:
        dict: {
            "decision":    str ('allowed'|'warning'|'denied'),
            "message":     str,
            "explanation": str,
            "rule":        dict (сработавшее правило),
            "chain":       list (цепочка вывода),
            "all_checked": list (все проверенные правила),
        }
    """
    chain = []          # цепочка сработавших правил (вся)
    all_checked = []    # все проверенные правила в порядке обработки

    # Сортируем правила по приоритету групп
    sorted_rules = sorted(RULES, key=lambda r: PRIORITY_ORDER.index(r["group"]))

    matched_rule = None

    for rule in sorted_rules:
        try:
            fired = rule["condition"](data)
        except Exception:
            fired = False

        checked_entry = {
            "id": rule["id"],
            "group": rule["group"],
            "group_name": GROUP_NAMES.get(rule["group"], ""),
            "name": rule["name"],
            "fired": fired,
        }
        all_checked.append(checked_entry)

        if fired:
            chain.append(checked_entry)
            if matched_rule is None:
                matched_rule = rule  # первое сработавшее правило — финальное решение

    if matched_rule is None:
        # Ни одно правило не сработало — нештатная ситуация
        return {
            "decision": "denied",
            "message": "Доступ запрещён — параметры не соответствуют ни одному правилу",
            "explanation": "МЭС не смогла применить ни одно из 32 правил к данным запроса",
            "rule": None,
            "chain": chain,
            "all_checked": all_checked,
        }

    conf = data.get("confidence", 0)
    attempts = data.get("failed_attempts", 0)

    explanation = matched_rule["explanation"].format(
        conf=conf,
        attempts=attempts,
    )

    return {
        "decision": matched_rule["result"],
        "message": matched_rule["message"],
        "explanation": explanation,
        "rule": {
            "id": matched_rule["id"],
            "group": matched_rule["group"],
            "group_name": GROUP_NAMES.get(matched_rule["group"], ""),
            "name": matched_rule["name"],
            "inputs": matched_rule["inputs"],
        },
        "chain": chain,
        "all_checked": all_checked,
    }


# Алиас для обратной совместимости с views.py
run_mes = run_engine