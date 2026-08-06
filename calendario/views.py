from django.conf import settings
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods

from calendario.forms import EventoForm, TareaForm
from calendario.models import CapaCalendario, Evento, Tarea
from calendario.notify import notify_whatsapp
from core.modal import modal_form, modal_success


def _ensure_default_capa(user):
    if not CapaCalendario.objects.filter(user=user).exists():
        CapaCalendario.objects.create(user=user, nombre='Principal', color='#3498db')


def _capas_qs(user):
    return CapaCalendario.objects.filter(user=user)


def _eventos_qs(user):
    qs = Evento.objects.select_related('proyecto', 'creador', 'capa').prefetch_related('asignados')
    if user.is_system_admin():
        return qs
    return qs.filter(asignados=user)


def _tareas_qs(user):
    qs = Tarea.objects.select_related('proyecto', 'creador', 'capa').prefetch_related('asignados')
    if user.is_system_admin():
        return qs
    return qs.filter(asignados=user)


def _filter_by_capas(qs, user):
    invisible = _capas_qs(user).filter(visible=False).values_list('pk', flat=True)
    if not invisible:
        return qs
    return qs.exclude(capa_id__in=invisible)


def _puede_ver_evento(user, evento) -> bool:
    return user.is_system_admin() or evento.asignados.filter(pk=user.pk).exists()


def _user_phone(user) -> str:
    return getattr(user, 'telefono', None) or getattr(user, 'phone', None) or ''


def _notify(evento, subject: str):
    asignados = list(evento.asignados.all())
    emails = [u.email for u in asignados if u.email]
    body = (
        f'Tipo: {evento.get_tipo_display()}\n'
        f'Ubicación: {evento.ubicacion or "—"}\n'
        f'{evento.descripcion or "(sin descripción)"}\n\n'
        f'Inicio: {evento.inicio:%d/%m/%Y %H:%M}\n'
        f'Fin: {evento.fin:%d/%m/%Y %H:%M}'
    )
    if emails:
        send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, emails, fail_silently=True)
    text = f'{subject}\n{body}'
    for u in asignados:
        notify_whatsapp(_user_phone(u), text)


def _toggle_capas(request):
    """POST: toggle visible for capas owned by the user. Returns True if handled."""
    if request.method != 'POST' or 'toggle_capa' not in request.POST:
        return False
    capa = get_object_or_404(_capas_qs(request.user), pk=request.POST.get('toggle_capa'))
    capa.visible = not capa.visible
    capa.save(update_fields=['visible'])
    return True


@require_http_methods(['GET', 'POST'])
def list_eventos(request):
    _ensure_default_capa(request.user)
    if _toggle_capas(request):
        return redirect('calendario:list')
    capas = _capas_qs(request.user)
    eventos = _filter_by_capas(_eventos_qs(request.user), request.user)
    return render(
        request,
        'calendario/list.html',
        {'eventos': eventos, 'capas': capas},
    )


@require_http_methods(['GET', 'POST'])
def create(request):
    _ensure_default_capa(request.user)
    form = EventoForm(request.POST or None, user=request.user)
    if request.method == 'POST' and form.is_valid():
        evento = form.save(commit=False)
        evento.creador = request.user
        evento.save()
        form.save_m2m()
        evento.asignados.add(request.user)  # privacy: creador always subscribed
        _notify(evento, f'Nuevo evento: {evento.titulo}')
        messages.success(request, 'Evento creado.')
        return modal_success(request, reverse('calendario:list'))
    return modal_form(
        request,
        title='Nuevo evento',
        form=form,
        action_url=reverse('calendario:create'),
        extra={'cancel_url': reverse('calendario:list')},
    )


def detail(request, pk):
    evento = get_object_or_404(_eventos_qs(request.user), pk=pk)
    return render(request, 'calendario/detail.html', {'evento': evento})


@require_http_methods(['GET', 'POST'])
def edit(request, pk):
    evento = get_object_or_404(Evento, pk=pk)
    if not _puede_ver_evento(request.user, evento):
        raise PermissionDenied
    form = EventoForm(request.POST or None, instance=evento, user=request.user)
    if request.method == 'POST' and form.is_valid():
        evento = form.save()
        evento.asignados.add(evento.creador)
        _notify(evento, f'Evento actualizado: {evento.titulo}')
        messages.success(request, 'Evento actualizado.')
        return redirect('calendario:detail', pk=evento.pk)
    return render(
        request,
        'calendario/form.html',
        {'form': form, 'title': 'Editar evento', 'evento': evento},
    )


@require_http_methods(['GET', 'POST'])
def list_tareas(request):
    _ensure_default_capa(request.user)
    if _toggle_capas(request):
        return redirect('calendario:tareas')
    capas = _capas_qs(request.user)
    tareas = _filter_by_capas(_tareas_qs(request.user), request.user)
    return render(
        request,
        'calendario/tareas_list.html',
        {'tareas': tareas, 'capas': capas},
    )


@require_http_methods(['GET', 'POST'])
def create_tarea(request):
    _ensure_default_capa(request.user)
    form = TareaForm(request.POST or None, user=request.user)
    if request.method == 'POST' and form.is_valid():
        tarea = form.save(commit=False)
        tarea.creador = request.user
        tarea.save()
        form.save_m2m()
        tarea.asignados.add(request.user)
        messages.success(request, 'Tarea creada.')
        return modal_success(request, reverse('calendario:tareas'))
    return modal_form(
        request,
        title='Nueva tarea',
        form=form,
        action_url=reverse('calendario:tarea_create'),
        extra={'cancel_url': reverse('calendario:tareas')},
    )
