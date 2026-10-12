"""Ayudas para importar hojas de Excel (las usa la importación de Equipos)."""
import unicodedata


def _normalizar(texto):
    if texto is None:
        return ""
    texto = unicodedata.normalize("NFD", str(texto))
    return "".join(c for c in texto if unicodedata.category(c) != "Mn").strip().lower()


def fila_de_encabezados(ws, primera_columna="categoria", limite=15):
    """Número de la fila de encabezados: la que empieza con 'Categoria' / 'Categoría'.
    Las hojas que descargamos llevan el logo arriba, así que los encabezados no siempre están en la fila 1.
    Si no se reconoce ninguna, se asume la fila 1 (los datos empiezan en la 2, como antes)."""
    for n, fila in enumerate(ws.iter_rows(min_row=1, max_row=limite, values_only=True), start=1):
        if fila and _normalizar(fila[0]) == primera_columna:
            return n
    return 1


def texto_celda(valor):
    """Texto limpio de una celda. Un número entero (IMEI o serie que Excel guardó como número) sale sin '.0'."""
    if valor is None:
        return ""
    if isinstance(valor, float) and valor.is_integer():
        valor = int(valor)
    return str(valor).strip()
