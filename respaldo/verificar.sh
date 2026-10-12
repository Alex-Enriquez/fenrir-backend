#!/bin/bash
# Comprueba que el respaldo MÁS RECIENTE se puede restaurar de verdad, sin tocar tus datos:
# revisa que el archivo esté íntegro, lo restaura en una base temporal, la compara con la real y la borra.
#   Uso:   ./respaldo/verificar.sh

DB_CONT="${DB_CONTAINER:-inventario_ti_db}"
BK_CONT="${BACKUP_CONTAINER:-inventario_ti_backup}"
USUARIO="${DB_USER:-inventario_user}"
BASE="${DB_NAME:-inventario_ti}"
TEMP="verificacion_respaldo"

psql_db() { docker exec "$DB_CONT" psql -U "$USUARIO" -v ON_ERROR_STOP=1 -qtA "$@"; }

archivo=$(docker exec "$BK_CONT" sh -c 'ls -1t /respaldos/diarios/fenrir_*.sql.gz 2>/dev/null | head -1' | tr -d '\r')
if [ -z "$archivo" ]; then
  echo "Todavía no hay respaldos. Espera unos minutos, o haz uno ahora:"
  echo "   docker exec $BK_CONT /respaldar.sh ahora"
  exit 1
fi
echo "Respaldo a verificar: $(basename "$archivo")"

# 1) ¿el archivo está completo? (no truncado, no corrupto, termina como debe terminar un respaldo)
if ! docker exec "$BK_CONT" sh -c "gzip -t '$archivo' && gunzip -c '$archivo' | tail -n 5 | grep -q 'PostgreSQL database dump complete'" 2> /dev/null; then
  echo "✗ El archivo está DAÑADO o incompleto: no sirve para restaurar."
  echo "  Haz uno nuevo:  docker exec $BK_CONT /respaldar.sh ahora   y vuelve a verificar."
  exit 1
fi

# 2) ¿se puede restaurar? (en una base temporal, dentro de una sola transacción)
psql_db -d postgres -c "DROP DATABASE IF EXISTS $TEMP" -c "CREATE DATABASE $TEMP" > /dev/null 2>&1 || { echo "No pude crear la base temporal."; exit 1; }
trap 'psql_db -d postgres -c "DROP DATABASE IF EXISTS '"$TEMP"'" > /dev/null 2>&1' EXIT
if ! docker exec "$BK_CONT" bash -c "set -o pipefail; gunzip -c '$archivo' | PGDATABASE=$TEMP psql -q -1 -v ON_ERROR_STOP=1 > /dev/null"; then
  echo "✗ El respaldo NO se pudo restaurar. Haz uno nuevo y vuelve a verificar."
  exit 1
fi

contar() {   # imprime: número de tablas y total de filas de una base
  local db="$1" t n total=0 ntablas=0
  for t in $(psql_db -d "$db" -c "select table_name from information_schema.tables where table_schema='public' and table_type='BASE TABLE' order by 1"); do
    n=$(psql_db -d "$db" -c "select count(*) from \"$t\"")
    total=$((total + n)); ntablas=$((ntablas + 1))
  done
  echo "$ntablas $total"
}
read -r t_resp f_resp < <(contar "$TEMP")
read -r t_real f_real < <(contar "$BASE")
echo "   restaurado en la base temporal: $t_resp tablas, $f_resp filas"
echo "   tu base de datos actual:        $t_real tablas, $f_real filas"
if [ "$t_resp" = "$t_real" ] && [ "$t_resp" -gt 0 ]; then
  echo "✓ El respaldo está completo y se restaura bien. (Las filas pueden diferir un poco si trabajaste después de la copia.)"
else
  echo "⚠ La cantidad de tablas no coincide: revisa el respaldo antes de confiar en él."
  exit 1
fi
