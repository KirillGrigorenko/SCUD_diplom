from django.contrib.auth import authenticate, login, logout
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView, RetrieveAPIView

from .models import Employee
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

        # Set session expiry based on remember-me.
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


class EmployeeListAPIView(ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = EmployeeSerializer

    def get_queryset(self):
        user = self.request.user
        if hasattr(user, 'administrator'):
            return Employee.objects.all()
        try:
            return Employee.objects.filter(user=user)
        except Exception:
            return Employee.objects.none()


class EmployeeDetailAPIView(RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = EmployeeSerializer
    queryset = Employee.objects.all()

    def get_object(self):
        obj = super().get_object()
        user = self.request.user
        if hasattr(user, 'administrator'):
            return obj
        if hasattr(user, 'employee') and user.employee.id == obj.id:
            return obj
        self.permission_denied(self.request, message='Not allowed to view this employee.')
