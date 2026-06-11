from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden,JsonResponse
from .models import InspeccionCampo, InspeccionCampoDetalle , Ubigeo2, Ubicacion,FotoDetalle
from django.db import transaction
from django.utils import timezone
from django.contrib import messages
from django.db.models import Max
from django.http import JsonResponse
from datetime import date
from django.db.models.functions import Trim
from .jmt_client import get_ubicaciones, get_ubicaciones_dict, get_departamentos, get_ubigeo
import os

@login_required
def home(request):
    # 1. Obtenemos el nombre del operador logueado
    usuario_actual = request.user.username.strip()

    # 2. FILTRO OBLIGATORIO:
    # Usamos Trim para limpiar espacios de SQL Server (campos CHAR)
    # Usamos __iexact para evitar problemas si uno empieza con Mayúscula y otro no
    registros = InspeccionCampo.objects.annotate(
        creador_limpio=Trim('UsuarioCreacion')
    ).filter(creador_limpio__iexact=usuario_actual).order_by('-FechaCreacion')

    # Para depuración (puedes borrarlo después)
    print(f"DEBUG: Operador: '{usuario_actual}' | Registros encontrados: {registros.count()}")

    return render(request, "dashboard/operador_dashboard.html", {
        "registros": registros,
    })

@login_required
def admin_dashboard(request):
    if not request.user.groups.filter(name="Administrador").exists():
        return HttpResponseForbidden("No tienes permisos")
    
    return render(request, "dashboard/admin_dashboard.html")

def ajax_provincias(request):
    dep = request.GET.get('dep')
    try:
        data = get_ubigeo()
        provincias = [
            {"CodigoProvincia": u["CodigoProvincia"].strip(), "Nombre": u["Nombre"]}
            for u in data
            if u["CodigoDepartamento"].strip() == dep
            and u["CodigoDistrito"].strip() == "00"
            and u["CodigoProvincia"].strip() != "00"
        ]
        provincias = sorted(provincias, key=lambda x: x["Nombre"])
    except Exception:
        provincias = []
    return JsonResponse(provincias, safe=False)

def ajax_distritos(request):
    dep  = request.GET.get('dep')
    prov = request.GET.get('prov')
    try:
        data = get_ubigeo()
        distritos = [
            {"CodigoDistrito": u["CodigoDistrito"].strip(), "Nombre": u["Nombre"]}
            for u in data
            if u["CodigoDepartamento"].strip() == dep
            and u["CodigoProvincia"].strip() == prov
            and u["CodigoDistrito"].strip() != "00"
        ]
        distritos = sorted(distritos, key=lambda x: x["Nombre"])
    except Exception:
        distritos = []
    return JsonResponse(distritos, safe=False)

def ajax_ubicaciones(request):
    dep  = request.GET.get('dep')
    prov = request.GET.get('prov')
    dist = request.GET.get('dist')

    try:
        data = get_ubicaciones(dep=dep, prov=prov, dist=dist)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse(data, safe=False)

@login_required
def inspeccion_campo(request):
    departamentos = get_departamentos()
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
        
    ids = request.POST.getlist("id_detalle[]")
    ubicaciones = request.POST.getlist("codigo_ubicacion[]")
    estados = request.POST.getlist("estado_elemento[]")
    puntos = request.POST.getlist("punto_luz[]")
    reflectores = request.POST.getlist("num_reflectores[]")
    est_reflectores = request.POST.getlist("estado_reflectores[]")
    lona = request.POST.getlist("publicidad_lona[]")
    control = request.POST.getlist("control_publicidad[]")
    est_lona = request.POST.getlist("estado_lona[]")
    est_logo = request.POST.getlist("estado_logo[]")
    obs = request.POST.getlist("observaciones[]")
    provincias = request.POST.getlist("codigo_provincia[]")
    distritos = request.POST.getlist("codigo_distrito[]")

    def clean(v):
        if v is None: return None
        v = str(v).strip()
        return None if v in ["", "None", "undefined"] else v

    def get_val(lista, i):
        try:
            return lista[i]
        except IndexError:
            return None

    ids_en_formulario = request.POST.getlist("id_detalle[]")
    # Convertimos a lista de enteros filtrando vacíos para comparar
    ids_en_formulario_limpios = [int(i) for i in ids_en_formulario if i and str(i).strip().isdigit()]

    if not creada: 
        InspeccionCampoDetalle.objects.filter(
            NumeroRegistro=inspeccion
        ).exclude(
            IdDetalle__in=ids_en_formulario_limpios
        ).delete()
    for i, cod in enumerate(ubicaciones):
        cod_clean = clean(cod)
        if not cod_clean:
            continue

        id_form = get_val(ids, i)
        
        # Construcción del diccionario de datos
        # IMPORTANTE: Asegúrate que los nombres coincidan con tu Model
        data_detalle = {
            "NumeroRegistro": inspeccion,
            "Ubicacion": cod_clean,
            "CodigoElementoRef": cod_clean,
            "CodigoDepartamento": clean(request.POST.get("CodigoDepartamento")),
            "CodigoProvincia": clean(get_val(provincias, i)),
            "CodigoDistrito": clean(get_val(distritos, i)),
            "EstadoElemento": clean(get_val(estados, i)),
            "PuntoLuz": clean(get_val(puntos, i)),
            "NumeroReflectores": clean(get_val(reflectores, i)) or 0,
            "EstadoReflectores": clean(get_val(est_reflectores, i)),
            "PublicidadLona": clean(get_val(lona, i)) or "NO",
            "ControlPublicidad": clean(get_val(control, i)),
            "EstadoLona": clean(get_val(est_lona, i)),
            "EstadoLogo": clean(get_val(est_logo, i)),
            "Observaciones": clean(get_val(obs, i)),
        }

        # Decisión: Si el ID viene del form y no está vacío, es UPDATE
        if id_form and str(id_form).strip().isdigit():
            InspeccionCampoDetalle.objects.filter(IdDetalle=id_form).update(**data_detalle)
            detalle = InspeccionCampoDetalle.objects.get(IdDetalle=id_form)  # ← agregar esta línea
        else:
            detalle = InspeccionCampoDetalle.objects.create(**data_detalle)  # ← asignar a detalle

        fotos_nuevas = request.FILES.getlist(f'fotos_{cod_clean}[]')
        fotos_a_borrar = request.POST.getlist(f'fotos_borrar_{cod_clean}[]')  # opcional: IDs a eliminar individualmente

        # Eliminar solo las fotos marcadas explícitamente para borrar
        for foto_id in fotos_a_borrar:
            try:
                foto_obj = FotoDetalle.objects.get(IdFoto=foto_id)
                if foto_obj.imagen and os.path.isfile(foto_obj.imagen.path):
                    os.remove(foto_obj.imagen.path)
                foto_obj.delete()
            except FotoDetalle.DoesNotExist:
                pass

        # Agregar las fotos nuevas SIN borrar las existentes
        for foto in fotos_nuevas:
            FotoDetalle.objects.create(detalle=detalle, imagen=foto)
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
    MAPA_TIPOS = {
        "01": "TORRE", "03": "OTRO", "04": "BANDEROLA", "06": "BANNER",
        "07": "CAJA LUMINOSA", "08": "LOGO CHICO", "09": "LOGO GRANDE",
        "10": "LUCES LED", "11": "MINIBANDEROLAS", "12": "MINIPOLAR",
        "13": "PANEL", "14": "PANEL CARRETERO", "15": "PANEL MONUMENTAL",
        "16": "PANEL PUBLICITARIO", "17": "PANEL VERTICAL", "18": "PANELETA",
        "20": "PARCHE", "23": "PORTICO", "24": "POSTE BANDERA",
        "25": "POSTE EN L", "26": "SEÑALETICAS", "27": "TORRE UNIPOLAR",
        "28": "VINIL", "29": "VALLAS ALTAS", "30": "TORRE MINIPOLAR",
        "31": "MEGAVALLA", "32": "TORRE TRIPOLAR", "36": "TROQUEL",
        "37": "SEÑALIZADOR DE CALLE", "43": "LED - TORRE UNIPOLAR",
        "44": "CAMION LED", "49": "TOTEM", "50": "LED - TORRE TRIPOLAR",
        "52": "LED - TORRE MINIPOLAR", "53": "PANEL / BANDEROLA",
        "54": "PANEL LED", "55": "VALLA LED", "56": "BASTIDOR"
    }
    # ==============================
    # DETALLES
    # ==============================
    detalles = InspeccionCampoDetalle.objects.filter(NumeroRegistro=inspeccion).order_by("IdDetalle").prefetch_related('fotos')
    codigos = [d.Ubicacion for d in detalles]

    ubicaciones_dict = get_ubicaciones_dict()

    for det in detalles:
        u = ubicaciones_dict.get(det.Ubicacion)
        if u:
            det.CodigoTipoElemento = u.get("CodigoTipoElemento", "")
            det.TipoElemento       = u.get("CodigoTipoElemento", "")
            det.Medidas            = u.get("Medidas", "")
            det.Direccion          = u.get("DireccionComercial", "")
            det.CodigoInterno      = u.get("CodigoInterno", "")
        else:
            det.CodigoTipoElemento = ""
            det.TipoElemento       = ""
            det.Medidas            = ""
            det.Direccion          = ""
            det.CodigoInterno      = ""
        codigo_limpio         = str(det.TipoElemento).strip()
        det.CodigoUbicacion   = det.Ubicacion
        det.DescripcionVisual = MAPA_TIPOS.get(codigo_limpio, codigo_limpio)


    try:
        departamentos = get_departamentos()
    except Exception:
        departamentos = []

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

        try:
            data = get_ubigeo()
            provincias = sorted([
                {"CodigoProvincia": u["CodigoProvincia"].strip(), "Nombre": u["Nombre"]}
                for u in data
                if u["CodigoDepartamento"].strip() == dep_seleccionado
                and u["CodigoDistrito"].strip() == "00"
                and u["CodigoProvincia"].strip() != "00"
            ], key=lambda x: x["Nombre"])
        except Exception:
            provincias = []
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

    return JsonResponse(list(distritos), safe=False)
@login_required
def operador_dashboard(request):
    if request.user.is_staff:
        # Si es el cliente (Admin), ve todas las inspecciones de todos
        inspecciones = InspeccionCampo.objects.all().order_by('-FechaCreacion')
    else:
        # Si es operador, filtramos por su nombre de usuario
        inspecciones = InspeccionCampo.objects.filter(
            UsuarioCreacion=request.user.username
        ).order_by('-FechaCreacion')
    
    return render(request, 'dashboard/operador_dashboard.html', {
        'inspecciones': inspecciones
    })

@login_required
def borrar_foto(request, foto_id):
    if request.method != "POST":
        return JsonResponse({"error": "Método no permitido"}, status=405)
    try:
        foto = FotoDetalle.objects.get(IdFoto=foto_id)
        if foto.imagen and os.path.isfile(foto.imagen.path):
            os.remove(foto.imagen.path)
        foto.delete()
        return JsonResponse({"ok": True})
    except FotoDetalle.DoesNotExist:
        return JsonResponse({"error": "Foto no encontrada"}, status=404)