from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods, require_POST

from core.modal import modal_form, modal_success
from mantenimiento.forms import VisitaMantenimientoForm
from mantenimiento.models import ChecklistTemplate, FotoVisita, VisitaChecklistItem, VisitaMantenimiento
from proyectos.models import Proyecto


def _visita_accesible(user, visita):
    return visita.proyecto.user_has_access(user)


def list_visitas(request, proyecto_id):
    proyecto = get_object_or_404(Proyecto, pk=proyecto_id)
    if not proyecto.user_has_access(request.user):
        raise PermissionDenied
    visitas = VisitaMantenimiento.objects.filter(proyecto=proyecto).select_related('creado_por')
    return render(request, 'mantenimiento/list.html', {
        'proyecto': proyecto,
        'visitas': visitas,
    })


@require_http_methods(['GET', 'POST'])
def create(request, proyecto_id):
    proyecto = get_object_or_404(Proyecto, pk=proyecto_id)
    if not proyecto.user_has_access(request.user):
        raise PermissionDenied
    form = VisitaMantenimientoForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        visita = form.save(commit=False)
        visita.proyecto = proyecto
        visita.creado_por = request.user
        visita.save()
        # Copiar checklist del template según tipo_servicio (si existe).
        template = ChecklistTemplate.objects.filter(tipo_servicio=visita.tipo_servicio).first()
        if template:
            VisitaChecklistItem.objects.bulk_create([
                VisitaChecklistItem(visita=visita, texto=item.texto, orden=item.orden, hecho=False)
                for item in template.items.all()
            ])
        messages.success(request, 'Visita de mantenimiento creada.')
        return modal_success(request, reverse('mantenimiento:detail', args=[visita.pk]))
    return modal_form(
        request,
        title='Nueva visita de mantenimiento',
        form=form,
        action_url=reverse('mantenimiento:create', args=[proyecto.pk]),
        extra={
            'cancel_url': reverse('mantenimiento:list', args=[proyecto.pk]),
            'proyecto': proyecto,
            'templates': ChecklistTemplate.objects.all(),
        },
    )


def detail(request, pk):
    visita = get_object_or_404(
        VisitaMantenimiento.objects.select_related('proyecto', 'creado_por').prefetch_related(
            'checklist', 'fotos__uploaded_by',
        ),
        pk=pk,
    )
    if not _visita_accesible(request.user, visita):
        raise PermissionDenied
    return render(request, 'mantenimiento/detail.html', {'visita': visita})


@require_POST
def toggle_checklist(request, pk, item_id):
    visita = get_object_or_404(VisitaMantenimiento.objects.select_related('proyecto'), pk=pk)
    if not _visita_accesible(request.user, visita):
        raise PermissionDenied
    item = get_object_or_404(VisitaChecklistItem, pk=item_id, visita=visita)
    item.hecho = not item.hecho
    item.save(update_fields=['hecho'])
    return redirect('mantenimiento:detail', pk=pk)


@require_POST
def upload_foto(request, pk):
    visita = get_object_or_404(VisitaMantenimiento.objects.select_related('proyecto'), pk=pk)
    if not _visita_accesible(request.user, visita):
        raise PermissionDenied
    imagen = request.FILES.get('imagen')
    if not imagen:
        messages.error(request, 'Selecciona una imagen.')
    else:
        FotoVisita.objects.create(visita=visita, imagen=imagen, uploaded_by=request.user)
        messages.success(request, 'Foto subida.')
    return redirect('mantenimiento:detail', pk=pk)
