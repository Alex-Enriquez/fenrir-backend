from rest_framework import serializers
from .models import Responsiva, ResponsivaItem


class ResponsivaItemSerializer(serializers.ModelSerializer):
    equipo_nombre = serializers.CharField(source="equipo.__str__", read_only=True)

    class Meta:
        model = ResponsivaItem
        fields = ["id", "equipo", "equipo_nombre", "cantidad"]


class ResponsivaSerializer(serializers.ModelSerializer):
    items = ResponsivaItemSerializer(many=True)
    empleado_nombre = serializers.CharField(source="empleado.nombre_completo", read_only=True)

    class Meta:
        model = Responsiva
        fields = ["id", "folio", "empleado", "empleado_nombre", "fecha", "quien_entrega", "observaciones", "items"]
        read_only_fields = ["folio", "fecha"]

    def validate_items(self, valor):
        if not valor:
            raise serializers.ValidationError("La responsiva debe incluir al menos un equipo.")
        return valor

    def create(self, validated_data):
        items_data = validated_data.pop("items")
        responsiva = Responsiva.objects.create(**validated_data)
        for item in items_data:
            ResponsivaItem.objects.create(responsiva=responsiva, **item)
        return responsiva
