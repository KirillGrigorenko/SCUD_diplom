# ============================================================
# ТЕСТОВЫЕ ДАННЫЕ СОТРУДНИКОВ — заглушка вместо нейронки
# В реальной системе нейронка вернёт employee_id + confidence
# ============================================================

EMPLOYEES = {
    1: {
        "id": 1,
        "name": "Иванов Иван Иванович",
        "status": "active",
        "access_level": "high",
        "zone": "main",
        "employee_zone": "main",
        "department": "IT отдел",
    },
    2: {
        "id": 2,
        "name": "Петров Пётр Петрович",
        "status": "active",
        "access_level": "medium",
        "zone": "main",
        "employee_zone": "main",
        "department": "IT отдел",
    },
    3: {
        "id": 3,
        "name": "Сидоров Сидор Сидорович",
        "status": "active",
        "access_level": "low",
        "zone": "restricted",
        "employee_zone": "main",
        "department": "Охрана",
    },
    4: {
        "id": 4,
        "name": "Козлов Андрей Викторович",
        "status": "blocked",
        "access_level": "medium",
        "zone": "main",
        "employee_zone": "main",
        "department": "IT отдел",
    },
}


def get_employee(employee_id):
    return EMPLOYEES.get(employee_id)


def mock_neural_network(employee_id, confidence):
    """
    Заглушка нейронки.
    В реальности: принимает фото → возвращает employee_id + confidence.
    Сейчас: пользователь сам выбирает employee_id и confidence для демо.
    """
    employee = get_employee(employee_id)
    if not employee:
        return None, confidence
    return employee, confidence