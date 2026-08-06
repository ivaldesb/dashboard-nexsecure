import django.db.models.deletion
from django.db import migrations, models

CATEGORIAS = [
    'Cámara',
    'NVR / DVR',
    'Control de acceso',
    'Red / Switch',
    'Computador',
    'Monitor',
    'Impresora',
    'UPS',
    'Almacenamiento',
    'Otro',
]


def seed_categorias(apps, schema_editor):
    CategoriaActivo = apps.get_model('activos', 'CategoriaActivo')
    for nombre in CATEGORIAS:
        CategoriaActivo.objects.get_or_create(nombre=nombre)


def copy_ip_to_ip_dominio(apps, schema_editor):
    Activo = apps.get_model('activos', 'Activo')
    for a in Activo.objects.all():
        if getattr(a, 'ip', None) and not a.ip_dominio:
            a.ip_dominio = a.ip
            a.save(update_fields=['ip_dominio'])


class Migration(migrations.Migration):

    dependencies = [
        ('activos', '0002_categoriaactivo_activo_ip_dominio_activo_tecnico_and_more'),
        ('presupuestos', '0006_presupuesto_numero'),
    ]

    operations = [
        migrations.RunPython(copy_ip_to_ip_dominio, migrations.RunPython.noop),
        migrations.RunPython(seed_categorias, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name='activo',
            name='factura_boleta',
        ),
        migrations.RemoveField(
            model_name='activo',
            name='ip',
        ),
        migrations.AddField(
            model_name='activo',
            name='factura',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='activos',
                to='presupuestos.facturaboleta',
                verbose_name='factura / boleta',
            ),
        ),
        migrations.AlterField(
            model_name='activo',
            name='archivo_compra',
            field=models.FileField(
                blank=True,
                help_text='Foto de la caja del equipo o del número de serie.',
                null=True,
                upload_to='activos/',
                verbose_name='Foto caja o S/N',
            ),
        ),
    ]
