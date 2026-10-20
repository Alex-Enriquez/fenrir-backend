import base64
from pathlib import Path
from django.conf import settings
from django.db import transaction
from django.template.loader import render_to_string
from django.http import HttpResponse
from rest_framework import viewsets
from rest_framework.permissions import IsAdminUser
from rest_framework.decorators import action
from rest_framework.response import Response
from xhtml2pdf import pisa
from asignaciones.models import Asignacion
from .models import Responsiva
from .serializers import ResponsivaSerializer


class ResponsivaViewSet(viewsets.ModelViewSet):
    queryset = Responsiva.objects.all().order_by("-id")
    serializer_class = ResponsivaSerializer
    permission_classes = [IsAdminUser]

    @transaction.atomic
    def perform_create(self, serializer):
        # Todo o nada: la responsiva, su folio y el cambio de asignaciones se guardan juntos.
        responsiva = serializer.save()

        # Sincroniza Asignaciones: cada equipo incluido queda asignado a este empleado
        for item in responsiva.items.all():
            ya_activa = Asignacion.objects.filter(
                equipo=item.equipo, fecha_devolucion__isnull=True
            ).first()
            if ya_activa and ya_activa.empleado_id != responsiva.empleado_id:
                ya_activa.fecha_devolucion = responsiva.fecha
                ya_activa.save()
                ya_activa = None
            if not ya_activa:
                Asignacion.objects.create(empleado=responsiva.empleado, equipo=item.equipo)

    @action(detail=True, methods=["get"])
    def pdf(self, request, pk=None):
        responsiva = self.get_object()
        items = responsiva.items.all()

        ruta_logo = Path(settings.BASE_DIR) / "alamex_logo.png"
        logo_base64 = base64.b64encode(ruta_logo.read_bytes()).decode() if ruta_logo.exists() else ""

        html = render_to_string("responsivas/responsiva_pdf.html", {
            "responsiva": responsiva,
            "items": items,
            "logo_base64": logo_base64,
        })

        response = HttpResponse(content_type="application/pdf")
        response["Content-Disposition"] = f'inline; filename="{responsiva.folio}.pdf"'

        pisa_status = pisa.CreatePDF(html, dest=response)
        if pisa_status.err:
            return Response({"error": "No se pudo generar el PDF."}, status=500)

        return response
