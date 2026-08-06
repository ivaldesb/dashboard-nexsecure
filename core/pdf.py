"""PDF helpers for presupuestos and project reports."""
from io import BytesIO

from django.http import HttpResponse
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas


def _pdf_response(filename: str, build) -> HttpResponse:
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    build(c)
    c.save()
    pdf = buffer.getvalue()
    buffer.close()
    resp = HttpResponse(pdf, content_type='application/pdf')
    resp['Content-Disposition'] = f'inline; filename="{filename}"'
    return resp


def _is_cliente(user) -> bool:
    if user is None or not getattr(user, 'is_authenticated', False):
        return False
    if user.is_system_admin():
        return False
    return hasattr(user, 'cliente_profile') and user.cliente_profile is not None


def render_presupuesto_pdf(presupuesto, viewer_user=None) -> HttpResponse:
    hide_internal = _is_cliente(viewer_user)

    def build(c):
        y = 26 * cm
        c.setFont('Helvetica-Bold', 14)
        c.drawString(2 * cm, y, f'Presupuesto: {presupuesto.titulo}')
        y -= 1 * cm
        c.setFont('Helvetica', 10)
        c.drawString(2 * cm, y, f'Proyecto: {presupuesto.proyecto.nombre}')
        y -= 0.6 * cm
        c.drawString(2 * cm, y, f'Estado: {presupuesto.get_estado_display()}')
        y -= 1 * cm
        c.setFont('Helvetica-Bold', 10)
        if hide_internal:
            c.drawString(2 * cm, y, 'Ítem')
            c.drawString(12 * cm, y, 'Cant.')
            c.drawString(15 * cm, y, 'Neto')
        else:
            c.drawString(2 * cm, y, 'Ítem')
            c.drawString(10 * cm, y, 'Cant.')
            c.drawString(12 * cm, y, 'P.Unit')
            c.drawString(15 * cm, y, 'Subtotal')
        y -= 0.5 * cm
        c.setFont('Helvetica', 9)
        total = 0
        for item in presupuesto.items.all():
            if y < 2 * cm:
                c.showPage()
                y = 26 * cm
                c.setFont('Helvetica', 9)
            desc = getattr(item, 'descripcion', None) or getattr(item, 'referencia', '') or str(item)
            cant = item.cantidad
            if hide_internal:
                neto = getattr(item, 'neto_unidad', None)
                if neto is None:
                    neto = item.precio_unitario
                line_total = cant * neto
                c.drawString(2 * cm, y, str(desc)[:50])
                c.drawRightString(13.5 * cm, y, f'{cant}')
                c.drawRightString(17.5 * cm, y, f'{line_total:,.0f}')
            else:
                sub = item.subtotal
                c.drawString(2 * cm, y, str(desc)[:40])
                c.drawRightString(11.5 * cm, y, f'{cant}')
                c.drawRightString(14 * cm, y, f'{item.precio_unitario:,.0f}')
                c.drawRightString(17.5 * cm, y, f'{sub:,.0f}')
                line_total = sub
            total += line_total
            y -= 0.45 * cm
        y -= 0.4 * cm
        c.setFont('Helvetica-Bold', 11)
        c.drawString(2 * cm, y, f'Total: ${total:,.0f}')

    return _pdf_response(f'presupuesto_{presupuesto.pk}.pdf', build)


def render_proyecto_reporte_pdf(proyecto, viewer_user=None) -> HttpResponse:
    hide_internal = _is_cliente(viewer_user)

    def build(c):
        y = 26 * cm
        c.setFont('Helvetica-Bold', 14)
        c.drawString(2 * cm, y, f'Reporte: {proyecto.nombre}')
        y -= 0.8 * cm
        c.setFont('Helvetica', 10)
        codigo = getattr(proyecto, 'codigo', None) or proyecto.pk
        c.drawString(2 * cm, y, f'Código: {codigo}')
        y -= 0.5 * cm
        c.drawString(2 * cm, y, f'Estado: {proyecto.estado.nombre}')
        y -= 0.5 * cm
        clientes = ', '.join(cl.display_name for cl in proyecto.clientes.all()) or '—'
        c.drawString(2 * cm, y, f'Clientes: {clientes[:80]}')
        y -= 1 * cm
        c.setFont('Helvetica-Bold', 11)
        c.drawString(2 * cm, y, 'Presupuestos')
        y -= 0.5 * cm
        c.setFont('Helvetica', 9)
        for p in proyecto.presupuestos.all():
            if y < 2 * cm:
                c.showPage()
                y = 26 * cm
            total = p.total_items
            line = f'{p.titulo} — {p.get_estado_display()}'
            if not hide_internal:
                line += f' — ${total:,.0f}'
            else:
                line += f' — ${total:,.0f}'
            c.drawString(2 * cm, y, line[:90])
            y -= 0.4 * cm
        y -= 0.5 * cm
        c.setFont('Helvetica-Bold', 11)
        c.drawString(2 * cm, y, 'Incidencias')
        y -= 0.5 * cm
        c.setFont('Helvetica', 9)
        for inc in proyecto.incidencias.all()[:20]:
            if y < 2 * cm:
                c.showPage()
                y = 26 * cm
            c.drawString(2 * cm, y, f'{inc.titulo} [{inc.estado}]'[:90])
            y -= 0.4 * cm
        if hide_internal:
            y -= 0.6 * cm
            c.setFont('Helvetica-Oblique', 8)
            c.drawString(2 * cm, y, 'Documento para cliente: costos internos omitidos.')

    return _pdf_response(f'proyecto_{proyecto.pk}.pdf', build)
