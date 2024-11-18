from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect

urlpatterns = [
    path('', lambda request: redirect('lista_casi'), name='home'),
    path('admin/', admin.site.urls),
    path('casi/', include('cases.urls')),
]
