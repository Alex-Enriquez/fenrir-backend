#!/bin/bash
# Restaura un respaldo REEMPLAZANDO los datos actuales de la base de datos.
# Antes de tocar nada comprueba que el archivo esté íntegro, y restaura dentro de UNA transacción:
# si algo falla a la mitad, tu base queda exactamente como estaba.
#   ./respaldo/restaurar.sh                          -> usa el respaldo más reciente
#   ./respaldo/restaurar.sh fenrir_20261012_080000.sql.gz   -> usa uno en particular (diario o semanal)

BK_CONT="${BACKUP_CONTAINER:-inventario_ti_backup}"

if [ -n "${1:-}" ]; then
  archivo=$(docker exec "$BK_CONT" sh -c "ls /respaldos/diarios/'$1' /respaldos/semanales/'$1' 2>/dev/null | head -1" | tr -d '\r')
else
  archivo=$(docker exec "$BK_CONT" sh -c 'ls -1t /respaldos/diarios/fenrir_*.sql.gz 2>/dev/null | head -1' | tr -d '\r')
fi
if [ -z "$archivo" ]; then
  echo "No encuentro ese respaldo. Los que hay:"
  docker exec "$BK_CONT" sh -c 'ls -1t /respaldos/diarios /respaldos/semanales 2>/dev/null'
  exit 1
fi
echo "Respaldo elegido: $(basename "$archivo")"

if ! docker exec "$BK_CONT" sh -c "gzip -t '$archivo' && gunzip -c '$archivo' | tail -n 5 | grep -q 'PostgreSQL database dump complete'" 2> /dev/null; then
  echo "✗ Ese archivo está DAÑADO o incompleto. No se tocó nada. Prueba con otro respaldo."
  exit 1
fi

if [ "${RESTAURAR_CONFIRMADO:-}" != "SI" ]; then
  echo
  echo "Esto REEMPLAZA todos los datos actuales por los del respaldo."
  echo "Antes de seguir, detén el backend (Ctrl+C en la terminal donde corre)."
  read -r -p "Escribe SI para continuar: " respuesta
  [ "$respuesta" = "SI" ] || { echo "Cancelado. No se cambió nada."; exit 1; }
fi

if docker exec "$BK_CONT" bash -c "set -o pipefail; gunzip -c '$archivo' | psql -q -1 -v ON_ERROR_STOP=1 > /dev/null"; then
  echo "✓ Restaurado. Ya puedes volver a arrancar el backend."
else
  echo "✗ La restauración falló y se deshizo: tu base de datos quedó como estaba."
  exit 1
fi
