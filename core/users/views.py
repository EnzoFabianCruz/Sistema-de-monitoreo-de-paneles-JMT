from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from .forms import RegistroUsuarioForm
from dashboard.models import InspeccionCampo, InspeccionCampoDetalle, Ubicacion


def admin_dashboard(request):
    """
    Vista principal del Panel Administrativo.
    Gestiona la creación de usuarios y lista las inspecciones globales.
    """
    # 1. Obtener usuarios locales de Django
    usuarios = User.objects.all().order_by('-date_joined')

    try:

        inspecciones = InspeccionCampo.objects.all().order_by('-FechaCreacion')
        cantidad = inspecciones.count() 
    except Exception as e:
        print(f"--- ERROR DE CONEXIÓN SQL SERVER: {e} ---")
        inspecciones = []
        messages.error(request, "No se pudo conectar con la base de datos de inspecciones.")

    # 3. Lógica del Formulario de Registro de Operadores
    if request.method == 'POST':
        form = RegistroUsuarioForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Operador registrado exitosamente.")
            return redirect('admin_dashboard')
        else:
            messages.error(request, "Error al registrar el usuario. Verifique los datos.")
    else:
        form = RegistroUsuarioForm()

    # 4. Renderizado
    return render(request, 'dashboard/admin_dashboard.html', {
        'usuarios': usuarios,
        'inspecciones': inspecciones,
        'form': form
    })

def detalle_inspeccion(request, numero_registro):
    inspeccion = get_object_or_404(InspeccionCampo, NumeroRegistro=numero_registro)
    # Traemos los detalles guardados
    detalles_db = InspeccionCampoDetalle.objects.filter(NumeroRegistro=inspeccion).order_by("IdDetalle")
    
    detalles_finales = []
    
    # Diccionario de tipos para la descripción
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

    for det in detalles_db:
        # 1. Obtenemos el código que viene del detalle. 
        # IMPORTANTE: Asegúrate si det.CodigoElementoRef guarda el CodigoUbicacion (PK) o el CodigoInterno.
        codigo_busqueda = str(det.CodigoElementoRef).strip() if det.CodigoElementoRef else ""
        
        # 2. Buscamos en tu modelo Ubicacion
        # Probamos buscando por CodigoInterno, si no funciona cambia a CodigoUbicacion=codigo_busqueda
        u = Ubicacion.objects.filter(CodigoInterno=codigo_busqueda).first()
        
        if not u:
            # Si no lo encuentra por Interno, intentamos por la Primary Key por si acaso
            u = Ubicacion.objects.filter(CodigoUbicacion=codigo_busqueda).first()

        # 3. Construimos el objeto para el template
        tipo_cod = str(u.CodigoTipoElemento).strip() if u else ""
        
        item = {
            # Datos de la tabla UBICACIONES
            "CodigoInterno": u.CodigoInterno if u else codigo_busqueda,
            "DireccionComercial": u.DireccionComercial if u else "No encontrada en DB",
            "Medidas": u.Medidas if u else "-",
            "DescripcionVisual": MAPA_TIPOS.get(tipo_cod, tipo_cod),
            
            # Datos de la tabla DETALLES (los que ya se guardaron)
            "EstadoElemento": det.EstadoElemento,
            "PuntoLuz": det.PuntoLuz,
            "NumeroReflectores": det.NumeroReflectores,
            "EstadoReflectores": det.EstadoReflectores,
            "PublicidadLona": det.PublicidadLona,
            "ControlPublicidad": det.ControlPublicidad,
            "EstadoLona": det.EstadoLona,
            "EstadoLogo": det.EstadoLogo,
            "Observaciones": det.Observaciones,
        }
        detalles_finales.append(item)
    
    return render(request, 'dashboard/detalle_inspeccion.html', {
        'inspeccion': inspeccion,
        'detalles': detalles_finales,
        'usuario_actual': request.user
    })