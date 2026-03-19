from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .models import Employee, Administrator, AccessHistory, EmployeeCard
from django.conf import settings


def get_minio_url(key, ext='jpg'):
    if not key:
        return '/static/css/placeholder.jpg'
    return f'http://localhost:9000/{settings.MINIO_BUCKET}/{key}.{ext}'


def login_view(request):
    if request.user.is_authenticated:
        return redirect_by_role(request.user)

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user:
            login(request, user)
            return redirect_by_role(user)
        else:
            return render(request, 'services/login.html', {'form': {'errors': True}})

    return render(request, 'services/login.html', {})


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

    query = request.GET.get('q', '')
    employees = Employee.objects.all()

    if query:
        employees = employees.filter(last_name__icontains=query)

    for e in employees:
        e.image_url = get_minio_url(e.photo)

    return render(request, 'services/employee_list.html', {
        'employees': employees,
        'query': query,
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

    if request.method == 'POST':
        employee.last_name = request.POST.get('last_name')
        employee.first_name = request.POST.get('first_name')
        employee.middle_name = request.POST.get('middle_name')
        employee.hire_date = request.POST.get('hire_date')
        employee.status = request.POST.get('status')
        employee.save()

        card, created = EmployeeCard.objects.get_or_create(employee=employee)
        card.passport_series = request.POST.get('passport_series', '')
        card.passport_number = request.POST.get('passport_number', '')
        card.citizenship = request.POST.get('citizenship', '')
        card.address = request.POST.get('address', '')
        card.snils = request.POST.get('snils', '')
        card.inn = request.POST.get('inn', '')
        card.save()

        return redirect('employee_detail', pk=pk)

    return render(request, 'services/employee_edit.html', {
        'employee': employee,
        'card': getattr(employee, 'employeecard', None),
    })