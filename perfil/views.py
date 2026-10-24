from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.authtoken.models import Token
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.core.cache import cache
import re
from .models import Perfil
from .serializers import PerfilSerializer
from api.seguridad import mensaje_password_invalida

MAX_INTENTOS = 5
BLOQUEO_SEGUNDOS = 15 * 60


class MiPerfilView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        perfil, _ = Perfil.objects.get_or_create(user=request.user)
        data = PerfilSerializer(perfil).data
        data["username"] = request.user.username
        data["email"] = request.user.email
        data["is_staff"] = request.user.is_staff
        return Response(data)

    def patch(self, request):
        perfil, _ = Perfil.objects.get_or_create(user=request.user)
        data = dict(request.data)
        nueva_password = data.pop("nueva_password", None)
        if nueva_password:
            problema = mensaje_password_invalida(nueva_password)
            if problema:
                return Response({"error": problema}, status=400)

        serializer = PerfilSerializer(perfil, data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        if nueva_password:
            request.user.set_password(nueva_password)
            request.user.save()

        resultado = serializer.data
        resultado["username"] = request.user.username
        resultado["email"] = request.user.email
        resultado["is_staff"] = request.user.is_staff
        return Response(resultado)


class RegistroView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        nombre_completo = (request.data.get("nombre_completo") or "").strip()
        correo = (request.data.get("correo") or "").strip().lower()
        password = request.data.get("password") or ""

        if not nombre_completo or " " not in nombre_completo:
            return Response({"error": "Escribe tu nombre y apellido."}, status=400)

        if not re.match(r"^[^\s@]+@alam\.mx$", correo):
            return Response({"error": "Debes usar un correo @alam.mx."}, status=400)

        if User.objects.filter(username=correo).exists():
            return Response({"error": "Ya existe una cuenta con ese correo."}, status=400)

        if len(password) < 8 or not re.search(r"[A-Z]", password) or not re.search(r"[0-9]", password):
            return Response({"error": "La contraseña debe tener 8+ caracteres, una mayúscula y un número."}, status=400)

        user = User.objects.create_user(username=correo, email=correo, password=password, is_active=False)
        Perfil.objects.create(user=user, nombre_completo=nombre_completo)

        return Response({"mensaje": "Cuenta creada. Un administrador debe aprobarla antes de que puedas entrar."}, status=201)


class LoginConLimiteView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username = (request.data.get("username") or "").strip().lower()
        password = request.data.get("password") or ""

        clave_intentos = f"login_intentos_{username}"
        clave_bloqueo = f"login_bloqueo_{username}"

        if cache.get(clave_bloqueo):
            return Response(
                {"error": "Demasiados intentos fallidos. Espera 15 minutos antes de volver a intentar."},
                status=429,
            )

        # Cuenta pendiente de aprobación (o desactivada): se avisa solo si la contraseña es correcta, para no revelar qué cuentas existen.
        candidato = User.objects.filter(username=username).first()
        if candidato is not None and not candidato.is_active and candidato.check_password(password):
            return Response(
                {"error": "Tu cuenta aún no está activa. Un administrador debe aprobarla antes de que puedas entrar."},
                status=403,
            )

        user = authenticate(username=username, password=password)

        if user is None:
            intentos = cache.get(clave_intentos, 0) + 1

            if intentos >= MAX_INTENTOS:
                cache.set(clave_bloqueo, True, BLOQUEO_SEGUNDOS)
                cache.delete(clave_intentos)
                return Response(
                    {"error": "Demasiados intentos fallidos. Tu cuenta quedó bloqueada temporalmente por 15 minutos."},
                    status=429,
                )

            cache.set(clave_intentos, intentos, BLOQUEO_SEGUNDOS)
            restantes = MAX_INTENTOS - intentos
            return Response(
                {"error": f"Usuario o contraseña incorrectos. Te quedan {restantes} intento(s)."},
                status=400,
            )

        cache.delete(clave_intentos)
        token, _ = Token.objects.get_or_create(user=user)
        return Response({"token": token.key})
