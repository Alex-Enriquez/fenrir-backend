from django.conf import settings
from django.db import models
from cryptography.fernet import Fernet


def _get_fernet():
    return Fernet(settings.FERNET_KEY.encode())


class CampoCifrado(models.TextField):
    """Campo de texto que se cifra automáticamente al guardar y se descifra al leer."""

    def get_prep_value(self, value):
        if value is None or value == '':
            return value
        f = _get_fernet()
        return f.encrypt(value.encode()).decode()

    def from_db_value(self, value, expression, connection):
        if value is None or value == '':
            return value
        f = _get_fernet()
        try:
            return f.decrypt(value.encode()).decode()
        except Exception:
            return value  # por si ya había datos sin cifrar (no debería pasar)

    def to_python(self, value):
        return value
