from django.urls import path
from .views import home , admin_dashboard,inspeccion_campo,ajax_provincias,ajax_ubicaciones,guardar_inspeccion,inspeccion_modificar
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("home/",home, name="home"),
    path("admin_dashboard/", admin_dashboard, name="admin"),
    path("home/inspeccion/", inspeccion_campo ,name="inspeccion"),
    path("ajax/provincias/", ajax_provincias),
    path("ajax/ubicaciones/", ajax_ubicaciones),
    path("home/inspeccion/guardar/", guardar_inspeccion, name="guardar_inspeccion"),
    path('inspeccion/<str:numero_registro>/',inspeccion_modificar, name='inspeccion_modificar'),
]
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)