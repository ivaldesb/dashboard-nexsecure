from django.contrib import messages
from django.core.exceptions import FieldDoesNotExist
from django.forms import ModelForm
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods, require_POST

from clientes.models import Cliente
from core.modal import modal_form, modal_success
from presupuestos.models import Presupuesto
from proyectos.models import EstadoProyecto


def _fc(form):
    for field in form.fields.values():
        if hasattr(field.widget, 'attrs'):
            field.widget.attrs.setdefault('class', 'form-control')
    return form


class ClienteForm(ModelForm):
    class Meta:
        model = Cliente
        fields = [
            'tipo', 'rut', 'nombre', 'apellido', 'nombre_empresa',
            'email', 'telefono', 'direccion',
            'razon_social', 'giro', 'comuna', 'ciudad',
            'activo', 'user',
        ]


def _is_cliente_user(user):
    return getattr(user, 'cliente_profile', None) is not None and not user.is_system_admin()


def _staff_or_portal(request):
    """Clientes van al portal; staff/admin siguen."""
    if _is_cliente_user(request.user):
        return redirect('clientes:portal')
    return None


def _estado_has_visible_cliente():
    try:
        EstadoProyecto._meta.get_field('visible_cliente')
        return True
    except FieldDoesNotExist:
        return False


def portal(request):
    user = request.user
    if user.is_system_admin():
        return redirect('clientes:list')

    cliente = getattr(user, 'cliente_profile', None)
    if cliente is None:
        return render(
            request,
            'clientes/portal.html',
            {'denied': True, 'cliente': None, 'proyectos': [], 'presupuestos': []},
            status=403,
        )

    proyectos = cliente.proyectos.select_related('estado').all()
    if _estado_has_visible_cliente():
        proyectos = proyectos.filter(estado__visible_cliente=True)

    presupuestos = (
        Presupuesto.objects.filter(
            proyecto__in=proyectos,
            estado__in=[Presupuesto.ENVIADO, Presupuesto.ACEPTADO, Presupuesto.RECHAZADO],
        )
        .select_related('proyecto')
        .prefetch_related('items')
    )
    return render(request, 'clientes/portal.html', {
        'denied': False,
        'cliente': cliente,
        'proyectos': proyectos,
        'presupuestos': presupuestos,
    })


def list(request):
    denied = _staff_or_portal(request)
    if denied:
        return denied
    clientes = Cliente.objects.select_related('user').all()
    return render(request, 'clientes/list.html', {'clientes': clientes})


@require_http_methods(['GET', 'POST'])
def create(request):
    denied = _staff_or_portal(request)
    if denied:
        return denied
    form = _fc(ClienteForm(request.POST or None))
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Cliente creado.')
        return modal_success(request, reverse('clientes:list'))
    return modal_form(
        request,
        title='Nuevo cliente',
        form=form,
        action_url=reverse('clientes:create'),
        extra={'cancel_url': reverse('clientes:list')},
    )


@require_http_methods(['GET', 'POST'])
def edit(request, pk):
    denied = _staff_or_portal(request)
    if denied:
        return denied
    cliente = get_object_or_404(Cliente, pk=pk)
    form = _fc(ClienteForm(request.POST or None, instance=cliente))
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Cliente actualizado.')
        return modal_success(request, reverse('clientes:list'))
    return modal_form(
        request,
        title='Editar cliente',
        form=form,
        action_url=reverse('clientes:edit', args=[pk]),
        extra={'cancel_url': reverse('clientes:list'), 'cliente': cliente},
    )


@require_POST
def toggle(request, pk):
    denied = _staff_or_portal(request)
    if denied:
        return denied
    cliente = get_object_or_404(Cliente, pk=pk)
    cliente.activo = not cliente.activo
    cliente.save(update_fields=['activo', 'updated_at'])
    messages.success(request, 'Estado del cliente actualizado.')
    return redirect('clientes:list')
