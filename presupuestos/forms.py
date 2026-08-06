from django import forms
from django.db.models import Q
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
            'precio_unitario',
        ):
            # es-cl usa coma; <input type="number"> exige punto → sin localizar
            self.fields[name].localize = False
            self.fields[name].widget.is_localized = False
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
        fields = ['factura', 'descripcion', 'monto', 'fecha']

    def __init__(self, *args, proyecto=None, presupuesto=None, **kwargs):
        super().__init__(*args, **kwargs)
        _fc(self)
        self.fields['monto'].localize = False
        self.fields['monto'].widget.is_localized = False
        self.fields['monto'].widget.attrs.setdefault('step', 'any')
        self.fields['factura'].required = True
        self.fields['factura'].label = 'Factura / boleta'
        self.fields['factura'].empty_label = 'Selecciona factura o boleta…'
        exclude_pk = getattr(self.instance, 'pk', None)
        qs = FacturaBoleta.objects.none()
        if proyecto is not None:
            qs = FacturaBoleta.objects.filter(proyecto=proyecto).order_by('-fecha', '-pk')
            if presupuesto is not None:
                qs = qs.filter(Q(presupuesto=presupuesto) | Q(presupuesto__isnull=True)).distinct()
        self.fields['factura'].queryset = qs

        def _label(f):
            saldo = f.saldo_disponible(exclude_gasto_pk=exclude_pk)
            return f'{f} — total ${f.total:,.0f} / disponible ${saldo:,.0f}'

        self.fields['factura'].label_from_instance = _label

    def clean(self):
        cleaned = super().clean()
        factura = cleaned.get('factura')
        monto = cleaned.get('monto')
        if factura is None or monto is None:
            return cleaned
        exclude_pk = self.instance.pk if self.instance and self.instance.pk else None
        usados = factura.suma_gastos(exclude_pk=exclude_pk)
        total = factura.total
        if usados + monto > total:
            raise forms.ValidationError(
                f'La suma de gastos vinculados (${usados + monto:,.2f}) supera el total '
                f'de la {factura.get_tipo_display().lower()} {factura.numero} (${total:,.2f}). '
                f'Saldo disponible: ${total - usados:,.2f}.'
            )
        return cleaned


class FacturaForm(ModelForm):
    class Meta:
        model = FacturaBoleta
        fields = ['tipo', 'numero', 'fecha', 'monto_neto', 'monto_iva', 'archivo']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _fc(self)
        self.fields['archivo'].required = True
        self.fields['archivo'].help_text = 'Obligatorio: adjunta el PDF o imagen de la factura/boleta.'
        for name in ('monto_neto', 'monto_iva'):
            self.fields[name].localize = False
            self.fields[name].widget.is_localized = False
            self.fields[name].widget.attrs.setdefault('step', 'any')
        if self.instance and self.instance.pk and self.instance.archivo:
            self.fields['archivo'].required = False
