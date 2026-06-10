from django.urls import path
from . import views

urlpatterns = [
    path('departamentos/', views.api_departamentos, name='api_departamentos'),
    path('provincias/',    views.api_provincias,    name='api_provincias'),
    path('distritos/',     views.api_distritos,     name='api_distritos'),
    path('ubicaciones/',   views.api_ubicaciones,   name='api_ubicaciones'),
]
