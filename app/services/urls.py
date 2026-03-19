from django.urls import path
from . import views

urlpatterns = [
    path('', views.employee_list, name='employee_list'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('employee/<int:pk>/', views.employee_detail, name='employee_detail'),
    path('employee/<int:pk>/edit/', views.employee_edit, name='employee_edit'),
]