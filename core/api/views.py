from django.http import JsonResponse
from dashboard.models import Ubigeo2, Ubicacion
from .auth import token_required


@token_required
def api_departamentos(request):
    """
    GET /api/departamentos/
    Devuelve todos los departamentos.
    """
    data = (
        Ubigeo2.objects
        .filter(CodigoProvincia='00', CodigoDistrito='00')
        .values('CodigoDepartamento', 'Nombre')
        .order_by('Nombre')
    )
    return JsonResponse(list(data), safe=False)


@token_required
def api_provincias(request):
    """
    GET /api/provincias/?dep=15
    Devuelve provincias de un departamento.
    """
    dep = request.GET.get('dep')
    if not dep:
        return JsonResponse({'error': 'Parámetro dep requerido'}, status=400)

    data = (
        Ubigeo2.objects
        .filter(CodigoDepartamento=dep, CodigoDistrito='00')
        .exclude(CodigoProvincia='00')
        .values('CodigoProvincia', 'Nombre')
        .order_by('Nombre')
    )
    return JsonResponse(list(data), safe=False)


@token_required
def api_distritos(request):
    """
    GET /api/distritos/?dep=15&prov=01
    Devuelve distritos de una provincia.
    """
    dep  = request.GET.get('dep')
    prov = request.GET.get('prov')

    if not dep or not prov:
        return JsonResponse(
            {'error': 'Parámetros dep y prov requeridos'},
            status=400
        )

    data = (
        Ubigeo2.objects
        .filter(CodigoDepartamento=dep, CodigoProvincia=prov)
        .exclude(CodigoDistrito='00')
        .values('CodigoDistrito', 'Nombre')
        .order_by('Nombre')
    )
    return JsonResponse(list(data), safe=False)


@token_required
def api_ubicaciones(request):
    """
    GET /api/ubicaciones/?dep=15&prov=01
    GET /api/ubicaciones/?dep=15&prov=01&dist=01  (solo Lima Lima)
    Devuelve ubicaciones filtradas por departamento y provincia.
    """
    dep  = request.GET.get('dep')
    prov = request.GET.get('prov')
    dist = request.GET.get('dist')

    if not dep or not prov:
        return JsonResponse(
            {'error': 'Parámetros dep y prov requeridos'},
            status=400
        )

    filtros = {
        'CodigoDepartamento': dep,
        'CodigoProvincia':    prov,
    }
    if dep == '15' and prov == '01' and dist:
        filtros['CodigoDistrito'] = dist

    data = Ubicacion.objects.filter(**filtros).values(
        'CodigoUbicacion',
        'CodigoInterno',
        'DireccionComercial',
        'CodigoProvincia',
        'CodigoDistrito',
        'CodigoTipoElemento',
        'Medidas',
    )

    result = [
        {
            'CodigoUbicacion':    d['CodigoUbicacion'],
            'CodigoInterno':      d['CodigoInterno'],
            'DireccionComercial': d['DireccionComercial'],
            'CodigoProvincia':    d['CodigoProvincia'].strip() if d['CodigoProvincia'] else '',
            'CodigoDistrito':     d['CodigoDistrito'].strip()  if d['CodigoDistrito']  else '',
            'CodigoTipoElemento': d['CodigoTipoElemento'],
            'Medidas':            d['Medidas'],
        }
        for d in data
    ]
    return JsonResponse(result, safe=False)
