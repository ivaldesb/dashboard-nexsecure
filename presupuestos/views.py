from urllib.parse import urlencode

from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods, require_POST

from accounts.permissions import require_admin
from core.modal import modal_form, modal_success
from core.pdf import render_presupuesto_pdf
from presupuestos.finance import resumen_financiero
from presupuestos.forms import (
    FacturaForm,
    GastoForm,
    PagoEmpleadoForm,
    PctEmpresaForm,
    PresupuestoAdicionalForm,
    PresupuestoItemForm,
)
from presupuestos.models import FacturaBoleta, PagoEmpleado, Presupuesto, PresupuestoItem
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


def _next_or_detail(request, presupuesto_id):
    nxt = (request.POST.get('next') or request.GET.get('next') or '').strip()
    # ponytail: solo paths relativos locales
    if nxt.startswith('/') and not nxt.startswith('//'):
        return nxt
    return _detail_url(presupuesto_id)


def pdf_presupuesto(request, pk):
    presupuesto = get_object_or_404(Presupuesto.objects.select_related('proyecto'), pk=pk)
    if not presupuesto.proyecto.user_has_access(request.user):
        raise PermissionDenied
    return render_presupuesto_pdf(presupuesto, viewer_user=request.user)


def detail(request, presupuesto_id):
    presupuesto = get_object_or_404(
        Presupuesto.objects.select_related('proyecto').prefetch_related(
            'items',
            'gastos__pagado_por',
            'gastos__factura',
            'facturas',
            'pagos_empleados__empleado',
            'proyecto__clientes',
        ),
        pk=presupuesto_id,
    )
    if not presupuesto.proyecto.user_has_access(request.user):
        raise PermissionDenied
    is_cliente_view = _is_cliente_view(request.user)
    is_admin = request.user.is_system_admin()
    ctx = {
        'presupuesto': presupuesto,
        'is_cliente_view': is_cliente_view,
        'is_admin': is_admin,
    }
    if is_admin:
        resumen = resumen_financiero(presupuesto)
        equipo = presupuesto.proyecto.equipo.all()
        ctx.update({
            'resumen': resumen,
            'secundarios': resumen.get('secundarios', []),
            'equipo_users': equipo,
            'pct_empresa_form': PctEmpresaForm(instance=presupuesto),
            'pct_form': PctEmpresaForm(instance=presupuesto),
            'pago_form': PagoEmpleadoForm(equipo=equipo),
            'gasto_form': GastoForm(
                proyecto=presupuesto.proyecto,
                presupuesto=presupuesto,
                equipo=equipo,
            ),
            'factura_form': FacturaForm(),
        })
    return render(request, 'presupuestos/detail.html', ctx)


@require_http_methods(['GET', 'POST'])
def create_adicional(request, proyecto_id):
    proyecto = _get_proyecto_or_403(request, proyecto_id)
    form = PresupuestoAdicionalForm(request.POST or None)
    success_url = _proyecto_presupuestos_url(proyecto)
    if request.method == 'POST' and form.is_valid():
        presupuesto = form.save(commit=False)
        presupuesto.proyecto = proyecto
        presupuesto.tipo = Presupuesto.ADICIONAL
        presupuesto.generalidades = proyecto.generalidades or presupuesto.generalidades
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
    back = _next_or_detail(request, presupuesto.pk)
    if request.method == 'POST' and form.is_valid():
        item = form.save(commit=False)
        item.presupuesto = presupuesto
        item.save()
        messages.success(request, 'Ítem añadido.')
        return modal_success(request, back)
    action = reverse('presupuestos:item_add', args=[presupuesto.pk])
    nxt = request.GET.get('next')
    if nxt:
        action += f'?next={nxt}'
    return modal_form(
        request,
        title='Añadir ítem',
        form=form,
        action_url=action,
        extra={
            'form_body_template': 'presupuestos/item_form_body.html',
            'presupuesto': presupuesto,
            'cancel_url': back,
            'include_matriz_js': True,
            'next': nxt or '',
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
    back = _next_or_detail(request, item.presupuesto_id)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Ítem actualizado.')
        return modal_success(request, back)
    action = reverse('presupuestos:item_edit', args=[pk])
    nxt = request.GET.get('next') or ''
    if nxt:
        action += '?' + urlencode({'next': nxt})
    return modal_form(
        request,
        title='Editar ítem',
        form=form,
        action_url=action,
        extra={
            'form_body_template': 'presupuestos/item_form_body.html',
            'presupuesto': item.presupuesto,
            'cancel_url': back,
            'include_matriz_js': True,
            'next': nxt,
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
    return redirect(_next_or_detail(request, presupuesto_id))


@require_admin
@require_http_methods(['GET', 'POST'])
def gasto_add(request, proyecto_id):
    proyecto = _get_proyecto_or_403(request, proyecto_id)
    presupuesto_id = request.GET.get('presupuesto') or request.POST.get('presupuesto')
    presupuesto = _presupuesto_de_proyecto(proyecto, presupuesto_id) if presupuesto_id else None
    form = GastoForm(
        request.POST or None,
        proyecto=proyecto,
        presupuesto=presupuesto,
        equipo=proyecto.equipo.all(),
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


@require_admin
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


@require_admin
@require_POST
def pct_empresa_save(request, pk):
    presupuesto = _get_presupuesto_or_403(request, pk)
    form = PctEmpresaForm(request.POST, instance=presupuesto)
    if form.is_valid():
        form.save()
        messages.success(request, '% empresa actualizado.')
    else:
        messages.error(request, 'No se pudo guardar el % empresa.')
    return redirect('presupuestos:detail', presupuesto_id=pk)


@require_admin
@require_http_methods(['GET', 'POST'])
def pago_add(request, presupuesto_id):
    presupuesto = _get_presupuesto_or_403(request, presupuesto_id)
    equipo = presupuesto.proyecto.equipo.all()
    form = PagoEmpleadoForm(request.POST or None, equipo=equipo)
    back = _detail_url(presupuesto.pk)
    if request.method == 'POST' and form.is_valid():
        pago = form.save(commit=False)
        pago.presupuesto = presupuesto
        pago.save()
        messages.success(request, 'Pago a empleado registrado.')
        return modal_success(request, back)
    return modal_form(
        request,
        title='Pago a empleado',
        form=form,
        action_url=reverse('presupuestos:pago_add', args=[presupuesto.pk]),
        extra={'cancel_url': back, 'presupuesto': presupuesto},
    )


@require_admin
@require_http_methods(['GET', 'POST'])
def pago_edit(request, pk):
    pago = get_object_or_404(
        PagoEmpleado.objects.select_related('presupuesto__proyecto'),
        pk=pk,
    )
    if not pago.presupuesto.proyecto.user_has_access(request.user):
        raise PermissionDenied
    equipo = pago.presupuesto.proyecto.equipo.all()
    form = PagoEmpleadoForm(request.POST or None, instance=pago, equipo=equipo)
    back = _detail_url(pago.presupuesto_id)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Pago a empleado actualizado.')
        return modal_success(request, back)
    return modal_form(
        request,
        title='Editar pago a empleado',
        form=form,
        action_url=reverse('presupuestos:pago_edit', args=[pk]),
        extra={'cancel_url': back, 'presupuesto': pago.presupuesto},
    )


@require_admin
@require_POST
def pago_delete(request, pk):
    pago = get_object_or_404(
        PagoEmpleado.objects.select_related('presupuesto__proyecto'),
        pk=pk,
    )
    if not pago.presupuesto.proyecto.user_has_access(request.user):
        raise PermissionDenied
    presupuesto_id = pago.presupuesto_id
    pago.delete()
    messages.success(request, 'Pago a empleado eliminado.')
    return redirect('presupuestos:detail', presupuesto_id=presupuesto_id)
