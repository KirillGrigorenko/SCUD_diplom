from django.urls import path

from .api import (
    LoginAPIView, LogoutAPIView, MeAPIView,
    EmployeeListAPIView, EmployeeDetailAPIView,
    EmployeeCreateAPIView, EmployeeUpdateAPIView,
    PositionListAPIView, DepartmentListAPIView,
)

urlpatterns = [
    path('auth/login/', LoginAPIView.as_view(), name='api_login'),
    path('auth/logout/', LogoutAPIView.as_view(), name='api_logout'),
    path('auth/me/', MeAPIView.as_view(), name='api_me'),
    path('employees/', EmployeeListAPIView.as_view(), name='api_employees'),
    path('employees/create/', EmployeeCreateAPIView.as_view(), name='api_employee_create'),
    path('employees/<int:pk>/', EmployeeDetailAPIView.as_view(), name='api_employee_detail'),
    path('employees/<int:pk>/update/', EmployeeUpdateAPIView.as_view(), name='api_employee_update'),
    path('positions/', PositionListAPIView.as_view(), name='api_positions'),
    path('departments/', DepartmentListAPIView.as_view(), name='api_departments'),
]
