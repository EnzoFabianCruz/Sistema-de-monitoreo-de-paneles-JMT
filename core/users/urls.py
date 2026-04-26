from django.urls import path
from . import views

urlpatterns = [
    path('gestion-usuarios/', views.admin_dashboard, name='admin_dashboard'),
    path('detalle/<str:numero_registro>/', views.detalle_inspeccion, name='detalle_inspeccion')
    
]