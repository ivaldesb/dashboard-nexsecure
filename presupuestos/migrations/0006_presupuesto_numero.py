from django.db import migrations, models


def backfill_numero(apps, schema_editor):
    Presupuesto = apps.get_model('presupuestos', 'Presupuesto')
    Proyecto = apps.get_model('proyectos', 'Proyecto')

    used = set()
    max_num = 0

    def take_numeric(val):
        nonlocal max_num
        if val and str(val).isdigit():
            max_num = max(max_num, int(val))

    for c in Proyecto.objects.exclude(codigo='').values_list('codigo', flat=True):
        take_numeric(c)

    # 1) iniciales = código del proyecto
    for p in Presupuesto.objects.filter(tipo='inicial').select_related('proyecto').order_by('pk'):
        codigo = (getattr(p.proyecto, 'codigo', None) or '').strip()
        if codigo and codigo not in used:
            p.numero = codigo
        else:
            max_num += 1
            p.numero = str(max_num)
        used.add(p.numero)
        take_numeric(p.numero)
        p.save(update_fields=['numero'])

    # 2) adicionales / resto = secuencia tras el máximo
    for p in Presupuesto.objects.exclude(tipo='inicial').order_by('pk'):
        max_num += 1
        while str(max_num) in used:
            max_num += 1
        p.numero = str(max_num)
        used.add(p.numero)
        p.save(update_fields=['numero'])


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('presupuestos', '0005_gestion_financiera'),
        ('proyectos', '0006_proyecto_generalidades'),
    ]

    operations = [
        migrations.AddField(
            model_name='presupuesto',
            name='numero',
            field=models.CharField(blank=True, max_length=32, verbose_name='Nº presupuesto'),
        ),
        migrations.RunPython(backfill_numero, noop),
        migrations.AlterField(
            model_name='presupuesto',
            name='numero',
            field=models.CharField(
                blank=True,
                max_length=32,
                unique=True,
                verbose_name='Nº presupuesto',
            ),
        ),
    ]
