from django.db import models

class InspeccionCampo(models.Model):
        NumeroRegistro = models.CharField(
            max_length=10,
            primary_key=True    
        )
        FechaInspeccion=models.DateField()

        ZonaInspeccion = models.CharField(
                max_length=2
        )
        CodigoResponsable = models.CharField(
                max_length=20,
                null=True,
                blank=True
        )
        UsuarioCreacion = models.CharField(
                max_length=30
        )
        FechaCreacion=models.DateField()
        EstadoRegistro = models.CharField(
                max_length=2,
                default = '00'
        )
        class Meta:
            db_table= 'InspeccionCampo'
            managed= False

class InspeccionCampoDetalle(models.Model):
    IdDetalle = models.AutoField(primary_key=True)  # <--- así Django sabe que es autoincrement
    NumeroRegistro = models.ForeignKey(
        InspeccionCampo,
        db_column='NumeroRegistro',
        on_delete=models.PROTECT
    )
    CodigoElementoRef = models.CharField(max_length=20)
    Ubicacion = models.CharField(max_length=50, null=True)
    CodigoDepartamento = models.CharField(max_length=2)
    CodigoProvincia = models.CharField(max_length=2)
    CodigoDistrito = models.CharField(max_length=2)
    EstadoElemento = models.CharField(max_length=2, null=True)
    PuntoLuz = models.BooleanField(null=True)
    NumeroReflectores = models.IntegerField(null=True)
    EstadoReflectores = models.CharField(max_length=2, null=True)
    PublicidadLona = models.CharField(max_length=2, null=True)
    ControlPublicidad = models.CharField(max_length=2, null=True)
    EstadoLona = models.CharField(max_length=2, null=True)
    EstadoLogo = models.CharField(max_length=2, null=True)
    Observaciones = models.CharField(max_length=500, null=True)

    class Meta:
        db_table = 'InspeccionCampoDetalle'
        managed = True

class Ubicacion(models.Model):
      CodigoUbicacion = models.CharField(
            primary_key=True,
            max_length=10
      )
      CodigoInterno = models.CharField(
            max_length=50
      )
      CodigoTipoElemento = models.CharField(
            max_length= 2
      )
      Medidas = models.CharField(
            max_length= 50
      )
      DireccionComercial = models.CharField(
            max_length= 200
      )
      DireccionReal = models.CharField(
            max_length=200
      )
      CodigoDepartamento = models.CharField(
            max_length= 2
      )
      CodigoProvincia = models.CharField(
            max_length= 2     
      )
      CodigoDistrito = models.CharField(
            max_length= 2
      )
      class Meta:
            db_table= 'UBICACIONES'
            managed= False

class Ubigeo2(models.Model):
    id = models.AutoField(primary_key=True)
    CodigoDepartamento = models.CharField(max_length=3)
    CodigoProvincia = models.CharField(max_length=3)
    CodigoDistrito = models.CharField(max_length=3)
    Nombre = models.CharField(max_length=100)

    class Meta:
        db_table = 'UBIGEO2'
        managed = False
