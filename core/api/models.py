from django.db import models
import secrets

class ApiToken(models.Model):
    token = models.CharField(max_length=64, unique=True)
    nombre = models.CharField(max_length=100)  # nombre del sistema cliente
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.token:
            self.token = secrets.token_hex(32)  # genera token aleatorio automáticamente
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.nombre} ({'activo' if self.activo else 'inactivo'})"

    class Meta:
        db_table = 'ApiToken'
        verbose_name = 'Token API'
        verbose_name_plural = 'Tokens API'
