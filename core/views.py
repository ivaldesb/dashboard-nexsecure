from django.shortcuts import render


def dashboard(request):
    from proyectos.models import Proyecto, proyectos_visibles_para
    from incidencias.models import Incidencia
    from calendario.models import Evento

    proyectos = proyectos_visibles_para(request.user)[:8]
    incidencias = Incidencia.objects.filter(proyecto__in=proyectos_visibles_para(request.user)).order_by('-created_at')[:8]
    if request.user.is_system_admin():
        eventos = Evento.objects.order_by('inicio')[:8]
    else:
        eventos = Evento.objects.filter(asignados=request.user).order_by('inicio')[:8]

    return render(
        request,
        'core/dashboard.html',
        {
            'proyectos': proyectos,
            'incidencias': incidencias,
            'eventos': eventos,
            'total_proyectos': proyectos_visibles_para(request.user).count(),
        },
    )
