from django.forms import ModelForm

from mantenimiento.models import VisitaMantenimiento


class VisitaMantenimientoForm(ModelForm):
    class Meta:
        model = VisitaMantenimiento
        fields = ['tipo', 'tipo_servicio', 'fecha', 'observaciones', 'estado']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if name == 'observaciones':
                field.widget.attrs.setdefault('rows', 3)
            field.widget.attrs.setdefault('class', 'form-control')
