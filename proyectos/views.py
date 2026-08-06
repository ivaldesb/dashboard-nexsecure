from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.forms import ModelForm
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods, require_POST

from accounts.permissions import require_admin
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
        fields = ['codigo', 'nombre', 'descripcion', 'estado', 'equipo', 'clientes']


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
        return redirect('proyectos:detail', pk=proyecto.pk)
    return render(request, 'proyectos/form.html', {'form': form, 'title': 'Nuevo proyecto'})


@require_http_methods(['GET', 'POST'])
def edit(request, pk):
    proyecto = _get_proyecto_or_403(request, pk)
    form = _fc(ProyectoForm(request.POST or None, instance=proyecto))
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Proyecto actualizado.')
        return redirect('proyectos:detail', pk=pk)
    return render(
        request,
        'proyectos/form.html',
        {'form': form, 'title': 'Editar proyecto', 'proyecto': proyecto, 'can_delete': _can_delete_proyecto(request.user, proyecto)},
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
    proyecto = _get_proyecto_or_403(request, pk)
    tab = request.GET.get('tab', 'resumen')
    if tab not in TABS:
        tab = 'resumen'

    ctx = {
        'proyecto': proyecto,
        'tab': tab,
        'estados': EstadoProyecto.objects.filter(activo=True),
        'can_delete': _can_delete_proyecto(request.user, proyecto),
        'comentarios': proyecto.comentarios.select_related('autor').all(),
        'comentario_form_url': reverse('proyectos:add_comentario', args=[proyecto.pk]),
    }
    if _can_config_timeline(request.user, proyecto):
        ctx['timeline_config_url'] = reverse('proyectos:timeline_config', args=[proyecto.pk])

    if tab == 'activos':
        ctx['activos'] = proyecto.activos.all()
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
        return redirect('proyectos:estado_list')
    return render(request, 'proyectos/estado_form.html', {'form': form, 'title': 'Nuevo estado'})


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
