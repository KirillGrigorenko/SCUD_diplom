from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods

from .engine import run_mes
from .thresholds import get as get_thresholds, save as save_thresholds


def index(request):
    thresholds = get_thresholds()
    return render(request, 'mes_app/index.html', {'thresholds': thresholds})


@require_http_methods(["POST"])
def analyze(request):
    POST = request.POST

    confidence      = int(POST.get('confidence', 80))
    status          = POST.get('status', 'active')
    access_level    = POST.get('access_level', 'medium')
    zone            = POST.get('zone', 'main')
    is_work_time    = POST.get('is_work_time') == 'on'
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

    for item in result.get('chain', []):
        rule_obj = next((r for r in __import__('mes_app.rules', fromlist=['RULES']).RULES if r['id'] == item['id']), None)
        if rule_obj:
            item['result'] = rule_obj['result']

    return render(request, 'mes_app/result.html', {
        'data':   data,
        'result': result,
    })


def settings_view(request):
    if request.GET.get('reset'):
        save_thresholds({})  # сохраняем пустой dict → defaults применятся при get()
        return redirect('settings')

    if request.method == 'POST':
        try:
            group1_min    = int(request.POST.get('group1_min', 80))
            group3_low    = int(request.POST.get('group3_low', 50))
            lockout_count = int(request.POST.get('lockout_count', 3))

            # sanity bounds
            group1_min    = max(1, min(100, group1_min))
            group3_low    = max(0, min(group1_min - 1, group3_low))
            lockout_count = max(1, min(20, lockout_count))

            save_thresholds({
                'group1_min':    group1_min,
                'group3_low':    group3_low,
                'lockout_count': lockout_count,
            })
        except (ValueError, TypeError):
            pass
        return redirect('settings')

    thresholds = get_thresholds()
    return render(request, 'mes_app/settings.html', {'thresholds': thresholds})
