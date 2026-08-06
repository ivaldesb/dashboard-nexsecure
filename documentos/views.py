import mimetypes
import os

from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods, require_POST

from documentos.forms import DocumentoAclForm, DocumentoUploadForm
from documentos.models import Documento, DocumentoAudit
from proyectos.models import Proyecto, TimelineEvent


def _proyecto_accesible(user, proyecto):
    if not proyecto.user_has_access(user):
        raise PermissionDenied
    return proyecto


def _can_manage_doc(user, doc):
    return user.is_system_admin() or doc.uploaded_by_id == user.pk


def _uploader_es_cliente_del_proyecto(user, proyecto):
    cliente = getattr(user, 'cliente_profile', None)
    if cliente is None:
        return False
    return proyecto.clientes.filter(pk=cliente.pk).exists()


@require_http_methods(['GET', 'POST'])
def upload(request, proyecto_id):
    proyecto = get_object_or_404(Proyecto, pk=proyecto_id)
    _proyecto_accesible(request.user, proyecto)
    form = DocumentoUploadForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        doc = form.save(commit=False)
        doc.proyecto = proyecto
        doc.uploaded_by = request.user
        # Cliente del proyecto: visible para clientes + equipo (vía user_can_access).
        if _uploader_es_cliente_del_proyecto(request.user, proyecto):
            doc.visible_cliente = True
        doc.save()
        form.save_m2m()
        TimelineEvent.objects.create(
            proyecto=proyecto,
            actor=request.user,
            tipo='documento',
            titulo=f'Documento: {doc.titulo}',
            detalle='Subido',
        )
        messages.success(request, 'Documento subido.')
        return redirect('proyectos:detail', pk=proyecto.pk)
    return render(request, 'documentos/upload_form.html', {'form': form, 'proyecto': proyecto})


def view_doc(request, pk):
    doc = get_object_or_404(Documento.objects.select_related('proyecto', 'categoria'), pk=pk)
    if not doc.user_can_access(request.user):
        raise PermissionDenied
    DocumentoAudit.objects.create(documento=doc, user=request.user, action=DocumentoAudit.VIEW)
    if not doc.archivo:
        raise Http404
    try:
        content_type, _ = mimetypes.guess_type(doc.archivo.name)
        return FileResponse(
            doc.archivo.open('rb'),
            content_type=content_type or 'application/octet-stream',
            filename=os.path.basename(doc.archivo.name),
        )
    except FileNotFoundError:
        return redirect(doc.archivo.url)


def download(request, pk):
    doc = get_object_or_404(Documento.objects.select_related('proyecto', 'categoria'), pk=pk)
    if not doc.user_can_access(request.user):
        raise PermissionDenied
    DocumentoAudit.objects.create(documento=doc, user=request.user, action=DocumentoAudit.DOWNLOAD)
    if not doc.archivo:
        raise Http404
    return FileResponse(doc.archivo.open('rb'), as_attachment=True, filename=os.path.basename(doc.archivo.name))


@require_http_methods(['GET', 'POST'])
def edit_acl(request, pk):
    doc = get_object_or_404(Documento.objects.select_related('proyecto'), pk=pk)
    if not _can_manage_doc(request.user, doc):
        raise PermissionDenied
    form = DocumentoAclForm(request.POST or None, instance=doc)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Permisos actualizados.')
        return redirect('proyectos:detail', pk=doc.proyecto_id)
    return render(request, 'documentos/acl_form.html', {'form': form, 'documento': doc})


@require_POST
def delete(request, pk):
    doc = get_object_or_404(Documento.objects.select_related('proyecto'), pk=pk)
    if not _can_manage_doc(request.user, doc):
        raise PermissionDenied
    proyecto_id = doc.proyecto_id
    doc.delete()
    messages.success(request, 'Documento eliminado.')
    return redirect('proyectos:detail', pk=proyecto_id)
