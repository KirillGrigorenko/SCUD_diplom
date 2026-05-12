from django.urls import path

from .api import LoginAPIView, LogoutAPIView, EmployeeDetailAPIView, EmployeeListAPIView


urlpatterns = [
    path('auth/login/', LoginAPIView.as_view(), name='api_login'),
    path('auth/logout/', LogoutAPIView.as_view(), name='api_logout'),
    path('employees/', EmployeeListAPIView.as_view(), name='api_employees'),
    path('employees/<int:pk>/', EmployeeDetailAPIView.as_view(), name='api_employee_detail'),
]
