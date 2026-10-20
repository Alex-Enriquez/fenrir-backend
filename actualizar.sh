#!/usr/bin/env bash
# Actualiza Fenrir en un equipo que YA lo tiene instalado. No toca los datos: respalda la base de datos antes de
# cambiar nada, trae el código nuevo de GitHub, aplica las migraciones y revisa que el frontend compile.
#
#   ./actualizar.sh --revisar   solo revisa y dice qué cambiaría; NO modifica nada
#   ./actualizar.sh             respalda la base de datos y actualiza el backend y el frontend
#   ./actualizar.sh --forzar    igual, pero si el código de este equipo ya no coincide con GitHub (porque la historia
#                               se reescribió) lo alinea con GitHub, guardando antes una copia de lo anterior
#
# Rutas (opcional; por defecto busca el frontend junto al backend):
#   FENRIR_BACKEND=/ruta/inventario-ti  FENRIR_FRONTEND=/ruta/inventario-ti-frontend  ./actualizar.sh
# Si Docker necesita sudo:   FENRIR_DOCKER="sudo docker" ./actualizar.sh
# Si en este equipo se llama «docker-compose» (versión vieja):   FENRIR_COMPOSE=docker-compose ./actualizar.sh

BD_CONTENEDOR="inventario_ti_db"

ok()    { printf '  ✓ %s\n' "$*"; }
aviso() { printf '  ! %s\n' "$*"; }
paso()  { printf '\n== %s\n' "$*"; }
alto()  { printf '\n✗ %s\n' "$*" >&2; }

ayuda() {
  cat << 'EOF'
Uso: ./actualizar.sh [--revisar | --forzar]
  --revisar   solo revisa y dice qué cambiaría; no modifica nada
  --forzar    si el código de este equipo no coincide con GitHub (historia reescrita), lo alinea con GitHub
              guardando antes una copia de lo anterior
Variables: FENRIR_BACKEND, FENRIR_FRONTEND (rutas), FENRIR_DOCKER (por ejemplo "sudo docker")
           y FENRIR_COMPOSE (por ejemplo "docker-compose", si «docker compose» no existe)
EOF
}

leer_env() {   # leer_env VARIABLE [valor_por_defecto]
  local v
  v=$(grep -E "^[[:space:]]*$1=" "$BACKEND/.env" 2>/dev/null | tail -1 | cut -d= -f2- | tr -d '\r' | sed -e "s/^[\"']//" -e "s/[\"']\$//")
  if [ -n "$v" ]; then printf '%s' "$v"; else printf '%s' "${2:-}"; fi
}

localizar() {
  BACKEND="${FENRIR_BACKEND:-$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)}"
  FRONTEND="${FENRIR_FRONTEND:-}"
  if [ ! -f "$BACKEND/manage.py" ] || [ ! -d "$BACKEND/.git" ]; then
    alto "No encuentro el backend en $BACKEND. Indica la ruta:  FENRIR_BACKEND=/ruta/inventario-ti ./actualizar.sh"; return 1
  fi
  BACKEND="$(cd "$BACKEND" && pwd)"
  if [ -z "$FRONTEND" ]; then
    local c
    for c in "$BACKEND/../inventario-ti-frontend" "$BACKEND/../fenrir-frontend"; do
      if [ -d "$c/.git" ]; then FRONTEND="$c"; break; fi
    done
  fi
  if [ -z "$FRONTEND" ] || [ ! -f "$FRONTEND/package.json" ] || [ ! -d "$FRONTEND/.git" ]; then
    alto "No encuentro el frontend. Indica la ruta:  FENRIR_FRONTEND=/ruta/inventario-ti-frontend ./actualizar.sh"; return 1
  fi
  FRONTEND="$(cd "$FRONTEND" && pwd)"
  ok "Backend:  $BACKEND"
  ok "Frontend: $FRONTEND"
}

relacion() {   # relacion DIRECTORIO -> igual | atras | adelante | divergente
  local d="$1" l r
  l=$(git -C "$d" rev-parse HEAD) && r=$(git -C "$d" rev-parse origin/main) || { echo error; return; }
  if [ "$l" = "$r" ]; then echo igual
  elif git -C "$d" merge-base --is-ancestor "$l" "$r"; then echo atras
  elif git -C "$d" merge-base --is-ancestor "$r" "$l"; then echo adelante
  else echo divergente
  fi
}

describir() {  # describir DIRECTORIO RELACION
  local n; n=$(basename "$1")
  case "$2" in
    igual)      ok "$n: ya está al día con GitHub" ;;
    atras)      ok "$n: GitHub tiene $(git -C "$1" rev-list --count HEAD..origin/main) cambios nuevos para traer" ;;
    adelante)   aviso "$n: tiene $(git -C "$1" rev-list --count origin/main..HEAD) cambios locales sin subir a GitHub (no se tocará)" ;;
    divergente) aviso "$n: su historia ya no coincide con GitHub (se reescribió)" ;;
    *)          aviso "$n: no pude comparar con GitHub" ;;
  esac
}

verificar_contrasena() {   # prueba la contraseña del .env contra la base de datos REAL, igual que lo hará Django
  local py="$BACKEND/venv/bin/python"
  [ -x "$py" ] || py="python3"
  DB_HOST="$(leer_env DB_HOST 127.0.0.1)" DB_PORT="$(leer_env DB_PORT 5432)" DB_USER="$(leer_env DB_USER inventario_user)" \
  DB_NAME="$(leer_env DB_NAME inventario_ti)" DB_PASSWORD="$(leer_env DB_PASSWORD)" "$py" - << 'PYEOF' > /dev/null 2>&1
import os
import sys
try:
    import psycopg2 as pg
except ImportError:
    try:
        import psycopg as pg
    except ImportError:
        sys.exit(3)
try:
    pg.connect(host=os.environ["DB_HOST"], port=os.environ["DB_PORT"], dbname=os.environ["DB_NAME"],
               user=os.environ["DB_USER"], password=os.environ["DB_PASSWORD"], connect_timeout=5).close()
except Exception:
    sys.exit(1)
PYEOF
}

comprobar_contrasena() {   # imprime el resultado; devuelve 1 SOLO si la contraseña es incorrecta
  verificar_contrasena; local rc=$?
  case $rc in
    0) ok "La contraseña del .env coincide con la base de datos"; return 0 ;;
    3) aviso "No pude comprobar la contraseña (falta el conector de Postgres en el entorno virtual). Sigo; si la migración falla, revisa DB_PASSWORD en el .env."; return 0 ;;
    *) aviso "La contraseña DB_PASSWORD del .env NO coincide con la de la base de datos. Corrígela antes de actualizar."; return 1 ;;
  esac
}

actualizar_repo() {   # actualizar_repo DIRECTORIO RELACION
  local d="$1" rel="$2" n; n=$(basename "$1")
  case "$rel" in
    igual)    ok "$n: ya estaba al día" ;;
    atras)    git -C "$d" merge --ff-only -q origin/main || return 1
              ok "$n: actualizado a $(git -C "$d" rev-parse --short HEAD)" ;;
    adelante) aviso "$n: tiene cambios locales sin subir; no lo toqué" ;;
    divergente)
              git -C "$d" bundle create "$DESTINO/${n}_$MARCA.bundle" --all > /dev/null 2>&1 \
                || { alto "No pude guardar una copia de $n antes de alinearlo. No lo toqué."; return 1; }
              git -C "$d" reset -q --hard origin/main || return 1
              ok "$n: alineado con GitHub ($(git -C "$d" rev-parse --short HEAD)); lo anterior quedó guardado en $DESTINO/${n}_$MARCA.bundle" ;;
  esac
}

main() {
  local FORZAR=0 REVISAR=0 a d rama rb rf bloqueos=0
  for a in "$@"; do
    case "$a" in
      --forzar)  FORZAR=1 ;;
      --revisar) REVISAR=1 ;;
      -h|--ayuda|--help) ayuda; return 0 ;;
      *) echo "Opción desconocida: $a"; ayuda; return 2 ;;
    esac
  done
  DOCKER="${FENRIR_DOCKER:-docker}"
  COMPOSE="${FENRIR_COMPOSE:-$DOCKER compose}"

  paso "Revisando este equipo"
  localizar || return 1
  for d in "$BACKEND" "$FRONTEND"; do
    rama=$(git -C "$d" symbolic-ref --short HEAD 2>/dev/null)
    if [ "$rama" != "main" ]; then alto "$(basename "$d") está en la rama «${rama:-ninguna}», no en main. No toco nada."; return 1; fi
    git -C "$d" fetch -q origin || { alto "No pude consultar GitHub desde $(basename "$d") (¿hay internet?). No toco nada."; return 1; }
  done
  rb=$(relacion "$BACKEND"); rf=$(relacion "$FRONTEND")
  describir "$BACKEND" "$rb"; describir "$FRONTEND" "$rf"

  for d in "$BACKEND" "$FRONTEND"; do
    if [ -n "$(git -C "$d" status --porcelain --untracked-files=no)" ]; then
      aviso "$(basename "$d") tiene cambios sin guardar (se perderían al actualizar):"
      git -C "$d" status --short --untracked-files=no | sed 's/^/        /'
      bloqueos=$((bloqueos + 1))
    fi
  done
  if { [ "$rb" = divergente ] || [ "$rf" = divergente ]; } && [ "$FORZAR" -eq 0 ]; then
    aviso "La historia de GitHub se reescribió. Para alinear este equipo con GitHub (guardando antes una copia de lo anterior) usa:  ./actualizar.sh --forzar"
    bloqueos=$((bloqueos + 1))
  fi

  if ! $COMPOSE version > /dev/null 2>&1; then
    aviso "No encuentro «docker compose». Si en este equipo se llama «docker-compose», usa:  FENRIR_COMPOSE=docker-compose ./actualizar.sh"
    bloqueos=$((bloqueos + 1))
  fi

  if [ ! -f "$BACKEND/.env" ] || [ -z "$(leer_env DB_PASSWORD)" ]; then
    aviso "El .env no tiene DB_PASSWORD. La versión nueva la necesita: agrega la línea DB_PASSWORD=<la contraseña actual de la base de datos>."
    bloqueos=$((bloqueos + 1))
  elif $DOCKER ps --format '{{.Names}}' 2> /dev/null | grep -qx "$BD_CONTENEDOR"; then
    comprobar_contrasena || bloqueos=$((bloqueos + 1))
  elif [ "$REVISAR" -eq 1 ]; then
    aviso "La base de datos no está encendida; no pude comprobar la contraseña (el modo normal la enciende y la comprueba antes de cambiar nada)."
  fi

  if [ "$bloqueos" -gt 0 ]; then alto "Hay cosas por resolver antes de actualizar. No modifiqué nada."; return 1; fi
  if [ "$REVISAR" -eq 1 ]; then paso "Todo en orden. Esto fue solo una revisión: no se modificó nada. Para actualizar:  ./actualizar.sh"; return 0; fi

  paso "Encendiendo la base de datos (si hacía falta)"
  if ! $DOCKER ps --format '{{.Names}}' 2> /dev/null | grep -qx "$BD_CONTENEDOR"; then
    (cd "$BACKEND" && $COMPOSE up -d) || { alto "No pude encender la base de datos. No modifiqué nada."; return 1; }
    local i; for i in $(seq 1 30); do $DOCKER exec "$BD_CONTENEDOR" pg_isready -q 2> /dev/null && break; sleep 1; done
    comprobar_contrasena || { alto "No modifiqué nada."; return 1; }
  fi
  ok "Base de datos encendida"

  paso "Respaldo de la base de datos (antes de cambiar nada)"
  local resp; resp="$(leer_env BACKUP_DIR "$BACKEND/../respaldos-fenrir")"
  case "$resp" in /*) ;; *) resp="$BACKEND/$resp" ;; esac
  MARCA="$(date +%Y%m%d_%H%M%S)"; DESTINO="$resp/antes-de-actualizar"
  mkdir -p "$DESTINO" || { alto "No pude crear $DESTINO. No modifiqué nada."; return 1; }
  local archivo="$DESTINO/fenrir_$MARCA.sql.gz"
  ( set -o pipefail; $DOCKER exec "$BD_CONTENEDOR" sh -c 'pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB"' | gzip > "$archivo" ) \
    && gzip -t "$archivo" && [ "$(wc -c < "$archivo")" -gt 1000 ] \
    || { rm -f "$archivo"; alto "El respaldo falló. No modifiqué nada."; return 1; }
  ok "Respaldo guardado: $archivo ($(du -h "$archivo" | cut -f1))"

  paso "Trayendo el código nuevo"
  actualizar_repo "$BACKEND" "$rb" || { alto "No pude actualizar el backend."; return 1; }
  actualizar_repo "$FRONTEND" "$rf" || { alto "No pude actualizar el frontend."; return 1; }

  paso "Backend: servicios, dependencias y migraciones"
  mkdir -p "$resp"   # que Docker no la cree con permisos de root
  (cd "$BACKEND" && $COMPOSE up -d) || { alto "No pude aplicar el docker-compose nuevo."; return 1; }
  for i in $(seq 1 30); do $DOCKER exec "$BD_CONTENEDOR" pg_isready -q 2> /dev/null && break; sleep 1; done
  [ -x "$BACKEND/venv/bin/python" ] || python3 -m venv "$BACKEND/venv" || { alto "No pude crear el entorno virtual."; return 1; }
  if [ -f "$BACKEND/requirements.txt" ]; then
    "$BACKEND/venv/bin/pip" install -q -r "$BACKEND/requirements.txt" || { alto "Falló la instalación de dependencias de Python."; return 1; }
  fi
  ok "Dependencias de Python al día"
  (cd "$BACKEND" && "$BACKEND/venv/bin/python" manage.py migrate --noinput) || { alto "Falló la migración. Tu respaldo está en $archivo"; return 1; }
  (cd "$BACKEND" && "$BACKEND/venv/bin/python" manage.py check) || { alto "Django reporta problemas de configuración."; return 1; }

  paso "Frontend: dependencias y compilación de prueba"
  (cd "$FRONTEND" && npm install --no-audit --no-fund > /dev/null 2>&1) || { alto "Falló npm install en el frontend."; return 1; }
  local salida; salida=$(cd "$FRONTEND" && npm run build 2>&1) || { printf '%s\n' "$salida" | tail -15; alto "El frontend no compila."; return 1; }
  printf '%s\n' "$salida" | grep -E "built in" | sed 's/^/  ✓ /'

  paso "Listo"
  ok "Backend:  $(git -C "$BACKEND" log -1 --format='%h %s')"
  ok "Frontend: $(git -C "$FRONTEND" log -1 --format='%h %s')"
  echo "  Reinicia el backend (Ctrl+C y 'python manage.py runserver') y el frontend ('npm run dev'), y recarga con Ctrl+Shift+R."
  return 0
}

main "$@"; exit $?
