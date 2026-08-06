from django.forms import ModelForm

from presupuestos.models import FacturaBoleta, Gasto, Presupuesto, PresupuestoItem


def _fc(form):
    for field in form.fields.values():
        if hasattr(field.widget, 'attrs'):
            field.widget.attrs.setdefault('class', 'form-control')
    return form


class PresupuestoAdicionalForm(ModelForm):
    class Meta:
        model = Presupuesto
        fields = ['titulo', 'notas', 'incidencia', 'visita_mantenimiento_id']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _fc(self)
        self.fields['notas'].widget.attrs.setdefault('rows', 3)
        self.fields['incidencia'].required = False
        self.fields['visita_mantenimiento_id'].required = False
        self.fields['visita_mantenimiento_id'].label = 'ID visita mantenimiento'


class PresupuestoItemForm(ModelForm):
    class Meta:
        model = PresupuestoItem
        fields = [
            'tipo',
            'referencia',
            'descripcion',
            'cantidad',
            'costo_insumo',
            'pct_maquila',
            'pct_instalacion',
            'pct_desinstalacion',
            'pct_ferreteria',
            'pct_flete',
            'pct_gg',
            'pct_utilidad',
            'utilidad_manual',
            'neto_unidad',
            'precio_unitario',
            'incidencia',
            'visita_mantenimiento_id',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _fc(self)
        for name in (
            'incidencia',
            'visita_mantenimiento_id',
            'descripcion',
            'utilidad_manual',
            'precio_unitario',
        ):
            self.fields[name].required = False
        self.fields['visita_mantenimiento_id'].label = 'ID visita mantenimiento'
        for name in (
            'costo_insumo',
            'pct_maquila',
            'pct_instalacion',
            'pct_desinstalacion',
            'pct_ferreteria',
            'pct_flete',
            'pct_gg',
            'pct_utilidad',
            'utilidad_manual',
            'neto_unidad',
            'cantidad',
        ):
            self.fields[name].widget.attrs.setdefault('step', 'any')
            self.fields[name].widget.attrs['class'] = (
                self.fields[name].widget.attrs.get('class', '') + f' matriz-input matriz-{name}'
            ).strip()
        self.fields['tipo'].widget.attrs['class'] = (
            self.fields['tipo'].widget.attrs.get('class', '') + ' matriz-tipo'
        ).strip()
        self.fields['neto_unidad'].widget.attrs['class'] = (
            self.fields['neto_unidad'].widget.attrs.get('class', '') + ' matriz-calc'
        ).strip()

    def clean(self):
        cleaned = super().clean()
        tipo = cleaned.get('tipo') or PresupuestoItem.MATERIAL
        ref = (cleaned.get('referencia') or '').strip()
        desc = (cleaned.get('descripcion') or '').strip()
        if not desc and ref:
            cleaned['descripcion'] = ref
        if tipo == PresupuestoItem.SERVICIO:
            cleaned['costo_insumo'] = 0
            for f in PresupuestoItem.PCT_FIELDS:
                cleaned[f] = 0
            neto = cleaned.get('neto_unidad')
            if neto is None:
                neto = cleaned.get('precio_unitario') or 0
            cleaned['neto_unidad'] = neto
            cleaned['precio_unitario'] = neto
        return cleaned


class GastoForm(ModelForm):
    class Meta:
        model = Gasto
        fields = ['descripcion', 'monto', 'fecha']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _fc(self)


class FacturaForm(ModelForm):
    class Meta:
        model = FacturaBoleta
        fields = ['tipo', 'numero', 'fecha', 'monto_neto', 'monto_iva', 'archivo']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _fc(self)
