from django.contrib.auth import get_user_model
from django.forms import ModelForm

from activos.models import Activo

User = get_user_model()


class ActivoForm(ModelForm):
    class Meta:
        model = Activo
        fields = [
            'proyecto', 'categoria', 'nombre', 'username', 'password',
            'ip', 'ip_dominio', 'ubicacion', 'sn', 'tecnico',
            'fecha_instalacion', 'fecha_compra', 'factura_boleta', 'archivo_compra', 'notas',
        ]

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user:
            from proyectos.models import proyectos_visibles_para
            self.fields['proyecto'].queryset = proyectos_visibles_para(user)
        self.fields['tecnico'].queryset = User.objects.filter(is_active=True).order_by('username')
        self.fields['tecnico'].required = False
        for name, field in self.fields.items():
            if name == 'notas':
                field.widget.attrs.setdefault('class', 'form-control')
                field.widget.attrs.setdefault('rows', 3)
            elif getattr(field.widget, 'input_type', None) != 'checkbox':
                field.widget.attrs.setdefault('class', 'form-control')
