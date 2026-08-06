from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods, require_POST

from core.modal import modal_form, modal_success
from core.pdf import render_presupuesto_pdf
from presupuestos.forms import FacturaForm, GastoForm, PresupuestoAdicionalForm, PresupuestoItemForm
from presupuestos.models import FacturaBoleta, Presupuesto, PresupuestoItem
from proyectos.models import Proyecto, TimelineEvent


def _is_cliente_view(user) -> bool:
    if not user or not user.is_authenticated:
        return False
    if user.is_system_admin():
        return False
    try:
        return user.cliente_profile is not None
    except ObjectDoesNotExist:
        return False


def _get_proyecto_or_403(request, pk):
    proyecto = get_object_or_404(Proyecto, pk=pk)
    if not proyecto.user_has_access(request.user):
        raise PermissionDenied
    return proyecto


def _get_presupuesto_or_403(request, pk):
    presupuesto = get_object_or_404(
        Presupuesto.objects.select_related('proyecto'),
        pk=pk,
    )
    if not presupuesto.proyecto.user_has_access(request.user):
        raise PermissionDenied
    return presupuesto


def _presupuesto_de_proyecto(proyecto, presupuesto_id):
    if not presupuesto_id:
        return None
    return get_object_or_404(Presupuesto, pk=presupuesto_id, proyecto=proyecto)


def _proyecto_presupuestos_url(proyecto):
    return reverse('proyectos:detail', kwargs={'pk': proyecto.pk}) + '?tab=presupuestos'


def _detail_url(presupuesto_id):
    return reverse('presupuestos:detail', kwargs={'presupuesto_id': presupuesto_id})


def pdf_presupuesto(request, pk):
    presupuesto = get_object_or_404(Presupuesto.objects.select_related('proyecto'), pk=pk)
    if not presupuesto.proyecto.user_has_access(request.user):
        raise PermissionDenied
    return render_presupuesto_pdf(presupuesto, viewer_user=request.user)


def detail(request, presupuesto_id):
    presupuesto = get_object_or_404(
        Presupuesto.objects.select_related('proyecto').prefetch_related('items', 'gastos', 'facturas'),
        pk=presupuesto_id,
    )
    if not presupuesto.proyecto.user_has_access(request.user):
        raise PermissionDenied
    is_cliente_view = _is_cliente_view(request.user)
    return render(request, 'presupuestos/detail.html', {
        'presupuesto': presupuesto,
        'is_cliente_view': is_cliente_view,
    })


@require_http_methods(['GET', 'POST'])
def create_adicional(request, proyecto_id):
    proyecto = _get_proyecto_or_403(request, proyecto_id)
    form = PresupuestoAdicionalForm(request.POST or None)
    success_url = _proyecto_presupuestos_url(proyecto)
    if request.method == 'POST' and form.is_valid():
        presupuesto = form.save(commit=False)
        presupuesto.proyecto = proyecto
        presupuesto.tipo = Presupuesto.ADICIONAL
        presupuesto.creado_por = request.user
        presupuesto.save()
        TimelineEvent.objects.create(
            proyecto=proyecto,
            actor=request.user,
            tipo='presupuesto',
            titulo=f'Presupuesto adicional: {presupuesto.titulo}',
        )
        messages.success(request, 'Presupuesto adicional creado.')
        return modal_success(request, success_url)
    return modal_form(
        request,
        title='Nuevo presupuesto adicional',
        form=form,
        action_url=reverse('presupuestos:create_adicional', args=[proyecto.pk]),
        extra={'cancel_url': success_url, 'proyecto': proyecto},
    )


@require_http_methods(['GET', 'POST'])
def item_add(request, presupuesto_id):
    presupuesto = _get_presupuesto_or_403(request, presupuesto_id)
    if _is_cliente_view(request.user):
        raise PermissionDenied
    form = PresupuestoItemForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        item = form.save(commit=False)
        item.presupuesto = presupuesto
        item.save()
        messages.success(request, 'Ítem añadido.')
        return modal_success(request, _detail_url(presupuesto.pk))
    return modal_form(
        request,
        title='Añadir ítem',
        form=form,
        action_url=reverse('presupuestos:item_add', args=[presupuesto.pk]),
        extra={
            'form_body_template': 'presupuestos/item_form_body.html',
            'presupuesto': presupuesto,
            'cancel_url': _detail_url(presupuesto.pk),
            'include_matriz_js': True,
        },
    )


@require_http_methods(['GET', 'POST'])
def item_edit(request, pk):
    item = get_object_or_404(PresupuestoItem.objects.select_related('presupuesto__proyecto'), pk=pk)
    if not item.presupuesto.proyecto.user_has_access(request.user):
        raise PermissionDenied
    if _is_cliente_view(request.user):
        raise PermissionDenied
    form = PresupuestoItemForm(request.POST or None, instance=item)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Ítem actualizado.')
        return modal_success(request, _detail_url(item.presupuesto_id))
    return modal_form(
        request,
        title='Editar ítem',
        form=form,
        action_url=reverse('presupuestos:item_edit', args=[pk]),
        extra={
            'form_body_template': 'presupuestos/item_form_body.html',
            'presupuesto': item.presupuesto,
            'cancel_url': _detail_url(item.presupuesto_id),
            'include_matriz_js': True,
        },
    )


@require_POST
def item_delete(request, pk):
    item = get_object_or_404(PresupuestoItem.objects.select_related('presupuesto__proyecto'), pk=pk)
    if not item.presupuesto.proyecto.user_has_access(request.user):
        raise PermissionDenied
    if _is_cliente_view(request.user):
        raise PermissionDenied
    presupuesto_id = item.presupuesto_id
    item.delete()
    messages.success(request, 'Ítem eliminado.')
    return redirect('presupuestos:detail', presupuesto_id=presupuesto_id)


@require_http_methods(['GET', 'POST'])
def gasto_add(request, proyecto_id):
    proyecto = _get_proyecto_or_403(request, proyecto_id)
    presupuesto_id = request.GET.get('presupuesto') or request.POST.get('presupuesto')
    presupuesto = _presupuesto_de_proyecto(proyecto, presupuesto_id) if presupuesto_id else None
    form = GastoForm(
        request.POST or None,
        proyecto=proyecto,
        presupuesto=presupuesto,
    )
    success_url = _detail_url(presupuesto.pk) if presupuesto else _proyecto_presupuestos_url(proyecto)
    action_url = reverse('presupuestos:gasto_add', args=[proyecto.pk])
    if presupuesto:
        action_url += f'?presupuesto={presupuesto.pk}'
    if request.method == 'POST' and form.is_valid():
        gasto = form.save(commit=False)
        gasto.proyecto = proyecto
        gasto.presupuesto = presupuesto
        gasto.creado_por = request.user
        gasto.save()
        TimelineEvent.objects.create(
            proyecto=proyecto,
            actor=request.user,
            tipo='otro',
            titulo=f'Gasto: {gasto.descripcion}',
            detalle=str(gasto.monto),
        )
        messages.success(request, 'Gasto registrado.')
        return modal_success(request, success_url)
    if not FacturaBoleta.objects.filter(proyecto=proyecto).exists():
        messages.warning(request, 'Primero sube una factura o boleta para poder registrar gastos.')
    extra = {
        'cancel_url': success_url,
        'proyecto': proyecto,
        'presupuesto': presupuesto,
    }
    if presupuesto:
        extra['extra_hidden'] = {'presupuesto': presupuesto.pk}
    return modal_form(
        request,
        title='Registrar gasto',
        form=form,
        action_url=action_url,
        extra=extra,
    )


@require_POST
def enviar(request, pk):
    presupuesto = _get_presupuesto_or_403(request, pk)
    if _is_cliente_view(request.user):
        raise PermissionDenied
    presupuesto.estado = Presupuesto.ENVIADO
    presupuesto.save(update_fields=['estado', 'updated_at'])
    TimelineEvent.objects.create(
        proyecto=presupuesto.proyecto,
        actor=request.user,
        tipo='presupuesto',
        titulo=f'Presupuesto enviado: {presupuesto.titulo}',
    )
    messages.success(request, 'Presupuesto enviado al cliente.')
    return redirect('presupuestos:detail', presupuesto_id=pk)


def _volver_proyecto_general(presupuesto):
    return reverse('proyectos:detail', args=[presupuesto.proyecto_id]) + '?tab=resumen'


@require_POST
def aceptar(request, pk):
    presupuesto = _get_presupuesto_or_403(request, pk)
    if not _is_cliente_view(request.user):
        raise PermissionDenied
    if presupuesto.estado != Presupuesto.ENVIADO:
        messages.error(request, 'Solo se pueden aceptar presupuestos enviados.')
        return redirect(_volver_proyecto_general(presupuesto))
    presupuesto.estado = Presupuesto.ACEPTADO
    presupuesto.save(update_fields=['estado', 'updated_at'])
    TimelineEvent.objects.create(
        proyecto=presupuesto.proyecto,
        actor=request.user,
        tipo='presupuesto',
        titulo=f'Presupuesto aceptado: {presupuesto.titulo}',
    )
    messages.success(request, 'Presupuesto aceptado.')
    next_url = request.POST.get('next') or _volver_proyecto_general(presupuesto)
    return redirect(next_url)


@require_POST
def rechazar(request, pk):
    presupuesto = _get_presupuesto_or_403(request, pk)
    if not _is_cliente_view(request.user):
        raise PermissionDenied
    if presupuesto.estado != Presupuesto.ENVIADO:
        messages.error(request, 'Solo se pueden rechazar presupuestos enviados.')
        return redirect(_volver_proyecto_general(presupuesto))
    comentario = (request.POST.get('comentario') or '').strip()
    if not comentario:
        messages.error(request, 'Indica un comentario al rechazar.')
        return redirect(_volver_proyecto_general(presupuesto))
    presupuesto.estado = Presupuesto.RECHAZADO
    presupuesto.notas = (presupuesto.notas + '\n' if presupuesto.notas else '') + f'[Rechazo] {comentario}'
    presupuesto.save(update_fields=['estado', 'notas', 'updated_at'])
    TimelineEvent.objects.create(
        proyecto=presupuesto.proyecto,
        actor=request.user,
        tipo='presupuesto',
        titulo=f'Presupuesto rechazado: {presupuesto.titulo}',
        detalle=comentario,
    )
    messages.success(request, 'Presupuesto rechazado.')
    next_url = request.POST.get('next') or _volver_proyecto_general(presupuesto)
    return redirect(next_url)


@require_http_methods(['GET', 'POST'])
def factura_add(request, proyecto_id):
    proyecto = _get_proyecto_or_403(request, proyecto_id)
    presupuesto_id = request.GET.get('presupuesto') or request.POST.get('presupuesto')
    presupuesto = _presupuesto_de_proyecto(proyecto, presupuesto_id) if presupuesto_id else None
    form = FacturaForm(request.POST or None, request.FILES or None)
    success_url = _detail_url(presupuesto.pk) if presupuesto else _proyecto_presupuestos_url(proyecto)
    action_url = reverse('presupuestos:factura_add', args=[proyecto.pk])
    if presupuesto:
        action_url += f'?presupuesto={presupuesto.pk}'
    if request.method == 'POST' and form.is_valid():
        factura = form.save(commit=False)
        factura.proyecto = proyecto
        factura.presupuesto = presupuesto
        factura.save()
        TimelineEvent.objects.create(
            proyecto=proyecto,
            actor=request.user,
            tipo='documento',
            titulo=f'{factura.get_tipo_display()} {factura.numero}',
            detalle=str(factura.total),
        )
        messages.success(request, 'Factura/boleta registrada.')
        return modal_success(request, success_url)
    extra = {
        'cancel_url': success_url,
        'proyecto': proyecto,
        'presupuesto': presupuesto,
    }
    if presupuesto:
        extra['extra_hidden'] = {'presupuesto': presupuesto.pk}
    return modal_form(
        request,
        title='Registrar factura/boleta',
        form=form,
        action_url=action_url,
        multipart=True,
        extra=extra,
    )
