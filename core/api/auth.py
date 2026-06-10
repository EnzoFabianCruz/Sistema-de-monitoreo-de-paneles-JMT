from functools import wraps
from django.http import JsonResponse
from .models import ApiToken

def token_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        auth_header = request.headers.get('Authorization', '')
        token = auth_header.replace('Bearer ', '').strip()

        if not token:
            return JsonResponse(
                {'error': 'Token no proporcionado'},
                status=401
            )

        if not ApiToken.objects.filter(token=token, activo=True).exists():
            return JsonResponse(
                {'error': 'Token inválido o inactivo'},
                status=401
            )

        return view_func(request, *args, **kwargs)
    return wrapper
