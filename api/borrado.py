"""Borrado con aviso claro.

Algunos registros no se pueden eliminar mientras otros dependan de ellos: por ejemplo, un equipo o un empleado que aparece en una
responsiva (la responsiva es un documento y no se debe quedar sin su equipo o su empleado). Antes, el servidor fallaba con un error
500 y la pantalla solo decía "No se pudo eliminar", sin decir por qué.
"""
from django.db.models import ProtectedError
from rest_framework.response import Response


class BorradoProtegidoMixin:
    # Cada pantalla ajusta el verbo y la sugerencia: «porque aparece en 2 responsivas», «porque tiene 2 responsivas»...
    verbo_borrado = "aparece en"
    sugerencia_borrado = "Elimina primero esas responsivas."

    def destroy(self, request, *args, **kwargs):
        objeto = self.get_object()
        try:
            return super().destroy(request, *args, **kwargs)
        except ProtectedError as error:
            # Lo protegido son las filas de responsiva (o sus renglones): de cualquiera de las dos se obtiene el folio.
            folios = sorted({getattr(getattr(p, "responsiva", p), "folio", str(p)) for p in error.protected_objects})
            n = len(folios)
            responsivas = f"{n} responsiva{'s' if n != 1 else ''}"
            texto = (f"No se puede eliminar «{objeto}» porque {self.verbo_borrado} {responsivas}: "
                     f"{', '.join(folios)}. {self.sugerencia_borrado}")
            return Response({"detail": texto}, status=409)
