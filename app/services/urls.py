from django.urls import path
from . import views

urlpatterns = [
    path('', views.employee_list, name='employee_list'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('employee/create/', views.employee_create, name='employee_create'),
    path('positions/create/', views.position_create, name='position_create'),
    path('departments/create/', views.department_create, name='department_create'),
    path('employee/<int:pk>/', views.employee_detail, name='employee_detail'),
    path('employee/<int:pk>/edit/', views.employee_edit, name='employee_edit'),
    path('employee/<int:pk>/delete/', views.employee_delete, name='employee_delete'),
    path('access-right/<int:pk>/delete/', views.access_right_delete, name='access_right_delete'),
    path('access-levels/', views.access_level_list, name='access_level_list'),
    path('access-levels/<int:pk>/delete/', views.access_level_delete, name='access_level_delete'),
    path('history/', views.history_list, name='history_list'),
    path('history/export/', views.history_export_csv, name='history_export_csv'),
]