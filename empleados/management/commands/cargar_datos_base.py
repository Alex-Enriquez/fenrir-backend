"""Carga los catálogos iniciales: departamentos, categorías de equipo, tipos de licencia y categorías de contraseñas.

    python manage.py cargar_datos_base                         # la lista básica
    python manage.py cargar_datos_base --simular               # muestra qué agregaría, sin crear nada
    python manage.py cargar_datos_base --archivo mis.json      # tus propias listas (el archivo queda fuera del repositorio)

Se puede correr las veces que quieras: lo que ya existe (sin importar mayúsculas ni espacios de más) se deja como está.

Formato de --archivo (todas las claves son opcionales; cada elemento puede ser un texto o, en los tipos de licencia,
un objeto con "nombre" y "proveedor"):
    {
      "departamentos": ["TI", "Finanzas"],
      "categorias_equipo": ["Laptop", "Monitor"],
      "tipos_licencia": [{"nombre": "Microsoft 365", "proveedor": "Microsoft"}, "Antivirus"],
      "categorias_contrasena": ["Correos"]
    }
"""
import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from contrasenas.models import CategoriaContrasena
from empleados.models import Departamento
from equipos.models import CategoriaEquipo
from licencias.models import TipoLicencia

DATOS_BASE = {
    "departamentos": [
        "Dirección", "Administración", "Finanzas", "Recursos Humanos", "Ventas",
        "Marketing", "Operaciones", "Almacén", "TI",
    ],
    "categorias_equipo": [
        "Laptop", "PC de escritorio", "Monitor", "Celular", "Tablet", "Impresora", "Teléfono IP",
        "Teclado", "Mouse", "Cargador", "Cámara", "Proyector", "Servidor", "Accesorio",
    ],
    "tipos_licencia": [
        {"nombre": "Microsoft 365", "proveedor": "Microsoft"},
        {"nombre": "Windows", "proveedor": "Microsoft"},
        {"nombre": "Antivirus", "proveedor": ""},
        {"nombre": "Adobe Creative Cloud", "proveedor": "Adobe"},
        {"nombre": "AutoCAD", "proveedor": "Autodesk"},
        {"nombre": "Zoom", "proveedor": "Zoom"},
    ],
    "categorias_contrasena": [
        "Correos", "Aplicativos internos", "Sistemas/Servidores", "Servicios externos", "Redes y WiFi",
    ],
}

# clave del archivo, modelo, nombre para mostrar, ¿admite "proveedor"?
CATALOGOS = [
    ("departamentos", Departamento, "Departamentos", False),
    ("categorias_equipo", CategoriaEquipo, "Categorías de equipo", False),
    ("tipos_licencia", TipoLicencia, "Tipos de licencia", True),
    ("categorias_contrasena", CategoriaContrasena, "Categorías de contraseñas", False),
]


class Command(BaseCommand):
    help = "Carga los catálogos iniciales (departamentos, categorías de equipo, tipos de licencia y de contraseñas)."

    def add_arguments(self, parser):
        parser.add_argument("--archivo", help="Archivo JSON con tus propias listas (ver el formato en este archivo).")
        parser.add_argument("--simular", action="store_true", help="Muestra qué se agregaría, sin crear nada.")

    def handle(self, *args, **opciones):
        datos = self.leer_datos(opciones.get("archivo"))
        pendientes, errores = [], []

        for clave, modelo, titulo, admite_proveedor in CATALOGOS:
            for elemento in datos.get(clave, []):
                try:
                    nombre, extra = self.normalizar(elemento, admite_proveedor)
                except ValueError as e:
                    errores.append(f"{titulo}: {e}")
                    continue
                pendientes.append((titulo, modelo, nombre, extra))
        if errores:
            raise CommandError("No se cargó nada porque hay datos inválidos:\n  - " + "\n  - ".join(errores))

        resumen = {titulo: {"nuevos": [], "existentes": 0} for _, _, titulo, _ in CATALOGOS}
        with transaction.atomic():
            for titulo, modelo, nombre, extra in pendientes:
                if modelo.objects.filter(nombre__iexact=nombre).exists():
                    resumen[titulo]["existentes"] += 1
                    continue
                resumen[titulo]["nuevos"].append(nombre)
                if not opciones["simular"]:
                    modelo.objects.create(nombre=nombre, **extra)

        total = 0
        for _, _, titulo, _ in CATALOGOS:
            nuevos, existentes = resumen[titulo]["nuevos"], resumen[titulo]["existentes"]
            total += len(nuevos)
            verbo = "se agregarían" if opciones["simular"] else "nuevos"
            self.stdout.write(f"  {titulo}: {len(nuevos)} {verbo}, {existentes} ya existían")
            if opciones["simular"] and nuevos:
                self.stdout.write("      " + ", ".join(nuevos))
        if opciones["simular"]:
            self.stdout.write(self.style.WARNING(f"Simulación: no se creó nada. Se agregarían {total} elementos."))
        else:
            self.stdout.write(self.style.SUCCESS(f"Listo. Elementos nuevos: {total}."))

    def leer_datos(self, ruta):
        if not ruta:
            return DATOS_BASE
        archivo = Path(ruta).expanduser()
        if not archivo.is_file():
            raise CommandError(f"No encuentro el archivo: {archivo}")
        try:
            datos = json.loads(archivo.read_text(encoding="utf-8"))
        except (ValueError, OSError) as e:
            raise CommandError(f"No pude leer {archivo} como JSON: {e}")
        if not isinstance(datos, dict):
            raise CommandError('El archivo debe ser un objeto JSON, por ejemplo {"departamentos": ["TI"]}.')
        validas = [c[0] for c in CATALOGOS]
        desconocidas = [k for k in datos if k not in validas]
        if desconocidas:
            raise CommandError(f"Claves desconocidas en el archivo: {', '.join(desconocidas)}. Las válidas: {', '.join(validas)}.")
        for clave, valor in datos.items():
            if not isinstance(valor, list):
                raise CommandError(f'"{clave}" debe ser una lista.')
        return datos

    @staticmethod
    def normalizar(elemento, admite_proveedor):
        extra = {}
        if isinstance(elemento, dict):
            if "nombre" not in elemento:
                raise ValueError(f"falta el \"nombre\" en {elemento!r}")
            otras = set(elemento) - {"nombre", "proveedor"}
            if otras or ("proveedor" in elemento and not admite_proveedor):
                raise ValueError(f"campos no permitidos en {elemento!r}")
            if "proveedor" in elemento:
                extra["proveedor"] = " ".join(str(elemento["proveedor"] or "").split())
                if len(extra["proveedor"]) > 100:
                    raise ValueError(f"el proveedor de {elemento['nombre']!r} es demasiado largo (máximo 100)")
            elemento = elemento["nombre"]
        if not isinstance(elemento, str):
            raise ValueError(f"se esperaba un texto y llegó {elemento!r}")
        nombre = " ".join(elemento.split())
        if not nombre:
            raise ValueError("hay un nombre vacío")
        if len(nombre) > 100:
            raise ValueError(f"el nombre {nombre[:30]!r}... es demasiado largo (máximo 100)")
        return nombre, extra
