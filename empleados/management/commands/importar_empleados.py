import csv
from django.core.management.base import BaseCommand
from empleados.models import Departamento, Empleado


class Command(BaseCommand):
    help = 'Importa empleados desde un archivo CSV (columnas: area,nombre,puesto,correo)'

    def add_arguments(self, parser):
        parser.add_argument('archivo_csv', type=str)

    def handle(self, *args, **options):
        ruta = options['archivo_csv']
        creados = 0
        actualizados = 0
        omitidos = 0

        with open(ruta, newline='', encoding='utf-8') as f:
            lector = csv.DictReader(f)
            for fila in lector:
                area = fila['area'].strip()
                nombre = fila['nombre'].strip()
                puesto = fila['puesto'].strip()
                correo = fila['correo'].strip().lower()

                if not correo or correo == 'n/a':
                    self.stdout.write(self.style.WARNING(f'Omitido (sin correo válido): {nombre}'))
                    omitidos += 1
                    continue

                departamento, _ = Departamento.objects.get_or_create(nombre=area)

                empleado, fue_creado = Empleado.objects.update_or_create(
                    correo=correo,
                    defaults={
                        'nombre_completo': nombre,
                        'puesto': puesto,
                        'departamento': departamento,
                        'estatus': 'activo',
                    }
                )

                if fue_creado:
                    creados += 1
                else:
                    actualizados += 1

        self.stdout.write(self.style.SUCCESS(
            f'Listo. Creados: {creados} | Actualizados: {actualizados} | Omitidos: {omitidos}'
        ))
