import re

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

from rest_framework import permissions, status
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView, RetrieveAPIView

from .models import AccessHistory, Department, Employee, EmployeeCard, Position
from .serializers import EmployeeSerializer


@method_decorator(csrf_exempt, name='dispatch')
class LoginAPIView(APIView):
    permission_classes = [permissions.AllowAny]

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

    def post(self, request, *args, **kwargs):
        logout(request)
        return Response({'detail': 'Logged out successfully.'})


class MeAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

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


class EmployeeListAPIView(ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = EmployeeSerializer

    def get_queryset(self):
        user = self.request.user
        if hasattr(user, 'administrator'):
            return Employee.objects.select_related('employeecard__position__department').all()
        if hasattr(user, 'employee'):
            return Employee.objects.select_related('employeecard__position__department').filter(user=user)
        return Employee.objects.none()


class EmployeeDetailAPIView(RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = EmployeeSerializer
    queryset = Employee.objects.select_related('employeecard__position__department').all()

    def get_object(self):
        obj = super().get_object()
        user = self.request.user
        if hasattr(user, 'administrator'):
            return obj
        if hasattr(user, 'employee') and user.employee.id == obj.id:
            return obj
        self.permission_denied(self.request, message='Not allowed to view this employee.')


@method_decorator(csrf_exempt, name='dispatch')
class EmployeeUpdateAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def patch(self, request, pk):
        if not hasattr(request.user, 'administrator'):
            return Response({'error': 'Нет доступа'}, status=403)

        employee = get_object_or_404(Employee, pk=pk)

        for field in ('last_name', 'first_name', 'middle_name', 'hire_date', 'status'):
            if field in request.data:
                setattr(employee, field, request.data[field])

        photo_file = request.FILES.get('photo')
        if photo_file:
            from .views import upload_photo
            key = f'employee_{employee.pk}'
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


@method_decorator(csrf_exempt, name='dispatch')
class EmployeeCreateAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def post(self, request):
        if not hasattr(request.user, 'administrator'):
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
            key = f'employee_{employee.pk}'
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


class PositionListAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

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

    def get(self, request):
        departments = Department.objects.all()
        data = [{'pk': d.pk, 'name': d.name} for d in departments]
        return Response(data)


class AllHistoryAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        if not hasattr(request.user, 'administrator'):
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
        if result_f in ('allowed', 'denied'):
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
            }
            for h in qs
        ]
        return Response(data)


class EmployeeHistoryAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        employee = get_object_or_404(Employee, pk=pk)
        user = request.user
        if not hasattr(user, 'administrator'):
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
            }
            for h in history
        ]
        return Response(data)
