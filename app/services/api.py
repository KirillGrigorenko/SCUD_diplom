import re

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

from rest_framework import permissions, status
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView, RetrieveAPIView

from .models import AccessHistory, BiometricData, Department, Employee, EmployeeCard, Position
from .serializers import EmployeeSerializer
from .palm_bio import detect_face, get_face_hash
from .mes_client import make_decision

# ---------------------------------------------------------------------------
# Общие переиспользуемые схемы ответов
# ---------------------------------------------------------------------------

_resp_403 = openapi.Response('Нет доступа', openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={'error': openapi.Schema(type=openapi.TYPE_STRING, example='Нет доступа')},
))
_resp_400 = openapi.Response('Ошибка валидации', openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={'error': openapi.Schema(type=openapi.TYPE_STRING)},
))
_resp_404 = openapi.Response('Не найдено', openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={'detail': openapi.Schema(type=openapi.TYPE_STRING, example='Not found.')},
))


# ---------------------------------------------------------------------------
# Авторизация
# ---------------------------------------------------------------------------

@method_decorator(csrf_exempt, name='dispatch')
class LoginAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(
        tags=['Авторизация'],
        operation_summary='Вход по логину и паролю',
        operation_description=(
            'Создаёт сессию Django. После успешного входа браузер получает '
            'cookie `sessionid`, которую нужно передавать во всех последующих '
            'запросах. Параметр `remember_me=true` продлевает сессию на 30 дней.'
        ),
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['username', 'password'],
            properties={
                'username': openapi.Schema(type=openapi.TYPE_STRING, description='Логин пользователя', example='admin'),
                'password': openapi.Schema(type=openapi.TYPE_STRING, description='Пароль', example='admin123'),
                'remember_me': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Запомнить на 30 дней', default=False),
            },
        ),
        responses={
            200: openapi.Response('Успешный вход', openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={'detail': openapi.Schema(type=openapi.TYPE_STRING, example='Logged in successfully.')},
            )),
            400: openapi.Response('Не переданы логин или пароль', openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={'detail': openapi.Schema(type=openapi.TYPE_STRING)},
            )),
            401: openapi.Response('Неверные учётные данные', openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={'detail': openapi.Schema(type=openapi.TYPE_STRING, example='Invalid credentials.')},
            )),
        },
    )
    def post(self, request, *args, **kwargs):
        username = request.data.get('username')
        password = request.data.get('password')
        remember = request.data.get('remember_me')

        if not username or not password:
            return Response({'detail': 'Username and password are required.'}, status=status.HTTP_400_BAD_REQUEST)

        user = authenticate(request, username=username, password=password)
        if not user:
            return Response({'detail': 'Invalid credentials.'}, status=status.HTTP_401_UNAUTHORIZED)

        login(request, user)

        if remember:
            request.session.set_expiry(30 * 24 * 60 * 60)
        else:
            request.session.set_expiry(0)

        return Response({'detail': 'Logged in successfully.'})


@method_decorator(csrf_exempt, name='dispatch')
class LogoutAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(
        tags=['Авторизация'],
        operation_summary='Выход из системы',
        operation_description='Уничтожает текущую сессию Django.',
        responses={
            200: openapi.Response('Сессия завершена', openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={'detail': openapi.Schema(type=openapi.TYPE_STRING, example='Logged out successfully.')},
            )),
        },
    )
    def post(self, request, *args, **kwargs):
        logout(request)
        return Response({'detail': 'Logged out successfully.'})


class MeAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        tags=['Авторизация'],
        operation_summary='Текущий пользователь',
        operation_description=(
            'Возвращает данные аутентифицированного пользователя. '
            'Поле `is_admin` — `true` для суперпользователей и staff. '
            'Поле `employee_id` — `null` для администраторов без привязанного сотрудника.'
        ),
        responses={
            200: openapi.Response('Данные пользователя', openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'id': openapi.Schema(type=openapi.TYPE_INTEGER, example=1),
                    'username': openapi.Schema(type=openapi.TYPE_STRING, example='admin'),
                    'is_admin': openapi.Schema(type=openapi.TYPE_BOOLEAN, example=True),
                    'employee_id': openapi.Schema(type=openapi.TYPE_INTEGER, nullable=True, example=5),
                },
            )),
            403: _resp_403,
        },
    )
    def get(self, request):
        user = request.user
        is_admin = hasattr(user, 'administrator') or user.is_staff or user.is_superuser
        employee_id = user.employee.id if hasattr(user, 'employee') else None
        return Response({
            'id': user.id,
            'username': user.username,
            'is_admin': is_admin,
            'employee_id': employee_id,
        })


# ---------------------------------------------------------------------------
# Сотрудники
# ---------------------------------------------------------------------------

class EmployeeListAPIView(ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = EmployeeSerializer

    def get_queryset(self):
        user = self.request.user
        if hasattr(user, 'administrator') or user.is_staff or user.is_superuser:
            return Employee.objects.select_related('employeecard__position__department').all()
        if hasattr(user, 'employee'):
            return Employee.objects.select_related('employeecard__position__department').filter(user=user)
        return Employee.objects.none()

    @swagger_auto_schema(
        tags=['Сотрудники'],
        operation_summary='Список сотрудников',
        operation_description=(
            'Администратор получает всех сотрудников. '
            'Обычный сотрудник — только свою запись.'
        ),
        responses={
            200: EmployeeSerializer(many=True),
            403: _resp_403,
        },
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


class EmployeeDetailAPIView(RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = EmployeeSerializer
    queryset = Employee.objects.select_related('employeecard__position__department').all()

    def get_object(self):
        obj = super().get_object()
        user = self.request.user
        if hasattr(user, 'administrator') or user.is_staff or user.is_superuser:
            return obj
        if hasattr(user, 'employee') and user.employee.id == obj.id:
            return obj
        self.permission_denied(self.request, message='Not allowed to view this employee.')

    @swagger_auto_schema(
        tags=['Сотрудники'],
        operation_summary='Карточка сотрудника',
        operation_description=(
            'Администратор может просматривать любого сотрудника. '
            'Обычный сотрудник — только свою карточку.'
        ),
        responses={
            200: EmployeeSerializer(),
            403: _resp_403,
            404: _resp_404,
        },
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)


@method_decorator(csrf_exempt, name='dispatch')
class EmployeeCreateAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    @swagger_auto_schema(
        tags=['Сотрудники'],
        operation_summary='Создать сотрудника',
        operation_description=(
            'Создаёт учётную запись (`User`) и объект `Employee`. '
            'Дополнительно можно передать данные карточки (паспорт, должность, образование). '
            'Только для администраторов.'
        ),
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['username', 'password', 'last_name', 'first_name', 'hire_date'],
            properties={
                'username': openapi.Schema(type=openapi.TYPE_STRING, description='Логин', example='ivanov_iv'),
                'password': openapi.Schema(type=openapi.TYPE_STRING, description='Пароль'),
                'last_name': openapi.Schema(type=openapi.TYPE_STRING, description='Фамилия', example='Иванов'),
                'first_name': openapi.Schema(type=openapi.TYPE_STRING, description='Имя', example='Иван'),
                'middle_name': openapi.Schema(type=openapi.TYPE_STRING, description='Отчество', example='Иванович'),
                'hire_date': openapi.Schema(type=openapi.TYPE_STRING, format='date', description='Дата найма', example='2024-01-15'),
                'fire_date': openapi.Schema(type=openapi.TYPE_STRING, format='date', description='Дата увольнения (если уволен)'),
                'status': openapi.Schema(type=openapi.TYPE_STRING, enum=['active', 'fired', 'blocked'], description='Статус', default='active'),
                'photo': openapi.Schema(type=openapi.TYPE_FILE, description='Фото сотрудника (JPEG/PNG)'),
                'inn': openapi.Schema(type=openapi.TYPE_STRING, description='ИНН (ровно 12 цифр)', example='123456789012'),
                'position_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID должности'),
                'passport_series': openapi.Schema(type=openapi.TYPE_STRING, description='Серия паспорта', example='4521'),
                'passport_number': openapi.Schema(type=openapi.TYPE_STRING, description='Номер паспорта', example='123456'),
                'citizenship': openapi.Schema(type=openapi.TYPE_STRING, description='Гражданство', example='Россия'),
                'address': openapi.Schema(type=openapi.TYPE_STRING, description='Адрес прописки'),
                'snils': openapi.Schema(type=openapi.TYPE_STRING, description='СНИЛС', example='123-456-789 00'),
            },
        ),
        responses={
            201: EmployeeSerializer(),
            400: _resp_400,
            403: _resp_403,
        },
    )
    def post(self, request):
        if not (hasattr(request.user, 'administrator') or request.user.is_staff or request.user.is_superuser):
            return Response({'error': 'Нет доступа'}, status=403)

        username = (request.data.get('username') or '').strip()
        password = (request.data.get('password') or '').strip()
        last_name = (request.data.get('last_name') or '').strip()
        first_name = (request.data.get('first_name') or '').strip()
        middle_name = (request.data.get('middle_name') or '').strip()
        hire_date = (request.data.get('hire_date') or '').strip()
        emp_status = request.data.get('status', 'active')
        inn = (request.data.get('inn') or '').strip()

        if not all([username, password, last_name, first_name, hire_date]):
            return Response({'error': 'Заполните все обязательные поля.'}, status=400)

        if inn and not re.fullmatch(r'\d{12}', inn):
            return Response({'error': 'ИНН должен содержать ровно 12 цифр.'}, status=400)

        if User.objects.filter(username=username).exists():
            return Response({'error': f'Пользователь «{username}» уже существует.'}, status=400)

        user = User.objects.create_user(username=username, password=password)
        employee = Employee.objects.create(
            user=user,
            last_name=last_name,
            first_name=first_name,
            middle_name=middle_name,
            hire_date=hire_date,
            status=emp_status,
        )

        photo_file = request.FILES.get('photo')
        if photo_file:
            from .views import upload_photo
            key = f'avatars/{employee.pk}'
            upload_photo(photo_file, key)
            employee.photo = key
            employee.save()

        position_id = (request.data.get('position_id') or request.data.get('position') or '').strip()
        passport_series = request.data.get('passport_series', '')
        passport_number = request.data.get('passport_number', '')
        citizenship = request.data.get('citizenship', '')
        address = request.data.get('address', '')
        snils = request.data.get('snils', '')

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

        employee.refresh_from_db()
        return Response(EmployeeSerializer(employee).data, status=201)


@method_decorator(csrf_exempt, name='dispatch')
class EmployeeUpdateAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    @swagger_auto_schema(
        tags=['Сотрудники'],
        operation_summary='Обновить данные сотрудника',
        operation_description=(
            'Частичное обновление (PATCH): передавайте только те поля, которые нужно изменить. '
            'Поддерживает загрузку нового фото. Только для администраторов.'
        ),
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'last_name': openapi.Schema(type=openapi.TYPE_STRING, description='Фамилия'),
                'first_name': openapi.Schema(type=openapi.TYPE_STRING, description='Имя'),
                'middle_name': openapi.Schema(type=openapi.TYPE_STRING, description='Отчество'),
                'hire_date': openapi.Schema(type=openapi.TYPE_STRING, format='date', description='Дата найма'),
                'status': openapi.Schema(type=openapi.TYPE_STRING, enum=['active', 'fired', 'blocked'], description='Статус'),
                'photo': openapi.Schema(type=openapi.TYPE_FILE, description='Новое фото'),
                'inn': openapi.Schema(type=openapi.TYPE_STRING, description='ИНН (ровно 12 цифр)'),
                'position_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID должности'),
                'passport_series': openapi.Schema(type=openapi.TYPE_STRING, description='Серия паспорта'),
                'passport_number': openapi.Schema(type=openapi.TYPE_STRING, description='Номер паспорта'),
                'citizenship': openapi.Schema(type=openapi.TYPE_STRING, description='Гражданство'),
                'address': openapi.Schema(type=openapi.TYPE_STRING, description='Адрес'),
                'snils': openapi.Schema(type=openapi.TYPE_STRING, description='СНИЛС'),
            },
        ),
        responses={
            200: EmployeeSerializer(),
            400: _resp_400,
            403: _resp_403,
            404: _resp_404,
        },
    )
    def patch(self, request, pk):
        if not (hasattr(request.user, 'administrator') or request.user.is_staff or request.user.is_superuser):
            return Response({'error': 'Нет доступа'}, status=403)

        employee = get_object_or_404(Employee, pk=pk)

        for field in ('last_name', 'first_name', 'middle_name', 'hire_date', 'status'):
            if field in request.data:
                setattr(employee, field, request.data[field])

        photo_file = request.FILES.get('photo')
        if photo_file:
            from .views import upload_photo
            key = f'avatars/{employee.pk}'
            upload_photo(photo_file, key)
            employee.photo = key

        inn = (request.data.get('inn') or '').strip()
        if inn and not re.fullmatch(r'\d{12}', inn):
            return Response({'error': 'ИНН должен содержать ровно 12 цифр.'}, status=400)

        employee.save()

        card, _ = EmployeeCard.objects.get_or_create(employee=employee)
        for field in ('passport_series', 'passport_number', 'citizenship', 'address', 'snils'):
            if field in request.data:
                setattr(card, field, request.data[field])
        if inn or 'inn' in request.data:
            card.inn = inn

        position_id = (request.data.get('position_id') or request.data.get('position') or '').strip()
        if 'position_id' in request.data or 'position' in request.data:
            if position_id:
                try:
                    card.position = Position.objects.get(pk=position_id)
                except Position.DoesNotExist:
                    card.position = None
            else:
                card.position = None

        card.save()
        return Response(EmployeeSerializer(employee).data)


# ---------------------------------------------------------------------------
# Справочники
# ---------------------------------------------------------------------------

class PositionListAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        tags=['Справочники'],
        operation_summary='Список должностей',
        operation_description='Возвращает все должности с привязанным отделом.',
        responses={
            200: openapi.Response('Список должностей', openapi.Schema(
                type=openapi.TYPE_ARRAY,
                items=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'pk': openapi.Schema(type=openapi.TYPE_INTEGER, example=1),
                        'name': openapi.Schema(type=openapi.TYPE_STRING, example='Инженер'),
                        'department': openapi.Schema(type=openapi.TYPE_STRING, nullable=True, example='ИТ-отдел'),
                        'department_id': openapi.Schema(type=openapi.TYPE_INTEGER, nullable=True, example=2),
                        'label': openapi.Schema(type=openapi.TYPE_STRING, example='Инженер · ИТ-отдел'),
                    },
                ),
            )),
            403: _resp_403,
        },
    )
    def get(self, request):
        positions = Position.objects.select_related('department').all()
        data = [
            {
                'pk': p.pk,
                'name': p.name,
                'department': p.department.name if p.department else None,
                'department_id': p.department.pk if p.department else None,
                'label': f'{p.name} · {p.department.name}' if p.department else p.name,
            }
            for p in positions
        ]
        return Response(data)


class DepartmentListAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        tags=['Справочники'],
        operation_summary='Список отделов',
        operation_description='Возвращает все отделы организации.',
        responses={
            200: openapi.Response('Список отделов', openapi.Schema(
                type=openapi.TYPE_ARRAY,
                items=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'pk': openapi.Schema(type=openapi.TYPE_INTEGER, example=1),
                        'name': openapi.Schema(type=openapi.TYPE_STRING, example='ИТ-отдел'),
                    },
                ),
            )),
            403: _resp_403,
        },
    )
    def get(self, request):
        departments = Department.objects.all()
        data = [{'pk': d.pk, 'name': d.name} for d in departments]
        return Response(data)


# ---------------------------------------------------------------------------
# История проходов
# ---------------------------------------------------------------------------

_history_item_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'id': openapi.Schema(type=openapi.TYPE_INTEGER),
        'datetime': openapi.Schema(type=openapi.TYPE_STRING, format='date-time', example='2024-05-14T09:15:00+03:00'),
        'employee_id': openapi.Schema(type=openapi.TYPE_INTEGER),
        'employee_name': openapi.Schema(type=openapi.TYPE_STRING, example='Иванов Иван'),
        'access_point': openapi.Schema(type=openapi.TYPE_STRING, example='main (laptop)'),
        'result': openapi.Schema(type=openapi.TYPE_STRING, enum=['allowed', 'denied', 'warning']),
        'method': openapi.Schema(type=openapi.TYPE_STRING, enum=['password', 'biometric']),
        'camera_source': openapi.Schema(type=openapi.TYPE_STRING, nullable=True, enum=['laptop', 'external']),
        'confidence': openapi.Schema(type=openapi.TYPE_INTEGER, nullable=True, example=87, description='Уверенность ИИ, 0–100'),
    },
)


class AllHistoryAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        tags=['История'],
        operation_summary='Глобальная история проходов',
        operation_description=(
            'Возвращает до 500 последних записей по всем сотрудникам. '
            'Только для администраторов. Поддерживает фильтрацию.'
        ),
        manual_parameters=[
            openapi.Parameter('employee', openapi.IN_QUERY, type=openapi.TYPE_STRING,
                              description='Поиск по ФИО (подстрока)'),
            openapi.Parameter('result', openapi.IN_QUERY, type=openapi.TYPE_STRING,
                              enum=['allowed', 'denied', 'warning'],
                              description='Фильтр по результату'),
            openapi.Parameter('date_from', openapi.IN_QUERY, type=openapi.TYPE_STRING,
                              format='date', description='Начало периода (YYYY-MM-DD)'),
            openapi.Parameter('date_to', openapi.IN_QUERY, type=openapi.TYPE_STRING,
                              format='date', description='Конец периода (YYYY-MM-DD)'),
        ],
        responses={
            200: openapi.Response('Список записей', openapi.Schema(
                type=openapi.TYPE_ARRAY, items=_history_item_schema,
            )),
            403: _resp_403,
        },
    )
    def get(self, request):
        if not (hasattr(request.user, 'administrator') or request.user.is_staff or request.user.is_superuser):
            return Response({'error': 'Нет доступа'}, status=403)

        qs = AccessHistory.objects.select_related('employee').order_by('-datetime')

        employee_q = request.query_params.get('employee', '').strip()
        if employee_q:
            qs = qs.filter(
                Q(employee__last_name__icontains=employee_q) |
                Q(employee__first_name__icontains=employee_q) |
                Q(employee__middle_name__icontains=employee_q)
            )

        result_f = request.query_params.get('result', '').strip()
        if result_f in ('allowed', 'denied', 'warning'):
            qs = qs.filter(result=result_f)

        date_from = request.query_params.get('date_from', '').strip()
        if date_from:
            qs = qs.filter(datetime__date__gte=date_from)

        date_to = request.query_params.get('date_to', '').strip()
        if date_to:
            qs = qs.filter(datetime__date__lte=date_to)

        qs = qs[:500]

        data = [
            {
                'id': h.id,
                'datetime': h.datetime.isoformat(),
                'employee_id': h.employee.id,
                'employee_name': str(h.employee),
                'access_point': h.access_point,
                'result': h.result,
                'method': h.method,
                'camera_source': h.camera_source,
                'confidence': h.confidence,
            }
            for h in qs
        ]
        return Response(data)


_employee_history_item_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'id': openapi.Schema(type=openapi.TYPE_INTEGER),
        'datetime': openapi.Schema(type=openapi.TYPE_STRING, format='date-time'),
        'access_point': openapi.Schema(type=openapi.TYPE_STRING),
        'result': openapi.Schema(type=openapi.TYPE_STRING, enum=['allowed', 'denied', 'warning']),
        'method': openapi.Schema(type=openapi.TYPE_STRING, enum=['password', 'biometric']),
        'camera_source': openapi.Schema(type=openapi.TYPE_STRING, nullable=True),
        'confidence': openapi.Schema(type=openapi.TYPE_INTEGER, nullable=True),
    },
)


class EmployeeHistoryAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        tags=['История'],
        operation_summary='История проходов сотрудника',
        operation_description=(
            'Возвращает 100 последних записей для конкретного сотрудника. '
            'Администратор видит историю любого сотрудника. '
            'Обычный сотрудник — только свою.'
        ),
        responses={
            200: openapi.Response('Список записей', openapi.Schema(
                type=openapi.TYPE_ARRAY, items=_employee_history_item_schema,
            )),
            403: _resp_403,
            404: _resp_404,
        },
    )
    def get(self, request, pk):
        employee = get_object_or_404(Employee, pk=pk)
        user = request.user
        if not (hasattr(user, 'administrator') or user.is_staff or user.is_superuser):
            if not (hasattr(user, 'employee') and user.employee.id == pk):
                return Response({'error': 'Нет доступа'}, status=403)

        history = AccessHistory.objects.filter(employee=employee).order_by('-datetime')[:100]
        data = [
            {
                'id': h.id,
                'datetime': h.datetime.isoformat(),
                'access_point': h.access_point,
                'result': h.result,
                'method': h.method,
                'camera_source': h.camera_source,
                'confidence': h.confidence,
            }
            for h in history
        ]
        return Response(data)


# ---------------------------------------------------------------------------
# Биометрия
# ---------------------------------------------------------------------------

@method_decorator(csrf_exempt, name='dispatch')
class BiometricLoginAPIView(APIView):
    permission_classes = [permissions.AllowAny]
    parser_classes = [MultiPartParser, FormParser]

    @swagger_auto_schema(
        tags=['Биометрия'],
        operation_summary='Вход по биометрии ладони',
        operation_description=(
            'Принимает фото ладони и логин сотрудника. '
            'Передаёт изображение в vein-service для сравнения с сохранённым хэшем. '
            'Результат обрабатывается МИВАР-движком: `allowed` (≥80%) / `warning` (50–79%) / `denied` (<50%). '
            'При `allowed` или `warning` создаётся Django-сессия. '
            'Запись в `AccessHistory` создаётся **всегда**.'
        ),
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['username', 'image'],
            properties={
                'username': openapi.Schema(type=openapi.TYPE_STRING, description='Логин сотрудника', example='ivanov_iv'),
                'image': openapi.Schema(type=openapi.TYPE_FILE, description='Фото ладони (JPEG/PNG)'),
                'zone': openapi.Schema(type=openapi.TYPE_STRING, description='Зона входа', default='main',
                                       enum=['main', 'restricted', 'server']),
                'camera_source': openapi.Schema(type=openapi.TYPE_STRING, description='Источник камеры',
                                                default='laptop', enum=['laptop', 'external']),
            },
        ),
        responses={
            200: openapi.Response('Доступ разрешён или предупреждение', openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'decision': openapi.Schema(type=openapi.TYPE_STRING, enum=['allowed', 'warning']),
                    'message': openapi.Schema(type=openapi.TYPE_STRING, example='Доступ разрешён'),
                    'confidence': openapi.Schema(type=openapi.TYPE_INTEGER, example=92),
                },
            )),
            400: _resp_400,
            403: openapi.Response('Доступ запрещён', openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'decision': openapi.Schema(type=openapi.TYPE_STRING, example='denied'),
                    'message': openapi.Schema(type=openapi.TYPE_STRING),
                    'confidence': openapi.Schema(type=openapi.TYPE_INTEGER, example=30),
                },
            )),
            404: _resp_404,
        },
    )
    def post(self, request):
        username = (request.data.get('username') or '').strip()
        zone = (request.data.get('zone') or 'main').strip()
        camera_source = (request.data.get('camera_source') or 'laptop').strip()
        image_file = request.FILES.get('image')

        if not username:
            return Response({'error': 'Укажите имя пользователя.'}, status=400)
        if not image_file:
            return Response({'error': 'Изображение не передано.'}, status=400)

        try:
            user = User.objects.get(username=username)
            employee = user.employee
        except (User.DoesNotExist, Employee.DoesNotExist):
            return Response({'error': 'Сотрудник не найден.'}, status=404)

        image_bytes = image_file.read()
        confidence = detect_face(image_bytes, employee)
        mes_result = make_decision(employee, confidence, zone)
        decision = mes_result['decision']

        log_result = decision
        AccessHistory.objects.create(
            employee=employee,
            access_point=f'{zone} ({camera_source})',
            result=log_result,
            method='biometric',
            camera_source=camera_source,
            confidence=confidence,
        )

        if decision in ('allowed', 'warning'):
            login(request, user)
            request.session.set_expiry(0)
            return Response({
                'decision': decision,
                'message': mes_result['message'],
                'confidence': confidence,
            })

        return Response({
            'decision': 'denied',
            'message': mes_result['message'],
            'confidence': confidence,
        }, status=403)


@method_decorator(csrf_exempt, name='dispatch')
class BiometricRegisterAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    @swagger_auto_schema(
        tags=['Биометрия'],
        operation_summary='Зарегистрировать биометрию ладони',
        operation_description=(
            'Отправляет фото ладони в vein-service (`POST /embed`), получает embedding '
            'и сохраняет его в `BiometricData.palm_hash`. '
            'Одновременно сохраняет фото как отдельный биометрический снимок в MinIO (ключ `bio_<id>`). '
            'Только для администраторов.'
        ),
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['employee_id', 'image'],
            properties={
                'employee_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID сотрудника', example=5),
                'image': openapi.Schema(type=openapi.TYPE_FILE, description='Фото ладони (JPEG/PNG)'),
            },
        ),
        responses={
            200: openapi.Response('Биометрия зарегистрирована', openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'status': openapi.Schema(type=openapi.TYPE_STRING, example='registered'),
                    'registered_at': openapi.Schema(type=openapi.TYPE_STRING, format='date', example='2024-05-14'),
                    'photo_url': openapi.Schema(type=openapi.TYPE_STRING, nullable=True,
                                                example='http://localhost:9000/skud/bio_5.jpg',
                                                description='URL биометрического снимка (не аватарки)'),
                    'photo_error': openapi.Schema(type=openapi.TYPE_STRING, nullable=True,
                                                  description='Ошибка сохранения снимка, если была'),
                },
            )),
            400: _resp_400,
            403: _resp_403,
            503: openapi.Response('Vein-service недоступен', openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={'error': openapi.Schema(type=openapi.TYPE_STRING)},
            )),
        },
    )
    def post(self, request):
        is_admin = (hasattr(request.user, 'administrator')
                    or request.user.is_staff
                    or request.user.is_superuser)
        if not is_admin:
            return Response({'error': 'Нет доступа'}, status=403)

        employee_id = request.data.get('employee_id')
        image_file = request.FILES.get('image')

        if not employee_id or not image_file:
            return Response({'error': 'Передайте employee_id и image.'}, status=400)

        employee = get_object_or_404(Employee, pk=employee_id)
        image_bytes = image_file.read()

        try:
            palm_hash = get_face_hash(image_bytes)
        except Exception as e:
            return Response({'error': f'Vein-service недоступен: {e}'}, status=503)

        from django.utils import timezone
        bio, _ = BiometricData.objects.get_or_create(employee=employee)
        bio.palm_hash = palm_hash
        bio.palm_registered_at = timezone.now().date()
        bio.status = True
        bio.save()

        import io as _io
        photo_url = None
        photo_error = None
        try:
            from .views import upload_photo, get_minio_url
            bio_key = f'biometrics/{employee.pk}'
            upload_photo(_io.BytesIO(image_bytes), bio_key)
            photo_url = get_minio_url(bio_key)
        except Exception as e:
            photo_error = str(e)

        return Response({
            'status': 'registered',
            'registered_at': bio.palm_registered_at.isoformat(),
            'photo_url': photo_url,
            'photo_error': photo_error,
        })


class BiometricStatusAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        tags=['Биометрия'],
        operation_summary='Статус биометрии сотрудника',
        operation_description=(
            'Возвращает, зарегистрирована ли биометрия ладони. '
            'Администратор видит статус любого сотрудника. '
            'Обычный сотрудник — только свой.'
        ),
        responses={
            200: openapi.Response('Статус биометрии', openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'registered': openapi.Schema(type=openapi.TYPE_BOOLEAN, example=True),
                    'registered_at': openapi.Schema(type=openapi.TYPE_STRING, format='date',
                                                    nullable=True, example='2024-05-14'),
                },
            )),
            403: _resp_403,
            404: _resp_404,
        },
    )
    def get(self, request, pk):
        employee = get_object_or_404(Employee, pk=pk)
        user = request.user
        is_admin = hasattr(user, 'administrator') or user.is_staff or user.is_superuser
        is_self = hasattr(user, 'employee') and user.employee.id == pk
        if not is_admin and not is_self:
            return Response({'error': 'Нет доступа'}, status=403)

        try:
            bio = employee.biometricdata
            registered = bool(bio.palm_hash and bio.status)
            registered_at = bio.palm_registered_at.isoformat() if bio.palm_registered_at else None
        except BiometricData.DoesNotExist:
            registered = False
            registered_at = None

        return Response({'registered': registered, 'registered_at': registered_at})
