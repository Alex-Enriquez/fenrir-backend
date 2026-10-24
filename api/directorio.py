"""Directorio telefónico: extensiones, líneas fijas y celulares de la empresa.
Todos los usuarios con sesión pueden VER el directorio; solo el administrador lo cambia.
Los detalles de la línea (operador, plan, chip, equipo y notas) los ve solo el administrador."""
import re

from rest_framework import serializers, viewsets
from rest_framework.decorators import action

from empleados.lineas import LineaTelefonica
from .catalogos import SoloAdminEscribe
from .excel_utils import generar_excel

CAMPOS_SOLO_ADMIN = ("operador", "plan", "chip", "equipo", "equipo_nombre", "notas")
ETIQUETA = {"extension": "la extensión", "celular": "el celular", "fijo": "la línea fija"}


def normalizar_numero(tipo, numero):
    """Deja solo los dígitos. Extensión: de 2 a 6. Celular o fija (México): 10, aceptando +52, 52 o 521 al inicio."""
    digitos = re.sub(r"\D", "", str(numero or ""))
    if tipo == "extension":
        if not re.fullmatch(r"\d{2,6}", digitos):
            raise serializers.ValidationError({"numero": "La extensión debe tener de 2 a 6 dígitos."})
        return digitos
    if len(digitos) == 13 and digitos.startswith("521"):
        digitos = digitos[3:]
    elif len(digitos) == 12 and digitos.startswith("52"):
        digitos = digitos[2:]
    if len(digitos) != 10:
        raise serializers.ValidationError({"numero": "El número debe tener 10 dígitos (por ejemplo 55 1234 5678)."})
    return digitos


def formatear_numero(tipo, numero):
    if tipo != "extension" and len(numero) == 10:
        return f"{numero[:2]} {numero[2:6]} {numero[6:]}"
    return numero


def departamento_de(linea):
    if linea.departamento:
        return linea.departamento.nombre
    if linea.empleado and linea.empleado.departamento:
        return linea.empleado.departamento.nombre
    return ""


class LineaTelefonicaSerializer(serializers.ModelSerializer):
    nombre = serializers.CharField(max_length=150, required=False, allow_blank=True)
    tipo_nombre = serializers.CharField(source="get_tipo_display", read_only=True)
    empleado_nombre = serializers.CharField(source="empleado.nombre_completo", read_only=True, default=None)
    equipo_nombre = serializers.SerializerMethodField()
    departamento_nombre = serializers.SerializerMethodField()
    # Sin la validación automática de unicidad de DRF (compara lo que se escribió, antes de limpiarlo, y en inglés):
    # el chip y el número se comprueban abajo, ya limpios y con un mensaje claro.
    chip = serializers.CharField(max_length=25, required=False, allow_blank=True, allow_null=True)

    class Meta:
        model = LineaTelefonica
        fields = "__all__"
        validators = []

    def get_departamento_nombre(self, obj):
        return departamento_de(obj)

    def get_equipo_nombre(self, obj):
        # Con source="equipo.__str__" una línea sin equipo mostraba el texto interno de None.__str__
        return str(obj.equipo) if obj.equipo else None

    def validate_chip(self, valor):
        valor = re.sub(r"\s+", "", str(valor or ""))
        if not valor:
            return None
        repetidas = LineaTelefonica.objects.filter(chip=valor)
        if self.instance is not None:
            repetidas = repetidas.exclude(pk=self.instance.pk)
        existente = repetidas.first()
        if existente is not None:
            raise serializers.ValidationError(f"Ya hay una línea con ese chip ({existente.nombre}).")
        return valor

    def validate(self, datos):
        actual = self.instance

        def valor(campo, defecto=None):
            if campo in datos:
                return datos[campo]
            return getattr(actual, campo, defecto) if actual else defecto

        tipo = valor("tipo")
        if not tipo:
            raise serializers.ValidationError({"tipo": "Elige el tipo de entrada."})
        numero = normalizar_numero(tipo, valor("numero"))
        datos["numero"] = numero

        nombre = " ".join(str(valor("nombre") or "").split())
        empleado = valor("empleado")
        if not nombre and empleado is not None:
            nombre = empleado.nombre_completo
        if not nombre:
            raise serializers.ValidationError({"nombre": "Escribe el nombre o el área, o elige un empleado."})
        datos["nombre"] = nombre

        if valor("activo", True):
            repetidas = LineaTelefonica.objects.filter(tipo=tipo, numero=numero, activo=True)
            if actual is not None:
                repetidas = repetidas.exclude(pk=actual.pk)
            existente = repetidas.first()
            if existente is not None:
                raise serializers.ValidationError({"numero": f"Ya existe {ETIQUETA[tipo]} {formatear_numero(tipo, numero)} ({existente.nombre})."})

        if tipo == "extension":      # una extensión no lleva chip, plan ni equipo
            datos.update({"operador": "", "plan": "", "chip": None, "equipo": None})
        for campo in ("ubicacion", "operador", "plan"):
            if campo in datos:
                datos[campo] = " ".join(str(datos[campo] or "").split())
        return datos

    def to_representation(self, instancia):
        datos = super().to_representation(instancia)
        if datos.get("chip") is None:
            datos["chip"] = ""
        peticion = self.context.get("request")
        if not (peticion and peticion.user and peticion.user.is_staff):
            for campo in CAMPOS_SOLO_ADMIN:
                datos[campo] = None if campo in ("equipo", "equipo_nombre") else ""
        return datos


class LineaTelefonicaViewSet(viewsets.ModelViewSet):
    queryset = LineaTelefonica.objects.select_related("empleado", "empleado__departamento", "departamento", "equipo")
    serializer_class = LineaTelefonicaSerializer
    permission_classes = [SoloAdminEscribe]

    @action(detail=False, methods=["get"])
    def exportar(self, request):
        es_admin = bool(request.user and request.user.is_staff)
        encabezados = ["Tipo", "Número", "Nombre", "Departamento", "Ubicación"]
        if es_admin:
            encabezados += ["Operador", "Plan", "Chip", "Equipo", "Notas"]
        encabezados.append("Activo")
        filas = []
        for linea in self.get_queryset():
            fila = [linea.get_tipo_display(), formatear_numero(linea.tipo, linea.numero), linea.nombre, departamento_de(linea), linea.ubicacion]
            if es_admin:
                fila += [linea.operador, linea.plan, linea.chip or "", str(linea.equipo) if linea.equipo else "", linea.notas]
            fila.append("Sí" if linea.activo else "No")
            filas.append(fila)
        return generar_excel("directorio.xlsx", encabezados, filas)
