# Respaldo de la base de datos de Fenrir

## Qué hace solo
Un contenedor (`inventario_ti_backup`) arranca junto con la base de datos. **Cada hora revisa si hay un respaldo de las
últimas 24 horas; si no, hace uno nuevo.** Funciona aunque la computadora esté apagada o suspendida a cualquier hora.

- Guarda los **14 diarios** más recientes y **8 semanales** (cada domingo se guarda una copia aparte).
- Solo da por bueno un respaldo si el archivo está íntegro; uno roto o a medias se descarta.
- Las copias quedan en la carpeta `respaldos-fenrir`, **junto a la carpeta del backend** (fuera del repositorio).
  Para usar otra carpeta, agrega a `.env`:  `BACKUP_DIR=/ruta/de/la/carpeta`  (por ejemplo, una carpeta del NAS) y
  vuelve a levantar con `docker compose up -d`.

> ⚠️ Los respaldos llevan **datos reales** (personas, equipos, contraseñas cifradas). Nunca los subas a GitHub.

## Comandos (desde la carpeta del backend)

| Para… | Comando |
|---|---|
| Hacer un respaldo ahora mismo | `docker exec inventario_ti_backup /respaldar.sh ahora` |
| Ver qué ha hecho el respaldo automático | `docker logs --tail 20 inventario_ti_backup` |
| Comprobar que el último respaldo sirve (no toca tus datos) | `./respaldo/verificar.sh` |
| Restaurar el último respaldo (**reemplaza los datos actuales**) | `./respaldo/restaurar.sh` |
| Restaurar uno en particular | `./respaldo/restaurar.sh fenrir_20261012_080000.sql.gz` |

`restaurar.sh` revisa que el archivo esté completo antes de tocar nada y restaura dentro de una sola transacción: si algo
falla a la mitad, la base queda exactamente como estaba. Antes de restaurar, detén el backend (Ctrl+C).

En Windows, los `.sh` se corren desde Git Bash o WSL.

## Lo más importante: una copia en la misma computadora no la salva de formatearla
Estos respaldos protegen contra borrados y errores. Para proteger contra un formateo o un disco dañado, **copia la carpeta
`respaldos-fenrir` a otro lugar** (el NAS, un USB, la nube de la empresa) de forma periódica, o apunta `BACKUP_DIR` a una
carpeta que ya esté en otro equipo.

## Recuperar en una computadora nueva
1. Instala Fenrir con el instalador (levanta la base vacía).
2. Copia tus respaldos a la carpeta `respaldos-fenrir`.
3. `./respaldo/restaurar.sh`
