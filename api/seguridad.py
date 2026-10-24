"""Reglas compartidas del servidor: contraseñas y avisos de «no se puede» con su motivo."""
import re

from rest_framework.exceptions import APIException


class ReglaDeNegocio(APIException):
    """Algo que el sistema no permite por una regla (no por un dato mal escrito).
    Responde 409 con el motivo en «detail», el mismo formato que usa el borrado."""
    status_code = 409
    default_detail = "La operación no se puede realizar."
    default_code = "regla_de_negocio"


def mensaje_password_invalida(password):
    """Reglas de contraseña de Fenrir (las mismas del registro): 8 caracteres o más, una mayúscula y un número.
    Devuelve el mensaje de error, o None si la contraseña es válida."""
    if not isinstance(password, str) or len(password) < 8 or not re.search(r"[A-Z]", password) or not re.search(r"[0-9]", password):
        return "La contraseña debe tener 8+ caracteres, una mayúscula y un número."
    return None
