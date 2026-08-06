from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods, require_POST

from activos.forms import ActivoForm
from activos.models import Activo
from core.modal import modal_form, modal_success
from proyectos.models import TimelineEvent, proyectos_visibles_para

_ESTADOS_ABIERTOS = ('abierta', 'en_progreso')


def _activo_accesible(user, activo):
    return activo.proyecto.user_has_access(user)


def _timeline_activo(proyecto, user, activo, accion):
    TimelineEvent.objects.create(
        proyecto=proyecto,
        actor=user,
        tipo='activo',
        titulo=f'Activo: {activo.nombre}',
        detalle=accion,
    )


def list_activos(request):
    proyectos = proyectos_visibles_para(request.user)
    qs = (
        Activo.objects.filter(proyecto__in=proyectos)
        .select_related('proyecto', 'categoria', 'tecnico')
        .annotate(
            incidencias_activas=Count(
                'proyecto__incidencias',
                filter=Q(proyecto__incidencias__estado__in=_ESTADOS_ABIERTOS),
                distinct=True,
            )
        )
    )
    # ponytail: sin M2M activos↔incidencias; conteo/monitor por proyecto abierto/en_progreso
    from incidencias.models import Incidencia
    monitor = (
        Incidencia.objects.filter(proyecto__in=proyectos, estado__in=_ESTADOS_ABIERTOS)
        .select_related('proyecto', 'autor')
        .order_by('-updated_at')[:50]
    )
    return render(request, 'activos/list.html', {'activos': qs, 'monitor': monitor})


@require_http_methods(['GET', 'POST'])
def create(request):
    initial = {}
    proyecto_id = request.GET.get('proyecto')
    if proyecto_id:
        initial['proyecto'] = proyecto_id
    form = ActivoForm(request.POST or None, request.FILES or None, user=request.user, initial=initial)
    action_url = reverse('activos:create')
    if proyecto_id:
        action_url += f'?proyecto={proyecto_id}'
    if request.method == 'POST' and form.is_valid():
        activo = form.save(commit=False)
        activo.creado_por = request.user
        if not activo.tecnico_id:
            activo.tecnico = request.user
        activo.save()
        _timeline_activo(activo.proyecto, request.user, activo, 'Creado')
        messages.success(request, 'Activo creado.')
        return modal_success(request, reverse('activos:list'))
    return modal_form(
        request,
        title='Nuevo activo',
        form=form,
        action_url=action_url,
        multipart=True,
        extra={'cancel_url': reverse('activos:list')},
    )


@require_http_methods(['GET', 'POST'])
def edit(request, pk):
    activo = get_object_or_404(Activo.objects.select_related('proyecto'), pk=pk)
    if not _activo_accesible(request.user, activo):
        raise PermissionDenied
    form = ActivoForm(request.POST or None, request.FILES or None, instance=activo, user=request.user)
    if request.method == 'POST' and form.is_valid():
        activo = form.save()
        _timeline_activo(activo.proyecto, request.user, activo, 'Actualizado')
        messages.success(request, 'Activo actualizado.')
        return modal_success(request, reverse('activos:list'))
    return modal_form(
        request,
        title='Editar activo',
        form=form,
        action_url=reverse('activos:edit', args=[pk]),
        multipart=True,
        extra={'cancel_url': reverse('activos:list'), 'activo': activo},
    )


@require_POST
def delete(request, pk):
    activo = get_object_or_404(Activo.objects.select_related('proyecto'), pk=pk)
    if not _activo_accesible(request.user, activo):
        raise PermissionDenied
    activo.delete()
    messages.success(request, 'Activo eliminado.')
    return redirect('activos:list')
