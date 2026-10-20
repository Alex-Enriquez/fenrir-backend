#!/usr/bin/env python3
"""
Instalador de Fenrir · Sistema de Inventario de TI (Alamex)
Corre en Windows, Linux (Ubuntu/Debian o Fedora) y Mac.
Las librerías que necesita (rich, questionary) las instala solo en un entorno propio.
"""

import os
import platform
import re
import secrets
import shutil
import socket
import subprocess
import sys
import time
from pathlib import Path


def _asegurar_dependencias():
    """Si faltan rich/questionary, crea un venv propio, las instala ahí y relanza el script."""
    try:
        import rich  # noqa: F401
        import questionary  # noqa: F401
        return
    except ImportError:
        pass

    if os.environ.get("FENRIR_BOOTSTRAP") == "1":
        print("No se pudieron cargar 'rich' y 'questionary' ni después de instalarlas.")
        sys.exit(1)

    venv_dir = Path.home() / ".fenrir-instalador-venv"
    py = venv_dir / ("Scripts/python.exe" if os.name == "nt" else "bin/python")

    print("Preparando el instalador por primera vez (instalando rich y questionary)...")
    if not py.exists():
        r = subprocess.run([sys.executable, "-m", "venv", str(venv_dir)])
        if r.returncode != 0:
            print("No pude crear un entorno virtual de Python.")
            print("En Ubuntu/Debian instala: sudo apt install python3-venv")
            sys.exit(1)

    r = subprocess.run([str(py), "-m", "pip", "install", "--quiet", "rich", "questionary"])
    if r.returncode != 0:
        print("No se pudieron instalar las librerías. Revisa tu conexión a internet.")
        sys.exit(1)

    env = dict(os.environ, FENRIR_BOOTSTRAP="1")
    r = subprocess.run([str(py)] + sys.argv, env=env)
    sys.exit(r.returncode)


_asegurar_dependencias()

from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.rule import Rule
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, TimeElapsedColumn
import questionary

console = Console()

REPO_BACKEND_URL = "https://github.com/Alex-Enriquez/fenrir-backend.git"
REPO_FRONTEND_URL = "https://github.com/Alex-Enriquez/fenrir-frontend.git"

# Pasos que muestra la barra: código, venv, dependencias, .env, base de datos, migraciones, frontend
TOTAL_PASOS = 7
SISTEMA = platform.system()  # "Windows", "Linux", "Darwin"
NOMBRE_CONTENEDOR_DB = "inventario_ti_db"


def gestor_linux():
    """Detecta si esta máquina Linux usa apt (Ubuntu/Debian) o dnf (Fedora/RHEL)."""
    if shutil.which("apt-get"):
        return "apt"
    if shutil.which("dnf"):
        return "dnf"
    return None


COMANDOS_INSTALACION = {
    "Windows": {
        "Git": ["winget", "install", "--id", "Git.Git", "-e",
                "--accept-source-agreements", "--accept-package-agreements"],
        "Python 3": ["winget", "install", "--id", "Python.Python.3.12", "-e",
                     "--accept-source-agreements", "--accept-package-agreements"],
        "Node.js": ["winget", "install", "--id", "OpenJS.NodeJS.LTS", "-e",
                    "--accept-source-agreements", "--accept-package-agreements"],
        "Docker": ["winget", "install", "--id", "Docker.DockerDesktop", "-e",
                   "--accept-source-agreements", "--accept-package-agreements"],
    },
    "apt": {
        "Git": ["sudo", "apt-get", "install", "-y", "git"],
        "Python 3": ["sudo", "apt-get", "install", "-y", "python3", "python3-venv", "python3-pip"],
        "Node.js": ["sudo", "apt-get", "install", "-y", "nodejs", "npm"],
        "Docker": ["sudo", "apt-get", "install", "-y", "docker.io", "docker-compose-plugin"],
    },
    "dnf": {
        "Git": ["sudo", "dnf", "install", "-y", "git"],
        "Python 3": ["sudo", "dnf", "install", "-y", "python3", "python3-pip"],
        "Node.js": ["sudo", "dnf", "install", "-y", "nodejs", "npm"],
        "Docker": ["sudo", "dnf", "install", "-y", "docker-ce", "docker-ce-cli",
                   "containerd.io", "docker-buildx-plugin", "docker-compose-plugin"],
    },
    "Darwin": {
        "Git": ["brew", "install", "git"],
        "Python 3": ["brew", "install", "python"],
        "Node.js": ["brew", "install", "node"],
        "Docker": ["brew", "install", "--cask", "docker"],
    },
}


# ---------------------------------------------------------------- utilidades

def banner():
    texto = Text()
    texto.append("F E N R I R", style="bold white")
    texto.append("  ·  ", style="dim")
    texto.append("Sistema de Inventario de TI", style="yellow")
    console.print()
    console.print(Panel(texto, subtitle="Alamex · Instalador", border_style="yellow", padding=(1, 4)))
    console.print()


def ok(texto):
    console.print(f"    [bold green]✔[/bold green] {texto}")


def error(texto):
    console.print(f"    [bold red]✘[/bold red] {texto}")


def aviso(texto):
    console.print(f"    [bold yellow]![/bold yellow] {texto}")


def mostrar_salida_cruda(salida, limite=1500):
    """Imprime texto tal cual lo devolvió un comando (sin interpretar corchetes como estilos)."""
    salida = (salida or "").strip()
    if salida:
        console.print(salida[-limite:], markup=False, highlight=False)


class ErrorComando(RuntimeError):
    def __init__(self, comando, salida=""):
        super().__init__(f"Falló el comando: {comando}")
        self.salida = salida or ""


def resolver_ejecutable(comando):
    if isinstance(comando, list) and comando:
        ruta = shutil.which(comando[0])
        if ruta:
            return [ruta] + comando[1:]
    return comando


def correr(comando, cwd=None, mostrar_salida=False, imprimir_error=True):
    comando = resolver_ejecutable(comando)
    resultado = subprocess.run(
        comando, cwd=cwd,
        stdout=None if mostrar_salida else subprocess.PIPE,
        stderr=None if mostrar_salida else subprocess.STDOUT,
        text=True, encoding="utf-8", errors="replace",
    )
    if resultado.returncode != 0:
        if imprimir_error and not mostrar_salida:
            mostrar_salida_cruda(resultado.stdout)
        raise ErrorComando(comando, resultado.stdout)


def existe_comando(nombre):
    return shutil.which(nombre) is not None


def cancelar():
    console.print("\nInstalación cancelada.")
    sys.exit(0)


# ----------------------------------------------------- puerto y .env de Postgres

def puerto_libre(puerto):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(("0.0.0.0", puerto))
            return True
        except OSError:
            return False


def buscar_puerto_libre(inicio, intentos=30):
    for p in range(inicio, inicio + intentos):
        if puerto_libre(p):
            return p
    return None


def leer_var_env(ruta_env, clave, defecto=None):
    if not ruta_env.exists():
        return defecto
    for linea in ruta_env.read_text(encoding="utf-8").splitlines():
        if linea.startswith(clave + "="):
            return linea.split("=", 1)[1].strip()
    return defecto


def escribir_var_env(ruta_env, clave, valor):
    lineas = ruta_env.read_text(encoding="utf-8").splitlines() if ruta_env.exists() else []
    nueva = f"{clave}={valor}"
    for i, linea in enumerate(lineas):
        if linea.startswith(clave + "="):
            lineas[i] = nueva
            break
    else:
        lineas.append(nueva)
    ruta_env.write_text("\n".join(lineas) + "\n", encoding="utf-8")


def contenedor_db_corriendo():
    try:
        r = subprocess.run(
            resolver_ejecutable(["docker", "ps", "--filter", f"name=^{NOMBRE_CONTENEDOR_DB}$",
                                 "--format", "{{.Names}}"]),
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, encoding="utf-8", errors="replace",
        )
        return NOMBRE_CONTENEDOR_DB in r.stdout
    except OSError:
        return False


def carpeta_respaldos(ruta_backend):
    """Carpeta donde el contenedor de respaldo guarda las copias de la base de datos (BACKUP_DIR del .env, o la de siempre)."""
    destino = leer_var_env(ruta_backend / ".env", "BACKUP_DIR", "")
    return (ruta_backend / destino).resolve() if destino else (ruta_backend.parent / "respaldos-fenrir").resolve()


def preparar_carpeta_respaldos(ruta_backend):
    """La crea ahora para que sea tuya; si la creara Docker, quedaría con dueño root."""
    carpeta = carpeta_respaldos(ruta_backend)
    try:
        carpeta.mkdir(parents=True, exist_ok=True)
        ok(f"Carpeta de respaldos de la base de datos: {carpeta}")
    except OSError as e:
        aviso(f"No pude crear la carpeta de respaldos ({carpeta}): {e}")


def preparar_puerto_db(ruta_backend):
    """Hace que el puerto de Postgres en esta máquina sea configurable y que no choque con otro."""
    compose = ruta_backend / "docker-compose.yml"
    if compose.exists():
        texto = compose.read_text(encoding="utf-8")
        if '"5432:5432"' in texto:
            compose.write_text(texto.replace('"5432:5432"', '"${DB_PORT:-5432}:5432"'), encoding="utf-8")
            ok("docker-compose.yml ahora toma el puerto de DB_PORT")

    settings = ruta_backend / "config" / "settings.py"
    if settings.exists() and "DB_PORT" not in settings.read_text(encoding="utf-8"):
        aviso("config/settings.py no parece leer DB_PORT: si el puerto cambia, Django no lo usará.")

    ruta_env = ruta_backend / ".env"
    puerto = int(leer_var_env(ruta_env, "DB_PORT", "5432"))

    if contenedor_db_corriendo():
        ok(f"La base de datos de Fenrir ya está corriendo (puerto {puerto})")
        return

    if puerto_libre(puerto):
        return

    nuevo = buscar_puerto_libre(puerto + 1)
    if nuevo is None:
        error(f"El puerto {puerto} está ocupado y no encontré otro libre cerca.")
        sys.exit(1)
    escribir_var_env(ruta_env, "DB_PORT", nuevo)
    aviso(f"El puerto {puerto} lo usa otro programa (¿otro Postgres?). Fenrir usará el {nuevo}.")


def esperar_postgres(maximo=40):
    for _ in range(maximo):
        r = subprocess.run(
            resolver_ejecutable(["docker", "exec", NOMBRE_CONTENEDOR_DB, "pg_isready"]),
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
        if r.returncode == 0:
            return True
        time.sleep(1)
    return False


def explicar_error_docker(salida, ruta_backend):
    s = (salida or "").lower()
    if "address already in use" in s or "port is already allocated" in s:
        puerto = leer_var_env(ruta_backend / ".env", "DB_PORT", "5432")
        error(f"El puerto {puerto} sigue ocupado por otro programa.")
        aviso("Cambia DB_PORT en el archivo .env por otro número libre (ej. 5440) y vuelve a correr el instalador.")
    elif "permission denied" in s:
        error("Tu usuario no tiene permiso para usar Docker.")
        aviso("Corre: sudo usermod -aG docker $USER   y luego cierra sesión, vuelve a entrar y repite el instalador.")
    elif ("cannot connect to the docker daemon" in s or "failed to connect to the docker api" in s
          or "docker_engine" in s or "is the docker daemon running" in s):
        error("Docker está instalado pero no está corriendo.")
        aviso("Windows/Mac: abre Docker Desktop y espera a que termine de iniciar. Linux: sudo systemctl start docker")
    else:
        error("No se pudo levantar Docker. Esto fue lo que respondió:")
    mostrar_salida_cruda(salida)
    if SISTEMA == "Linux" and gestor_linux() == "dnf":
        aviso("En Fedora, si ves errores de permisos en los volúmenes, usa el sufijo ':Z' en los volúmenes del docker-compose.yml (SELinux).")


# ------------------------------------------------------------------- requisitos

def _clave_comandos():
    if SISTEMA == "Linux":
        return gestor_linux()
    return SISTEMA


def _nombre_comando(nombre):
    return {
        "Git": "git",
        "Python 3": "python" if SISTEMA == "Windows" else "python3",
        "Node.js": "node",
        "Docker": "docker",
    }[nombre]


def instalar_requisito_faltante(nombre, apt_actualizado):
    clave = _clave_comandos()
    comando = COMANDOS_INSTALACION.get(clave, {}).get(nombre)

    if not comando:
        error(f"No sé cómo instalar {nombre} automáticamente aquí ({clave}). Instálalo manualmente.")
        return False

    if clave == "dnf" and nombre == "Docker":
        console.print("    [dim]Agregando el repositorio oficial de Docker...[/dim]")
        try:
            correr(["sudo", "dnf", "-y", "install", "dnf-plugins-core"], mostrar_salida=True)
            correr(["sudo", "dnf", "config-manager", "addrepo",
                    "--from-repofile=https://download.docker.com/linux/fedora/docker-ce.repo"], mostrar_salida=True)
        except ErrorComando:
            error("No se pudo agregar el repositorio de Docker. Instálalo manualmente.")
            return False

    if clave == "apt" and not apt_actualizado[0]:
        console.print("    [dim]Actualizando lista de paquetes (puede pedir tu contraseña)...[/dim]")
        try:
            correr(["sudo", "apt-get", "update"], mostrar_salida=True)
            apt_actualizado[0] = True
        except ErrorComando:
            aviso("No se pudo actualizar apt, se intentará instalar de todos modos.")

    console.print(f"    [dim]Instalando {nombre} — puede pedirte contraseña o confirmación...[/dim]")
    try:
        correr(comando, mostrar_salida=True)
    except ErrorComando:
        error(f"La instalación de {nombre} falló o fue cancelada.")
        return False

    ok(f"{nombre} instalado")
    return True


def verificar_requisitos():
    requisitos = ["Git", "Python 3", "Node.js", "Docker"]
    apt_actualizado = [False]

    if SISTEMA == "Linux" and not gestor_linux():
        console.print(Panel(
            "No encontré 'apt' ni 'dnf' en este Linux — este instalador no sabe instalar "
            "requisitos automáticamente en tu distro. Instala Git, Python, Node y Docker "
            "manualmente y vuelve a correr el instalador.",
            title="Distro no reconocida", border_style="red",
        ))
        sys.exit(1)

    faltantes = []
    for nombre in requisitos:
        if existe_comando(_nombre_comando(nombre)):
            ok(f"{nombre} encontrado")
        else:
            aviso(f"{nombre} NO encontrado")
            faltantes.append(nombre)

    if not faltantes:
        return

    console.print()
    console.print(Panel(f"Falta instalar: {', '.join(faltantes)}",
                        title="Requisitos faltantes", border_style="yellow"))
    if not questionary.confirm("¿Quieres que el instalador intente instalarlos automáticamente ahora?",
                               default=True).ask():
        console.print(Panel("Instálalos manualmente y vuelve a correr este instalador.",
                            title="Instalación cancelada", border_style="red"))
        sys.exit(1)

    console.print()
    fallaron = [n for n in faltantes if not instalar_requisito_faltante(n, apt_actualizado)]
    if fallaron:
        console.print()
        console.print(Panel(
            f"No se pudieron instalar automáticamente: {', '.join(fallaron)}.\n"
            "Instálalos manualmente y vuelve a correr este instalador.",
            title="Instalación incompleta", border_style="red"))
        sys.exit(1)

    # Tras instalar, esta misma terminal a veces aún no "ve" los programas nuevos (PATH sin refrescar)
    sin_detectar = [n for n in faltantes if not existe_comando(_nombre_comando(n))]
    if sin_detectar:
        extra = ""
        if SISTEMA == "Windows" and "Docker" in faltantes:
            extra = "\nAdemás, abre Docker Desktop una vez y espera a que termine de iniciar."
        console.print()
        console.print(Panel(
            f"Ya se instalaron, pero esta ventana todavía no los detecta: {', '.join(sin_detectar)}.\n"
            "Cierra esta terminal, abre una nueva y vuelve a correr el instalador." + extra,
            title="Falta un último paso", border_style="yellow"))
        sys.exit(0)
    console.print()


# ----------------------------------------------------------- pasos de instalación

def clonar_o_usar_existente(url, carpeta_destino, nombre):
    if carpeta_destino.exists():
        ok(f"{nombre} ya existe en {carpeta_destino}")
        return
    ok(f"Clonando {nombre} desde GitHub...")
    correr(["git", "clone", url, str(carpeta_destino)])
    ok(f"{nombre} clonado correctamente")


def generar_clave_secreta():
    return secrets.token_urlsafe(50)


def _valida_password(texto):
    """Contraseña de Postgres: larga y sin caracteres que rompen el .env o el docker-compose ($, #, comillas, espacios)."""
    if len(texto) < 12:
        return "Usa al menos 12 caracteres."
    if not re.fullmatch(r"[A-Za-z0-9._@%+:=-]+", texto):
        return "Solo letras, números y . _ - @ % + : =   (sin espacios, $, # ni comillas)."
    return True


def generar_fernet_key():
    import base64
    return base64.urlsafe_b64encode(os.urandom(32)).decode()


def preparar_env(ruta_backend, db_password):
    ruta_env = ruta_backend / ".env"
    if ruta_env.exists():
        ok(".env ya existe, no se sobreescribe")
        return

    contenido = f"""DEBUG=True
SECRET_KEY={generar_clave_secreta()}
DB_NAME=inventario_ti
DB_USER=inventario_user
DB_PASSWORD={db_password}
DB_HOST=localhost
DB_PORT=5432
FERNET_KEY={generar_fernet_key()}
"""
    ruta_env.write_text(contenido, encoding="utf-8")
    ok(".env generado con claves reales y aleatorias")


def instalar_backend(ruta_backend, progress, tarea, db_password):
    progress.update(tarea, description="Preparando entorno virtual de Python...")
    ruta_venv = ruta_backend / "venv"
    python_venv = ruta_venv / ("Scripts/python.exe" if SISTEMA == "Windows" else "bin/python")

    if not ruta_venv.exists():
        correr([sys.executable, "-m", "venv", str(ruta_venv)])
        ok("Entorno virtual creado")
    else:
        ok("Entorno virtual ya existía")
    progress.advance(tarea)

    progress.update(tarea, description="Instalando dependencias de Python...")
    correr([str(python_venv), "-m", "pip", "install", "--upgrade", "pip"], cwd=ruta_backend)
    requirements = ruta_backend / "requirements.txt"
    if requirements.exists():
        correr([str(python_venv), "-m", "pip", "install", "-r", "requirements.txt"], cwd=ruta_backend)
    ok("Dependencias de Python instaladas")
    progress.advance(tarea)

    progress.update(tarea, description="Generando configuración (.env)...")
    preparar_env(ruta_backend, db_password)
    progress.advance(tarea)

    progress.update(tarea, description="Levantando base de datos (Docker)...")
    preparar_puerto_db(ruta_backend)
    preparar_carpeta_respaldos(ruta_backend)
    try:
        correr(["docker", "compose", "up", "-d"], cwd=ruta_backend, imprimir_error=False)
    except ErrorComando as e:
        explicar_error_docker(e.salida, ruta_backend)
        sys.exit(1)
    if not esperar_postgres():
        aviso("Postgres tardó en responder; se intentará migrar de todos modos.")
    ok("Postgres corriendo")
    progress.advance(tarea)

    progress.update(tarea, description="Aplicando migraciones de base de datos...")
    try:
        correr([str(python_venv), "manage.py", "migrate"], cwd=ruta_backend, imprimir_error=False)
    except ErrorComando as e:
        error("No se pudieron aplicar las migraciones. Esto fue lo que respondió:")
        mostrar_salida_cruda(e.salida)
        puerto = leer_var_env(ruta_backend / ".env", "DB_PORT", "5432")
        aviso(f"Revisa que Django use el mismo puerto que Docker (DB_PORT={puerto} en el .env).")
        sys.exit(1)
    ok("Migraciones aplicadas")
    progress.advance(tarea)

    return python_venv


def instalar_frontend(ruta_frontend, progress, tarea):
    progress.update(tarea, description="Instalando dependencias de React (npm install)...")
    correr(["npm", "install"], cwd=ruta_frontend)
    ok("Dependencias de React instaladas")
    progress.advance(tarea)


def cargar_catalogos_iniciales(python_venv, ruta_backend):
    """Llena las listas de los formularios (departamentos, categorías, tipos). Se puede repetir sin duplicar nada."""
    try:
        correr([str(python_venv), "manage.py", "cargar_datos_base"], cwd=ruta_backend, mostrar_salida=True)
    except ErrorComando:
        aviso("No pude cargar los catálogos iniciales (¿tu copia del backend es anterior?). "
              "Puedes crearlos desde la pantalla Catálogos dentro de la app.")


def main():
    banner()
    console.print("Este instalador va a preparar Fenrir en esta computadora.\n")
    if not questionary.confirm("¿Deseas continuar?", default=True).ask():
        cancelar()

    carpeta = questionary.text("¿En qué carpeta quieres instalar Fenrir?",
                               default=str(Path.home() / "proyectos")).ask()
    if not carpeta:
        cancelar()
    ruta_base = Path(carpeta).expanduser()
    ruta_base.mkdir(parents=True, exist_ok=True)

    ruta_backend = ruta_base / "inventario-ti"
    ruta_frontend = ruta_base / "inventario-ti-frontend"

    # Fase 1 y preguntas: SIN barra de progreso, para que todo se vea y se pueda contestar.
    console.print()
    console.print(Rule("Requisitos", style="yellow"))
    console.print()
    verificar_requisitos()

    db_password = None
    if not (ruta_backend / ".env").exists():
        console.print("[dim]Se sugiere una contraseña aleatoria; con Enter la aceptas. Queda guardada en el .env del backend.[/dim]")
        db_password = questionary.text("Contraseña para la base de datos Postgres:",
                                       default=secrets.token_urlsafe(16),
                                       validate=_valida_password).ask()
        if db_password is None:
            cancelar()
        console.print()

    # Fase 2: pasos automáticos, sin preguntas, con barra de progreso.
    console.print(Rule("Instalando", style="yellow"))
    console.print()

    with Progress(
        SpinnerColumn(style="yellow"),
        TextColumn("[bold]{task.description}"),
        BarColumn(bar_width=36, complete_style="green", finished_style="green"),
        TaskProgressColumn(),
        TimeElapsedColumn(),
        console=console,
    ) as progress:
        tarea = progress.add_task("Obteniendo el código fuente...", total=TOTAL_PASOS)

        clonar_o_usar_existente(REPO_BACKEND_URL, ruta_backend, "Backend (Django)")
        clonar_o_usar_existente(REPO_FRONTEND_URL, ruta_frontend, "Frontend (React)")
        progress.advance(tarea)

        python_venv = instalar_backend(ruta_backend, progress, tarea, db_password)
        instalar_frontend(ruta_frontend, progress, tarea)

        progress.update(tarea, description="¡Listo!", completed=TOTAL_PASOS)

    console.print()
    if questionary.confirm("¿Cargar los catálogos iniciales (departamentos, categorías de equipo, tipos de licencia y "
                           "de contraseñas)? Después los puedes cambiar en Catálogos.", default=True).ask():
        cargar_catalogos_iniciales(python_venv, ruta_backend)
        console.print()
    if questionary.confirm("¿Quieres crear el superusuario administrador ahora?", default=True).ask():
        console.print()
        subprocess.run([str(python_venv), "manage.py", "createsuperuser"], cwd=ruta_backend)

    activar = "venv\\Scripts\\activate" if SISTEMA == "Windows" else "source venv/bin/activate"
    console.print()
    console.print(Panel(
        f"[bold]Backend:[/bold]  cd {ruta_backend} && "
        f"{activar} "
        f"&& python manage.py runserver\n\n"
        f"[bold]Frontend:[/bold] cd {ruta_frontend} && npm run dev\n\n"
        f"Luego abre: [link]http://localhost:5173[/link]\n\n"
        f"[dim]La contraseña de la base de datos está en {ruta_backend / '.env'}[/dim]\n"
        f"[dim]Respaldos automáticos de la base de datos: {carpeta_respaldos(ruta_backend)}[/dim]",
        title="🐺 Fenrir está listo", border_style="green", padding=(1, 2),
    ))


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n\nInstalación cancelada por el usuario.")
        sys.exit(1)
    except ErrorComando as e:
        console.print()
        error(f"Un paso falló: {e}")
        sys.exit(1)
