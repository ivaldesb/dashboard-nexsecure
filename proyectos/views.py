from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.forms import ModelForm
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods, require_POST

from accounts.permissions import require_admin
from core.modal import modal_form, modal_success
from core.pdf import render_proyecto_reporte_pdf
from presupuestos.models import Presupuesto
from proyectos.models import (
    ComentarioProyecto,
    EstadoProyecto,
    Proyecto,
    TimelineConfig,
    TimelineEvent,
    proyectos_visibles_para,
)

TABS = frozenset(
    {'resumen', 'activos', 'documentos', 'incidencias', 'presupuestos', 'timeline', 'descargas', 'mantenimiento'}
)


def _fc(form):
    for field in form.fields.values():
        if hasattr(field.widget, 'attrs'):
            field.widget.attrs.setdefault('class', 'form-control')
    return form


class ProyectoForm(ModelForm):
    class Meta:
        model = Proyecto
        # generalidades se editan en el detalle del proyecto (default en el modelo)
        fields = ['codigo', 'nombre', 'descripcion', 'progreso', 'estado', 'equipo', 'clientes']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['progreso'].required = False
        self.fields['progreso'].initial = self.fields['progreso'].initial or 0
        for name, placeholder in (
            ('equipo', 'Buscar usuario para añadir…'),
            ('clientes', 'Buscar cliente para añadir…'),
        ):
            f = self.fields[name]
            f.required = False
            f.help_text = 'Arriba: disponibles (buscar y añadir). Abajo: asignados (X para quitar).'
            f.widget.attrs.update({
                'class': 'nx-m2m-picker',
                'data-placeholder': placeholder,
                'multiple': 'multiple',
            })
            # fuerza <select multiple> aunque el widget base ya lo sea
            f.widget.allow_multiple_selected = True
        self.fields['equipo'].label_from_instance = lambda u: (
            f'{(u.get_full_name() or "").strip() or u.username}'
            + (f' — {u.email}' if u.email else '')
        )
        self.fields['clientes'].label_from_instance = lambda c: (
            f'{c.display_name}'
            + (f' — {c.rut}' if c.rut else '')
            + (f' · {c.email}' if c.email else '')
        )
        self.fields['equipo'].queryset = self.fields['equipo'].queryset.order_by(
            'first_name', 'last_name', 'username'
        )
        self.fields['clientes'].queryset = self.fields['clientes'].queryset.order_by(
            'nombre_empresa', 'apellido', 'nombre'
        )


class EstadoProyectoForm(ModelForm):
    class Meta:
        model = EstadoProyecto
        fields = ['nombre', 'slug', 'orden', 'color', 'activo', 'visible_cliente']


class TimelineConfigForm(ModelForm):
    class Meta:
        model = TimelineConfig
        fields = [
            'auto_estado',
            'auto_documento',
            'auto_incidencia',
            'auto_presupuesto',
            'auto_activo',
            'visible_cliente_estado',
            'visible_cliente_documento',
            'visible_cliente_incidencia',
            'visible_cliente_presupuesto',
            'visible_cliente_activo',
        ]


def _get_proyecto_or_403(request, pk):
    proyecto = get_object_or_404(
        Proyecto.objects.select_related('estado', 'creado_por').prefetch_related('equipo', 'clientes'),
        pk=pk,
    )
    if not proyecto.user_has_access(request.user):
        raise PermissionDenied
    return proyecto


def _can_delete_proyecto(user, proyecto):
    return user.is_system_admin() or proyecto.creado_por_id == user.pk


def _can_config_timeline(user, proyecto):
    return user.is_system_admin() or proyecto.equipo.filter(pk=user.pk).exists()


def _is_cliente_viewer(user):
    return getattr(user, 'cliente_profile', None) is not None and not user.is_system_admin()


def list(request):
    proyectos = proyectos_visibles_para(request.user)
    return render(request, 'proyectos/list.html', {'proyectos': proyectos})


@require_http_methods(['GET', 'POST'])
def create(request):
    initial = {}
    borrador = EstadoProyecto.objects.filter(slug='borrador').first()
    if borrador:
        initial['estado'] = borrador
    form = _fc(ProyectoForm(request.POST or None, initial=initial))
    if request.method == 'POST' and form.is_valid():
        proyecto = form.save(commit=False)
        proyecto.creado_por = request.user
        if not proyecto.estado_id and borrador:
            proyecto.estado = borrador
        proyecto.save()
        form.save_m2m()
        Presupuesto.objects.create(
            proyecto=proyecto,
            tipo=Presupuesto.INICIAL,
            titulo=f'Presupuesto inicial — {proyecto.nombre}',
            generalidades=proyecto.generalidades or '',
            creado_por=request.user,
        )
        TimelineEvent.objects.create(
            proyecto=proyecto,
            actor=request.user,
            tipo='estado',
            titulo=f'Estado: {proyecto.estado.nombre}',
            detalle='Proyecto creado',
        )
        messages.success(request, 'Proyecto creado.')
        return modal_success(request, reverse('proyectos:list'))
    return modal_form(
        request,
        title='Nuevo proyecto',
        form=form,
        action_url=reverse('proyectos:create'),
        extra={'cancel_url': reverse('proyectos:list')},
    )


@require_http_methods(['GET', 'POST'])
def edit(request, pk):
    proyecto = _get_proyecto_or_403(request, pk)
    form = _fc(ProyectoForm(request.POST or None, instance=proyecto))
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Proyecto actualizado.')
        return modal_success(request, reverse('proyectos:detail', args=[pk]))
    return modal_form(
        request,
        title='Editar proyecto',
        form=form,
        action_url=reverse('proyectos:edit', args=[pk]),
        extra={'cancel_url': reverse('proyectos:detail', args=[pk]), 'proyecto': proyecto},
    )


@require_POST
def delete(request, pk):
    proyecto = get_object_or_404(Proyecto, pk=pk)
    if not _can_delete_proyecto(request.user, proyecto):
        raise PermissionDenied
    proyecto.delete()
    messages.success(request, 'Proyecto eliminado.')
    return redirect('proyectos:list')


def detail(request, pk):
    from django.conf import settings as dj_settings
    from decimal import Decimal

    proyecto = _get_proyecto_or_403(request, pk)
    tab = request.GET.get('tab', 'resumen')
    if tab not in TABS:
        tab = 'resumen'

    is_cliente = _is_cliente_viewer(request.user)
    is_admin = request.user.is_system_admin()
    ultimo_enviado = (
        proyecto.presupuestos.filter(estado=Presupuesto.ENVIADO)
        .prefetch_related('items')
        .order_by('-updated_at', '-pk')
        .first()
    )
    ultimo_ppto = (
        proyecto.presupuestos.prefetch_related('items').order_by('-updated_at', '-pk').first()
    )
    # Vista cotización: enviado al cliente si hay; si no, el último (staff)
    ppto_vista = ultimo_enviado or (None if is_cliente else ultimo_ppto)
    cotizacion = ppto_vista.totales_cotizacion() if ppto_vista else None
    cliente_principal = proyecto.clientes.first()
    gastos_total = sum((g.monto for g in proyecto.gastos.all()), Decimal('0'))
    if ppto_vista:
        margen = (cotizacion['neto'] if cotizacion else Decimal('0')) - gastos_total
    else:
        margen = Decimal('0') - gastos_total

    ctx = {
        'proyecto': proyecto,
        'tab': tab,
        'estados': EstadoProyecto.objects.filter(activo=True),
        'can_delete': _can_delete_proyecto(request.user, proyecto),
        'comentarios': proyecto.comentarios.select_related('autor').all(),
        'comentario_form_url': reverse('proyectos:add_comentario', args=[proyecto.pk]),
        'is_cliente_view': is_cliente,
        'is_admin': is_admin,
        'ultimo_presupuesto_enviado': ultimo_enviado,
        'ultimo_presupuesto': ultimo_ppto,
        'ppto_vista': ppto_vista,
        'cotizacion': cotizacion,
        'cliente_principal': cliente_principal,
        'iva_rate_pct': int(float(getattr(dj_settings, 'FINANZAS_IVA_RATE', 0.19)) * 100),
        'gastos_total': gastos_total,
        'margen_estimado': margen,
        'timeline_recientes': proyecto.timeline.select_related('actor').all()[:5],
    }
    if is_admin and ppto_vista:
        from presupuestos.finance import resumen_financiero

        ctx['resumen_ppto'] = resumen_financiero(ppto_vista)
    if _can_config_timeline(request.user, proyecto):
        ctx['timeline_config_url'] = reverse('proyectos:timeline_config', args=[proyecto.pk])

    if tab == 'activos':
        ctx['activos'] = proyecto.activos.select_related('categoria', 'factura').all()
    elif tab == 'documentos':
        ctx['documentos'] = [d for d in proyecto.documentos.all() if d.user_can_access(request.user)]
    elif tab == 'incidencias':
        ctx['incidencias'] = proyecto.incidencias.all()
    elif tab == 'presupuestos':
        ctx['presupuestos'] = proyecto.presupuestos.all()
    elif tab == 'timeline':
        timeline = proyecto.timeline.select_related('actor').all()
        if _is_cliente_viewer(request.user):
            config, _ = TimelineConfig.objects.get_or_create(proyecto=proyecto)
            tipos = config.tipos_visibles_cliente()
            timeline = timeline.filter(tipo__in=tipos) if tipos else timeline.none()
        ctx['timeline'] = timeline
    elif tab == 'descargas':
        ctx['presupuestos'] = proyecto.presupuestos.all()
    elif tab == 'mantenimiento':
        try:
            from mantenimiento.models import VisitaMantenimiento  # noqa: F401

            ctx['visitas'] = proyecto.visitas_mantenimiento.all()
            ctx['mantenimiento_create_url'] = reverse('mantenimiento:create', args=[proyecto.pk])
        except ImportError:
            ctx['visitas'] = []
            ctx['mantenimiento_create_url'] = None

    return render(request, 'proyectos/detail.html', ctx)


@require_POST
def change_estado(request, pk):
    proyecto = _get_proyecto_or_403(request, pk)
    nuevo = get_object_or_404(EstadoProyecto, pk=request.POST.get('estado'))
    viejo = proyecto.estado
    if viejo.pk != nuevo.pk:
        proyecto.estado = nuevo
        proyecto.save(update_fields=['estado', 'updated_at'])
        config = TimelineConfig.objects.filter(proyecto=proyecto).first()
        if config is None or config.auto_estado:
            TimelineEvent.objects.create(
                proyecto=proyecto,
                actor=request.user,
                tipo='estado',
                titulo=f'Estado: {viejo.nombre} → {nuevo.nombre}',
            )
        messages.success(request, 'Estado actualizado.')
    return redirect('proyectos:detail', pk=pk)


@require_POST
def add_comentario(request, pk):
    proyecto = _get_proyecto_or_403(request, pk)
    texto = (request.POST.get('texto') or '').strip()
    if not texto:
        messages.error(request, 'El comentario no puede estar vacío.')
    else:
        ComentarioProyecto.objects.create(proyecto=proyecto, autor=request.user, texto=texto)
        messages.success(request, 'Comentario añadido.')
    return redirect(request.POST.get('next') or reverse('proyectos:detail', args=[pk]))


@require_POST
def save_generalidades(request, pk):
    proyecto = _get_proyecto_or_403(request, pk)
    if _is_cliente_viewer(request.user):
        raise PermissionDenied
    from proyectos.models import GENERALIDADES_DEFAULT

    texto = request.POST.get('generalidades')
    if texto is None:
        texto = ''
    texto = texto.strip() or GENERALIDADES_DEFAULT
    proyecto.generalidades = texto
    proyecto.save(update_fields=['generalidades', 'updated_at'])
    # ponytail: sincroniza al presupuesto en vista (si hay)
    ppto_id = request.POST.get('presupuesto_id')
    if ppto_id:
        Presupuesto.objects.filter(pk=ppto_id, proyecto=proyecto).update(generalidades=texto)
    else:
        Presupuesto.objects.filter(proyecto=proyecto, tipo=Presupuesto.INICIAL).update(generalidades=texto)
    messages.success(request, 'Generalidades actualizadas.')
    return redirect(reverse('proyectos:detail', args=[pk]) + '?tab=resumen')


@require_http_methods(['GET', 'POST'])
def timeline_config(request, pk):
    proyecto = _get_proyecto_or_403(request, pk)
    if not _can_config_timeline(request.user, proyecto):
        raise PermissionDenied
    config, _ = TimelineConfig.objects.get_or_create(proyecto=proyecto)
    form = _fc(TimelineConfigForm(request.POST or None, instance=config))
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Configuración de timeline guardada.')
        return redirect(f"{reverse('proyectos:detail', args=[pk])}?tab=timeline")
    return render(
        request,
        'proyectos/timeline_config.html',
        {'form': form, 'proyecto': proyecto, 'title': 'Configuración de timeline'},
    )


@require_admin
def estado_list(request):
    return render(request, 'proyectos/estados_list.html', {'estados': EstadoProyecto.objects.all()})


@require_admin
@require_http_methods(['GET', 'POST'])
def estado_create(request):
    form = _fc(EstadoProyectoForm(request.POST or None))
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Estado creado.')
        return modal_success(request, reverse('proyectos:estado_list'))
    return modal_form(
        request,
        title='Nuevo estado',
        form=form,
        action_url=reverse('proyectos:estado_create'),
        extra={'cancel_url': reverse('proyectos:estado_list')},
    )


@require_admin
@require_http_methods(['GET', 'POST'])
def estado_edit(request, pk):
    estado = get_object_or_404(EstadoProyecto, pk=pk)
    form = _fc(EstadoProyectoForm(request.POST or None, instance=estado))
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Estado actualizado.')
        return redirect('proyectos:estado_list')
    return render(request, 'proyectos/estado_form.html', {'form': form, 'title': 'Editar estado', 'estado': estado})


def pdf_reporte(request, pk):
    proyecto = _get_proyecto_or_403(request, pk)
    return render_proyecto_reporte_pdf(proyecto, viewer_user=request.user)
