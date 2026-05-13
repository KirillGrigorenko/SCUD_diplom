from django.shortcuts import render
from django.views.decorators.http import require_http_methods

from .engine import run_mes


def index(request):
    return render(request, 'mes_app/index.html')


@require_http_methods(["POST"])
def analyze(request):
    POST = request.POST

    confidence     = int(POST.get('confidence', 80))
    status         = POST.get('status', 'active')
    access_level   = POST.get('access_level', 'medium')
    zone           = POST.get('zone', 'main')
    is_work_time   = POST.get('is_work_time') == 'on'   # checkbox
    failed_attempts = int(POST.get('failed_attempts', 0))

    data = {
        'confidence':      confidence,
        'status':          status,
        'access_level':    access_level,
        'zone':            zone,
        'is_work_time':    is_work_time,
        'failed_attempts': failed_attempts,
    }

    result = run_mes(data)

    # Добавляем result поля из chain для отображения цвета
    for item in result.get('chain', []):
        rule_obj = next((r for r in __import__('mes_app.rules', fromlist=['RULES']).RULES if r['id'] == item['id']), None)
        if rule_obj:
            item['result'] = rule_obj['result']

    return render(request, 'mes_app/result.html', {
        'data':   data,
        'result': result,
    })
