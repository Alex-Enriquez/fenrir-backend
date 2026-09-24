from rest_framework import serializers
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

    class Meta:
        model = Equipo
        fields = "__all__"


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
    equipo_nombre = serializers.CharField(source="equipo.__str__", read_only=True)
    licencia_nombre = serializers.CharField(source="licencia.__str__", read_only=True)

    class Meta:
        model = Asignacion
        fields = "__all__"


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

    def create(self, validated_data):
        password = validated_data.pop("password", None)
        user = User(**validated_data)
        if password:
            user.set_password(password)
        user.save()
        return user

class ProveedorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Proveedor
        fields = "__all__"

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
