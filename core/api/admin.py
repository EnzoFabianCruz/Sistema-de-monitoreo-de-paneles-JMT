from django.contrib import admin
from .models import ApiToken

@admin.register(ApiToken)
class ApiTokenAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'token', 'activo', 'fecha_creacion')
    list_filter = ('activo',)
    readonly_fields = ('token', 'fecha_creacion')  # el token se genera solo
    search_fields = ('nombre',)
