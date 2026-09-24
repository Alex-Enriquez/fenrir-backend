from rest_framework.routers import DefaultRouter
from .views import (
    CategoriaEquipoViewSet, EquipoViewSet, MantenimientoViewSet,
    DepartamentoViewSet, EmpleadoViewSet,
    TipoLicenciaViewSet, LicenciaViewSet,
    AsignacionViewSet,
    CategoriaContrasenaViewSet, RegistroContrasenaViewSet, UsuarioSistemaViewSet, ProveedorViewSet,
    ServicioContratadoViewSet,
    RackViewSet, DispositivoRedViewSet, PuertoRedViewSet,
)
from responsivas.views import ResponsivaViewSet

router = DefaultRouter()
router.register(r"categorias-equipo", CategoriaEquipoViewSet)
router.register(r"equipos", EquipoViewSet)
router.register(r"mantenimientos", MantenimientoViewSet)
router.register(r"departamentos", DepartamentoViewSet)
router.register(r"empleados", EmpleadoViewSet)
router.register(r"tipos-licencia", TipoLicenciaViewSet)
router.register(r"licencias", LicenciaViewSet)
router.register(r"asignaciones", AsignacionViewSet)
router.register(r"categorias-contrasena", CategoriaContrasenaViewSet)
router.register(r"registros-contrasena", RegistroContrasenaViewSet)
router.register(r"usuarios-sistema", UsuarioSistemaViewSet, basename="usuario-sistema")
router.register(r"responsivas", ResponsivaViewSet)
router.register(r"proveedores", ProveedorViewSet)
router.register(r"servicios-contratados", ServicioContratadoViewSet)
router.register(r"racks", RackViewSet)
router.register(r"dispositivos-red", DispositivoRedViewSet)
router.register(r"puertos-red", PuertoRedViewSet)

urlpatterns = router.urls
