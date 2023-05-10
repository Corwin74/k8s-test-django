from django.shortcuts import redirect
from django.contrib import admin
from django.urls import path
from django.http import HttpResponse


urlpatterns = [
    path('', lambda request: redirect('/admin/')),
    path('admin/', admin.site.urls),
    path('secret/', lambda request: HttpResponse('Badams!!!'))
]
