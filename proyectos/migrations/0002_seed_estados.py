from django.db import migrations


ESTADOS = [
    (0, 'Borrador', 'borrador', '#999999', False),
    (1, 'Creado', 'creado', '#0066FF', False),
    (2, 'Generando ppto', 'generando-ppto', '#5BC0DE', False),
    (3, 'Esperando confirmación equipo', 'esperando-confirmacion-equipo', '#F0AD4E', False),
    (4, 'Esperando aceptación cliente', 'esperando-aceptacion-cliente', '#FF9800', True),
    (5, 'Instalación en progreso', 'instalacion-en-progreso', '#337AB7', True),
    (6, 'Finalizado', 'finalizado', '#5CB85C', True),
    (7, 'Con incidencia', 'con-incidencia', '#D9534F', True),
    (8, 'Esperando incidencia', 'esperando-incidencia', '#C9302C', True),
]


def seed(apps, schema_editor):
    Estado = apps.get_model('proyectos', 'EstadoProyecto')
    # visible_cliente may not exist yet on historical model
    fields = {f.name for f in Estado._meta.fields}
    for orden, nombre, slug, color, visible in ESTADOS:
        defaults = {'nombre': nombre, 'orden': orden, 'color': color, 'activo': True}
        if 'visible_cliente' in fields:
            defaults['visible_cliente'] = visible
        Estado.objects.update_or_create(slug=slug, defaults=defaults)


def unseed(apps, schema_editor):
    Estado = apps.get_model('proyectos', 'EstadoProyecto')
    Estado.objects.filter(slug__in=[e[2] for e in ESTADOS]).delete()


class Migration(migrations.Migration):
    dependencies = [
        ('proyectos', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(seed, unseed),
    ]
