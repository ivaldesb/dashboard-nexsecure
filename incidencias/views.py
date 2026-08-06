from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods, require_POST

from core.modal import modal_form, modal_success
from incidencias.forms import FotoUploadForm, IncidenciaForm
from incidencias.models import ComentarioIncidencia, FotoIncidencia, Incidencia
from proyectos.models import Proyecto, TimelineEvent, proyectos_visibles_para


def _incidencia_accesible(user, incidencia):
    return incidencia.proyecto.user_has_access(user)


def _save_fotos(request, incidencia):
    for f in request.FILES.getlist('fotos'):
        FotoIncidencia.objects.create(incidencia=incidencia, imagen=f, uploaded_by=request.user)


def list_incidencias(request):
    qs = Incidencia.objects.filter(
        proyecto__in=proyectos_visibles_para(request.user),
    ).select_related('proyecto', 'autor', 'tecnico')
    proyecto_id = request.GET.get('proyecto')
    if proyecto_id:
        qs = qs.filter(proyecto_id=proyecto_id)
    return render(request, 'incidencias/list.html', {'incidencias': qs})


@require_http_methods(['GET', 'POST'])
def create(request, proyecto_id):
    proyecto = get_object_or_404(Proyecto, pk=proyecto_id)
    if not proyecto.user_has_access(request.user):
        raise PermissionDenied
    form = IncidenciaForm(request.POST or None, proyecto=proyecto)
    success_url = reverse('proyectos:detail', args=[proyecto.pk]) + '?tab=incidencias'
    if request.method == 'POST' and form.is_valid():
        incidencia = form.save(commit=False)
        incidencia.proyecto = proyecto
        incidencia.autor = request.user
        incidencia.tecnico = request.user
        incidencia.save()
        form.save_m2m()
        _save_fotos(request, incidencia)
        TimelineEvent.objects.create(
            proyecto=proyecto,
            actor=request.user,
            tipo='incidencia',
            titulo=f'Incidencia: {incidencia.titulo}',
            detalle='Abierta',
        )
        messages.success(request, 'Incidencia creada.')
        return modal_success(request, success_url)
    return modal_form(
        request,
        title='Nueva incidencia',
        form=form,
        action_url=reverse('incidencias:create', args=[proyecto.pk]),
        multipart=True,
        extra={
            'cancel_url': success_url,
            'proyecto': proyecto,
            'form_body_template': 'incidencias/form_body.html',
        },
    )


@require_http_methods(['GET', 'POST'])
def detail(request, pk):
    incidencia = get_object_or_404(
        Incidencia.objects.select_related('proyecto', 'autor', 'tecnico').prefetch_related(
            'comentarios__autor', 'fotos__uploaded_by', 'activos',
        ),
        pk=pk,
    )
    if not _incidencia_accesible(request.user, incidencia):
        raise PermissionDenied

    if request.method == 'POST' and 'update_incidencia' in request.POST:
        form = IncidenciaForm(request.POST, instance=incidencia, proyecto=incidencia.proyecto)
        if form.is_valid():
            form.save()
            _save_fotos(request, incidencia)
            messages.success(request, 'Incidencia actualizada.')
            return redirect('incidencias:detail', pk=pk)
    else:
        form = IncidenciaForm(instance=incidencia, proyecto=incidencia.proyecto)

    return render(request, 'incidencias/detail.html', {
        'incidencia': incidencia,
        'form': form,
        'estados': Incidencia.ESTADO_CHOICES,
        'foto_form': FotoUploadForm(),
    })


@require_POST
def update_estado(request, pk):
    incidencia = get_object_or_404(Incidencia.objects.select_related('proyecto'), pk=pk)
    if not _incidencia_accesible(request.user, incidencia):
        raise PermissionDenied
    estado = request.POST.get('estado')
    valid = {c[0] for c in Incidencia.ESTADO_CHOICES}
    if estado not in valid:
        messages.error(request, 'Estado no válido.')
    else:
        incidencia.estado = estado
        incidencia.save(update_fields=['estado', 'updated_at'])
        messages.success(request, 'Estado actualizado.')
    return redirect('incidencias:detail', pk=pk)


@require_POST
def add_comentario(request, pk):
    incidencia = get_object_or_404(Incidencia.objects.select_related('proyecto'), pk=pk)
    if not _incidencia_accesible(request.user, incidencia):
        raise PermissionDenied
    texto = (request.POST.get('texto') or '').strip()
    if not texto:
        messages.error(request, 'El comentario no puede estar vacío.')
    else:
        ComentarioIncidencia.objects.create(incidencia=incidencia, autor=request.user, texto=texto)
        messages.success(request, 'Comentario añadido.')
    return redirect('incidencias:detail', pk=pk)


@require_POST
def add_foto(request, pk):
    incidencia = get_object_or_404(Incidencia.objects.select_related('proyecto'), pk=pk)
    if not _incidencia_accesible(request.user, incidencia):
        raise PermissionDenied
    form = FotoUploadForm(request.POST, request.FILES)
    if form.is_valid() and form.cleaned_data.get('imagen'):
        FotoIncidencia.objects.create(
            incidencia=incidencia,
            imagen=form.cleaned_data['imagen'],
            uploaded_by=request.user,
        )
        messages.success(request, 'Foto subida.')
    else:
        messages.error(request, 'Selecciona un archivo.')
    return redirect('incidencias:detail', pk=pk)
