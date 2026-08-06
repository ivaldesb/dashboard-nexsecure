from django.db import migrations, models

# slug → (orden, nombre, color, visible_cliente)
ESTADOS = {
    'borrador': (0, 'Borrador', '#999999', False),
    'creado': (1, 'Creado', '#0066FF', False),
    'generando-ppto': (2, 'Generando ppto', '#5BC0DE', False),
    'esperando-confirmacion-equipo': (3, 'Esperando confirmación equipo', '#F0AD4E', False),
    'esperando-aceptacion-cliente': (4, 'Esperando aceptación cliente', '#FF9800', True),
    'instalacion-en-progreso': (5, 'Instalación en progreso', '#337AB7', True),
    'finalizado': (6, 'Finalizado', '#5CB85C', True),
    'con-incidencia': (7, 'Con incidencia', '#D9534F', True),
    'esperando-incidencia': (8, 'Esperando incidencia', '#C9302C', True),
}

# aliases legacy → visible
LEGACY_VISIBLE = {
    'esperando-confirmacion-ppto-equipo': False,
    'esperando-aceptacion-ppto-cliente': True,
}


def forwards(apps, schema_editor):
    Estado = apps.get_model('proyectos', 'EstadoProyecto')
    for slug, (orden, nombre, color, visible) in ESTADOS.items():
        Estado.objects.update_or_create(
            slug=slug,
            defaults={
                'nombre': nombre,
                'orden': orden,
                'color': color,
                'activo': True,
                'visible_cliente': visible,
            },
        )
    for slug, visible in LEGACY_VISIBLE.items():
        Estado.objects.filter(slug=slug).update(visible_cliente=visible)

    Proyecto = apps.get_model('proyectos', 'Proyecto')
    for p in Proyecto.objects.filter(models.Q(codigo='') | models.Q(codigo__isnull=True)).order_by('pk'):
        p.codigo = str(p.pk)
        p.save(update_fields=['codigo'])


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ('proyectos', '0003_codigo_comentarios_timeline_visible'),
    ]

    operations = [
        migrations.RunPython(forwards, noop),
    ]
