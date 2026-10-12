#!/bin/bash
# Respaldo automático de la base de datos de Fenrir (corre dentro del contenedor "inventario_ti_backup").
#
#  - Cada hora revisa si existe un respaldo de las últimas 24 horas. Si no, hace uno nuevo.
#    (Funciona aunque la computadora esté apagada o suspendida a cualquier hora.)
#  - Guarda los 14 diarios más recientes, y 8 semanales (cada domingo se guarda una copia aparte).
#  - Solo da por bueno un respaldo si el archivo está íntegro y termina como debe terminar un dump.
#
# Los datos de conexión los pone docker-compose: PGHOST, PGUSER, PGDATABASE, PGPASSWORD.
# Para hacer un respaldo en este momento:   docker exec inventario_ti_backup /respaldar.sh ahora

DIR="${RESPALDOS_DIR:-/respaldos}"
DIARIOS="${RESPALDAR_DIARIOS:-14}"
SEMANALES="${RESPALDAR_SEMANALES:-8}"
CADA="${RESPALDAR_CADA:-3600}"           # cada cuántos segundos se revisa
EDAD_MIN="${RESPALDAR_EDAD_MIN:-1440}"   # "reciente" = de hace menos de estos minutos (24 h)

mkdir -p "$DIR/diarios" "$DIR/semanales"

registrar() { echo "[$(date '+%F %T')] $*"; }

hacer_respaldo() {
  local archivo tmp
  archivo="$DIR/diarios/fenrir_$(date +%Y%m%d_%H%M%S).sql.gz"
  tmp="$archivo.tmp"
  # --clean --if-exists: el respaldo se puede restaurar encima de una base que ya tenga datos.
  if ( set -o pipefail; pg_dump --clean --if-exists --no-owner --no-privileges | gzip > "$tmp" ) \
     && gzip -t "$tmp" \
     && gunzip -c "$tmp" | tail -n 5 | grep -q "PostgreSQL database dump complete"; then
    mv "$tmp" "$archivo"
    registrar "respaldo creado: $(basename "$archivo") ($(du -h "$archivo" | cut -f1))"
    if [ "$(date +%u)" = "7" ]; then cp "$archivo" "$DIR/semanales/"; fi
    return 0
  fi
  rm -f "$tmp"
  registrar "ERROR: el respaldo falló (¿la base de datos está disponible?). Se reintenta en la próxima revisión."
  return 1
}

limpiar() {
  ls -1t "$DIR"/diarios/fenrir_*.sql.gz 2>/dev/null | tail -n +"$((DIARIOS + 1))" | xargs -r rm -f
  ls -1t "$DIR"/semanales/fenrir_*.sql.gz 2>/dev/null | tail -n +"$((SEMANALES + 1))" | xargs -r rm -f
}

hay_reciente() {
  [ -n "$(find "$DIR/diarios" -name 'fenrir_*.sql.gz' -mmin "-$EDAD_MIN" 2>/dev/null | head -n 1)" ]
}

if [ "${1:-}" = "ahora" ]; then
  hacer_respaldo && limpiar
  exit $?
fi

registrar "Respaldo automático activo (esperando a la base de datos...)"
until pg_isready -q; do sleep 5; done
registrar "Listo: cada $((CADA / 60)) min se revisa si falta un respaldo de las últimas $((EDAD_MIN / 60)) h. Carpeta: $DIR"
while true; do
  if ! hay_reciente; then
    hacer_respaldo && limpiar
  fi
  sleep "$CADA"
done
