"""Helpers para formularios en modal (misma pestaña)."""
from django.http import JsonResponse
from django.shortcuts import redirect, render


def is_modal(request) -> bool:
    if request.GET.get('modal') == '1' or request.POST.get('modal') == '1':
        return True
    return request.headers.get('X-NX-Modal') == '1'


def modal_form(request, *, title, form, action_url, extra=None, multipart=False, form_template=None):
    """GET/POST inválido: HTML del form para el modal (o página completa si no es modal)."""
    ctx = {
        'title': title,
        'form': form,
        'action_url': action_url,
        'multipart': multipart,
        'modal': is_modal(request),
    }
    if extra:
        ctx.update(extra)
    template = form_template or 'includes/modal_form.html'
    if is_modal(request):
        return render(request, template, ctx)
    # Página completa: envolver con base
    return render(request, 'includes/modal_form_page.html', ctx)


def modal_success(request, url):
    """Tras guardar: JSON para el JS del modal, o redirect clásico."""
    if is_modal(request):
        return JsonResponse({'ok': True, 'redirect': url})
    return redirect(url)
