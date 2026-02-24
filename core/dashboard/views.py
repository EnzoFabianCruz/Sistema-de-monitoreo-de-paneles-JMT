from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from .models import InspeccionCampo, InspeccionCampoDetalle , Ubigeo2, Ubicacion
from django.http import JsonResponse
from django.db import transaction
from django.utils import timezone
from django.contrib import messages
from .models import InspeccionCampo, InspeccionCampoDetalle, Ubicacion
from django.db.models import Max

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

    data = Ubicacion.objects.filter(
        CodigoDepartamento=dep,
        CodigoProvincia=prov
    ).values(
        'CodigoUbicacion',
        'CodigoInterno',
        'DireccionComercial',
        'CodigoProvincia',
        'CodigoDistrito',
        'CodigoTipoElemento',
        'Medidas'
    )

    return JsonResponse(list(data), safe=False)

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
        'departamentos' : departamentos,
        'provincias' : provincias,
        'ubicaciones' : ubicaciones
    }

    return render(request, "dashboard/inspeccion_operador.html", context)
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
    inspeccion = InspeccionCampo.objects.filter(
        NumeroRegistro=numero
    ).first()

    if inspeccion:
        inspeccion.ZonaInspeccion = zona
        inspeccion.FechaInspeccion = fecha
        inspeccion.CodigoResponsable = responsable   # ← FALTABA ESTO
        inspeccion.save()

        # BORRAR DETALLES VIEJOS
        InspeccionCampoDetalle.objects.filter(
            NumeroRegistro=inspeccion
        ).delete()

    else:
        # CREAR
        inspeccion = InspeccionCampo.objects.create(
            NumeroRegistro=numero,
            FechaInspeccion=fecha,
            ZonaInspeccion=zona,
            CodigoResponsable=responsable,  # ← FALTABA ESTO
            UsuarioCreacion=usuario,
            FechaCreacion=timezone.now().date(),
            EstadoRegistro="00"
        )
    # =============================
    # LEER ARRAYS (SIEMPRE)
    # =============================
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

    # =============================
    # CREAR DETALLES
    # =============================
    detalles_objs = []

    for i, cod in enumerate(ubicaciones):
        if not cod:
            continue

        detalles_objs.append(
            InspeccionCampoDetalle(
                NumeroRegistro=inspeccion,
                CodigoElementoRef=cod,
                Ubicacion=cod,
                CodigoDepartamento=departamento, 
                CodigoProvincia=provincias[i] if i < len(provincias) else "",
                CodigoDistrito=distritos[i] if i < len(distritos) else "",
                EstadoElemento=clean(estados[i]) if i < len(estados) else None,
                PuntoLuz=clean(puntos[i]) if i < len(puntos) else None,
                NumeroReflectores=clean(reflectores[i]) if i < len(reflectores) else None,
                EstadoReflectores=clean(estados_reflectores[i]) if i < len(estados_reflectores) else None,
                PublicidadLona=clean(lona[i]) if i < len(lona) else None,
                ControlPublicidad=clean(control[i]) if i < len(control) else None,
                EstadoLona=clean(estado_lona[i]) if i < len(estado_lona) else None,
                EstadoLogo=clean(estado_logo[i]) if i < len(estado_logo) else None,
                Observaciones=clean(observaciones[i]) if i < len(observaciones) else None,
            )
        )

    if detalles_objs:
        InspeccionCampoDetalle.objects.bulk_create(detalles_objs)

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
    ).order_by('IdDetalle')

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

    # ==============================
    # SI EXISTEN DETALLES
    # ==============================
    if detalles.exists():
        first = detalles.first()

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

        # 🔥 LIMPIAMOS TAMBIÉN PROVINCIAS
        provincias = [
            {
                "CodigoProvincia": p["CodigoProvincia"].strip(),
                "Nombre": p["Nombre"]
            }
            for p in provincias_raw
        ]

    context = {
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