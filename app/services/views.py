from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Q
from django.contrib.auth.models import User
from .models import Employee, Administrator, AccessHistory, EmployeeCard, Position, Department, AccessLevel, AccessRight
from django.utils import timezone
from django.conf import settings
from minio import Minio
import io
import re
from PIL import Image

COUNTRIES = [
    'Россия', 'Беларусь', 'Казахстан', 'Украина', 'Узбекистан',
    'Таджикистан', 'Кыргызстан', 'Азербайджан', 'Армения', 'Грузия',
    'Молдова', 'Туркменистан', 'Германия', 'Франция', 'Италия',
    'Испания', 'Польша', 'Чехия', 'Австрия', 'Швейцария',
    'Нидерланды', 'Бельгия', 'Швеция', 'Норвегия', 'Финляндия',
    'Дания', 'Великобритания', 'США', 'Канада', 'Австралия',
    'Китай', 'Япония', 'Индия', 'Турция', 'Израиль',
    'ОАЭ', 'Бразилия', 'Аргентина', 'Мексика', 'Египет', 'Другое',
]


def get_minio_url(key, ext='jpg'):
    if not key:
        return '/static/img/no-photo.svg'
    public_host = getattr(settings, 'MINIO_PUBLIC_ENDPOINT', 'localhost:9000')
    return f'http://{public_host}/{settings.MINIO_BUCKET}/{key}.{ext}'


def _minio_client():
    return Minio(
        settings.MINIO_ENDPOINT,
        access_key=settings.MINIO_ACCESS_KEY,
        secret_key=settings.MINIO_SECRET_KEY,
        secure=False,
    )


def upload_photo(file, key):
    client = _minio_client()
    bucket = settings.MINIO_BUCKET

    if not client.bucket_exists(bucket):
        client.make_bucket(bucket)

    img = Image.open(file)
    if img.mode != 'RGB':
        img = img.convert('RGB')

    buf = io.BytesIO()
    img.save(buf, format='JPEG', quality=90)
    buf.seek(0)

    client.put_object(
        bucket,
        f'{key}.jpg',
        buf,
        length=buf.getbuffer().nbytes,
        content_type='image/jpeg',
    )


def login_view(request):
    if request.user.is_authenticated:
        return redirect_by_role(request.user)

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        remember = request.POST.get('remember_me')

        user = authenticate(request, username=username, password=password)

        if user:
            login(request, user)

            if remember:
                request.session.set_expiry(30 * 24 * 60 * 60)
            else:
                request.session.set_expiry(0)

            return redirect_by_role(user)
        else:
            return render(request, 'services/login.html', {'form': {'errors': True}, 'remember': bool(remember)})

    return render(request, 'services/login.html', {'remember': False})


def redirect_by_role(user):
    if hasattr(user, 'administrator'):
        return redirect('employee_list')
    elif hasattr(user, 'employee'):
        return redirect('employee_detail', pk=user.employee.id)
    else:
        return redirect('employee_list')


def logout_view(request):
    logout(request)
    return redirect('login')


@login_required(login_url='login')
def employee_list(request):
    if hasattr(request.user, 'employee') and not hasattr(request.user, 'administrator'):
        return redirect('employee_detail', pk=request.user.employee.id)

    query = request.GET.get('q', '').strip()
    department = request.GET.get('department', '').strip()
    status = request.GET.get('status', '').strip()

    employees = Employee.objects.select_related(
        'employeecard__position__department',
    ).all()

    if query:
        employees = employees.filter(
            Q(last_name__icontains=query)
            | Q(first_name__icontains=query)
            | Q(middle_name__icontains=query)
        )

    if department:
        employees = employees.filter(
            employeecard__position__department__name__icontains=department
        )

    if status:
        employees = employees.filter(status=status)

    for e in employees:
        e.image_url = get_minio_url(e.photo)
        if hasattr(e, 'employeecard') and e.employeecard and e.employeecard.position:
            e.position_name = str(e.employeecard.position)
            e.department_name = str(e.employeecard.position.department) if e.employeecard.position.department else ''
        else:
            e.position_name = ''
            e.department_name = ''

    stats = {
        'total': employees.count(),
        'active': employees.filter(status='active').count(),
        'fired': employees.filter(status='fired').count(),
        'blocked': employees.filter(status='blocked').count(),
    }

    return render(request, 'services/employee_list.html', {
        'employees': employees,
        'query': query,
        'department': department,
        'status': status,
        'stats': stats,
    })


@login_required(login_url='login')
def employee_detail(request, pk):
    if hasattr(request.user, 'employee') and not hasattr(request.user, 'administrator'):
        if request.user.employee.id != pk:
            return redirect('employee_detail', pk=request.user.employee.id)

    employee = get_object_or_404(Employee, pk=pk)
    employee.image_url = get_minio_url(employee.photo)
    history = AccessHistory.objects.filter(employee=employee).order_by('-datetime')
    access_rights = AccessRight.objects.filter(employee=employee).select_related('access_level')

    return render(request, 'services/employee_detail.html', {
        'employee': employee,
        'history': history,
        'access_rights': access_rights,
    })


@login_required(login_url='login')
def employee_edit(request, pk):
    if not hasattr(request.user, 'administrator'):
        return redirect('employee_detail', pk=pk)

    employee = get_object_or_404(Employee, pk=pk)
    error = None

    if request.method == 'POST':
        inn = request.POST.get('inn', '').strip()
        new_username = request.POST.get('new_username', '').strip()
        new_password = request.POST.get('new_password', '').strip()
        new_password2 = request.POST.get('new_password2', '').strip()

        if inn and not re.fullmatch(r'\d{12}', inn):
            error = 'ИНН должен содержать ровно 12 цифр.'
        elif new_username and User.objects.filter(username=new_username).exclude(pk=employee.user.pk).exists():
            error = f'Логин «{new_username}» уже занят.'
        elif new_password and new_password != new_password2:
            error = 'Пароли не совпадают.'

        if not error:
            employee.last_name = request.POST.get('last_name')
            employee.first_name = request.POST.get('first_name')
            employee.middle_name = request.POST.get('middle_name')
            employee.hire_date = request.POST.get('hire_date')
            employee.fire_date = request.POST.get('fire_date') or None
            employee.status = request.POST.get('status')

            photo_file = request.FILES.get('photo')
            if photo_file:
                try:
                    key = f'employee_{employee.pk}'
                    upload_photo(photo_file, key)
                    employee.photo = key
                except Exception as e:
                    error = f'Ошибка загрузки фото: {e}'

            employee.save()

            card, _ = EmployeeCard.objects.get_or_create(employee=employee)
            card.passport_series = request.POST.get('passport_series', '')
            card.passport_number = request.POST.get('passport_number', '')
            card.passport_date = request.POST.get('passport_date') or None
            card.passport_issued_by = request.POST.get('passport_issued_by', '')
            card.citizenship = request.POST.get('citizenship', '')
            card.address = request.POST.get('address', '')
            card.snils = request.POST.get('snils', '')
            card.inn = inn
            card.education_year = request.POST.get('education_year') or None
            card.education_name = request.POST.get('education_name', '')
            card.specialty = request.POST.get('specialty', '')
            card.diploma_number = request.POST.get('diploma_number', '')
            position_id = request.POST.get('position', '').strip()
            if position_id:
                try:
                    card.position = Position.objects.get(pk=position_id)
                except Position.DoesNotExist:
                    card.position = None
            else:
                card.position = None
            card.save()

            new_al_id = request.POST.get('new_access_level', '').strip()
            new_assigned_at = request.POST.get('new_assigned_at', '').strip()
            if new_al_id and new_assigned_at:
                try:
                    al = AccessLevel.objects.get(pk=new_al_id)
                    expires = request.POST.get('new_expires_at') or None
                    AccessRight.objects.create(
                        employee=employee,
                        access_level=al,
                        assigned_at=new_assigned_at,
                        expires_at=expires,
                    )
                except AccessLevel.DoesNotExist:
                    pass

            if new_username:
                employee.user.username = new_username
                employee.user.save(update_fields=['username'])
            if new_password:
                employee.user.set_password(new_password)
                employee.user.save()

            return redirect('employee_detail', pk=pk)

    bio = getattr(employee, 'biometricdata', None)
    return render(request, 'services/employee_edit.html', {
        'employee': employee,
        'card': getattr(employee, 'employeecard', None),
        'photo_url': get_minio_url(employee.photo),
        'positions': Position.objects.select_related('department').all(),
        'departments': Department.objects.all(),
        'access_levels': AccessLevel.objects.all(),
        'access_rights': AccessRight.objects.filter(employee=employee).select_related('access_level'),
        'countries': COUNTRIES,
        'error': error,
        'today': timezone.now().date().isoformat(),
        'bio_registered': bool(bio and bio.face_hash and bio.status),
        'bio_registered_at': bio.face_registered_at if bio and bio.face_hash and bio.status else None,
    })


@login_required(login_url='login')
def employee_create(request):
    if not hasattr(request.user, 'administrator'):
        return redirect('employee_list')

    positions = Position.objects.select_related('department').all()
    departments = Department.objects.all()
    access_levels = AccessLevel.objects.all()
    error = None

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        first_name = request.POST.get('first_name', '').strip()
        middle_name = request.POST.get('middle_name', '').strip()
        hire_date = request.POST.get('hire_date', '').strip()
        status = request.POST.get('status', 'active')
        inn = request.POST.get('inn', '').strip()

        if not username or not password or not last_name or not first_name or not hire_date:
            error = 'Заполните все обязательные поля.'
        elif inn and not re.fullmatch(r'\d{12}', inn):
            error = 'ИНН должен содержать ровно 12 цифр.'
        elif User.objects.filter(username=username).exists():
            error = f'Пользователь «{username}» уже существует.'
        else:
            user = User.objects.create_user(username=username, password=password)
            employee = Employee.objects.create(
                user=user,
                last_name=last_name,
                first_name=first_name,
                middle_name=middle_name,
                hire_date=hire_date,
                fire_date=request.POST.get('fire_date') or None,
                status=status,
            )

            photo_file = request.FILES.get('photo')
            if photo_file:
                try:
                    key = f'employee_{employee.pk}'
                    upload_photo(photo_file, key)
                    employee.photo = key
                    employee.save()
                except Exception as e:
                    error = f'Сотрудник создан, но фото не загружено: {e}'

            card = EmployeeCard.objects.create(employee=employee)
            position_id = request.POST.get('position', '').strip()
            if position_id:
                try:
                    card.position = Position.objects.get(pk=position_id)
                except Position.DoesNotExist:
                    pass
            card.passport_series = request.POST.get('passport_series', '')
            card.passport_number = request.POST.get('passport_number', '')
            card.passport_date = request.POST.get('passport_date') or None
            card.passport_issued_by = request.POST.get('passport_issued_by', '')
            card.citizenship = request.POST.get('citizenship', '')
            card.address = request.POST.get('address', '')
            card.snils = request.POST.get('snils', '')
            card.inn = inn
            card.education_year = request.POST.get('education_year') or None
            card.education_name = request.POST.get('education_name', '')
            card.specialty = request.POST.get('specialty', '')
            card.diploma_number = request.POST.get('diploma_number', '')
            card.save()

            new_al_id = request.POST.get('new_access_level', '').strip()
            new_assigned_at = request.POST.get('new_assigned_at', '').strip()
            if new_al_id and new_assigned_at:
                try:
                    al = AccessLevel.objects.get(pk=new_al_id)
                    expires = request.POST.get('new_expires_at') or None
                    AccessRight.objects.create(
                        employee=employee,
                        access_level=al,
                        assigned_at=new_assigned_at,
                        expires_at=expires,
                    )
                except AccessLevel.DoesNotExist:
                    pass

            face_b64 = request.POST.get('face_b64', '').strip()
            if face_b64:
                try:
                    import base64 as _b64
                    import io as _io
                    from django.utils import timezone as _tz
                    from .face_stub import get_face_hash
                    from .models import BiometricData
                    image_bytes = _b64.b64decode(face_b64)
                    bio, _ = BiometricData.objects.get_or_create(employee=employee)
                    bio.face_hash = get_face_hash(image_bytes)
                    bio.face_registered_at = _tz.now().date()
                    bio.status = True
                    bio.save()
                    if not employee.photo:
                        key = f'employee_{employee.pk}'
                        upload_photo(_io.BytesIO(image_bytes), key)
                        employee.photo = key
                        employee.save(update_fields=['photo'])
                except Exception:
                    pass

            if not error:
                return redirect('employee_detail', pk=employee.pk)

    return render(request, 'services/employee_create.html', {
        'positions': positions,
        'departments': departments,
        'access_levels': access_levels,
        'countries': COUNTRIES,
        'error': error,
        'post': request.POST,
        'today': timezone.now().date().isoformat(),
    })


@login_required(login_url='login')
def position_create(request):
    if not hasattr(request.user, 'administrator'):
        return JsonResponse({'error': 'Нет доступа'}, status=403)

    if request.method != 'POST':
        return JsonResponse({'error': 'Метод не поддерживается'}, status=405)

    name = request.POST.get('name', '').strip()
    if not name:
        return JsonResponse({'error': 'Название обязательно'}, status=400)

    position = Position(name=name)
    dept_id = request.POST.get('department', '').strip()
    if dept_id:
        try:
            position.department = Department.objects.get(pk=dept_id)
        except Department.DoesNotExist:
            pass
    position.save()

    label = position.name
    if position.department:
        label += f' · {position.department.name}'

    return JsonResponse({'pk': position.pk, 'label': label})


@login_required(login_url='login')
def employee_delete(request, pk):
    if not hasattr(request.user, 'administrator'):
        return redirect('employee_detail', pk=pk)
    if request.method != 'POST':
        return redirect('employee_detail', pk=pk)
    employee = get_object_or_404(Employee, pk=pk)
    user_account = employee.user
    employee.delete()
    user_account.delete()
    return redirect('employee_list')


@login_required(login_url='login')
def department_create(request):
    if not hasattr(request.user, 'administrator'):
        return JsonResponse({'error': 'Нет доступа'}, status=403)

    if request.method != 'POST':
        return JsonResponse({'error': 'Метод не поддерживается'}, status=405)

    name = request.POST.get('name', '').strip()
    if not name:
        return JsonResponse({'error': 'Название обязательно'}, status=400)

    department = Department.objects.create(name=name)
    return JsonResponse({'pk': department.pk, 'name': department.name})


@login_required(login_url='login')
def access_right_delete(request, pk):
    if not hasattr(request.user, 'administrator'):
        return redirect('employee_list')
    if request.method != 'POST':
        return redirect('employee_list')
    ar = get_object_or_404(AccessRight, pk=pk)
    employee_pk = ar.employee_id
    ar.delete()
    return redirect('employee_edit', pk=employee_pk)


@login_required(login_url='login')
def access_level_list(request):
    if not hasattr(request.user, 'administrator'):
        return redirect('employee_list')

    error = None
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        code = request.POST.get('code', '').strip()
        zone = request.POST.get('zone', '').strip()
        description = request.POST.get('description', '').strip()
        if not name or not code or not zone:
            error = 'Название, код и зона обязательны.'
        else:
            AccessLevel.objects.create(name=name, code=code, zone=zone, description=description)
            return redirect('access_level_list')

    levels = AccessLevel.objects.all()
    return render(request, 'services/access_level_list.html', {
        'levels': levels,
        'error': error,
    })


@login_required(login_url='login')
def access_level_delete(request, pk):
    if not hasattr(request.user, 'administrator'):
        return redirect('access_level_list')
    if request.method != 'POST':
        return redirect('access_level_list')
    get_object_or_404(AccessLevel, pk=pk).delete()
    return redirect('access_level_list')


@login_required(login_url='login')
def history_list(request):
    if not hasattr(request.user, 'administrator'):
        return redirect('employee_detail', pk=request.user.employee.id)

    qs = AccessHistory.objects.select_related('employee').order_by('-datetime')

    employee_q = request.GET.get('employee', '').strip()
    result_f = request.GET.get('result', '').strip()
    date_from = request.GET.get('date_from', '').strip()
    date_to = request.GET.get('date_to', '').strip()

    if employee_q:
        qs = qs.filter(
            Q(employee__last_name__icontains=employee_q) |
            Q(employee__first_name__icontains=employee_q) |
            Q(employee__middle_name__icontains=employee_q)
        )
    if result_f in ('allowed', 'denied', 'warning'):
        qs = qs.filter(result=result_f)
    if date_from:
        qs = qs.filter(datetime__date__gte=date_from)
    if date_to:
        qs = qs.filter(datetime__date__lte=date_to)

    total = qs.count()
    return render(request, 'services/history_list.html', {
        'history': qs[:500],
        'employee_q': employee_q,
        'result_f': result_f,
        'date_from': date_from,
        'date_to': date_to,
        'total': total,
        'allowed_count': qs.filter(result='allowed').count(),
        'denied_count': qs.filter(result__in=['denied', 'warning']).count(),
    })


import csv
from django.http import HttpResponse


@login_required(login_url='login')
def employee_history_export_csv(request, pk):
    if not hasattr(request.user, 'administrator'):
        return redirect('employee_list')
    employee = get_object_or_404(Employee, pk=pk)
    qs = AccessHistory.objects.filter(employee=employee).order_by('-datetime')

    response = HttpResponse(content_type='text/csv; charset=utf-8')
    name = f'{employee.last_name}_{employee.first_name}'
    response['Content-Disposition'] = f'attachment; filename="history_{name}.csv"'
    response.write('﻿')

    writer = csv.writer(response)
    writer.writerow(['Дата/время', 'Точка доступа', 'Результат', 'Способ', 'Камера', 'Уверенность ИИ (%)'])
    for h in qs:
        writer.writerow([
            h.datetime.strftime('%d.%m.%Y %H:%M:%S'),
            h.access_point,
            h.get_result_display(),
            h.get_method_display(),
            h.get_camera_source_display() if h.camera_source else '',
            h.confidence if h.confidence is not None else '',
        ])
    return response


@login_required(login_url='login')
def history_export_csv(request):
    if not hasattr(request.user, 'administrator'):
        return redirect('employee_list')

    qs = AccessHistory.objects.select_related('employee').order_by('-datetime')

    employee_q = request.GET.get('employee', '').strip()
    if employee_q:
        qs = qs.filter(
            Q(employee__last_name__icontains=employee_q) |
            Q(employee__first_name__icontains=employee_q) |
            Q(employee__middle_name__icontains=employee_q)
        )
    result_f = request.GET.get('result', '').strip()
    if result_f in ('allowed', 'denied', 'warning'):
        qs = qs.filter(result=result_f)
    date_from = request.GET.get('date_from', '').strip()
    if date_from:
        qs = qs.filter(datetime__date__gte=date_from)
    date_to = request.GET.get('date_to', '').strip()
    if date_to:
        qs = qs.filter(datetime__date__lte=date_to)

    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="history.csv"'
    response.write('﻿')  # BOM для Excel

    writer = csv.writer(response)
    writer.writerow(['Дата/время', 'Сотрудник', 'Точка доступа', 'Результат', 'Способ', 'Камера', 'Уверенность ИИ (%)'])
    for h in qs[:5000]:
        writer.writerow([
            h.datetime.strftime('%d.%m.%Y %H:%M:%S'),
            str(h.employee),
            h.access_point,
            h.get_result_display(),
            h.get_method_display(),
            h.get_camera_source_display() if h.camera_source else '',
            h.confidence if h.confidence is not None else '',
        ])
    return response
