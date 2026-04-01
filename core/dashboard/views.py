from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden,JsonResponse
from .models import InspeccionCampo, InspeccionCampoDetalle , Ubigeo2, Ubicacion
from django.db import transaction
from django.utils import timezone
from django.contrib import messages
from django.db.models import Max
from django.http import JsonResponse
from datetime import date

@login_required
def home(request):
    registros = InspeccionCampo.objects.all()
    return render(request,
                  'dashboard/operador_dashboard.html',
                  {'registros':registros})

@login_required
def admin_dashboard(request):
    if not request.user.groups.filter(name="Administrador").exists():
        return HttpResponseForbidden("No tienes permisos")
    
    return render(request, "dashboard/admin_dashboard.html")

def ajax_provincias(request):
    dep = request.GET.get('dep')

    provincias = Ubigeo2.objects.filter(
        CodigoDepartamento=dep,
        CodigoDistrito='00'
    ).exclude(CodigoProvincia='00').values(
        'CodigoProvincia','Nombre'
    ).order_by('Nombre')

    return JsonResponse(list(provincias), safe=False)

def ajax_ubicaciones(request):
    dep = request.GET.get('dep')
    prov = request.GET.get('prov')
    dist = request.GET.get('dist')  # 🔥 NUEVO

    filtros = {
        "CodigoDepartamento": dep,
        "CodigoProvincia": prov
    }

    # 🔥 SOLO SI ES LIMA LIMA → FILTRA DISTRITO
    if dep == "15" and prov == "01" and dist:
        filtros["CodigoDistrito"] = dist

    data = Ubicacion.objects.filter(**filtros).values(
        'CodigoUbicacion',
        'CodigoInterno',
        'DireccionComercial',
        'CodigoProvincia',
        'CodigoDistrito',
        'CodigoTipoElemento',   # 👈 NUEVO
        'Medidas'
    )

    result = []
    for d in data:
        result.append({
            "CodigoUbicacion": d["CodigoUbicacion"],
            "CodigoInterno": d["CodigoInterno"],
            "DireccionComercial": d["DireccionComercial"],
            "CodigoProvincia": d["CodigoProvincia"].strip() if d["CodigoProvincia"] else "",
            "CodigoDistrito": d["CodigoDistrito"].strip() if d["CodigoDistrito"] else "",
            "CodigoTipoElemento": d.get("CodigoTipoElemento"),  # 👈 NUEVO
            "Medidas": d.get("Medidas"),                        # 👈 NUEVO
        })

    return JsonResponse(result, safe=False)

@login_required
def inspeccion_campo(request):
    departamentos = (
        Ubigeo2.objects.filter(CodigoProvincia='00', CodigoDistrito = '00')
        .values('CodigoDepartamento', 'Nombre')
        .distinct()
        .order_by('Nombre')
    )
    provincias = []
    ubicaciones = []

    if request.method == 'POST':
        dep = request.POST.get('CodigoDepartamento')
        prov = request.POST.get('CodigoProvincia')

        if dep:
            provincias = (
                Ubigeo2.objects.filter(CodigoDepartamento = dep, CodigoDistrito = '00')
                .exclude(CodigoProvincia = '00')
                .values('CodigoProvincia', 'Nombre')
                .distinct()
                .order_by('Nombre')
            )

        if dep and prov:
            ubicaciones = (
                Ubicacion.objects.filter(CodigoDepartamento = dep, CodigoProvincia = prov)
                .order_by('CodigoDistrito','CodigoUbicacion')
            )
    context = {
        "usuario_actual": request.user,
        'departamentos' : departamentos,
        'provincias' : provincias,
        'ubicaciones' : ubicaciones,
        "fecha_hoy": date.today()
    }

    return render(request, "dashboard/inspeccion_operador.html", context)

def to_bool(v):
    return str(v).lower() == "true"
@login_required
@transaction.atomic
def guardar_inspeccion(request):

    if request.method != "POST":
        return redirect("inspeccion_campo")

    usuario = request.user.username
    numero = request.POST.get("NumeroRegistro")

    # =============================
    # GENERAR NUMERO SI ES NUEVO
    # =============================
    if not numero:
        ultimo = InspeccionCampo.objects.aggregate(
            Max('NumeroRegistro')
        )['NumeroRegistro__max']

        numero = str(int(ultimo or 0) + 1).zfill(10)

    zona = request.POST.get("ZonaInspeccion", "")
    fecha = request.POST.get("fecha") or timezone.now().date()
    departamento = request.POST.get("CodigoDepartamento")
    responsable = request.POST.get("responsable")

    # =============================
    # CREAR O ACTUALIZAR CABECERA
    # =============================
    inspeccion, creada = InspeccionCampo.objects.get_or_create(
        NumeroRegistro=numero,
        defaults={
            "FechaInspeccion": fecha,
            "ZonaInspeccion": zona,
            "CodigoResponsable": responsable,
            "UsuarioCreacion": usuario,
            "FechaCreacion": timezone.now().date(),
            "EstadoRegistro": "00"
        }
    )

    if not creada:
        inspeccion.ZonaInspeccion = zona
        inspeccion.FechaInspeccion = fecha
        inspeccion.CodigoResponsable = responsable
        inspeccion.save()

    # =============================
    # LEER ARRAYS
    # =============================
    ids = request.POST.getlist("id_detalle[]")
    ubicaciones = request.POST.getlist("codigo_ubicacion[]")
    estados = request.POST.getlist("estado_elemento[]")
    puntos = request.POST.getlist("punto_luz[]")
    reflectores = request.POST.getlist("num_reflectores[]")
    estados_reflectores = request.POST.getlist("estado_reflectores[]")
    lona = request.POST.getlist("publicidad_lona[]")
    control = request.POST.getlist("control_publicidad[]")
    estado_lona = request.POST.getlist("estado_lona[]")
    estado_logo = request.POST.getlist("estado_logo[]")
    observaciones = request.POST.getlist("observaciones[]")
    provincias = request.POST.getlist("codigo_provincia[]")
    distritos = request.POST.getlist("codigo_distrito[]")

    def clean(v):
        return None if v in ["", None] else v

    def get_val(lista, i):
        return lista[i] if i < len(lista) else None

    # =============================
    # IDS EXISTENTES EN BD
    # =============================
    ids_bd = set(
        InspeccionCampoDetalle.objects.filter(
            NumeroRegistro=inspeccion
        ).values_list("IdDetalle", flat=True)
    )

    ids_form = set(int(i) for i in ids if i and i.isdigit())

    # =============================
    # ELIMINAR LOS QUE YA NO VIENEN
    # =============================
    ids_eliminar = ids_bd - ids_form

    if ids_eliminar:
        InspeccionCampoDetalle.objects.filter(
            IdDetalle__in=ids_eliminar
        ).delete()

    # =============================
    # CREAR / ACTUALIZAR
    # =============================
    for i, cod in enumerate(ubicaciones):

        id_det = get_val(ids, i)

        data = {
            "NumeroRegistro": inspeccion,
            "CodigoElementoRef": cod,
            "Ubicacion": cod,
            "CodigoDepartamento": departamento,
            "CodigoProvincia": get_val(provincias, i),
            "CodigoDistrito": get_val(distritos, i),
            "EstadoElemento": clean(get_val(estados, i)),
            "PuntoLuz": clean(get_val(puntos, i)),
            "NumeroReflectores": clean(get_val(reflectores, i)),
            "EstadoReflectores": clean(get_val(estados_reflectores, i)),
            "PublicidadLona": get_val(lona, i) or "",
            "ControlPublicidad": clean(get_val(control, i)),
            "EstadoLona": clean(get_val(estado_lona, i)),
            "EstadoLogo": clean(get_val(estado_logo, i)),
            "Observaciones": clean(get_val(observaciones, i)),
        }

        if id_det:
            # 🔥 UPDATE
            InspeccionCampoDetalle.objects.filter(
                IdDetalle=id_det
            ).update(**data)
        else:
            # 🔥 CREATE
            InspeccionCampoDetalle.objects.create(**data)

    messages.success(request, f"Inspección {numero} guardada correctamente")
    return redirect("home")
@login_required
def inspeccion_modificar(request, numero_registro):

    try:
        inspeccion = InspeccionCampo.objects.get(
            NumeroRegistro=numero_registro
        )
    except InspeccionCampo.DoesNotExist:
        messages.error(
            request,
            f"No existe la inspección {numero_registro}"
        )
        return redirect("home")
    # ==============================
    # DETALLES
    # ==============================
    detalles = InspeccionCampoDetalle.objects.filter(
    NumeroRegistro=inspeccion
).order_by("IdDetalle")
    codigos = [d.Ubicacion for d in detalles]

    ubicaciones_dict = {
        u.CodigoUbicacion: u
        for u in Ubicacion.objects.filter(CodigoUbicacion__in=codigos)
    }

    for det in detalles:
        u = ubicaciones_dict.get(det.Ubicacion)

        det.TipoElemento = u.CodigoTipoElemento if u else ""
        det.Medidas = u.Medidas if u else ""
        det.Direccion = u.DireccionComercial if u else ""

    # ==============================
    # DEPARTAMENTOS (LIMPIOS)
    # ==============================
    departamentos_raw = (
        Ubigeo2.objects.filter(
            CodigoProvincia='00',
            CodigoDistrito='00'
        )
        .values('CodigoDepartamento', 'Nombre')
        .distinct()
        .order_by('Nombre')
    )

    # 🔥 LIMPIAMOS ESPACIOS DE CHAR
    departamentos = [
        {
            "CodigoDepartamento": d["CodigoDepartamento"].strip(),
            "Nombre": d["Nombre"]
        }
        for d in departamentos_raw
    ]

    dep_seleccionado = None
    provincia_seleccionada = None
    provincias = []
    ubicaciones = []
    zona_calculada = ""
    
    # ==============================
    # SI EXISTEN DETALLES
    # ==============================
    if detalles:
        first = detalles[0]

        dep_seleccionado = first.CodigoDepartamento.strip()
        provincia_seleccionada = first.CodigoProvincia.strip()

        if dep_seleccionado == "15" and provincia_seleccionada == "01":
            zona_calculada = "L"
        else:
            zona_calculada = "P"

        provincias_raw = (
            Ubigeo2.objects.filter(
                CodigoDepartamento=dep_seleccionado,
                CodigoDistrito='00'
            )
            .exclude(CodigoProvincia='00')
            .values('CodigoProvincia', 'Nombre')
            .distinct()
            .order_by('Nombre')
        )

        provincias = [
            {
                "CodigoProvincia": p["CodigoProvincia"].strip(),
                "Nombre": p["Nombre"]
            }
            for p in provincias_raw
        ]
    context = {
    "usuario_actual": request.user,
    "fecha_hoy": date.today(),
    "dep_seleccionado": dep_seleccionado,
    "provincia_seleccionada": provincia_seleccionada,
    "zona_calculada": zona_calculada,
    "detalles": detalles,
    "departamentos": departamentos,
    "provincias": provincias,
    "ubicaciones": ubicaciones,
    "inspeccion": inspeccion,
    "modo_modificacion": True,
    }
    return render(
        request,
        "dashboard/inspeccion_operador.html",
        context
    )
def ajax_distritos(request):
    dep = request.GET.get('dep')
    prov = request.GET.get('prov')

    distritos = (
        Ubigeo2.objects
        .filter(
            CodigoDepartamento=dep,
            CodigoProvincia=prov
        )
        .exclude(CodigoDistrito='00')
        .values('CodigoDistrito', 'Nombre')
        .order_by('Nombre')
    )

    return JsonResponse(list(distritos), safe=False)