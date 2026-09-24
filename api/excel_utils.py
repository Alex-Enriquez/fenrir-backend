import openpyxl
from openpyxl.utils import get_column_letter
from django.http import HttpResponse


def generar_excel(nombre_archivo, encabezados, filas):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(encabezados)

    for fila in filas:
        ws.append(fila)

    for i, _ in enumerate(encabezados, start=1):
        ws.column_dimensions[get_column_letter(i)].width = 22

    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="{nombre_archivo}"'
    wb.save(response)
    return response
