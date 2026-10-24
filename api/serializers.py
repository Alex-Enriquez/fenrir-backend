from rest_framework import serializers
from .seguridad import ReglaDeNegocio, mensaje_password_invalida
from equipos.models import CategoriaEquipo, Equipo, Mantenimiento
from empleados.models import Departamento, Empleado
from licencias.models import TipoLicencia, Licencia
from asignaciones.models import Asignacion
from contrasenas.models import CategoriaContrasena, RegistroContrasena
from django.contrib.auth.models import User
from proveedores.models import Proveedor
from servicios.models import ServicioContratado, PagoServicio
from infraestructura.models import Rack, DispositivoRed, PuertoRed

class CategoriaEquipoSerializer(serializers.ModelSerializer):
    class Meta:
        model = CategoriaEquipo
        fields = "__all__"


class EquipoSerializer(serializers.ModelSerializer):
    categoria_nombre = serializers.CharField(source="categoria.nombre", read_only=True)

    # Serie, inventario e IMEI son opcionales pero únicos cuando traen valor: lo vacío se guarda como NULL
    # (así varios equipos pueden quedar sin serie) y hacia el frontend se sigue mostrando como "".
    CAMPOS_OPCIONALES = ("numero_serie", "numero_inventario", "imei")

    class Meta:
        model = Equipo
        fields = "__all__"

    @staticmethod
    def _vacio_a_none(valor):
        if valor is None:
            return None
        valor = str(valor).strip()
        return valor or None

    def validate_numero_serie(self, valor):
        return self._vacio_a_none(valor)

    def validate_numero_inventario(self, valor):
        return self._vacio_a_none(valor)

    def validate_imei(self, valor):
        return self._vacio_a_none(valor)

    def to_representation(self, instance):
        datos = super().to_representation(instance)
        for campo in self.CAMPOS_OPCIONALES:
            if datos.get(campo) is None:
                datos[campo] = ""
        return datos


class MantenimientoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Mantenimiento
        fields = "__all__"


class DepartamentoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Departamento
        fields = "__all__"


class EmpleadoSerializer(serializers.ModelSerializer):
    departamento_nombre = serializers.CharField(source="departamento.nombre", read_only=True)

    class Meta:
        model = Empleado
        fields = "__all__"


class TipoLicenciaSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoLicencia
        fields = "__all__"


class LicenciaSerializer(serializers.ModelSerializer):
    tipo_nombre = serializers.CharField(source="tipo.nombre", read_only=True)
    asientos_disponibles = serializers.IntegerField(read_only=True)

    class Meta:
        model = Licencia
        fields = "__all__"


class AsignacionSerializer(serializers.ModelSerializer):
    empleado_nombre = serializers.CharField(source="empleado.nombre_completo", read_only=True)
    equipo_nombre = serializers.SerializerMethodField()
    licencia_nombre = serializers.SerializerMethodField()

    class Meta:
        model = Asignacion
        fields = "__all__"

    # Con source="equipo.__str__", una asignación sin equipo (o sin licencia) mostraba el texto interno de None.__str__
    def get_equipo_nombre(self, obj):
        return str(obj.equipo) if obj.equipo else None

    def get_licencia_nombre(self, obj):
        return str(obj.licencia) if obj.licencia else None

    def validate(self, datos):
        actual = self.instance

        def valor(campo):
            if campo in datos:
                return datos[campo]
            return getattr(actual, campo, None) if actual else None

        empleado, equipo, licencia = valor("empleado"), valor("equipo"), valor("licencia")
        if equipo is None and licencia is None:
            raise ReglaDeNegocio("La asignación debe incluir un equipo o una licencia.")
        if valor("fecha_devolucion") is not None:
            return datos  # una asignación devuelta ya no ocupa nada

        # Solo se revisa si es nueva, si cambia de persona, equipo o licencia, o si se vuelve a abrir una devuelta.
        if actual is not None and actual.fecha_devolucion is None and all(valor(c) == getattr(actual, c) for c in ("empleado", "equipo", "licencia")):
            return datos

        otras = Asignacion.objects.filter(fecha_devolucion__isnull=True)
        if actual is not None:
            otras = otras.exclude(pk=actual.pk)
        if equipo is not None:
            ocupante = otras.filter(equipo=equipo).select_related("empleado").first()
            if ocupante is not None:
                raise ReglaDeNegocio(f"El equipo «{equipo}» ya está asignado a {ocupante.empleado.nombre_completo}. Devuélvelo o reasígnalo primero.")
            if (actual is None or actual.equipo_id != equipo.pk) and equipo.estado != "disponible":
                raise ReglaDeNegocio(f"El equipo «{equipo}» está en estado «{equipo.get_estado_display()}»: solo se pueden asignar equipos disponibles.")
        if licencia is not None:
            de_la_licencia = otras.filter(licencia=licencia)
            if de_la_licencia.filter(empleado=empleado).exists():
                raise ReglaDeNegocio(f"{empleado.nombre_completo} ya tiene la licencia «{licencia}» asignada.")
            if licencia.asientos_totales and de_la_licencia.count() >= licencia.asientos_totales:
                raise ReglaDeNegocio(f"La licencia «{licencia}» no tiene asientos libres ({de_la_licencia.count()} de {licencia.asientos_totales} en uso).")
        return datos


class CategoriaContrasenaSerializer(serializers.ModelSerializer):
    class Meta:
        model = CategoriaContrasena
        fields = "__all__"


class RegistroContrasenaSerializer(serializers.ModelSerializer):
    categoria_nombre = serializers.CharField(source="categoria.nombre", read_only=True)
    empleado_nombre = serializers.CharField(source="empleado.nombre_completo", read_only=True, default=None)

    class Meta:
        model = RegistroContrasena
        fields = "__all__"


class UsuarioSistemaSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = User
        fields = ["id", "username", "email", "is_staff", "is_active", "date_joined", "password"]
        read_only_fields = ["date_joined"]

    def validate_password(self, valor):
        problema = mensaje_password_invalida(valor)
        if problema:
            raise serializers.ValidationError(problema)
        return valor

    def create(self, validated_data):
        password = validated_data.pop("password", None)
        user = User(**validated_data)
        if password:
            user.set_password(password)
        user.save()
        return user

    def update(self, instance, validated_data):
        # Sin esto, la contraseña nueva se guardaba tal cual (texto plano) y el usuario no podía volver a entrar.
        password = validated_data.pop("password", None)
        user = super().update(instance, validated_data)
        if password:
            user.set_password(password)
            user.save()
        return user

class ProveedorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Proveedor
        fields = "__all__"

    def validate_calificacion(self, valor):
        if valor is not None and not 0 <= valor <= 5:
            raise serializers.ValidationError("La calificación va de 0 a 5 estrellas.")
        return valor

class PagoServicioSerializer(serializers.ModelSerializer):
    class Meta:
        model = PagoServicio
        fields = "__all__"


class ServicioContratadoSerializer(serializers.ModelSerializer):
    proveedor_nombre = serializers.CharField(source="proveedor.nombre", read_only=True, default=None)

    class Meta:
        model = ServicioContratado
        fields = "__all__"

class PuertoRedSerializer(serializers.ModelSerializer):
    class Meta:
        model = PuertoRed
        fields = "__all__"


class RackSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rack
        fields = "__all__"


class DispositivoRedSerializer(serializers.ModelSerializer):
    rack_nombre = serializers.CharField(source="rack.nombre", read_only=True, default=None)

    class Meta:
        model = DispositivoRed
        fields = "__all__"

    def validate(self, datos):
        actual = self.instance

        def valor(campo, defecto=None):
            if campo in datos:
                return datos[campo]
            return getattr(actual, campo, defecto) if actual else defecto

        rack, pos, alto = valor("rack"), valor("posicion_u"), valor("altura_u", 1) or 1
        if rack is None or not pos:
            return datos
        if actual is not None and all(valor(c) == getattr(actual, c) for c in ("rack", "posicion_u", "altura_u")):
            return datos  # no se movió: no se vuelve a revisar
        fin = pos + alto - 1  # un dispositivo ocupa de posicion_u a posicion_u + altura_u - 1 (así lo dibuja el rack)
        if rack.altura_u and fin > rack.altura_u:
            raise ReglaDeNegocio(f"No cabe: el rack «{rack.nombre}» tiene {rack.altura_u} U y este dispositivo llegaría hasta la U{fin}.")
        vecinos = DispositivoRed.objects.filter(rack=rack, posicion_u__isnull=False)
        if actual is not None:
            vecinos = vecinos.exclude(pk=actual.pk)
        for otro in vecinos:
            otro_fin = otro.posicion_u + (otro.altura_u or 1) - 1
            if pos <= otro_fin and otro.posicion_u <= fin:
                raise ReglaDeNegocio(f"La posición ya está ocupada por «{otro.nombre}» (U{otro.posicion_u} a U{otro_fin}).")
        return datos
