from django.contrib.auth import get_user_model
from django.forms import ModelForm

from activos.models import Activo, CategoriaActivo
from presupuestos.models import FacturaBoleta

User = get_user_model()


def _label_factura(f):
    prov = f' · {f.proveedor}' if f.proveedor else ''
    proy = f.proyecto.nombre if f.proyecto_id else '—'
    fecha = f.fecha.strftime('%d/%m/%Y') if f.fecha else '—'
    return (
        f'{f.get_tipo_display()} {f.numero}{prov} — {proy} · {fecha} · ${f.total:,.0f}'
    )


class ActivoForm(ModelForm):
    class Meta:
        model = Activo
        fields = [
            'proyecto', 'categoria', 'nombre', 'username', 'password',
            'ip_dominio', 'ubicacion', 'sn', 'tecnico',
            'fecha_instalacion', 'fecha_compra', 'factura', 'archivo_compra', 'notas',
        ]

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user:
            from proyectos.models import proyectos_visibles_para
            self.fields['proyecto'].queryset = proyectos_visibles_para(user)
        self.fields['categoria'].queryset = CategoriaActivo.objects.order_by('nombre')
        self.fields['categoria'].empty_label = 'Selecciona categoría…'
        self.fields['categoria'].required = False

        self.fields['tecnico'].queryset = User.objects.filter(is_active=True).order_by('username')
        self.fields['tecnico'].required = False

        self.fields['factura'].queryset = FacturaBoleta.objects.select_related(
            'proyecto',
        ).order_by('-fecha', '-pk')
        self.fields['factura'].required = False
        self.fields['factura'].empty_label = 'Sin factura / boleta…'
        self.fields['factura'].label_from_instance = _label_factura
        self.fields['factura'].help_text = 'Busca por número, proveedor o proyecto.'
        self.fields['factura'].widget.attrs.update({
            'class': 'form-control nx-select-search',
            'data-placeholder': 'Buscar factura o boleta…',
        })

        self.fields['categoria'].widget.attrs.update({
            'class': 'form-control nx-select-search',
            'data-placeholder': 'Buscar categoría…',
        })

        for name, field in self.fields.items():
            if name == 'notas':
                field.widget.attrs.setdefault('class', 'form-control')
                field.widget.attrs.setdefault('rows', 3)
            elif name in ('factura', 'categoria'):
                continue
            elif getattr(field.widget, 'input_type', None) != 'checkbox':
                field.widget.attrs.setdefault('class', 'form-control')
