from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Asignacion
from equipos.models import Equipo


@receiver(post_save, sender=Asignacion)
def actualizar_estado_equipo_al_guardar(sender, instance, **kwargs):
    if not instance.equipo_id:
        return

    # Se devolvió: el equipo queda disponible. Asignación activa: queda asignado.
    # Se escribe directo en la base de datos y NO a partir del objeto en memoria, que puede estar desactualizado
    # cuando una misma operación cierra una asignación y abre otra sobre el mismo equipo (una reasignación).
    nuevo_estado = 'disponible' if instance.fecha_devolucion else 'asignado'
    Equipo.objects.filter(pk=instance.equipo_id).exclude(estado=nuevo_estado).update(estado=nuevo_estado)


@receiver(post_delete, sender=Asignacion)
def liberar_equipo_al_eliminar(sender, instance, **kwargs):
    # No se lee instance.equipo: si lo que se está eliminando es el equipo mismo (con sus asignaciones), esa fila ya no
    # existe y leerla fallaba con DoesNotExist. Se escribe directo; si el equipo ya no existe, simplemente no hay nada que liberar.
    if instance.equipo_id and not instance.fecha_devolucion:
        Equipo.objects.filter(pk=instance.equipo_id).update(estado='disponible')
