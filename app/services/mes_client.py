"""
Обёртка над МИВАР-движком (mes/mes_app/engine.py).
Вызывается напрямую через импорт — не по HTTP.
"""

import os
import sys
from datetime import datetime, time

# Добавляем путь к mes/ чтобы импортировать движок
_MES_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'mes')
if _MES_PATH not in sys.path:
    sys.path.insert(0, os.path.abspath(_MES_PATH))

from mes_app.engine import run_engine  # noqa: E402


_WORK_START = time(9, 0)
_WORK_END = time(18, 0)

# Маппинг кодов уровня доступа из AccessLevel.code в формат MES
_ACCESS_LEVEL_MAP = {
    'high': 'high',
    'medium': 'medium',
    'low': 'low',
    # расширить при добавлении новых кодов
}


def _get_access_level(employee) -> str:
    """Определяет уровень доступа сотрудника для MES (high/medium/low)."""
    from django.utils import timezone
    today = timezone.now().date()
    rights = employee.accessright_set.filter(
        expires_at__isnull=True
    ) | employee.accessright_set.filter(expires_at__gte=today)
    for right in rights.select_related('access_level').order_by('-id'):
        code = right.access_level.code.lower()
        if code in _ACCESS_LEVEL_MAP:
            return _ACCESS_LEVEL_MAP[code]
    return 'low'


def _is_work_time() -> bool:
    now = datetime.now().time()
    return _WORK_START <= now <= _WORK_END


def _get_failed_attempts(employee) -> int:
    """Считает последовательные неудачные попытки входа по биометрии."""
    from .models import AccessHistory
    recent = AccessHistory.objects.filter(
        employee=employee,
        method='biometric',
    ).order_by('-datetime')[:10]

    count = 0
    for entry in recent:
        if entry.result == 'denied':
            count += 1
        else:
            break
    return count


def make_decision(employee, confidence: int, zone: str = 'main') -> dict:
    """
    Собирает все параметры и вызывает МИВАР-движок.

    Возвращает словарь из run_engine:
      {decision, message, explanation, rule, chain, all_checked}
    """
    data = {
        'confidence': confidence,
        'status': employee.status,          # 'active' / 'blocked' / 'fired'
        'access_level': _get_access_level(employee),
        'zone': zone,
        'is_work_time': _is_work_time(),
        'failed_attempts': _get_failed_attempts(employee),
    }
    # MES понимает только 'active'/'blocked'; 'fired' = blocked
    if data['status'] == 'fired':
        data['status'] = 'blocked'

    return run_engine(data)
