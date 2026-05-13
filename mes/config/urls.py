from django.urls import path, include

urlpatterns = [
    path('', include('mes_app.urls')),
]