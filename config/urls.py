from django.contrib import admin
from django.urls import path, include
from rest_framework.authtoken.views import obtain_auth_token
from perfil.views import MiPerfilView, RegistroView, LoginConLimiteView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    path('api/auth/login/', LoginConLimiteView.as_view()),
    path('api/perfil/', MiPerfilView.as_view()),
    path('api/auth/registro/', RegistroView.as_view()),
]
