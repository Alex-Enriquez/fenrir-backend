from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Asignacion


@receiver(post_save, sender=Asignacion)
def actualizar_estado_equipo_al_guardar(sender, instance, **kwargs):
    equipo = instance.equipo
    if not equipo:
        return

    if instance.fecha_devolucion:
        # Se devolvió: el equipo queda disponible
        if equipo.estado != 'disponible':
            equipo.estado = 'disponible'
            equipo.save(update_fields=['estado'])
    else:
        # Asignación activa: el equipo queda marcado como asignado
        if equipo.estado != 'asignado':
            equipo.estado = 'asignado'
            equipo.save(update_fields=['estado'])


@receiver(post_delete, sender=Asignacion)
def liberar_equipo_al_eliminar(sender, instance, **kwargs):
    equipo = instance.equipo
    if equipo and not instance.fecha_devolucion:
        equipo.estado = 'disponible'
        equipo.save(update_fields=['estado'])
