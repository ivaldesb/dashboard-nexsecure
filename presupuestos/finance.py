"""Cálculo financiero de presupuesto (port de legacy/app.py ~877-1018)."""

from decimal import Decimal

from django.conf import settings

from .models import Gasto, PagoEmpleado, ZERO, HUNDRED

ONE = Decimal('1')


def _d(value):
    if value is None:
        return ZERO
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def _user_label(user):
    if user is None:
        return ''
    full = (user.get_full_name() or '').strip()
    return full or user.username or user.email or str(user.pk)


def _round_money(value):
    # ponytail: round() de legacy (float) → quantize a peso entero
    return _d(value).quantize(ONE)


def resumen_financiero(presupuesto):
    """Devuelve dict serializable con totales, distribución y verificaciones."""
    tot = presupuesto.totales_cotizacion()
    sub_neto = tot['sub_neto']
    descuento = tot['descuento']
    neto = tot['neto']
    iva = tot['iva']
    total_proyecto = tot['total']
    pct_empresa = _d(presupuesto.pct_empresa)

    gastos = list(presupuesto.gastos.all())
    total_gastos = sum((_d(g.monto) for g in gastos), ZERO)
    utilidad_real = neto - total_gastos

    gastos_empresa = sum((_d(g.monto) for g in gastos if g.pagado_por_tipo == Gasto.PAGADO_EMPRESA), ZERO)
    gastos_caja = sum((_d(g.monto) for g in gastos if g.pagado_por_tipo == Gasto.PAGADO_CAJA), ZERO)

    gastos_por_empleado = {}
    for g in gastos:
        if g.pagado_por_tipo == Gasto.PAGADO_USUARIO and g.pagado_por_id:
            gastos_por_empleado[g.pagado_por_id] = gastos_por_empleado.get(g.pagado_por_id, ZERO) + _d(g.monto)

    utilidad_empresa = _round_money(utilidad_real * pct_empresa / HUNDRED)

    pagos_qs = (
        presupuesto.pagos_empleados.select_related('empleado', 'quien_anticipo').all()
    )
    pagos = []
    for p in pagos_qs:
        pct = _d(p.porcentaje_pago)
        anticipo = _d(p.anticipo)
        utilidad_empleado = _round_money(utilidad_real * pct / HUNDRED)
        gastos_pagados = gastos_por_empleado.get(p.empleado_id, ZERO)
        pagos.append({
            'id': p.pk,
            'empleado_id': p.empleado_id,
            'empleado_nombre': _user_label(p.empleado),
            'porcentaje_pago': pct,
            'anticipo': anticipo,
            'quien_anticipo_tipo': p.quien_anticipo_tipo,
            'quien_anticipo_id': p.quien_anticipo_id,
            'quien_anticipo_nombre': _user_label(p.quien_anticipo) if p.quien_anticipo_id else '',
            'pago_por_utilidad': utilidad_empleado,
            'utilidad_empleado': utilidad_empleado,
            'gastos_pagados': gastos_pagados,
            'pago_total': ZERO,  # se completa abajo
        })

    total_utilidad_empleados = sum((p['utilidad_empleado'] for p in pagos), ZERO)
    utilidad_distribuida = utilidad_empresa + total_utilidad_empleados
    delta_utilidad = utilidad_real - utilidad_distribuida
    if abs(delta_utilidad) > Decimal('0.01') and pagos:
        pagos[-1]['utilidad_empleado'] += delta_utilidad
        pagos[-1]['pago_por_utilidad'] += delta_utilidad
        utilidad_distribuida = utilidad_real

    anticipos_a_devolver = {}
    anticipos_empresa = ZERO
    anticipos_caja = ZERO

    for p in pagos:
        anticipo = p['anticipo']
        p['pago_total'] = p['utilidad_empleado'] + p['gastos_pagados'] - anticipo
        if anticipo <= ZERO:
            continue
        tipo = p['quien_anticipo_tipo']
        if tipo == PagoEmpleado.QUIEN_EMPRESA:
            anticipos_empresa += anticipo
        elif tipo == PagoEmpleado.QUIEN_USUARIO and p['quien_anticipo_id']:
            uid = p['quien_anticipo_id']
            if uid not in anticipos_a_devolver:
                anticipos_a_devolver[uid] = {
                    'nombre': p['quien_anticipo_nombre'] or 'Usuario',
                    'total': ZERO,
                }
            anticipos_a_devolver[uid]['total'] += anticipo
        else:
            anticipos_caja += anticipo

    reembolso_empresa = gastos_empresa
    recibe_empresa = utilidad_empresa + reembolso_empresa + anticipos_empresa
    total_pagos_empleados = sum((p['pago_total'] for p in pagos), ZERO)

    total_porcentaje_empleados = sum((p['porcentaje_pago'] for p in pagos), ZERO)
    total_porcentaje_distribucion = total_porcentaje_empleados + pct_empresa
    total_anticipos_a_devolver = sum((info['total'] for info in anticipos_a_devolver.values()), ZERO)

    verificacion_neto_valor = utilidad_real + total_gastos
    verificacion_neto_ok = abs(verificacion_neto_valor - neto) < Decimal('0.01')
    verificacion_utilidad_ok = abs(utilidad_real - utilidad_distribuida) < Decimal('0.01')

    neto_check = recibe_empresa + total_pagos_empleados + gastos_caja + anticipos_caja
    diferencia_verificacion_neto = neto - neto_check
    verificacion_final_ok = abs(diferencia_verificacion_neto) < Decimal('0.01')
    if abs(diferencia_verificacion_neto) > Decimal('0.01'):
        recibe_empresa += diferencia_verificacion_neto
        verificacion_final_ok = True

    verificacion_porcentajes_ok = abs(total_porcentaje_distribucion - HUNDRED) < Decimal('0.01')

    facturas = list(presupuesto.facturas.all())
    iva_credito = sum((_d(f.monto_iva) for f in facturas), ZERO)
    iva_compra = iva
    iva_a_pagar = iva_compra - iva_credito

    secundarios = list(
        presupuesto.proyecto.presupuestos.exclude(pk=presupuesto.pk).filter(
            tipo=presupuesto.ADICIONAL,
        )
    )

    return {
        'sub_neto': sub_neto,
        'descuento_pct': tot['descuento_pct'],
        'descuento': descuento,
        'neto': neto,
        'iva': iva,
        'iva_pct': tot['iva_pct'],
        'total_proyecto': total_proyecto,
        'total_gastos': total_gastos,
        'utilidad_real': utilidad_real,
        'gastos_empresa': gastos_empresa,
        'gastos_caja': gastos_caja,
        'gastos_por_empleado': gastos_por_empleado,
        'pct_empresa': pct_empresa,
        'utilidad_empresa': utilidad_empresa,
        'reembolso_empresa': reembolso_empresa,
        'anticipos_empresa': anticipos_empresa,
        'anticipos_caja': anticipos_caja,
        'anticipos_a_devolver': anticipos_a_devolver,
        'total_anticipos_a_devolver': total_anticipos_a_devolver,
        'recibe_empresa': recibe_empresa,
        'diferencia': recibe_empresa,
        'total_pagos_empleados': total_pagos_empleados,
        'pagos': pagos,
        'total_porcentaje_empleados': total_porcentaje_empleados,
        'total_porcentaje_distribucion': total_porcentaje_distribucion,
        'utilidad_distribuida': utilidad_distribuida,
        'verificacion_neto_valor': verificacion_neto_valor,
        'verificacion_neto_ok': verificacion_neto_ok,
        'verificacion_utilidad_ok': verificacion_utilidad_ok,
        'verificacion_final_ok': verificacion_final_ok,
        'verificacion_porcentajes_ok': verificacion_porcentajes_ok,
        'neto_check': neto_check,
        'diferencia_verificacion_neto': diferencia_verificacion_neto,
        'iva_credito': iva_credito,
        'iva_compra': iva_compra,
        'iva_a_pagar': iva_a_pagar,
        'diferencia_iva': iva_a_pagar,
        'secundarios': secundarios,
        'iva_rate': Decimal(str(getattr(settings, 'FINANZAS_IVA_RATE', '0.19'))),
    }
