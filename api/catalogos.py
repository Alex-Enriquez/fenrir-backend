"""Catálogos: departamentos, categorías de equipo, tipos de licencia y categorías de contraseñas."""
from django.db.models import ProtectedError
from rest_framework import serializers
from rest_framework.permissions import SAFE_METHODS, BasePermission
from rest_framework.response import Response


class SoloAdminEscribe(BasePermission):
    """Cualquier usuario con sesión puede LEER; solo el administrador puede crear, cambiar o eliminar."""

    def has_permission(self, request, view):
        usuario = request.user
        if not (usuario and usuario.is_authenticated):
            return False
        if request.method in SAFE_METHODS:
            return True
        return bool(usuario.is_staff)


_SERIALIZERS = {}


def serializer_catalogo(base, relacion):
    """Variante del serializador que agrega cuántos registros usan cada elemento ("usos") y evita nombres
    repetidos, sin importar mayúsculas ni espacios de más."""
    clave = (base, relacion)
    if clave not in _SERIALIZERS:
        def get_usos(self, obj):
            return getattr(obj, relacion).count()

        def validate_nombre(self, valor):
            valor = " ".join(str(valor).split())
            if not valor:
                raise serializers.ValidationError("El nombre no puede quedar vacío.")
            repetidos = self.Meta.model.objects.filter(nombre__iexact=valor)
            if self.instance is not None:
                repetidos = repetidos.exclude(pk=self.instance.pk)
            existente = repetidos.first()
            if existente is not None:
                raise serializers.ValidationError(f"Ya existe «{existente.nombre}».")
            return valor

        _SERIALIZERS[clave] = type(base.__name__ + "Catalogo", (base,), {
            "usos": serializers.SerializerMethodField(),
            "get_usos": get_usos,
            "validate_nombre": validate_nombre,
        })
    return _SERIALIZERS[clave]


class CatalogoViewSetMixin:
    """Se pone antes de ModelViewSet. Cada catálogo indica con qué relación se cuenta su uso
    (relacion_uso) y cómo se llaman, en singular y plural, los registros que lo usan (etiqueta_uso)."""
    relacion_uso = None
    etiqueta_uso = ("registro", "registros")
    permission_classes = [SoloAdminEscribe]

    def get_serializer_class(self):
        return serializer_catalogo(super().get_serializer_class(), self.relacion_uso)

    def contar_usos(self, objeto):
        return getattr(objeto, self.relacion_uso).count()

    def destroy(self, request, *args, **kwargs):
        objeto = self.get_object()
        usos = self.contar_usos(objeto)
        if usos:
            nombre = self.etiqueta_uso[0] if usos == 1 else self.etiqueta_uso[1]
            return Response({"detail": f"No se puede eliminar «{objeto}» porque está en uso: {usos} {nombre}."}, status=409)
        try:
            return super().destroy(request, *args, **kwargs)
        except ProtectedError:
            return Response({"detail": f"No se puede eliminar «{objeto}» porque está en uso."}, status=409)
