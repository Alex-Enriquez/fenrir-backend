from rest_framework import serializers
from .models import Perfil


class PerfilSerializer(serializers.ModelSerializer):
    class Meta:
        model = Perfil
        fields = ["nombre_completo", "puesto", "ha_visto_bienvenida", "mostrar_tips", "fecha_ultimo_tip"]
