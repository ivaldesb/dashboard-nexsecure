from django import forms
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.forms import ModelForm

from presupuestos.models import FacturaBoleta, Gasto, PagoEmpleado, Presupuesto, PresupuestoItem

User = get_user_model()


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
            'ubicacion',
            'tipologia',
            'caracteristicas',
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
            'ubicacion',
            'tipologia',
            'caracteristicas',
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
        fields = ['factura', 'tipo', 'descripcion', 'monto', 'fecha', 'pagado_por_tipo', 'pagado_por']

    def __init__(self, *args, proyecto=None, presupuesto=None, equipo=None, **kwargs):
        super().__init__(*args, **kwargs)
        _fc(self)
        self.fields['monto'].localize = False
        self.fields['monto'].widget.is_localized = False
        self.fields['monto'].widget.attrs.setdefault('step', 'any')
        self.fields['factura'].required = True
        self.fields['factura'].label = 'Factura / boleta'
        self.fields['factura'].empty_label = 'Selecciona factura o boleta…'
        self.fields['pagado_por'].required = False
        self.fields['pagado_por'].empty_label = '—'
        exclude_pk = getattr(self.instance, 'pk', None)
        qs = FacturaBoleta.objects.none()
        users = User.objects.none()
        if proyecto is not None:
            qs = FacturaBoleta.objects.filter(proyecto=proyecto).order_by('-fecha', '-pk')
            if presupuesto is not None:
                qs = qs.filter(Q(presupuesto=presupuesto) | Q(presupuesto__isnull=True)).distinct()
            users = proyecto.equipo.all().order_by('first_name', 'username')
        if equipo is not None:
            users = equipo
        self.fields['factura'].queryset = qs
        self.fields['pagado_por'].queryset = users

        def _label(f):
            saldo = f.saldo_disponible(exclude_gasto_pk=exclude_pk)
            return f'{f} — total ${f.total:,.0f} / disponible ${saldo:,.0f}'

        self.fields['factura'].label_from_instance = _label

    def clean(self):
        cleaned = super().clean()
        factura = cleaned.get('factura')
        monto = cleaned.get('monto')
        if cleaned.get('pagado_por_tipo') == Gasto.PAGADO_USUARIO and not cleaned.get('pagado_por'):
            self.add_error('pagado_por', 'Indica el usuario que pagó.')
        elif cleaned.get('pagado_por_tipo') != Gasto.PAGADO_USUARIO:
            cleaned['pagado_por'] = None
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
        fields = ['tipo', 'numero', 'proveedor', 'fecha', 'monto_neto', 'monto_iva', 'archivo']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _fc(self)
        self.fields['proveedor'].required = False
        self.fields['archivo'].required = True
        self.fields['archivo'].help_text = 'Obligatorio: adjunta el PDF o imagen de la factura/boleta.'
        for name in ('monto_neto', 'monto_iva'):
            self.fields[name].localize = False
            self.fields[name].widget.is_localized = False
            self.fields[name].widget.attrs.setdefault('step', 'any')
        if self.instance and self.instance.pk and self.instance.archivo:
            self.fields['archivo'].required = False


class PagoEmpleadoForm(ModelForm):
    class Meta:
        model = PagoEmpleado
        fields = ['empleado', 'porcentaje_pago', 'anticipo', 'quien_anticipo_tipo', 'quien_anticipo']

    def __init__(self, *args, proyecto=None, equipo=None, **kwargs):
        super().__init__(*args, **kwargs)
        _fc(self)
        self.fields['quien_anticipo'].required = False
        self.fields['quien_anticipo'].empty_label = '—'
        for name in ('porcentaje_pago', 'anticipo'):
            self.fields[name].localize = False
            self.fields[name].widget.is_localized = False
            self.fields[name].widget.attrs.setdefault('step', 'any')
        users = User.objects.none()
        if proyecto is not None:
            users = proyecto.equipo.all().order_by('first_name', 'username')
        if equipo is not None:
            users = equipo
        # incluir empleado actual al editar aunque no esté en equipo
        if self.instance and self.instance.pk and self.instance.empleado_id:
            users = (users | User.objects.filter(pk=self.instance.empleado_id)).distinct()
        self.fields['empleado'].queryset = users
        self.fields['quien_anticipo'].queryset = users

    def clean(self):
        cleaned = super().clean()
        if cleaned.get('quien_anticipo_tipo') == PagoEmpleado.QUIEN_USUARIO and not cleaned.get('quien_anticipo'):
            self.add_error('quien_anticipo', 'Indica quién dio el anticipo.')
        elif cleaned.get('quien_anticipo_tipo') != PagoEmpleado.QUIEN_USUARIO:
            cleaned['quien_anticipo'] = None
        return cleaned


class PctEmpresaForm(ModelForm):
    class Meta:
        model = Presupuesto
        fields = ['pct_empresa']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _fc(self)
        self.fields['pct_empresa'].localize = False
        self.fields['pct_empresa'].widget.is_localized = False
        self.fields['pct_empresa'].widget.attrs.setdefault('step', 'any')
        self.fields['pct_empresa'].label = '% Empresa'
