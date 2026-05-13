from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Q
from django.contrib.auth.models import User
from .models import Employee, Administrator, AccessHistory, EmployeeCard, Position, Department
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
        return 'https://via.placeholder.com/460x520/0b0f1a/ffffff?text=Нет+фото'
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
    history = AccessHistory.objects.filter(employee=employee)

    return render(request, 'services/employee_detail.html', {
        'employee': employee,
        'history': history,
    })


@login_required(login_url='login')
def employee_edit(request, pk):
    if not hasattr(request.user, 'administrator'):
        return redirect('employee_detail', pk=pk)

    employee = get_object_or_404(Employee, pk=pk)
    error = None

    if request.method == 'POST':
        employee.last_name = request.POST.get('last_name')
        employee.first_name = request.POST.get('first_name')
        employee.middle_name = request.POST.get('middle_name')
        employee.hire_date = request.POST.get('hire_date')
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

        inn = request.POST.get('inn', '').strip()
        if inn and not re.fullmatch(r'\d{12}', inn):
            error = 'ИНН должен содержать ровно 12 цифр.'

        if not error:
            card, _ = EmployeeCard.objects.get_or_create(employee=employee)
            card.passport_series = request.POST.get('passport_series', '')
            card.passport_number = request.POST.get('passport_number', '')
            card.citizenship = request.POST.get('citizenship', '')
            card.address = request.POST.get('address', '')
            card.snils = request.POST.get('snils', '')
            card.inn = inn
            position_id = request.POST.get('position', '').strip()
            if position_id:
                try:
                    card.position = Position.objects.get(pk=position_id)
                except Position.DoesNotExist:
                    card.position = None
            else:
                card.position = None
            card.save()
            return redirect('employee_detail', pk=pk)

    bio = getattr(employee, 'biometricdata', None)
    return render(request, 'services/employee_edit.html', {
        'employee': employee,
        'card': getattr(employee, 'employeecard', None),
        'photo_url': get_minio_url(employee.photo),
        'positions': Position.objects.select_related('department').all(),
        'departments': Department.objects.all(),
        'countries': COUNTRIES,
        'error': error,
        'bio_registered': bool(bio and bio.face_hash and bio.status),
        'bio_registered_at': bio.face_registered_at if bio and bio.face_hash and bio.status else None,
    })


@login_required(login_url='login')
def employee_create(request):
    if not hasattr(request.user, 'administrator'):
        return redirect('employee_list')

    positions = Position.objects.select_related('department').all()
    departments = Department.objects.all()
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

            position_id = request.POST.get('position')
            passport_series = request.POST.get('passport_series', '')
            passport_number = request.POST.get('passport_number', '')
            citizenship = request.POST.get('citizenship', '')
            address = request.POST.get('address', '')
            snils = request.POST.get('snils', '')

            if any([position_id, passport_series, passport_number, citizenship, address, snils, inn]):
                card = EmployeeCard.objects.create(employee=employee)
                if position_id:
                    try:
                        card.position = Position.objects.get(pk=position_id)
                    except Position.DoesNotExist:
                        pass
                card.passport_series = passport_series
                card.passport_number = passport_number
                card.citizenship = citizenship
                card.address = address
                card.snils = snils
                card.inn = inn
                card.save()

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
                    # Если отдельное фото не загружено — используем фото с биометрии
                    if not employee.photo:
                        key = f'employee_{employee.pk}'
                        upload_photo(_io.BytesIO(image_bytes), key)
                        employee.photo = key
                        employee.save(update_fields=['photo'])
                except Exception:
                    pass  # биометрия необязательна, сотрудник уже создан

            if not error:
                return redirect('employee_detail', pk=employee.pk)

    return render(request, 'services/employee_create.html', {
        'positions': positions,
        'departments': departments,
        'countries': COUNTRIES,
        'error': error,
        'post': request.POST,
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
