from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, g, send_file
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import User, create_users_table, Cliente, create_clientes_table, Proyecto, create_proyectos_table, create_proyecto_asignaciones_table, create_proyecto_comentarios_table, create_proyecto_cambios_table, create_presupuestos_table, create_presupuesto_items_table, create_presupuesto_costos_table, create_presupuesto_facturas_table, create_presupuesto_gastos_table, create_presupuesto_pagos_empleados_table, create_activos_table, create_incidencias_table, create_incidencia_comentarios_table, create_proyecto_mantenimiento_config_table, create_proyecto_mantenimiento_visitas_table, create_proyecto_mantenimiento_fotos_table, create_proyecto_mantenimiento_visitas_activos_table, create_proyecto_mantenimiento_checklist_items_table, create_proyecto_mantenimiento_checklist_respuestas_table, create_proyecto_instalacion_sesiones_table, create_proyecto_instalacion_checklist_items_table, create_proyecto_instalacion_checklist_completados_table, create_proyecto_documentos_table, create_proyecto_valoraciones_table, create_user_logs_table, create_all_marketing_tables, Comentario, CambioProyecto, Presupuesto, PresupuestoItem, PresupuestoCosto, PresupuestoGasto, PresupuestoFactura, PresupuestoPagoEmpleado, Activo, Incidencia, ComentarioIncidencia, MantenimientoConfig, MantenimientoVisita, MantenimientoFoto, MantenimientoChecklistItem, MantenimientoChecklistRespuesta, InstalacionSesion, InstalacionChecklistItem, InstalacionChecklistCompletado, DocumentoProyecto, ProyectoValoracion, UserLog, get_db_connection
import os
import json
from datetime import datetime
from io import BytesIO
try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Inicializar tablas
create_users_table()
create_clientes_table()
create_proyectos_table()
create_proyecto_asignaciones_table()
create_proyecto_comentarios_table()
create_proyecto_cambios_table()
create_presupuestos_table()
create_presupuesto_items_table()
create_presupuesto_costos_table()
create_presupuesto_facturas_table()
create_presupuesto_gastos_table()
create_presupuesto_pagos_empleados_table()
create_activos_table()
create_incidencias_table()
create_incidencia_comentarios_table()
create_proyecto_mantenimiento_config_table()
create_proyecto_mantenimiento_visitas_table()
create_proyecto_mantenimiento_fotos_table()
create_proyecto_mantenimiento_visitas_activos_table()
create_proyecto_mantenimiento_checklist_items_table()
create_proyecto_mantenimiento_checklist_respuestas_table()
create_proyecto_instalacion_sesiones_table()
create_proyecto_instalacion_checklist_items_table()
create_proyecto_instalacion_checklist_completados_table()
create_proyecto_documentos_table()
create_proyecto_valoraciones_table()
create_user_logs_table()
create_all_marketing_tables()

# Configuración de Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"
login_manager.login_message = "Por favor, inicia sesión para acceder a esta página."
login_manager.login_message_category = "warning"

@login_manager.user_loader
def load_user(user_id):
    # Si el ID tiene el prefijo 'cliente_', es un cliente
    if user_id.startswith('cliente_'):
        cliente_id = int(user_id.replace('cliente_', ''))
        return Cliente.get_by_id(cliente_id)
    else:
        # Es un usuario normal
        return User.get_by_id(int(user_id))

# Funciones helper
def is_user(user):
    """Verifica si el usuario es un usuario normal (no cliente)"""
    if not user or not user.is_authenticated:
        return False
    return not hasattr(user, 'tipo_cliente')

def is_cliente(user):
    """Verifica si el usuario es un cliente"""
    if not user or not user.is_authenticated:
        return False
    return hasattr(user, 'tipo_cliente')

def is_admin(user):
    """Verifica si el usuario es administrador"""
    if not user or not user.is_authenticated:
        return False
    if hasattr(user, 'is_admin'):
        return user.is_admin
    return False

# Función helper para registrar logs
def log_user_action(accion, descripcion=None, datos_adicionales=None):
    """Registra una acción del usuario en los logs"""
    if current_user and current_user.is_authenticated:
        usuario_id = current_user.id
        usuario_tipo = 'cliente' if is_cliente(current_user) else 'user'
        
        # Obtener nombre del usuario
        usuario_nombre = 'Usuario desconocido'
        if usuario_tipo == 'user':
            if hasattr(current_user, 'nombre') and hasattr(current_user, 'apellido'):
                usuario_nombre = f"{current_user.nombre} {current_user.apellido}".strip() or current_user.username or current_user.email
            else:
                usuario_nombre = current_user.username or current_user.email
        else:
            if hasattr(current_user, 'tipo_cliente') and current_user.tipo_cliente == 'empresa':
                usuario_nombre = current_user.nombre_empresa or f"{current_user.nombre} {current_user.apellido}".strip()
            else:
                usuario_nombre = f"{current_user.nombre} {current_user.apellido}".strip()
        
        # Obtener información de la solicitud
        ruta = request.path
        metodo = request.method
        ip_address = request.remote_addr
        user_agent = request.headers.get('User-Agent', '')
        
        # Registrar en los logs
        try:
            UserLog.create(
                usuario_id=usuario_id,
                usuario_tipo=usuario_tipo,
                usuario_nombre=usuario_nombre,
                accion=accion,
                descripcion=descripcion,
                ruta=ruta,
                metodo=metodo,
                ip_address=ip_address,
                user_agent=user_agent,
                datos_adicionales=datos_adicionales
            )
        except Exception as e:
            print(f"Error al registrar log: {e}")

# Middleware para registrar todas las acciones (comentado para evitar demasiados logs)
# Se registrarán acciones específicas en cada ruta importante
# @app.before_request
# def before_request():
#     if current_user and current_user.is_authenticated:
#         if request.method == 'GET' and request.endpoint and request.endpoint != 'static':
#             if request.endpoint in ['dashboard', 'projects', 'project_detail', 'users', 'clientes', 'logs']:
#                 accion = f"Acceso a {request.endpoint}"
#                 log_user_action(accion, f"Usuario accedió a {request.path}")

@app.route('/')
def index():
    if current_user.is_authenticated:
        if is_cliente(current_user):
            return redirect(url_for('projects'))
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    next_page = request.args.get('next')
    if request.method == 'POST':
        login_input = request.form.get('uiv-input-name')
        password = request.form.get('uiv-input-password')
        
        # Primero intentar buscar como usuario normal
        user = User.get_by_email(login_input)
        if not user:
            user = User.get_by_username(login_input)
        
        if user:
            # Es un usuario normal
            if not user.is_active:
                flash("El usuario se encuentra deshabilitado. Si crees que es un error, escríbenos a soporte@nexsecure.cl", "danger")
            elif user.check_password(password):
                login_user(user)
                user.update_last_login()
                log_user_action("Login", f"Usuario {user.username or user.email} inició sesión")
                return redirect(next_page or url_for('dashboard'))
            else:
                flash("Usuario o contraseña incorrectos", "danger")
        else:
            # Intentar buscar como cliente
            cliente = Cliente.get_by_correo(login_input)
            if not cliente:
                # Intentar buscar por RUT
                cliente = Cliente.get_by_rut(login_input)
            
            if cliente:
                # Es un cliente - la contraseña debe ser el RUT
                if not cliente.is_active:
                    flash("El cliente se encuentra deshabilitado. Si crees que es un error, escríbenos a soporte@nexsecure.cl", "danger")
                elif cliente.check_rut_password(password):
                    login_user(cliente)
                    cliente.update_last_login()
                    cliente_nombre = cliente.nombre_empresa if cliente.tipo_cliente == 'empresa' else f"{cliente.nombre} {cliente.apellido}"
                    log_user_action("Login", f"Cliente {cliente_nombre} inició sesión")
                    # Redirigir a presupuestos para clientes
                    return redirect(next_page or url_for('projects'))
                else:
                    flash("Correo/RUT o contraseña incorrectos", "danger")
            else:
                flash("Usuario o contraseña incorrectos", "danger")
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('uiv-input-name')
        password = request.form.get('uiv-input-password')
        nombre = request.form.get('nombre')
        apellido = request.form.get('apellido')
        username = request.form.get('username')
        if User.get_by_email(email):
            flash("El correo ya está registrado", "warning")
        else:
            user = User.create(email, password, nombre, apellido, username)
            if isinstance(user, User):
                flash("Usuario registrado correctamente. Ahora puedes iniciar sesión.", "success")
                return redirect(url_for('login'))
            else:
                flash(f"Error al registrar usuario: {user}", "danger")
    return render_template('login.html', register=True)

@app.route('/dashboard')
@login_required
def dashboard():
    from datetime import datetime
    return render_template('dashboard.html', now=datetime.now())

@app.route('/users')
@login_required
def users():
    from datetime import datetime
    log_user_action("Acceso Usuarios", "Usuario accedió a la sección de usuarios")
    all_users = User.get_all()
    return render_template('users.html', now=datetime.now(), users=all_users)

@app.route('/clientes')
@login_required
def clientes():
    from datetime import datetime
    log_user_action("Acceso Clientes", "Usuario accedió a la sección de clientes")
    all_clientes = Cliente.get_all()
    clientes_dict = [c.to_dict() for c in all_clientes]
    # Obtener usuarios para el selector de referidor
    all_users = User.get_all()
    users_dict = [u.to_dict() for u in all_users]
    return render_template('clientes.html', now=datetime.now(), clientes=clientes_dict, users=users_dict)

@app.route('/project_detail')
@login_required
def project_detail():
    from datetime import datetime
    proyecto_id = request.args.get('id', type=int)
    
    if not proyecto_id:
        flash('Proyecto no especificado', 'error')
        return redirect(url_for('projects'))
    
    # Obtener el proyecto
    proyecto = Proyecto.get_by_id(proyecto_id)
    if not proyecto:
        flash('Proyecto no encontrado', 'error')
        return redirect(url_for('projects'))
    
    # Verificar permisos: el usuario debe estar asignado al proyecto o ser admin
    # Para clientes, también pueden ver si son el cliente del presupuesto
    is_admin_user = is_admin(current_user)
    tiene_acceso = False
    
    if is_admin_user:
        tiene_acceso = True
    else:
        # Verificar si el usuario está asignado al proyecto usando la tabla de asignaciones directamente
        conn = get_db_connection()
        cur = conn.cursor()
        if is_cliente(current_user):
            # Verificar si está asignado como parte del equipo
            cur.execute("""
                SELECT COUNT(*) FROM proyecto_asignaciones 
                WHERE proyecto_id = %s AND asignado_id = %s AND tipo_asignado = 'cliente'
            """, (proyecto_id, current_user.id))
            count_asignado = cur.fetchone()[0]
            
            # Verificar si es el cliente del presupuesto
            cur.execute("""
                SELECT COUNT(*) FROM presupuestos 
                WHERE proyecto_id = %s AND cliente_id = %s
            """, (proyecto_id, current_user.id))
            count_presupuesto = cur.fetchone()[0]
            
            tiene_acceso = count_asignado > 0 or count_presupuesto > 0
        else:
            cur.execute("""
                SELECT COUNT(*) FROM proyecto_asignaciones 
                WHERE proyecto_id = %s AND asignado_id = %s AND tipo_asignado = 'user'
            """, (proyecto_id, current_user.id))
            count = cur.fetchone()[0]
            tiene_acceso = count > 0
        cur.close()
        conn.close()
    
    if not tiene_acceso:
        flash('No tienes permisos para ver este proyecto', 'error')
        return redirect(url_for('projects'))
    
    # Registrar acceso al proyecto
    if is_cliente(current_user):
        cliente_nombre = current_user.nombre_empresa if current_user.tipo_cliente == 'empresa' else f"{current_user.nombre} {current_user.apellido}"
        log_user_action("Revisar Proyecto", f"Cliente '{cliente_nombre}' revisó el proyecto '{proyecto.nombre}'", {'proyecto_id': proyecto_id, 'proyecto_nombre': proyecto.nombre, 'cliente_id': current_user.id})
    else:
        log_user_action("Acceso Detalle Proyecto", f"Usuario accedió al detalle del proyecto '{proyecto.nombre}'", {'proyecto_id': proyecto_id, 'proyecto_nombre': proyecto.nombre})
    
    # Obtener asignados con información completa
    asignados = proyecto.get_asignados()
    
    # Obtener comentarios del proyecto (incluir eliminados solo si es admin)
    comentarios = Comentario.get_by_proyecto(proyecto_id, include_deleted=is_admin_user)
    comentarios_dict = [c.to_dict() for c in comentarios]
    
    # Obtener cambios recientes del proyecto (para mostrar en sidebar)
    cambios = CambioProyecto.get_by_proyecto(proyecto_id, limit=10)
    cambios_dict = [c.to_dict() for c in cambios]
    
    # Obtener TODOS los cambios del proyecto para la línea de tiempo
    cambios_timeline = CambioProyecto.get_by_proyecto(proyecto_id, limit=None)
    cambios_timeline_dict = [c.to_dict() for c in cambios_timeline]
    
    # Obtener presupuesto principal del proyecto (solo principal para la pestaña principal)
    presupuesto = Presupuesto.get_by_proyecto(proyecto_id)
    presupuesto_dict = None
    items_dict = []
    cliente_info = None
    pagos_empleados_dict = []
    total_items_presupuesto = 0
    
    # Obtener todos los presupuestos secundarios del proyecto
    todos_presupuestos = Presupuesto.get_all_by_proyecto(proyecto_id)
    presupuestos_secundarios = [p for p in todos_presupuestos if p.tipo_presupuesto == 'secundario']
    
    # Obtener incidencias y visitas para mostrar información de vínculos
    incidencias = Incidencia.get_by_proyecto(proyecto_id)
    incidencias_dict = {i.id: i.to_dict() for i in incidencias}
    
    visitas_mantenimiento = MantenimientoVisita.get_by_proyecto(proyecto_id)
    visitas_dict = {}
    for visita in visitas_mantenimiento:
        visitas_dict[visita.id] = {
            'id': visita.id,
            'fecha_visita': visita.fecha_visita.strftime('%d-%m-%Y') if visita.fecha_visita else '',
            'tipo_visita': visita.tipo_visita,
            'comentarios': visita.comentarios
        }
    
    # Enriquecer presupuestos secundarios con información de vínculos e items
    presupuestos_secundarios_dict = []
    pendientes_aprobacion = 0
    pendientes_pago = 0
    
    for presup_sec in presupuestos_secundarios:
        presup_dict = presup_sec.to_dict()
        
        # Agregar información de vínculo
        if presup_sec.incidencia_id and presup_sec.incidencia_id in incidencias_dict:
            presup_dict['incidencia_info'] = incidencias_dict[presup_sec.incidencia_id]
        if presup_sec.visita_mantenimiento_id and presup_sec.visita_mantenimiento_id in visitas_dict:
            presup_dict['visita_info'] = visitas_dict[presup_sec.visita_mantenimiento_id]
        
        # Obtener items del presupuesto secundario
        items_sec = PresupuestoItem.get_by_presupuesto(presup_sec.id)
        presup_dict['presupuesto_items'] = [item.to_dict() for item in items_sec]
        
        # Calcular totales
        subtotal = sum(item.importe_total for item in items_sec)
        descuento_porcentaje = presup_sec.descuento or 0
        descuento_monto = subtotal * (descuento_porcentaje / 100)
        neto = subtotal - descuento_monto
        iva_porcentaje = presup_sec.iva or 19
        iva_monto = neto * (iva_porcentaje / 100)
        total = neto + iva_monto
        
        presup_dict['subtotal'] = subtotal
        presup_dict['descuento_porcentaje'] = descuento_porcentaje
        presup_dict['descuento_monto'] = descuento_monto
        presup_dict['neto'] = neto
        presup_dict['iva_porcentaje'] = iva_porcentaje
        presup_dict['iva_monto'] = iva_monto
        presup_dict['total'] = total
        
        # Contar pendientes
        if presup_sec.estado_presupuesto == 'pendiente_aprobacion':
            pendientes_aprobacion += 1
        elif presup_sec.estado_presupuesto == 'aprobado':
            pendientes_pago += 1
        
        presupuestos_secundarios_dict.append(presup_dict)
    
    if presupuesto:
        presupuesto_dict = presupuesto.to_dict()
        items = PresupuestoItem.get_by_presupuesto(presupuesto.id)
        items_dict = [item.to_dict() for item in items]
        total_items_presupuesto = sum(item['importe_total'] for item in items_dict)
        
        # Si el presupuesto tiene cliente_id, obtener información completa del cliente
        if presupuesto.cliente_id:
            cliente = Cliente.get_by_id(presupuesto.cliente_id)
            if cliente:
                cliente_info = cliente.to_dict()
        
        # Obtener pagos a empleados
        pagos_empleados = PresupuestoPagoEmpleado.get_by_presupuesto(presupuesto.id)
        
        # Calcular gastos pagados por cada empleado
        gastos_por_empleado = {}
        gastos = PresupuestoGasto.get_by_presupuesto(presupuesto.id)
        for gasto in gastos:
            if gasto.pagado_por_id:
                empleado_id = gasto.pagado_por_id
                if empleado_id not in gastos_por_empleado:
                    gastos_por_empleado[empleado_id] = 0
                gastos_por_empleado[empleado_id] += gasto.monto
        
        for pago in pagos_empleados:
            empleado = User.get_by_id(pago.empleado_id)
            pago_dict = pago.to_dict()
            if empleado:
                pago_dict['empleado_nombre'] = f"{empleado.nombre} {empleado.apellido}".strip() or empleado.username or empleado.email
            
            # Sumar gastos pagados por este empleado (estos se suman al pago)
            gastos_pagados = gastos_por_empleado.get(pago.empleado_id, 0)
            pago_dict['gastos_pagados'] = gastos_pagados
            
            # Obtener información de quién pagó el anticipo
            pago_dict['anticipo'] = pago.anticipo
            # Convertir -1 a 'empresa' para el template
            if pago.quien_pago_anticipo_id == -1:
                pago_dict['quien_pago_anticipo_id'] = 'empresa'
            elif pago.quien_pago_anticipo_id and pago.quien_pago_anticipo_id > 0:
                # Empleado
                pago_dict['quien_pago_anticipo_id'] = pago.quien_pago_anticipo_id
                quien_pago = User.get_by_id(pago.quien_pago_anticipo_id)
                if quien_pago:
                    pago_dict['quien_pago_anticipo_nombre'] = f"{quien_pago.nombre} {quien_pago.apellido}".strip() or quien_pago.username or quien_pago.email
            else:
                # None o 0 = Caja del Proyecto
                pago_dict['quien_pago_anticipo_id'] = None
            
            # Calcular neto del presupuesto
            descuento_monto = total_items_presupuesto * (presupuesto.descuento / 100)
            neto_presupuesto = total_items_presupuesto - descuento_monto
            
            # Calcular utilidad real del presupuesto
            gastos_presupuesto = PresupuestoGasto.get_by_presupuesto(presupuesto.id)
            total_gastos_presupuesto = sum(g.monto for g in gastos_presupuesto)
            utilidad_real_presupuesto = neto_presupuesto - total_gastos_presupuesto
            
            # Calcular pago según nueva lógica: (Utilidad Real * % trabajador) + Gastos pagados - Anticipo
            # El anticipo SÍ se descuenta del pago del empleado
            pago_por_utilidad = utilidad_real_presupuesto * (pago.porcentaje_pago / 100)
            pago_dict['pago_por_utilidad'] = pago_por_utilidad
            pago_dict['pago_total'] = pago_por_utilidad + gastos_pagados - pago_dict.get('anticipo', 0)
            
            pagos_empleados_dict.append(pago_dict)
    
    # Obtener activos del proyecto
    activos = Activo.get_by_proyecto(proyecto_id)
    activos_dict = []
    current_user_id = current_user.id if current_user and current_user.is_authenticated else None
    current_user_tipo = 'user' if is_user(current_user) else 'cliente' if is_cliente(current_user) else None
    
    for activo in activos:
        activo_dict = activo.to_dict(
            current_user_id=current_user_id,
            current_user_is_admin=is_admin_user,
            current_user_tipo=current_user_tipo
        )
        activos_dict.append(activo_dict)
    
    # Obtener incidencias del proyecto
    incidencias = Incidencia.get_by_proyecto(proyecto_id)
    incidencias_dict = []
    for incidencia in incidencias:
        incidencia_dict = incidencia.to_dict()
        # Obtener comentarios de la incidencia
        comentarios_incidencia = ComentarioIncidencia.get_by_incidencia(incidencia.id)
        incidencia_dict['comentarios'] = [c.to_dict() for c in comentarios_incidencia]
        incidencias_dict.append(incidencia_dict)
    
    # Convertir proyecto a dict con asignados
    proyecto_dict = proyecto.to_dict(include_asignados=True)
    
    # Obtener configuración de mantenimiento si el proyecto incluye mantenimiento
    mantenimiento_config = None
    mantenimiento_visitas = []
    if proyecto_dict.get('incluye_mantenimiento'):
        mantenimiento_config_obj = MantenimientoConfig.get_by_proyecto(proyecto_id)
        if mantenimiento_config_obj:
            mantenimiento_config = mantenimiento_config_obj.to_dict()
        else:
            # Crear configuración por defecto si no existe
            mantenimiento_config_obj = MantenimientoConfig.create_or_update(
                proyecto_id, 
                '1 visita mensual', 
                False, 
                None
            )
            if isinstance(mantenimiento_config_obj, MantenimientoConfig):
                mantenimiento_config = mantenimiento_config_obj.to_dict()
        
        # Obtener visitas de mantenimiento
        visitas = MantenimientoVisita.get_by_proyecto(proyecto_id)
        mantenimiento_visitas = [v.to_dict() for v in visitas]
    
    # Obtener documentos del proyecto
    documentos = DocumentoProyecto.get_by_proyecto(proyecto_id)
    documentos_dict = [d.to_dict() for d in documentos]
    
    # Obtener valoración del cliente si es cliente
    valoracion_cliente = None
    if is_cliente(current_user):
        valoracion_cliente_obj = ProyectoValoracion.get_by_cliente_proyecto(proyecto_id, current_user.id)
        if valoracion_cliente_obj:
            valoracion_cliente = valoracion_cliente_obj.to_dict()
    
    # Obtener usuarios para selector de instaladores
    usuarios = User.get_all()
    usuarios_dict = [{'id': u.id, 'nombre': f"{u.nombre} {u.apellido}".strip() or u.username or u.email} for u in usuarios]
    
    # Obtener sesiones de instalación y checklist
    sesiones_instalacion = InstalacionSesion.get_by_proyecto(proyecto_id)
    sesiones_instalacion_dict = [s.to_dict() for s in sesiones_instalacion]
    
    checklist_instalacion_items = InstalacionChecklistItem.get_by_proyecto(proyecto_id, solo_activos=True)
    checklist_instalacion_dict = [item.to_dict() for item in checklist_instalacion_items]
    
    # Calcular métricas de instalación
    total_sesiones = len(sesiones_instalacion)
    tiempo_total_minutos = sum(s.calcular_tiempo_total() for s in sesiones_instalacion)
    horas_totales = int(tiempo_total_minutos // 60)
    minutos_totales = int(tiempo_total_minutos % 60)
    
    # Items completados (contar items únicos completados en todas las sesiones)
    items_completados_ids = set()
    for sesion in sesiones_instalacion:
        completados = InstalacionChecklistCompletado.get_by_sesion(sesion.id)
        items_completados_ids.update(c.checklist_item_id for c in completados)
    total_items_completados = len(items_completados_ids)
    
    # Progreso basado en items completados vs total
    progreso_instalacion = 0
    if len(checklist_instalacion_dict) > 0:
        progreso_instalacion = round((total_items_completados / len(checklist_instalacion_dict)) * 100)
    
    return render_template('project_detail.html',
                         presupuestos_secundarios=presupuestos_secundarios_dict,
                         pendientes_aprobacion=pendientes_aprobacion,
                         pendientes_pago=pendientes_pago, 
                         now=datetime.now(), 
                         proyecto=proyecto_dict,
                         asignados=asignados,
                         comentarios=comentarios_dict,
                         cambios=cambios_dict,
                         presupuesto=presupuesto_dict,
                         presupuesto_items=items_dict,
                         cliente_info=cliente_info,
                         activos=activos_dict,
                         incidencias=incidencias_dict,
                         mantenimiento_config=mantenimiento_config,
                         mantenimiento_visitas=mantenimiento_visitas,
                         documentos=documentos_dict,
                         valoracion_cliente=valoracion_cliente,
                         is_admin_user=is_admin_user,
                         pagos_empleados=pagos_empleados_dict,
                         total_items_presupuesto=total_items_presupuesto,
                         cambios_timeline=cambios_timeline_dict,
                         usuarios=usuarios_dict,
                         sesiones_instalacion=sesiones_instalacion_dict,
                         checklist_instalacion=checklist_instalacion_dict,
                         total_sesiones_instalacion=total_sesiones,
                         tiempo_total_instalacion_minutos=tiempo_total_minutos,
                         tiempo_total_instalacion_display=f"{horas_totales}h {minutos_totales}min" if horas_totales > 0 else f"{minutos_totales}min",
                         items_completados_instalacion=total_items_completados,
                         progreso_instalacion=progreso_instalacion)

@app.route('/projects')
@login_required
def projects():
    from datetime import datetime
    # Determinar si es admin
    is_admin_user = False
    if hasattr(current_user, 'username') and current_user.username == 'Olmeiri':
        is_admin_user = True
    
    # Obtener proyectos según el tipo de usuario
    if is_cliente(current_user):
        proyectos = Proyecto.get_by_asignado(current_user.id, 'cliente', is_admin_user)
    else:
        proyectos = Proyecto.get_by_asignado(current_user.id, 'user', is_admin_user)
    
    proyectos_dict = []
    for proyecto in proyectos:
        proyecto_dict = proyecto.to_dict(include_asignados=True)
        # Obtener cliente del presupuesto si existe
        presupuesto = Presupuesto.get_by_proyecto(proyecto.id)
        if presupuesto and presupuesto.cliente_id:
            cliente = Cliente.get_by_id(presupuesto.cliente_id)
            if cliente:
                if cliente.tipo_cliente == 'empresa':
                    proyecto_dict['cliente_presupuesto'] = cliente.nombre_empresa
                else:
                    proyecto_dict['cliente_presupuesto'] = f"{cliente.nombre} {cliente.apellido}"
                proyecto_dict['cliente_presupuesto_email'] = cliente.correo
            else:
                proyecto_dict['cliente_presupuesto'] = None
                proyecto_dict['cliente_presupuesto_email'] = None
        else:
            proyecto_dict['cliente_presupuesto'] = None
            proyecto_dict['cliente_presupuesto_email'] = None
        proyectos_dict.append(proyecto_dict)
    
    return render_template('projects.html', now=datetime.now(), proyectos=proyectos_dict, is_admin_user=is_admin_user)

@app.route('/presupuestos')
@login_required
def presupuestos():
    """Lista todos los proyectos con presupuestos"""
    from datetime import datetime
    is_admin_user = is_admin(current_user)
    
    # Obtener todos los proyectos con presupuesto
    proyectos = Proyecto.get_con_presupuesto(is_admin_user)
    
    proyectos_dict = []
    for proyecto in proyectos:
        proyecto_dict = proyecto.to_dict(include_asignados=True)
        presupuesto = Presupuesto.get_by_proyecto(proyecto.id)
        if presupuesto:
            proyecto_dict['presupuesto_id'] = presupuesto.id
            proyecto_dict['numero_presupuesto'] = presupuesto.numero_presupuesto
            proyecto_dict['tipo_presupuesto'] = presupuesto.tipo_presupuesto if hasattr(presupuesto, 'tipo_presupuesto') else 'principal'
            if presupuesto.cliente_id:
                cliente = Cliente.get_by_id(presupuesto.cliente_id)
                if cliente:
                    if cliente.tipo_cliente == 'empresa':
                        proyecto_dict['cliente_presupuesto'] = cliente.nombre_empresa
                    else:
                        proyecto_dict['cliente_presupuesto'] = f"{cliente.nombre} {cliente.apellido}"
        proyectos_dict.append(proyecto_dict)
    
    return render_template('presupuestos.html', now=datetime.now(), proyectos=proyectos_dict, is_admin_user=is_admin_user)

@app.route('/presupuesto/<int:presupuesto_id>/gestion')
@login_required
def gestion_presupuesto(presupuesto_id):
    """Vista para gestionar un presupuesto específico"""
    from datetime import datetime
    is_admin_user = is_admin(current_user)
    
    # Obtener presupuesto
    presupuesto = Presupuesto.get_by_id(presupuesto_id)
    if not presupuesto:
        flash('Presupuesto no encontrado', 'error')
        return redirect(url_for('presupuestos'))
    
    # Obtener proyecto
    proyecto = Proyecto.get_by_id(presupuesto.proyecto_id)
    if not proyecto:
        flash('Proyecto no encontrado', 'error')
        return redirect(url_for('presupuestos'))
    
    # Verificar si es proyecto de mantenimiento o tiene ciclo de pago
    proyecto_dict = proyecto.to_dict()
    es_mantenimiento_o_ciclo = (
        (hasattr(proyecto, 'es_solo_mantenimiento') and proyecto.es_solo_mantenimiento) or
        (hasattr(proyecto, 'ciclo_pago_mensual') and proyecto.ciclo_pago_mensual and proyecto.ciclo_pago_mensual > 0)
    )
    
    # Obtener todos los presupuestos del proyecto (principal y secundarios)
    todos_presupuestos = Presupuesto.get_all_by_proyecto(presupuesto.proyecto_id)
    presupuestos_secundarios = [p for p in todos_presupuestos if p.tipo_presupuesto == 'secundario']
    
    # Obtener incidencias del proyecto para vincular
    incidencias = Incidencia.get_by_proyecto(presupuesto.proyecto_id)
    incidencias_dict = []
    for incidencia in incidencias:
        incidencia_dict = incidencia.to_dict()
        # Agregar información adicional útil
        incidencia_dict['display'] = f"Incidencia #{incidencia.id} - {incidencia.titulo}"
        incidencias_dict.append(incidencia_dict)
    
    # Obtener visitas de mantenimiento del proyecto para vincular
    visitas_mantenimiento = MantenimientoVisita.get_by_proyecto(presupuesto.proyecto_id)
    visitas_dict = []
    for visita in visitas_mantenimiento:
        visita_dic = {
            'id': visita.id,
            'fecha_visita': visita.fecha_visita.strftime('%d-%m-%Y') if visita.fecha_visita else '',
            'tipo_visita': visita.tipo_visita,
            'comentarios': visita.comentarios,
            'display': f"Visita {visita.tipo_visita.title()} - {visita.fecha_visita.strftime('%d-%m-%Y') if visita.fecha_visita else 'N/A'}"
        }
        visitas_dict.append(visita_dic)
    
    # Enriquecer presupuestos secundarios con información de vínculos
    for presup_sec in presupuestos_secundarios:
        if presup_sec.incidencia_id:
            incidencia_vinculada = next((i for i in incidencias if i.id == presup_sec.incidencia_id), None)
            if incidencia_vinculada:
                presup_sec.incidencia_info = incidencia_vinculada.to_dict()
        if presup_sec.visita_mantenimiento_id:
            visita_vinculada = next((v for v in visitas_mantenimiento if v.id == presup_sec.visita_mantenimiento_id), None)
            if visita_vinculada:
                presup_sec.visita_info = {
                    'id': visita_vinculada.id,
                    'fecha_visita': visita_vinculada.fecha_visita.strftime('%d-%m-%Y') if visita_vinculada.fecha_visita else '',
                    'tipo_visita': visita_vinculada.tipo_visita
                }
    
    # Obtener items del presupuesto
    items = PresupuestoItem.get_by_presupuesto(presupuesto_id)
    items_dict = []
    for item in items:
        item_dict = item.to_dict()
        # Obtener costos del item
        costo = PresupuestoCosto.get_by_item_id(item.id)
        if costo:
            item_dict['costo'] = costo.to_dict()
        items_dict.append(item_dict)
    
    # Obtener facturas/boletas
    facturas = PresupuestoFactura.get_by_presupuesto(presupuesto_id)
    facturas_dict = [f.to_dict() for f in facturas]
    
    # Verificar si es proyecto de mantenimiento o tiene ciclo de pago
    es_mantenimiento_o_ciclo = (
        (hasattr(proyecto, 'es_solo_mantenimiento') and proyecto.es_solo_mantenimiento) or
        (hasattr(proyecto, 'ciclo_pago_mensual') and proyecto.ciclo_pago_mensual and proyecto.ciclo_pago_mensual > 0)
    )
    
    # Obtener gastos
    gastos = PresupuestoGasto.get_by_presupuesto(presupuesto_id)
    gastos_dict = []
    gastos_por_mes = {}  # Para agrupar por mes cuando es mantenimiento o ciclo
    
    from datetime import datetime
    import calendar
    
    for gasto in gastos:
        gasto_dict = gasto.to_dict()
        # Agregar nombre del empleado si fue pagado por uno
        if gasto_dict.get('pagado_por_id') and gasto_dict['pagado_por_id'] != 'empresa' and gasto_dict['pagado_por_id']:
            try:
                empleado_id = int(gasto_dict['pagado_por_id'])
                empleado = User.get_by_id(empleado_id)
                if empleado:
                    gasto_dict['pagado_por_nombre'] = f"{empleado.nombre} {empleado.apellido}".strip() or empleado.username or empleado.email
            except (ValueError, TypeError):
                pass
        # Agregar información de factura si está vinculada
        if gasto_dict.get('factura_id'):
            factura = PresupuestoFactura.get_by_id(gasto_dict['factura_id'])
            if factura:
                gasto_dict['factura_info'] = {
                    'tipo': 'Factura' if factura.tipo_documento == 'factura' else 'Boleta',
                    'numero': factura.numero_documento or 'N/A',
                    'proveedor': factura.proveedor or 'N/A'
                }
        
        # Agrupar por mes si es proyecto de mantenimiento o tiene ciclo de pago
        if es_mantenimiento_o_ciclo and gasto_dict.get('fecha'):
            try:
                # Convertir fecha string a date si es necesario
                if isinstance(gasto_dict['fecha'], str):
                    fecha_obj = datetime.strptime(gasto_dict['fecha'], '%Y-%m-%d').date()
                else:
                    fecha_obj = gasto_dict['fecha']
                
                # Obtener año-mes como clave (ej: "2024-01")
                mes_clave = f"{fecha_obj.year}-{fecha_obj.month:02d}"
                mes_nombre = f"{calendar.month_name[fecha_obj.month]} {fecha_obj.year}"
                
                if mes_clave not in gastos_por_mes:
                    gastos_por_mes[mes_clave] = {
                        'mes_nombre': mes_nombre,
                        'mes_numero': fecha_obj.month,
                        'año': fecha_obj.year,
                        'gastos': [],
                        'total': 0,
                        'total_empresa': 0,
                        'total_caja': 0,
                        'total_empleados': {}
                    }
                
                gastos_por_mes[mes_clave]['gastos'].append(gasto_dict)
                gastos_por_mes[mes_clave]['total'] += gasto_dict['monto']
                
                # Clasificar por quién pagó
                pagado_por_id = gasto_dict.get('pagado_por_id')
                if pagado_por_id == 'empresa':
                    gastos_por_mes[mes_clave]['total_empresa'] += gasto_dict['monto']
                elif pagado_por_id is None:
                    gastos_por_mes[mes_clave]['total_caja'] += gasto_dict['monto']
                elif pagado_por_id:
                    try:
                        empleado_id = int(pagado_por_id)
                        if empleado_id not in gastos_por_mes[mes_clave]['total_empleados']:
                            # Obtener nombre del empleado
                            empleado_nombre = 'Empleado'
                            if gasto_dict.get('pagado_por_nombre'):
                                empleado_nombre = gasto_dict['pagado_por_nombre']
                            else:
                                empleado_obj = User.get_by_id(empleado_id)
                                if empleado_obj:
                                    empleado_nombre = f"{empleado_obj.nombre} {empleado_obj.apellido}".strip() or empleado_obj.username or empleado_obj.email
                            gastos_por_mes[mes_clave]['total_empleados'][empleado_id] = {
                                'nombre': empleado_nombre,
                                'total': 0
                            }
                        gastos_por_mes[mes_clave]['total_empleados'][empleado_id]['total'] += gasto_dict['monto']
                    except (ValueError, TypeError):
                        pass
            except (ValueError, AttributeError, TypeError):
                # Si hay error al parsear la fecha, agregarlo sin agrupar
                pass
        
        gastos_dict.append(gasto_dict)
    
    # Ordenar meses por fecha (más reciente primero)
    if gastos_por_mes:
        gastos_por_mes_ordenados = dict(sorted(gastos_por_mes.items(), key=lambda x: (x[1]['año'], x[1]['mes_numero']), reverse=True))
        gastos_por_mes = gastos_por_mes_ordenados
    
    # Obtener pagos a empleados
    pagos_empleados = PresupuestoPagoEmpleado.get_by_presupuesto(presupuesto_id)
    pagos_dict = []
    
    # Calcular gastos pagados por cada empleado
    # Solo contar gastos pagados por empleados (ID positivo), no por empresa ('empresa') ni caja del proyecto (None)
    gastos_por_empleado = {}
    for gasto in gastos_dict:
        pagado_por_id = gasto.get('pagado_por_id')
        # Solo contar si es un ID positivo (empleado), no si es 'empresa' o None (caja proyecto)
        if pagado_por_id and pagado_por_id != 'empresa':
            try:
                empleado_id = int(pagado_por_id)
                if empleado_id > 0:
                    if empleado_id not in gastos_por_empleado:
                        gastos_por_empleado[empleado_id] = 0
                    gastos_por_empleado[empleado_id] += gasto['monto']
            except (ValueError, TypeError):
                pass
    
    for pago in pagos_empleados:
        empleado = User.get_by_id(pago.empleado_id)
        pago_dict = pago.to_dict()
        if empleado:
            pago_dict['empleado_nombre'] = f"{empleado.nombre} {empleado.apellido}".strip() or empleado.username or empleado.email
        
        # Sumar gastos pagados por este empleado (estos se suman al pago)
        gastos_pagados = gastos_por_empleado.get(pago.empleado_id, 0)
        pago_dict['gastos_pagados'] = gastos_pagados
        
        # Obtener información de quién pagó el anticipo
        pago_dict['anticipo'] = pago.anticipo
        # Convertir -1 a 'empresa' para el template
        if pago.quien_pago_anticipo_id == -1:
            pago_dict['quien_pago_anticipo_id'] = 'empresa'
        elif pago.quien_pago_anticipo_id and pago.quien_pago_anticipo_id > 0:
            # Empleado
            pago_dict['quien_pago_anticipo_id'] = pago.quien_pago_anticipo_id
            quien_pago = User.get_by_id(pago.quien_pago_anticipo_id)
            if quien_pago:
                pago_dict['quien_pago_anticipo_nombre'] = f"{quien_pago.nombre} {quien_pago.apellido}".strip() or quien_pago.username or quien_pago.email
        else:
            # None o 0 = Caja del Proyecto
            pago_dict['quien_pago_anticipo_id'] = None
        
        pagos_dict.append(pago_dict)
    
    # Obtener todos los usuarios para el selector de empleados
    usuarios = User.get_all()
    usuarios_dict = [{'id': u.id, 'nombre': f"{u.nombre} {u.apellido}".strip() or u.username or u.email} for u in usuarios]
    
    # Calcular totales
    total_items = sum(item['importe_total'] for item in items_dict)
    total_gastos = sum(g['monto'] for g in gastos_dict)
    
    # Calcular neto (subtotal - descuento)
    descuento_monto = total_items * (presupuesto.descuento / 100)
    neto = total_items - descuento_monto
    
    # Calcular IVA
    iva_monto = neto * (presupuesto.iva / 100)
    
    # Calcular total proyecto (neto + IVA)
    total_proyecto = neto + iva_monto
    
    # 1) CALCULAR GASTOS
    # Calcular utilidad real (neto - gastos del proyecto)
    utilidad_real = neto - total_gastos
    
    # Clasificar gastos según quién los pagó
    gastos_pagados_empresa = sum(g['monto'] for g in gastos_dict if g.get('pagado_por_id') == 'empresa')
    # Gastos pagados por Caja del Proyecto: pagado_por_id es None
    # (en to_dict(), los gastos con pagado_por_id = None en BD se mantienen como None)
    gastos_pagados_caja = sum(g['monto'] for g in gastos_dict if g.get('pagado_por_id') is None)
    
    # 2) DISTRIBUCIÓN DE UTILIDAD REAL (sin incluir reembolsos)
    # Calcular utilidad para empresa
    utilidad_empresa = round(utilidad_real * (presupuesto.porcentaje_empresa / 100))
    
    # Calcular utilidad para cada empleado
    for pago_dict in pagos_dict:
        # Utilidad del empleado = Utilidad Real * % del empleado
        utilidad_empleado = round(utilidad_real * (pago_dict['porcentaje_pago'] / 100))
        pago_dict['pago_por_utilidad'] = utilidad_empleado
        pago_dict['utilidad_empleado'] = utilidad_empleado
    
    # Suma de utilidades distribuidas (para verificación)
    total_utilidad_empleados = sum(p['utilidad_empleado'] for p in pagos_dict)
    utilidad_distribuida = utilidad_empresa + total_utilidad_empleados
    
    # Aplicar delta de redondeo si existe
    delta_utilidad = utilidad_real - utilidad_distribuida
    if abs(delta_utilidad) > 0.01:
        # Aplicar delta al último empleado o a la empresa
        if pagos_dict:
            pagos_dict[-1]['utilidad_empleado'] += delta_utilidad
            pagos_dict[-1]['pago_por_utilidad'] += delta_utilidad
            utilidad_distribuida = utilidad_real
    
    # 3) REEMBOLSOS Y PAGOS FINALES
    # Reembolso empresa = gastos pagados por empresa
    reembolso_empresa = gastos_pagados_empresa
    
    # Calcular totales de anticipos según quién los pagó
    anticipos_a_devolver = {}
    anticipos_empresa = 0  # Sumar anticipos pagados por la empresa
    anticipos_pagados_caja = 0  # Sumar anticipos pagados por Caja del Proyecto
    
    for pago_dict in pagos_dict:
        # Reembolso del empleado = gastos pagados por el empleado
        reembolso_empleado = pago_dict.get('gastos_pagados', 0)
        anticipo = pago_dict.get('anticipo', 0)
        
        # Pago total empleado = utilidad + reembolso - anticipo
        pago_dict['pago_total'] = pago_dict['utilidad_empleado'] + reembolso_empleado - anticipo
        
        # Si hay anticipo, determinar a quién se devuelve
        if anticipo > 0:
            quien_pago_id = pago_dict.get('quien_pago_anticipo_id')
            # quien_pago_id puede ser: None (caja proyecto), -1 o 'empresa' (empresa), o ID positivo (empleado)
            if quien_pago_id == -1 or (isinstance(quien_pago_id, str) and quien_pago_id == 'empresa'):
                # Si lo pagó la empresa, se devuelve a la empresa
                anticipos_empresa += anticipo
            elif quien_pago_id and quien_pago_id != '' and quien_pago_id != 'empresa':
                # Si lo pagó otro empleado, se devuelve a ese empleado
                try:
                    quien_pago_id_int = int(quien_pago_id) if isinstance(quien_pago_id, str) else quien_pago_id
                    if quien_pago_id_int > 0:  # Solo IDs positivos son empleados
                        if quien_pago_id_int not in anticipos_a_devolver:
                            anticipos_a_devolver[quien_pago_id_int] = {
                                'nombre': pago_dict.get('quien_pago_anticipo_nombre', 'Usuario'),
                                'total': 0
                            }
                        anticipos_a_devolver[quien_pago_id_int]['total'] += anticipo
                except (ValueError, TypeError):
                    # Si no es un ID válido, se ignora
                    pass
            else:
                # Si quien_pago_id es None, 0, o vacío, significa que viene de la caja del proyecto
                # No se devuelve a nadie, pero SÍ se cuenta como salida de caja del proyecto
                anticipos_pagados_caja += anticipo
    
    # Recibe empresa = utilidad empresa + reembolso empresa + anticipos empresa
    recibe_empresa = utilidad_empresa + reembolso_empresa + anticipos_empresa
    
    # Calcular diferencia (lo que recibe la empresa)
    diferencia = recibe_empresa
    
    # Total pagos empleados
    total_pagos_empleados_final = sum(p['pago_total'] for p in pagos_dict)
    
    # Calcular totales para verificación
    total_porcentaje_empleados = sum(p['porcentaje_pago'] for p in pagos_dict)
    total_porcentaje_distribucion = total_porcentaje_empleados + presupuesto.porcentaje_empresa
    
    # Calcular total de anticipos a devolver
    total_anticipos_a_devolver = sum(info['total'] for info in anticipos_a_devolver.values())
    
    # VERIFICACIONES
    # Verificación 1: Neto debe ser igual a Utilidad Real + Gastos
    verificacion_neto_valor = utilidad_real + total_gastos
    verificacion_neto_ok = abs(verificacion_neto_valor - neto) < 0.01
    
    # Verificación 2: Utilidad Real debe ser igual a la suma de utilidades distribuidas (sin reembolsos)
    verificacion_utilidad_ok = abs(utilidad_real - utilidad_distribuida) < 0.01
    
    # Verificación 3: Neto debe ser igual a Recibe Empresa + Total Pagos Empleados + Gastos Caja + Anticipos Caja
    # Esto incluye todas las salidas de caja del proyecto
    neto_check = recibe_empresa + total_pagos_empleados_final + gastos_pagados_caja + anticipos_pagados_caja
    verificacion_final_ok = abs(neto - neto_check) < 0.01
    diferencia_verificacion_neto = neto - neto_check
    
    # Aplicar delta de redondeo al neto si existe
    if abs(diferencia_verificacion_neto) > 0.01:
        recibe_empresa += diferencia_verificacion_neto
        diferencia = recibe_empresa
        verificacion_final_ok = True
    
    # Verificación adicional: Suma de porcentajes debe ser 100%
    verificacion_porcentajes_ok = abs(total_porcentaje_distribucion - 100) < 0.01
    
    # Calcular IVA Crédito e IVA Compra
    # IVA Crédito: Suma del IVA de todas las facturas/boletas (compras)
    iva_credito = sum(f['iva'] for f in facturas_dict if f.get('iva'))
    
    # IVA Compra: IVA del presupuesto (ventas) - esto es el IVA que se cobra
    iva_compra = iva_monto
    
    # IVA a pagar real = IVA Compra - IVA Crédito
    iva_a_pagar = iva_compra - iva_credito
    
    # Diferencia de IVA (si es positivo, hay que pagar; si es negativo, hay crédito a favor)
    diferencia_iva = iva_a_pagar
    
    return render_template('gestion_presupuesto.html',
                         facturas=facturas_dict, 
                         now=datetime.now(),
                         proyecto=proyecto,
                         proyecto_dict=proyecto_dict,
                         presupuesto=presupuesto,
                         items=items_dict,
                         gastos=gastos_dict,
                         gastos_por_mes=gastos_por_mes,
                         es_mantenimiento_o_ciclo=es_mantenimiento_o_ciclo,
                         pagos_empleados=pagos_dict,
                         usuarios=usuarios_dict,
                         total_items=total_items,
                         total_gastos=total_gastos,
                         neto=neto,
                         iva_monto=iva_monto,
                         total_proyecto=total_proyecto,
                         utilidad_empresa=utilidad_empresa,
                         recibe_empresa=recibe_empresa,
                         gastos_pagados_empresa=gastos_pagados_empresa,
                         anticipos_empresa=anticipos_empresa,
                         utilidad_real=utilidad_real,
                         diferencia=diferencia,
                         descuento=presupuesto.descuento,
                         iva=presupuesto.iva,
                         porcentaje_empresa=presupuesto.porcentaje_empresa,
                         anticipos_a_devolver=anticipos_a_devolver,
                         total_porcentaje_empleados=total_porcentaje_empleados,
                         total_porcentaje_distribucion=total_porcentaje_distribucion,
                         utilidad_distribuida=utilidad_distribuida,
                         reembolso_empresa=reembolso_empresa,
                         total_pagos_empleados_final=total_pagos_empleados_final,
                         total_anticipos_a_devolver=total_anticipos_a_devolver,
                         gastos_pagados_caja=gastos_pagados_caja,
                         anticipos_pagados_caja=anticipos_pagados_caja,
                         verificacion_neto_valor=verificacion_neto_valor,
                         verificacion_neto_ok=verificacion_neto_ok,
                         verificacion_utilidad_ok=verificacion_utilidad_ok,
                         verificacion_final_ok=verificacion_final_ok,
                         verificacion_porcentajes_ok=verificacion_porcentajes_ok,
                         neto_check=neto_check,
                         diferencia_verificacion_neto=diferencia_verificacion_neto,
                         iva_credito=iva_credito,
                         iva_compra=iva_compra,
                         iva_a_pagar=iva_a_pagar,
                         diferencia_iva=diferencia_iva,
                         is_admin_user=is_admin_user,
                         presupuestos_secundarios=presupuestos_secundarios,
                         incidencias=incidencias_dict,
                         visitas_mantenimiento=visitas_dict)

@app.route('/api/presupuesto/upload-factura', methods=['POST'])
@login_required
def api_presupuesto_upload_factura():
    """API para subir y procesar facturas/boletas con OCR y Ollama"""
    from werkzeug.utils import secure_filename
    import uuid
    import json
    
    file = request.files.get('archivo')
    presupuesto_id = request.form.get('presupuesto_id', type=int)
    usar_ocr_str = request.form.get('usar_ocr', 'true')
    # Si no se envía o es None, asumir True (por defecto OCR está activo)
    if usar_ocr_str is None or usar_ocr_str == '':
        usar_ocr = True
    else:
        usar_ocr = str(usar_ocr_str).lower() in ('true', '1', 'on', 'yes')
    
    # Debug: imprimir valores recibidos
    print(f"DEBUG: usar_ocr_str = {usar_ocr_str}, usar_ocr = {usar_ocr}")
    print(f"DEBUG: tiene archivo = {file and file.filename}")
    print(f"DEBUG: neto_manual inicial = {request.form.get('neto')}")
    print(f"DEBUG: iva_manual inicial = {request.form.get('iva')}")
    print(f"DEBUG: total_manual inicial = {request.form.get('total')}")
    
    if not presupuesto_id:
        return jsonify({'status': 'error', 'message': 'presupuesto_id es requerido'}), 400
    
    # Si OCR está activo, se requiere archivo
    if usar_ocr and (not file or not file.filename):
        return jsonify({'status': 'error', 'message': 'Se requiere un archivo cuando OCR está activado'}), 400
    
    # Procesar montos manuales (con punto como separador de miles)
    def parse_chilean_number(value):
        if not value:
            return 0
        cleaned = str(value).replace('.', '').replace(' ', '')
        try:
            return int(cleaned)
        except:
            return 0
    
    tipo_documento = request.form.get('tipo_documento', 'factura')
    numero_documento = request.form.get('numero_documento')
    proveedor = request.form.get('proveedor')
    fecha_emision = request.form.get('fecha_emision')
    neto_manual = parse_chilean_number(request.form.get('neto'))
    iva_manual = parse_chilean_number(request.form.get('iva'))
    total_manual = parse_chilean_number(request.form.get('total'))
    
    texto_extraido = None
    items_extraidos = {'items': []}
    ruta_relativa = None
    filepath = None
    
    # Si hay archivo, guardarlo primero
    if file and file.filename:
        # Guardar archivo primero
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4()}_{filename}"
        upload_folder = os.path.join('static', 'uploads', 'facturas')
        os.makedirs(upload_folder, exist_ok=True)
        filepath = os.path.join(upload_folder, unique_filename)
        file.save(filepath)
        ruta_relativa = f"/static/uploads/facturas/{unique_filename}"
        
        if usar_ocr:
            try:
                # Extraer texto con OCR
                texto_extraido = extraer_texto_factura(filepath)
                
                if texto_extraido:
                    # Procesar con Ollama para extraer datos
                    items_extraidos = procesar_factura_con_ollama(texto_extraido)
                    
                    # Complementar datos manuales con datos extraídos
                    if not numero_documento:
                        numero_documento = items_extraidos.get('numero_documento') or items_extraidos.get('numero')
                    if not proveedor:
                        proveedor = items_extraidos.get('proveedor')
                    if not fecha_emision:
                        fecha_emision = items_extraidos.get('fecha')
                    if not total_manual:
                        total_manual = parse_chilean_number(items_extraidos.get('total'))
                    
                    # Si no hay total pero hay items, calcular el total desde los items
                    if not total_manual and items_extraidos.get('items'):
                        total_items = 0
                        for item in items_extraidos.get('items', []):
                            cantidad = parse_chilean_number(item.get('cantidad', 1))
                            monto = parse_chilean_number(item.get('monto', 0))
                            total_items += cantidad * monto
                        if total_items > 0:
                            total_manual = total_items
                            # Si es boleta, el total ya incluye IVA, así que no hacer nada
                            # Si es factura, el total calculado es sin IVA, así que agregar IVA después
                            # Pero por ahora, dejamos el total como está y se calculará después según tipo_documento
            except Exception as e:
                # Si falla OCR, continuar con datos manuales
                texto_extraido = None
                items_extraidos = {'items': []}
        else:
            # Sin OCR, solo guardar archivo
            texto_extraido = None
            items_extraidos = {'items': []}
    
    try:
        # Validar que tenemos datos mínimos para crear la factura
        if not usar_ocr and not file:
            # Sin OCR y sin archivo: validar que tenemos datos manuales
            if not numero_documento or not proveedor or (neto_manual == 0 and iva_manual == 0 and total_manual == 0):
                return jsonify({'status': 'error', 'message': 'Se requieren número de documento, proveedor y al menos un monto cuando OCR está desactivado y no hay archivo'}), 400
        
        # Calcular total desde items si no hay total pero hay items
        tiene_items = items_extraidos.get('items') and len(items_extraidos.get('items', [])) > 0
        if not total_manual and tiene_items:
            # Calcular total desde items
            total_items = 0
            for item in items_extraidos.get('items', []):
                cantidad = parse_chilean_number(item.get('cantidad', 1))
                monto = parse_chilean_number(item.get('monto', 0))
                total_items += cantidad * monto
            if total_items > 0:
                total_manual = total_items
        
        # Debug: imprimir estado antes de validar
        print(f"DEBUG: Antes de validar - usar_ocr = {usar_ocr}, tiene_items = {tiene_items}, total_manual = {total_manual}, neto_manual = {neto_manual}, iva_manual = {iva_manual}")
        
        # Si hay OCR activo, SIEMPRE permitir crear factura (se pueden editar después en paso 3)
        # Solo validar montos si NO hay OCR
        if not usar_ocr:
            # Sin OCR: validar que tenemos montos
            if neto_manual == 0 and iva_manual == 0 and total_manual == 0:
                print(f"DEBUG: Error - Sin OCR y sin montos")
                return jsonify({'status': 'error', 'message': 'Se requiere al menos un monto (neto, IVA o total)'}), 400
        else:
            print(f"DEBUG: OCR activo - permitiendo crear factura sin validar montos")
        
        # Calcular IVA y neto según tipo de documento (priorizar valores manuales)
        iva = 0
        neto = 0
        total = 0
        
        if neto_manual > 0 or iva_manual > 0 or total_manual > 0:
            # Usar valores manuales si están disponibles
            neto = neto_manual
            iva = iva_manual
            total = total_manual
            # Si falta alguno, calcularlo
            if total > 0 and neto == 0 and iva == 0:
                if tipo_documento == 'factura':
                    # Si es factura y solo tenemos total, asumimos que es con IVA
                    neto = round(total / 1.19)
                    iva = total - neto
                else:
                    # Boleta: total incluye IVA
                    neto = round(total / 1.19)
                    iva = total - neto
            elif neto > 0 and iva == 0 and total == 0:
                # Solo tenemos neto
                if tipo_documento == 'factura':
                    iva = round(neto * 0.19)
                    total = neto + iva
                else:
                    total = neto
                    neto = round(neto / 1.19)
                    iva = total - neto
        elif total:
            # Calcular desde total extraído
            if tipo_documento == 'factura':
                # Factura: total es sin IVA, calcular IVA
                neto = total
                iva = round(neto * 0.19)
                total = neto + iva
            else:
                # Boleta: total incluye IVA
                neto = round(total / 1.19)
                iva = total - neto
        
        # Si el total es 0 pero hay OCR activo, permitir crear factura con valores por defecto
        # (el usuario podrá editarlos en el paso 3)
        if total <= 0:
            if usar_ocr:
                # Con OCR activo, permitir crear factura con valores por defecto
                # El usuario podrá editarlos en el paso 3
                total = 0
                neto = 0
                iva = 0
            else:
                return jsonify({'status': 'error', 'message': 'El total debe ser mayor a 0'}), 400
        else:
            # Solo calcular neto e iva si el total es mayor a 0
            # Asegurar que neto e iva sean válidos
            if neto <= 0 and total > 0:
                if tipo_documento == 'boleta':
                    neto = round(total / 1.19)
                else:
                    neto = round(total / 1.19)
            if iva <= 0 and total > 0:
                iva = total - neto
        
        # Guardar factura en BD
        try:
            factura = PresupuestoFactura.create(
                presupuesto_id=presupuesto_id,
                tipo_documento=tipo_documento,
                numero_documento=numero_documento,
                proveedor=proveedor,
                fecha_emision=fecha_emision,
                total=total,
                iva=iva,
                neto=neto,
                archivo_ruta=ruta_relativa,
                texto_extraido=texto_extraido
            )
            
            if isinstance(factura, str):
                # Error al crear factura
                return jsonify({'status': 'error', 'message': f'Error al guardar factura: {factura}'}), 500
        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            print(f"Error al crear factura en BD: {str(e)}")
            print(f"Traceback: {error_trace}")
            return jsonify({'status': 'error', 'message': f'Error al guardar factura en BD: {str(e)}'}), 500
        
        # Si hay items extraídos, mostrar paso 3, sino solo guardar factura
        tiene_items = items_extraidos.get('items') and len(items_extraidos.get('items', [])) > 0
        
        try:
            factura_dict = factura.to_dict()
        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            print(f"Error al convertir factura a dict: {str(e)}")
            print(f"Traceback: {error_trace}")
            # Crear dict manualmente si to_dict falla
            factura_dict = {
                'id': factura.id,
                'presupuesto_id': factura.presupuesto_id,
                'tipo_documento': factura.tipo_documento,
                'numero_documento': factura.numero_documento,
                'proveedor': factura.proveedor,
                'fecha_emision': factura.fecha_emision.strftime('%Y-%m-%d') if factura.fecha_emision else None,
                'total': factura.total,
                'iva': factura.iva,
                'neto': factura.neto,
                'archivo_ruta': factura.archivo_ruta,
                'texto_extraido': factura.texto_extraido[:500] + '...' if factura.texto_extraido and len(factura.texto_extraido) > 500 else (factura.texto_extraido if factura.texto_extraido else '')
            }
        
        return jsonify({
            'status': 'success',
            'items': items_extraidos,
            'texto_extraido': (texto_extraido[:500] + '...' if texto_extraido and len(texto_extraido) > 500 else texto_extraido) if texto_extraido else '',
            'archivo': ruta_relativa,
            'nombre_archivo': file.filename if (file and hasattr(file, 'filename') and file.filename) else None,
            'factura_id': factura.id,
            'tiene_items': tiene_items,
            'factura_data': factura_dict
        })
    except Exception as e:
        # Eliminar archivo si hay error
        if filepath and os.path.exists(filepath):
            try:
                os.remove(filepath)
            except:
                pass
        import traceback
        error_trace = traceback.format_exc()
        print(f"Error al procesar factura: {str(e)}")
        print(f"Traceback: {error_trace}")
        return jsonify({'status': 'error', 'message': f'Error al procesar factura: {str(e)}'}), 500

def extraer_texto_factura(filepath):
    """Extrae texto de una factura usando OCR"""
    try:
        # Verificar si es PDF
        if filepath.lower().endswith('.pdf'):
            try:
                from pdf2image import convert_from_path
                import pytesseract
                
                # Convertir PDF a imágenes
                images = convert_from_path(filepath)
                texto_completo = ""
                for image in images:
                    texto = pytesseract.image_to_string(image, lang='spa')
                    texto_completo += texto + "\n"
                return texto_completo
            except Exception as e:
                if "poppler" in str(e).lower() or "page count" in str(e).lower():
                    raise Exception("Poppler no está instalado. Por favor instala Poppler para procesar PDFs. Ver REQUIREMENTS_FACTURAS.md para instrucciones.")
                else:
                    # Intentar con easyocr como alternativa
                    try:
                        import easyocr
                        reader = easyocr.Reader(['es', 'en'])
                        from pdf2image import convert_from_path
                        images = convert_from_path(filepath)
                        texto_completo = ""
                        for image in images:
                            resultados = reader.readtext(image)
                            texto = " ".join([result[1] for result in resultados])
                            texto_completo += texto + "\n"
                        return texto_completo
                    except Exception as e2:
                        raise Exception(f"Error al procesar PDF: {str(e)}. Alternativa también falló: {str(e2)}")
        else:
            # Es una imagen
            try:
                from PIL import Image
                import pytesseract
                
                image = Image.open(filepath)
                texto = pytesseract.image_to_string(image, lang='spa')
                return texto
            except ImportError:
                # Intentar con easyocr
                try:
                    import easyocr
                    reader = easyocr.Reader(['es', 'en'])
                    resultados = reader.readtext(filepath)
                    texto = " ".join([result[1] for result in resultados])
                    return texto
                except ImportError:
                    raise Exception("Se requiere instalar pytesseract o easyocr para procesar facturas")
    except Exception as e:
        # Re-lanzar el error con mensaje más claro
        if "poppler" in str(e).lower():
            raise Exception("Poppler no está instalado. Por favor instala Poppler para procesar PDFs. Ver REQUIREMENTS_FACTURAS.md para instrucciones.")
        else:
            raise

def procesar_factura_con_ollama(texto):
    """Procesa el texto extraído con Ollama para extraer items estructurados"""
    try:
        import requests
        
        # URL de Ollama (ajustar según configuración)
        ollama_url = os.getenv('OLLAMA_URL', 'http://190.100.247.39:11434/api/generate')
        model = os.getenv('OLLAMA_MODEL', 'llama3.2')
        # Timeout configurable (por defecto 300 segundos = 5 minutos)
        timeout_ollama = int(os.getenv('OLLAMA_TIMEOUT', '300'))
        
        # Limitar texto a los primeros 3000 caracteres para evitar problemas y acelerar procesamiento
        texto_limite = texto[:3000] if len(texto) > 3000 else texto
        
        prompt = f"""Analiza el siguiente texto de una factura o boleta y extrae los items de compra.

Texto de la factura:
{texto_limite}

Extrae los items y devuelve un JSON con el siguiente formato:
{{
    "items": [
        {{
            "descripcion": "descripción del item",
            "monto": 12345.67,
            "cantidad": 1,
            "unidad": "unidad" (opcional)
        }}
    ],
    "fecha": "YYYY-MM-DD" (si está disponible),
    "proveedor": "nombre del proveedor" (si está disponible),
    "total": 12345.67 (si está disponible)
}}

Solo devuelve el JSON, sin texto adicional ni markdown."""

        response = requests.post(
            ollama_url,
            json={
                'model': model,
                'prompt': prompt,
                'stream': False,
                'format': 'json'
            },
            timeout=timeout_ollama
        )
        
        if response.status_code == 200:
            resultado = response.json()
            texto_respuesta = resultado.get('response', '')
            
            # Limpiar respuesta (puede tener markdown code blocks)
            texto_respuesta = texto_respuesta.strip()
            if texto_respuesta.startswith('```'):
                # Remover markdown code blocks
                lines = texto_respuesta.split('\n')
                texto_respuesta = '\n'.join([l for l in lines if not (l.startswith('```') or l.startswith('json'))])
                texto_respuesta = texto_respuesta.strip()
            
            # Parsear JSON
            datos = json.loads(texto_respuesta)
            
            # Validar estructura
            if 'items' not in datos:
                datos['items'] = []
            
            return datos
        else:
            raise Exception(f"Error al comunicarse con Ollama: {response.status_code} - {response.text}")
    except requests.exceptions.Timeout as e:
        raise Exception(f"Timeout al procesar con Ollama (tiempo máximo: {timeout_ollama}s). El servidor puede estar sobrecargado o la conexión es lenta. Intenta nuevamente o verifica la conexión con el servidor Ollama.")
    except requests.exceptions.ConnectionError as e:
        raise Exception(f"Error de conexión con Ollama. Verifica que el servidor esté accesible en {ollama_url}")
    except requests.exceptions.RequestException as e:
        raise Exception(f"Error de conexión con Ollama: {str(e)}")
    except json.JSONDecodeError as e:
        raise Exception(f"Error al parsear respuesta de Ollama: {str(e)}")
    except Exception as e:
        raise Exception(f"Error al procesar con Ollama: {str(e)}")

@app.route('/api/presupuesto/costo', methods=['POST'])
@login_required
def api_presupuesto_costo():
    """API para crear o actualizar costos de un item"""
    data = request.get_json()
    item_id = data.get('item_id')
    if not item_id:
        return jsonify({'status': 'error', 'message': 'item_id es requerido'}), 400
    
    resultado = PresupuestoCosto.create_or_update(
        item_id=item_id,
        insumos=data.get('insumos', 0),
        maquila=data.get('maquila', 0),
        instalacion=data.get('instalacion', 0),
        desinstalacion=data.get('desinstalacion', 0),
        materiales_ferreteria=data.get('materiales_ferreteria', 0),
        gastos_generales=data.get('gastos_generales', 0),
        utilidad_porcentaje=data.get('utilidad_porcentaje', 0),
        flete=data.get('flete', 0)
    )
    
    if isinstance(resultado, str):
        return jsonify({'status': 'error', 'message': resultado}), 400
    
    # Actualizar valor_unitario del item con el valor calculado
    item = PresupuestoItem.get_by_id(item_id)
    if item:
        item.update(valor_unitario=resultado.valor_con_utilidad)
    
    return jsonify({'status': 'success', 'data': resultado.to_dict()})

@app.route('/api/presupuesto/gasto', methods=['POST'])
@login_required
def api_presupuesto_gasto():
    """API para crear un gasto"""
    data = request.get_json()
    presupuesto_id = data.get('presupuesto_id')
    if not presupuesto_id:
        return jsonify({'status': 'error', 'message': 'presupuesto_id es requerido'}), 400
    
    # Procesar pagado_por_id
    # '' o None = Caja del Proyecto (no se devuelve)
    # 'empresa' = Empresa (se devuelve a empresa, usamos -1 como marcador)
    # ID numérico = Empleado (se devuelve a ese empleado)
    pagado_por_id = data.get('pagado_por_id')
    if pagado_por_id == '' or pagado_por_id is None:
        # Caja del Proyecto - guardamos como None
        pagado_por_id = None
    elif str(pagado_por_id) == 'empresa':
        # Empresa - usamos -1 como marcador especial
        pagado_por_id = -1
    else:
        # Es un ID de empleado
        try:
            pagado_por_id = int(pagado_por_id)
        except (ValueError, TypeError):
            pagado_por_id = None
    
    resultado = PresupuestoGasto.create(
        presupuesto_id=presupuesto_id,
        descripcion=data.get('descripcion', ''),
        monto=data.get('monto', 0),
        tipo=data.get('tipo', 'general'),
        pagado_por_id=pagado_por_id,
        pagado_por_tipo=data.get('pagado_por_tipo', 'user'),
        fecha=data.get('fecha'),
        factura_id=data.get('factura_id')
    )
    
    if isinstance(resultado, str):
        return jsonify({'status': 'error', 'message': resultado}), 400
    
    return jsonify({'status': 'success', 'data': resultado.to_dict()})

@app.route('/api/presupuesto/gasto/<int:gasto_id>', methods=['GET', 'PUT', 'DELETE'])
@login_required
def api_presupuesto_gasto_get_update_delete(gasto_id):
    """API para obtener, actualizar o eliminar un gasto"""
    if request.method == 'GET':
        # Obtener gasto
        gasto = PresupuestoGasto.get_by_id(gasto_id)
        if not gasto:
            return jsonify({'status': 'error', 'message': 'Gasto no encontrado'}), 404
        return jsonify({'status': 'success', 'data': gasto.to_dict()})
    
    elif request.method == 'PUT':
        # Actualizar gasto
        try:
            data = request.get_json()
            if not data:
                return jsonify({'status': 'error', 'message': 'No se proporcionaron datos'}), 400
            
            gasto = PresupuestoGasto.get_by_id(gasto_id)
            if not gasto:
                return jsonify({'status': 'error', 'message': 'Gasto no encontrado'}), 404
            
            # Procesar pagado_por_id para actualización
            pagado_por_id = data.get('pagado_por_id')
            if pagado_por_id == '' or pagado_por_id is None:
                pagado_por_id = None
            elif str(pagado_por_id) == 'empresa':
                pagado_por_id = -1
            else:
                try:
                    pagado_por_id = int(pagado_por_id)
                except (ValueError, TypeError):
                    pagado_por_id = None
            
            # Procesar factura_id
            factura_id = data.get('factura_id')
            update_factura_id = 'factura_id' in data  # Verificar si la clave está presente
            if factura_id == '' or factura_id is None:
                factura_id = None
            else:
                try:
                    factura_id = int(factura_id) if factura_id else None
                except (ValueError, TypeError):
                    factura_id = None
            
            # Procesar monto
            monto = data.get('monto')
            if monto is not None:
                try:
                    monto = float(monto) if monto else 0
                except (ValueError, TypeError):
                    monto = 0
            
            # Verificar si pagado_por_id está presente en los datos (para permitir actualizar a None)
            update_pagado_por_id = 'pagado_por_id' in data
            
            resultado = gasto.update(
                descripcion=data.get('descripcion'),
                monto=monto,
                tipo=data.get('tipo'),
                pagado_por_id=pagado_por_id,
                pagado_por_tipo=data.get('pagado_por_tipo', 'user'),
                fecha=data.get('fecha'),
                factura_id=factura_id,
                _update_pagado_por_id=update_pagado_por_id,
                _update_factura_id=update_factura_id
            )
            
            if resultado:
                # Recargar gasto desde BD para asegurar datos actualizados
                gasto_actualizado = PresupuestoGasto.get_by_id(gasto_id)
                if gasto_actualizado:
                    return jsonify({'status': 'success', 'data': gasto_actualizado.to_dict()})
                return jsonify({'status': 'success', 'data': gasto.to_dict()})
            return jsonify({'status': 'error', 'message': 'No se pudo actualizar el gasto'}), 400
        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            print(f"Error al actualizar gasto: {str(e)}")
            print(f"Traceback: {error_trace}")
            return jsonify({'status': 'error', 'message': f'Error al actualizar el gasto: {str(e)}'}), 500
    
    else:  # DELETE
        resultado = PresupuestoGasto.delete(gasto_id)
        if resultado:
            return jsonify({'status': 'success'})
        return jsonify({'status': 'error', 'message': 'No se pudo eliminar el gasto'}), 400

@app.route('/api/presupuesto/pago-empleado', methods=['POST'])
@login_required
def api_presupuesto_pago_empleado():
    """API para crear o actualizar pago de empleado"""
    data = request.get_json()
    presupuesto_id = data.get('presupuesto_id')
    empleado_id = data.get('empleado_id')
    
    if not presupuesto_id or not empleado_id:
        return jsonify({'status': 'error', 'message': 'presupuesto_id y empleado_id son requeridos'}), 400
    
    # Procesar quien_pago_anticipo_id
    # '' o None = Caja del Proyecto (no se devuelve)
    # 'empresa' = Empresa (se devuelve a empresa, usamos -1 como marcador)
    # ID numérico = Empleado (se devuelve a ese empleado)
    quien_pago_anticipo_id = data.get('quien_pago_anticipo_id')
    if quien_pago_anticipo_id == '' or quien_pago_anticipo_id is None:
        # Caja del Proyecto - guardamos como None
        quien_pago_anticipo_id = None
    elif str(quien_pago_anticipo_id) == 'empresa':
        # Empresa - usamos -1 como marcador especial
        quien_pago_anticipo_id = -1
    else:
        # Es un ID de empleado
        try:
            quien_pago_anticipo_id = int(quien_pago_anticipo_id)
        except (ValueError, TypeError):
            quien_pago_anticipo_id = None
    
    resultado = PresupuestoPagoEmpleado.create_or_update(
        presupuesto_id=presupuesto_id,
        empleado_id=empleado_id,
        porcentaje_pago=data.get('porcentaje_pago', 0),
        anticipo=data.get('anticipo', 0),
        quien_pago_anticipo_id=quien_pago_anticipo_id
    )
    
    if isinstance(resultado, str):
        return jsonify({'status': 'error', 'message': resultado}), 400
    
    return jsonify({'status': 'success', 'data': resultado.to_dict()})

@app.route('/api/presupuesto/facturas/<int:presupuesto_id>', methods=['GET'])
@login_required
def api_presupuesto_facturas(presupuesto_id):
    """API para obtener todas las facturas/boletas de un presupuesto"""
    facturas = PresupuestoFactura.get_by_presupuesto(presupuesto_id)
    return jsonify({
        'status': 'success',
        'facturas': [f.to_dict() for f in facturas]
    })

@app.route('/api/presupuesto/factura/create', methods=['POST'])
@login_required
def api_presupuesto_factura_create():
    """API para crear una factura manualmente"""
    data = request.get_json()
    presupuesto_id = data.get('presupuesto_id')
    if not presupuesto_id:
        return jsonify({'status': 'error', 'message': 'presupuesto_id es requerido'}), 400
    
    def parse_chilean_number(value):
        if not value:
            return 0
        cleaned = str(value).replace('.', '').replace(' ', '')
        try:
            return int(cleaned)
        except:
            return 0
    
    factura = PresupuestoFactura.create(
        presupuesto_id=presupuesto_id,
        tipo_documento=data.get('tipo_documento', 'factura'),
        numero_documento=data.get('numero_documento'),
        proveedor=data.get('proveedor'),
        neto=parse_chilean_number(data.get('neto', 0)),
        iva=parse_chilean_number(data.get('iva', 0)),
        total=parse_chilean_number(data.get('total', 0))
    )
    
    if isinstance(factura, str):
        return jsonify({'status': 'error', 'message': factura}), 400
    
    return jsonify({'status': 'success', 'data': factura.to_dict()})

@app.route('/api/presupuesto/factura/<int:factura_id>', methods=['GET', 'PUT', 'DELETE'])
@login_required
def api_presupuesto_factura(factura_id):
    """API para obtener, actualizar o eliminar una factura específica con sus gastos vinculados"""
    if request.method == 'GET':
        factura = PresupuestoFactura.get_by_id(factura_id)
        if not factura:
            return jsonify({'status': 'error', 'message': 'Factura no encontrada'}), 404
        
        gastos = PresupuestoFactura.get_gastos_vinculados(factura_id)
        
        return jsonify({
            'status': 'success',
            'factura': factura.to_dict(),
            'gastos': [g.to_dict() for g in gastos]
        })
    elif request.method == 'PUT':
        data = request.get_json()
        factura = PresupuestoFactura.get_by_id(factura_id)
        if not factura:
            return jsonify({'status': 'error', 'message': 'Factura no encontrada'}), 404
        
        # Procesar montos (con punto como separador de miles)
        def parse_chilean_number(value):
            if not value:
                return 0
            cleaned = str(value).replace('.', '').replace(' ', '')
            try:
                return int(cleaned)
            except:
                return 0
        
        # Actualizar factura
        tipo_documento = data.get('tipo_documento', factura.tipo_documento)
        numero_documento = data.get('numero_documento')
        proveedor = data.get('proveedor')
        fecha_emision = data.get('fecha_emision')
        # Convertir cadena vacía a None
        if fecha_emision == '' or fecha_emision is None:
            fecha_emision = None
        neto = parse_chilean_number(data.get('neto', 0))
        iva = parse_chilean_number(data.get('iva', 0))
        total = parse_chilean_number(data.get('total', 0))
        
        # Calcular valores faltantes
        if total > 0 and neto == 0 and iva == 0:
            if tipo_documento == 'factura':
                neto = round(total / 1.19)
                iva = total - neto
            else:
                neto = round(total / 1.19)
                iva = total - neto
        elif neto > 0 and iva == 0 and total == 0:
            if tipo_documento == 'factura':
                iva = round(neto * 0.19)
                total = neto + iva
            else:
                total = neto
                neto = round(neto / 1.19)
                iva = total - neto
        
        # Actualizar en BD
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                UPDATE presupuesto_facturas
                SET tipo_documento = %s, numero_documento = %s, proveedor = %s, 
                    fecha_emision = %s, neto = %s, iva = %s, total = %s, updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (tipo_documento, numero_documento, proveedor, fecha_emision, neto, iva, total, factura_id))
            conn.commit()
            
            # Recargar factura desde BD para asegurar tipos correctos
            factura_actualizada = PresupuestoFactura.get_by_id(factura_id)
            if not factura_actualizada:
                return jsonify({'status': 'error', 'message': 'Error al recargar factura actualizada'}), 500
            
            return jsonify({'status': 'success', 'data': factura_actualizada.to_dict()})
        except Exception as e:
            conn.rollback()
            return jsonify({'status': 'error', 'message': f'Error al actualizar factura: {str(e)}'}), 500
        finally:
            cur.close()
            conn.close()
    else:  # DELETE
        resultado = PresupuestoFactura.delete(factura_id)
        if resultado:
            return jsonify({'status': 'success', 'message': 'Factura eliminada correctamente'})
        return jsonify({'status': 'error', 'message': 'No se pudo eliminar la factura'}), 400

@app.route('/api/presupuesto/pago-empleado/<int:pago_id>', methods=['GET', 'DELETE'])
@login_required
def api_presupuesto_pago_empleado_get_or_delete(pago_id):
    """API para obtener o eliminar un pago de empleado"""
    if request.method == 'GET':
        try:
            # Obtener pago
            pago = PresupuestoPagoEmpleado.get_by_id(pago_id)
            if not pago:
                return jsonify({'status': 'error', 'message': 'Pago no encontrado'}), 404
            
            pago_dict = pago.to_dict()
            # Asegurar que todos los campos estén presentes
            pago_dict['anticipo'] = pago_dict.get('anticipo', 0) or 0
            pago_dict['quien_pago_anticipo_id'] = pago_dict.get('quien_pago_anticipo_id') or None
            return jsonify({'status': 'success', 'data': pago_dict})
        except Exception as e:
            return jsonify({'status': 'error', 'message': f'Error al obtener el pago: {str(e)}'}), 500
    else:
        # Eliminar pago
        resultado = PresupuestoPagoEmpleado.delete(pago_id)
        if resultado:
            return jsonify({'status': 'success'})
        return jsonify({'status': 'error', 'message': 'No se pudo eliminar el pago'}), 400

@app.route('/api/presupuesto/update-porcentaje-empresa', methods=['POST'])
@login_required
def api_presupuesto_update_porcentaje_empresa():
    """API para actualizar el porcentaje de empresa"""
    data = request.get_json()
    presupuesto_id = data.get('presupuesto_id')
    porcentaje_empresa = data.get('porcentaje_empresa', 0)
    
    if not presupuesto_id:
        return jsonify({'status': 'error', 'message': 'presupuesto_id es requerido'}), 400
    
    try:
        porcentaje_empresa = float(porcentaje_empresa)
    except (ValueError, TypeError):
        return jsonify({'status': 'error', 'message': 'porcentaje_empresa debe ser un número válido'}), 400
    
    presupuesto = Presupuesto.get_by_id(presupuesto_id)
    if not presupuesto:
        return jsonify({'status': 'error', 'message': 'Presupuesto no encontrado'}), 404
    
    resultado = presupuesto.update(porcentaje_empresa=porcentaje_empresa)
    if resultado:
        return jsonify({'status': 'success', 'message': 'Porcentaje de empresa actualizado correctamente'})
    return jsonify({'status': 'error', 'message': 'No se pudo actualizar el porcentaje'}), 400

@app.route('/projects_clientes')
@login_required
def projects_clientes():
    from datetime import datetime
    return render_template('projects_clientes.html', now=datetime.now())

@app.route('/dashboard2')
@login_required
def dashboard2():
    from datetime import datetime
    return render_template('dashboard2.html', now=datetime.now())

@app.route('/dashboard3')
@login_required
def dashboard3():
    from datetime import datetime
    return render_template('dashboard3.html', now=datetime.now())

@app.route('/add_user', methods=['POST'])
@login_required
def add_user():
    email = request.form.get('email')
    password = request.form.get('password')
    nombre = request.form.get('nombre')
    apellido = request.form.get('apellido')
    username = request.form.get('username')
    tag = request.form.get('tag', 'Usuario')
    is_admin = request.form.get('is_admin') == 'true' or request.form.get('is_admin') == 'on'
    
    if not email or not password or not nombre or not apellido or not username:
        return jsonify({'status': 'error', 'message': 'Todos los campos son obligatorios'})
    elif User.get_by_email(email):
        return jsonify({'status': 'error', 'message': 'El correo ya está registrado'})
    else:
        result = User.create(email, password, nombre, apellido, username, tag=tag, is_admin=is_admin)
        if isinstance(result, User):
            log_user_action("Crear Usuario", f"Usuario '{result.username or result.email}' creado", {'user_id': result.id, 'username': result.username, 'email': result.email})
            return jsonify({
                'status': 'success',
                'message': 'Usuario registrado correctamente',
                'user': {
                    'id': result.id,
                    'username': result.username,
                    'nombre': result.nombre,
                    'apellido': result.apellido,
                    'email': result.email,
                    'tag': result.tag,
                    'is_admin': result.is_admin,
                    'last_login': result.last_login.strftime('%Y-%m-%d %H:%M:%S') if result.last_login else 'Nunca',
                    'estado': result.estado
                }
            })
        else:
            return jsonify({'status': 'error', 'message': f'Error al registrar usuario: {result}'})

@app.route('/logout')
@login_required
def logout():
    # Registrar logout antes de cerrar sesión
    if current_user and current_user.is_authenticated:
        usuario_nombre = 'Usuario desconocido'
        if is_cliente(current_user):
            usuario_nombre = current_user.nombre_empresa if current_user.tipo_cliente == 'empresa' else f"{current_user.nombre} {current_user.apellido}"
        else:
            usuario_nombre = f"{current_user.nombre} {current_user.apellido}".strip() or current_user.username or current_user.email
        log_user_action("Logout", f"Usuario {usuario_nombre} cerró sesión")
    logout_user()
    return redirect(url_for('login'))

@app.route('/toggle_user_status/<int:user_id>', methods=['POST'])
@login_required
def toggle_user_status(user_id):
    user = User.get_by_id(user_id)
    if not user:
        return jsonify({'status': 'error', 'message': 'Usuario no encontrado'})
    new_status = 'deshabilitado' if user.estado == 'habilitado' else 'habilitado'
    result = user.set_estado(new_status)
    if result:
        return jsonify({'status': 'success', 'new_status': new_status})
    else:
        return jsonify({'status': 'error', 'message': 'No se pudo actualizar el estado'})

@app.route('/add_cliente', methods=['POST'])
@login_required
def add_cliente():
    tipo_cliente = request.form.get('tipo_cliente')
    nombre = request.form.get('nombre')
    apellido = request.form.get('apellido')
    rut = request.form.get('rut')
    rut_contacto = request.form.get('rut_contacto')  # RUT del contacto (opcional cuando es empresa)
    correo = request.form.get('correo')
    telefono = request.form.get('telefono')
    nombre_empresa = request.form.get('nombre_empresa')
    rut_empresa = request.form.get('rut_empresa')  # RUT de la empresa (cuando es empresa)
    giro = request.form.get('giro')
    usuario_referidor_id = request.form.get('usuario_referidor_id', type=int) or None

    # Validaciones
    if not tipo_cliente:
        return jsonify({'status': 'error', 'message': 'El tipo de cliente es obligatorio'})
    
    if tipo_cliente == 'empresa':
        # Para empresa: RUT de la empresa es obligatorio, RUT del contacto es opcional
        if not (nombre and apellido and correo and telefono):
            return jsonify({'status': 'error', 'message': 'Los campos de contacto son obligatorios'})
        if not (nombre_empresa and rut_empresa and giro):
            return jsonify({'status': 'error', 'message': 'Todos los campos de empresa son obligatorios'})
        # Cuando es empresa: rut = RUT de la empresa, rut_empresa = RUT del contacto (opcional)
        rut_final = rut_empresa
        rut_contacto_final = rut_contacto if rut_contacto else None
    else:
        # Para persona natural: RUT es obligatorio
        if not (nombre and apellido and rut and correo and telefono):
            return jsonify({'status': 'error', 'message': 'Todos los campos son obligatorios'})
        rut_final = rut
        rut_contacto_final = None

    result = Cliente.create(
        tipo_cliente=tipo_cliente,
        nombre=nombre,
        apellido=apellido,
        rut=rut_final,  # RUT de la empresa si es empresa, RUT de la persona si es persona
        correo=correo,
        telefono=telefono,
        nombre_empresa=nombre_empresa if tipo_cliente == 'empresa' else None,
        rut_empresa=rut_contacto_final,  # RUT del contacto cuando es empresa (opcional)
        giro=giro if tipo_cliente == 'empresa' else None,
        usuario_referidor_id=usuario_referidor_id
    )
    if isinstance(result, Cliente):
        cliente_nombre = result.nombre_empresa if result.tipo_cliente == 'empresa' else f"{result.nombre} {result.apellido}"
        log_user_action("Crear Cliente", f"Cliente '{cliente_nombre}' creado", {'cliente_id': result.id, 'tipo_cliente': result.tipo_cliente, 'nombre': cliente_nombre})
        return jsonify({
            'status': 'success',
            'message': 'Cliente registrado correctamente',
            'cliente': result.to_dict()
        })
    else:
        return jsonify({'status': 'error', 'message': f'Error al registrar cliente: {result}'})

@app.route('/toggle_cliente_status/<int:cliente_id>', methods=['POST'])
@login_required
def toggle_cliente_status(cliente_id):
    cliente = Cliente.get_by_id(cliente_id)
    if not cliente:
        return jsonify({'status': 'error', 'message': 'Cliente no encontrado'})
    new_status = 'deshabilitado' if cliente.estado == 'habilitado' else 'habilitado'
    cliente_nombre = cliente.nombre_empresa if cliente.tipo_cliente == 'empresa' else f"{cliente.nombre} {cliente.apellido}"
    result = cliente.set_estado(new_status)
    if result:
        log_user_action("Cambiar Estado Cliente", f"Estado del cliente '{cliente_nombre}' cambiado a {new_status}", {'cliente_id': cliente_id, 'estado_anterior': cliente.estado, 'estado_nuevo': new_status})
        return jsonify({'status': 'success', 'new_status': new_status})
    else:
        return jsonify({'status': 'error', 'message': 'No se pudo actualizar el estado'})

@app.route('/delete_user/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    user = User.get_by_id(user_id)
    if not user:
        return jsonify({'status': 'error', 'message': 'Usuario no encontrado'})
    try:
        user_username = user.username or user.email
        result = User.delete(user_id)
        if result:
            log_user_action("Eliminar Usuario", f"Usuario '{user_username}' eliminado", {'user_id': user_id, 'username': user_username})
            return jsonify({'status': 'success', 'message': 'Usuario eliminado correctamente'})
        else:
            return jsonify({'status': 'error', 'message': 'No se pudo eliminar el usuario'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/get_user/<int:user_id>', methods=['GET'])
@login_required
def get_user(user_id):
    """Obtiene los datos de un usuario para editar"""
    user = User.get_by_id(user_id)
    if not user:
        return jsonify({'status': 'error', 'message': 'Usuario no encontrado'})
    
    return jsonify({
        'status': 'success',
        'user': {
            'id': user.id,
            'username': user.username,
            'nombre': user.nombre,
            'apellido': user.apellido,
            'email': user.email,
            'tag': user.tag if hasattr(user, 'tag') else 'Usuario',
            'is_admin': user.is_admin if hasattr(user, 'is_admin') else False,
            'estado': user.estado
        }
    })

@app.route('/edit_user/<int:user_id>', methods=['POST'])
@login_required
def edit_user(user_id):
    user = User.get_by_id(user_id)
    if not user:
        return jsonify({'status': 'error', 'message': 'Usuario no encontrado'})
    data = request.form
    try:
        # Solo Olmeiri puede cambiar is_admin
        is_admin_value = None
        if is_admin(current_user):
            is_admin_value = data.get('is_admin') == 'true' or data.get('is_admin') == 'on'
        
        result = user.edit(
            nombre=data.get('nombre'),
            apellido=data.get('apellido'),
            username=data.get('username'),
            email=data.get('email'),
            estado=data.get('estado'),
            tag=data.get('tag'),
            is_admin=is_admin_value
        )
        if result:
            log_user_action("Editar Usuario", f"Usuario '{user.username or user.email}' editado", {'user_id': user_id, 'username': user.username, 'email': user.email})
            return jsonify({'status': 'success', 'message': 'Usuario editado correctamente'})
        else:
            return jsonify({'status': 'error', 'message': 'No se pudo editar el usuario'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/delete_cliente/<int:cliente_id>', methods=['POST'])
@login_required
def delete_cliente(cliente_id):
    cliente = Cliente.get_by_id(cliente_id)
    if not cliente:
        return jsonify({'status': 'error', 'message': 'Cliente no encontrado'})
    try:
        cliente_nombre = cliente.nombre_empresa if cliente.tipo_cliente == 'empresa' else f"{cliente.nombre} {cliente.apellido}"
        result = Cliente.delete(cliente_id)
        if result:
            log_user_action("Eliminar Cliente", f"Cliente '{cliente_nombre}' eliminado", {'cliente_id': cliente_id, 'tipo_cliente': cliente.tipo_cliente})
            return jsonify({'status': 'success', 'message': 'Cliente eliminado correctamente'})
        else:
            return jsonify({'status': 'error', 'message': 'No se pudo eliminar el cliente'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/edit_cliente/<int:cliente_id>', methods=['POST'])
@login_required
def edit_cliente(cliente_id):
    cliente = Cliente.get_by_id(cliente_id)
    if not cliente:
        return jsonify({'status': 'error', 'message': 'Cliente no encontrado'})
    data = request.form
    tipo_cliente = data.get('tipo_cliente')
    
    # Lógica similar a add_cliente para manejar RUTs correctamente
    if tipo_cliente == 'empresa':
        # Cuando es empresa: rut = RUT de la empresa, rut_empresa = RUT del contacto (opcional)
        rut_final = data.get('rut_empresa')  # RUT de la empresa viene en rut_empresa
        rut_contacto_final = data.get('rut_contacto') if data.get('rut_contacto') else None
    else:
        # Para persona natural: rut = RUT de la persona
        rut_final = data.get('rut')
        rut_contacto_final = None
    
    usuario_referidor_id = data.get('usuario_referidor_id', type=int) or None
    
    # Obtener el estado actual del cliente si no se proporciona en el formulario
    estado = data.get('estado')
    if not estado:
        estado = cliente.estado  # Mantener el estado actual
    
    try:
        result = cliente.edit(
            tipo_cliente=tipo_cliente,
            nombre=data.get('nombre'),
            apellido=data.get('apellido'),
            rut=rut_final,
            correo=data.get('correo'),
            telefono=data.get('telefono'),
            nombre_empresa=data.get('nombre_empresa'),
            rut_empresa=rut_contacto_final,  # RUT del contacto cuando es empresa
            giro=data.get('giro'),
            estado=estado,
            usuario_referidor_id=usuario_referidor_id
        )
        if result:
            # Recargar el cliente actualizado desde la base de datos
            cliente_actualizado = Cliente.get_by_id(cliente_id)
            cliente_nombre = cliente_actualizado.nombre_empresa if cliente_actualizado.tipo_cliente == 'empresa' else f"{cliente_actualizado.nombre} {cliente_actualizado.apellido}"
            log_user_action("Editar Cliente", f"Cliente '{cliente_nombre}' editado", {'cliente_id': cliente_id, 'tipo_cliente': cliente_actualizado.tipo_cliente})
            return jsonify({
                'status': 'success',
                'message': 'Cliente editado correctamente',
                'cliente': cliente_actualizado.to_dict()
            })
        else:
            return jsonify({'status': 'error', 'message': 'No se pudo editar el cliente'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/get_cliente_info', methods=['GET'])
@login_required
def get_cliente_info():
    """Obtiene información completa de un cliente"""
    cliente_id = request.args.get('cliente_id', type=int)
    if not cliente_id:
        return jsonify({'status': 'error', 'message': 'Cliente no especificado'})
    
    cliente = Cliente.get_by_id(cliente_id)
    if not cliente:
        return jsonify({'status': 'error', 'message': 'Cliente no encontrado'})
    
    return jsonify({
        'status': 'success',
        'cliente': cliente.to_dict()
    })

@app.route('/search_usuarios_clientes', methods=['GET'])
@login_required
def search_usuarios_clientes():
    """Busca usuarios y clientes para asignar a proyectos"""
    query = request.args.get('q', '').strip()
    if not query or len(query) < 2:
        return jsonify({'results': []})
    
    results = []
    
    # Buscar usuarios
    all_users = User.get_all()
    for user in all_users:
        if user.estado == 'habilitado':
            nombre_completo = f"{user.nombre} {user.apellido}".lower()
            if query.lower() in nombre_completo or query.lower() in user.email.lower() or (user.username and query.lower() in user.username.lower()):
                user_tag = user.tag if hasattr(user, 'tag') else 'Usuario'
                results.append({
                    'id': user.id,
                    'tipo': 'user',
                    'nombre': f"{user.nombre} {user.apellido}",
                    'email': user.email,
                    'username': user.username,
                    'tag': user_tag,
                    'display': f"{user.nombre} {user.apellido} ({user.email}) - {user_tag}"
                })
    
    # Buscar clientes
    all_clientes = Cliente.get_all()
    for cliente in all_clientes:
        if cliente.estado == 'habilitado':
            nombre_completo = f"{cliente.nombre} {cliente.apellido}".lower()
            nombre_empresa = cliente.nombre_empresa.lower() if cliente.nombre_empresa else ''
            if (query.lower() in nombre_completo or 
                query.lower() in cliente.correo.lower() or 
                query.lower() in nombre_empresa or
                (cliente.rut and query.lower() in cliente.rut.lower())):
                if cliente.tipo_cliente == 'empresa':
                    display = f"{cliente.nombre_empresa} - {cliente.nombre} {cliente.apellido} ({cliente.correo}) - Cliente Empresa"
                else:
                    display = f"{cliente.nombre} {cliente.apellido} ({cliente.correo}) - Cliente"
                results.append({
                    'id': cliente.id,
                    'tipo': 'cliente',
                    'nombre': cliente.nombre_empresa if cliente.tipo_cliente == 'empresa' else f"{cliente.nombre} {cliente.apellido}",
                    'email': cliente.correo,
                    'telefono': cliente.telefono,
                    'rut': cliente.rut,
                    'giro': cliente.giro,
                    'tipo_cliente': cliente.tipo_cliente,
                    'nombre_empresa': cliente.nombre_empresa,
                    'representante_nombre': f"{cliente.nombre} {cliente.apellido}" if cliente.tipo_cliente == 'empresa' else None,
                    'representante_rut': cliente.rut_empresa if cliente.tipo_cliente == 'empresa' else None,
                    'display': display
                })
    
    return jsonify({'results': results[:20]})  # Limitar a 20 resultados

@app.route('/add_proyecto', methods=['POST'])
@login_required
def add_proyecto():
    if is_cliente(current_user):
        return jsonify({'status': 'error', 'message': 'No tienes permisos para crear proyectos'})
    
    nombre = request.form.get('nombre')
    descripcion = request.form.get('descripcion')
    estado = request.form.get('estado', 'en_desarrollo')
    progreso = int(request.form.get('progreso', 0))
    incluye_mantenimiento = request.form.get('incluye_mantenimiento') == '1'
    es_solo_mantenimiento = request.form.get('es_solo_mantenimiento') == '1'
    ciclo_pago_mensual = float(request.form.get('ciclo_pago_mensual', 0) or 0)
    asignados = request.form.getlist('asignados[]')  # Lista de IDs de usuarios/clientes asignados
    cliente_presupuesto_id = request.form.get('cliente_presupuesto_id', type=int)  # Cliente para el presupuesto
    
    if not nombre:
        return jsonify({'status': 'error', 'message': 'El nombre del proyecto es obligatorio'})
    
    result = Proyecto.create(nombre, descripcion, estado, progreso, incluye_mantenimiento, es_solo_mantenimiento, ciclo_pago_mensual)
    if isinstance(result, Proyecto):
        # Asignar el proyecto al usuario que lo crea (si no está en la lista)
        tipo_asignado = 'cliente' if is_cliente(current_user) else 'user'
        current_user_id = f"{tipo_asignado}_{current_user.id}"
        if current_user_id not in asignados:
            result.asignar(current_user.id, tipo_asignado)
        
        # Asignar a los usuarios/clientes seleccionados
        for asignado in asignados:
            if asignado and '_' in asignado:
                tipo, asignado_id = asignado.split('_', 1)
                try:
                    result.asignar(int(asignado_id), tipo)
                except ValueError:
                    continue
        
        # Si hay un cliente seleccionado para el presupuesto, crear/actualizar el presupuesto
        if cliente_presupuesto_id:
            cliente = Cliente.get_by_id(cliente_presupuesto_id)
            if cliente:
                # Obtener información del cliente
                cliente_nombre = cliente.nombre_empresa if cliente.tipo_cliente == 'empresa' else f"{cliente.nombre} {cliente.apellido}"
                cliente_email = cliente.correo
                cliente_telefono = cliente.telefono
                
                # Crear presupuesto con el cliente (sin añadirlo al equipo)
                presupuesto = Presupuesto.create(
                    proyecto_id=result.id,
                    obra=nombre,
                    cliente_id=cliente_presupuesto_id,
                    cliente_nombre=cliente_nombre,
                    cliente_email=cliente_email,
                    cliente_telefono=cliente_telefono
                )
        
        log_user_action("Crear Proyecto", f"Proyecto '{nombre}' creado", {'proyecto_id': result.id, 'nombre': nombre})
        return jsonify({
            'status': 'success',
            'message': 'Proyecto creado correctamente',
            'proyecto': result.to_dict()
        })
    else:
        return jsonify({'status': 'error', 'message': f'Error al crear proyecto: {result}'})

@app.route('/get_proyecto/<int:proyecto_id>', methods=['GET'])
@login_required
def get_proyecto(proyecto_id):
    """Obtiene los datos de un proyecto para editar"""
    proyecto = Proyecto.get_by_id(proyecto_id)
    if not proyecto:
        return jsonify({'status': 'error', 'message': 'Proyecto no encontrado'})
    
    asignados = proyecto.get_asignados()
    asignados_formatted = []
    for asignado in asignados:
        user_tag = asignado.get('tag', 'Usuario') if asignado['tipo'] == 'user' else None
        display_tag = user_tag if user_tag else ('Cliente' if asignado['tipo'] == 'cliente' else 'Usuario')
        asignados_formatted.append({
            'id': f"{asignado['tipo']}_{asignado['id']}",
            'tipo': asignado['tipo'],
            'nombre': asignado['nombre'],
            'email': asignado['email'],
            'tag': user_tag,
            'display': f"{asignado['nombre']} ({asignado['email']}) - {display_tag}"
        })
    
    # Obtener cliente del presupuesto si existe
    presupuesto = Presupuesto.get_by_proyecto(proyecto_id)
    cliente_presupuesto_id = None
    cliente_presupuesto = None
    if presupuesto and presupuesto.cliente_id:
        cliente_presupuesto_id = presupuesto.cliente_id
        cliente = Cliente.get_by_id(presupuesto.cliente_id)
        if cliente:
            if cliente.tipo_cliente == 'empresa':
                nombre_display = cliente.nombre_empresa
            else:
                nombre_display = f"{cliente.nombre} {cliente.apellido}"
            cliente_presupuesto = {
                'id': cliente.id,
                'tipo': 'cliente',
                'nombre': nombre_display,
                'email': cliente.correo,
                'display': f"{nombre_display} ({cliente.correo}) - Cliente"
            }
    
    return jsonify({
        'status': 'success',
        'proyecto': {
            'id': proyecto.id,
            'nombre': proyecto.nombre,
            'descripcion': proyecto.descripcion,
            'estado': proyecto.estado,
            'progreso': proyecto.progreso,
            'incluye_mantenimiento': proyecto.incluye_mantenimiento if hasattr(proyecto, 'incluye_mantenimiento') else False,
            'es_solo_mantenimiento': proyecto.es_solo_mantenimiento if hasattr(proyecto, 'es_solo_mantenimiento') else False,
            'ciclo_pago_mensual': float(proyecto.ciclo_pago_mensual) if hasattr(proyecto, 'ciclo_pago_mensual') else 0,
            'asignados': asignados_formatted,
            'cliente_presupuesto_id': cliente_presupuesto_id,
            'cliente_presupuesto': cliente_presupuesto
        }
    })

@app.route('/edit_proyecto/<int:proyecto_id>', methods=['POST'])
@login_required
def edit_proyecto(proyecto_id):
    if is_cliente(current_user):
        return jsonify({'status': 'error', 'message': 'No tienes permisos para editar proyectos'})
    
    proyecto = Proyecto.get_by_id(proyecto_id)
    if not proyecto:
        return jsonify({'status': 'error', 'message': 'Proyecto no encontrado'})
    
    nombre = request.form.get('nombre')
    descripcion = request.form.get('descripcion')
    estado = request.form.get('estado')
    progreso = request.form.get('progreso')
    incluye_mantenimiento = request.form.get('incluye_mantenimiento') == '1'
    es_solo_mantenimiento = request.form.get('es_solo_mantenimiento') == '1'
    ciclo_pago_mensual = request.form.get('ciclo_pago_mensual')
    asignados = request.form.getlist('asignados[]')
    cliente_presupuesto_id = request.form.get('cliente_presupuesto_id', type=int)  # Cliente para el presupuesto
    
    # Guardar valores anteriores para comparar
    valores_anteriores = {
        'nombre': proyecto.nombre,
        'descripcion': proyecto.descripcion,
        'estado': proyecto.estado,
        'progreso': str(proyecto.progreso),
        'incluye_mantenimiento': proyecto.incluye_mantenimiento if hasattr(proyecto, 'incluye_mantenimiento') else False,
        'es_solo_mantenimiento': proyecto.es_solo_mantenimiento if hasattr(proyecto, 'es_solo_mantenimiento') else False,
        'ciclo_pago_mensual': float(proyecto.ciclo_pago_mensual) if hasattr(proyecto, 'ciclo_pago_mensual') else 0
    }
    
    # Determinar tipo de autor
    tipo_autor = 'cliente' if is_cliente(current_user) else 'user'
    
    try:
        result = proyecto.update(
            nombre=nombre if nombre else None,
            descripcion=descripcion if descripcion else None,
            estado=estado if estado else None,
            progreso=int(progreso) if progreso else None,
            incluye_mantenimiento=incluye_mantenimiento,
            es_solo_mantenimiento=es_solo_mantenimiento,
            ciclo_pago_mensual=float(ciclo_pago_mensual) if ciclo_pago_mensual else None
        )
        if result:
            # Registrar cambios
            if nombre and nombre != valores_anteriores['nombre']:
                CambioProyecto.create(proyecto_id, current_user.id, tipo_autor, 'nombre', 
                                     valores_anteriores['nombre'], nombre)
            
            if descripcion is not None and descripcion != valores_anteriores['descripcion']:
                CambioProyecto.create(proyecto_id, current_user.id, tipo_autor, 'descripcion', 
                                     valores_anteriores['descripcion'], descripcion)
            
            if estado and estado != valores_anteriores['estado']:
                CambioProyecto.create(proyecto_id, current_user.id, tipo_autor, 'estado', 
                                     valores_anteriores['estado'], estado)
            
            if progreso and str(progreso) != valores_anteriores['progreso']:
                CambioProyecto.create(proyecto_id, current_user.id, tipo_autor, 'progreso', 
                                     valores_anteriores['progreso'], str(progreso))
            
            # Obtener asignaciones anteriores antes de eliminarlas
            asignados_anteriores = proyecto.get_asignados()
            asignados_anteriores_ids = [f"{a['tipo']}_{a['id']}" for a in asignados_anteriores]
            asignados_nuevos_ids = [a for a in asignados if a and '_' in a]
            
            # Eliminar todas las asignaciones actuales
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("DELETE FROM proyecto_asignaciones WHERE proyecto_id = %s", (proyecto_id,))
            conn.commit()
            cur.close()
            conn.close()
            
            # Asignar nuevos usuarios/clientes
            for asignado in asignados:
                if asignado and '_' in asignado:
                    tipo, asignado_id = asignado.split('_', 1)
                    try:
                        proyecto.asignar(int(asignado_id), tipo)
                    except ValueError:
                        continue
            
            # Si hay un cliente seleccionado para el presupuesto, actualizar el presupuesto (sin añadirlo al equipo)
            if cliente_presupuesto_id is not None and cliente_presupuesto_id != 0:
                cliente = Cliente.get_by_id(cliente_presupuesto_id)
                if cliente:
                    # Actualizar cliente del presupuesto
                    presupuesto = Presupuesto.get_by_proyecto(proyecto_id)
                    cliente_nombre = cliente.nombre_empresa if cliente.tipo_cliente == 'empresa' else f"{cliente.nombre} {cliente.apellido}"
                    cliente_email = cliente.correo
                    cliente_telefono = cliente.telefono
                    
                    if presupuesto:
                        # Actualizar presupuesto existente
                        presupuesto.update(
                            cliente_id=cliente_presupuesto_id,
                            cliente_nombre=cliente_nombre,
                            cliente_email=cliente_email,
                            cliente_telefono=cliente_telefono
                        )
                    else:
                        # Crear nuevo presupuesto
                        Presupuesto.create(
                            proyecto_id=proyecto_id,
                            obra=proyecto.nombre,
                            cliente_id=cliente_presupuesto_id,
                            cliente_nombre=cliente_nombre,
                            cliente_email=cliente_email,
                            cliente_telefono=cliente_telefono
                        )
            elif cliente_presupuesto_id == 0:
                # Si se envía 0, significa que se quiere eliminar el cliente del presupuesto
                presupuesto = Presupuesto.get_by_proyecto(proyecto_id)
                if presupuesto:
                    presupuesto.update(
                        cliente_id=None,
                        cliente_nombre=None,
                        cliente_email=None,
                        cliente_telefono=None
                    )
            
            # Verificar si hubo cambios en asignados y registrar
            if set(asignados_anteriores_ids) != set(asignados_nuevos_ids):
                asignados_ant_str = ', '.join([a['nombre'] for a in asignados_anteriores]) if asignados_anteriores else 'Ninguno'
                # Obtener nombres de nuevos asignados
                asignados_nuevos_nombres = []
                for asignado_id in asignados_nuevos_ids:
                    tipo, id_asignado = asignado_id.split('_', 1)
                    try:
                        if tipo == 'user':
                            user = User.get_by_id(int(id_asignado))
                            if user:
                                asignados_nuevos_nombres.append(f"{user.nombre} {user.apellido}")
                        elif tipo == 'cliente':
                            cliente = Cliente.get_by_id(int(id_asignado))
                            if cliente:
                                if cliente.tipo_cliente == 'empresa':
                                    asignados_nuevos_nombres.append(cliente.nombre_empresa)
                                else:
                                    asignados_nuevos_nombres.append(f"{cliente.nombre} {cliente.apellido}")
                    except (ValueError, TypeError):
                        continue
                asignados_nuevos_str = ', '.join(asignados_nuevos_nombres) if asignados_nuevos_nombres else 'Ninguno'
                
                CambioProyecto.create(proyecto_id, current_user.id, tipo_autor, 'asignados', 
                                     asignados_ant_str, asignados_nuevos_str)
            
            log_user_action("Editar Proyecto", f"Proyecto '{nombre}' actualizado", {'proyecto_id': proyecto_id, 'nombre': nombre})
            return jsonify({
                'status': 'success',
                'message': 'Proyecto editado correctamente',
                'proyecto': proyecto.to_dict(include_asignados=True)
            })
        else:
            return jsonify({'status': 'error', 'message': 'No se pudo editar el proyecto'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/update_proyecto_estado/<int:proyecto_id>', methods=['POST'])
@login_required
def update_proyecto_estado(proyecto_id):
    """Actualiza solo el estado de un proyecto (solo para administradores)"""
    if not is_admin(current_user):
        return jsonify({'status': 'error', 'message': 'No tienes permisos para cambiar el estado del proyecto'})
    
    proyecto = Proyecto.get_by_id(proyecto_id)
    if not proyecto:
        return jsonify({'status': 'error', 'message': 'Proyecto no encontrado'})
    
    nuevo_estado = request.form.get('estado')
    if not nuevo_estado:
        return jsonify({'status': 'error', 'message': 'Estado no especificado'})
    
    # Guardar valor anterior para registrar el cambio
    estado_anterior = proyecto.estado
    
    # Determinar tipo de autor
    tipo_autor = 'cliente' if is_cliente(current_user) else 'user'
    
    try:
        result = proyecto.update(estado=nuevo_estado)
        if result:
            # Registrar el cambio
            if nuevo_estado != estado_anterior:
                CambioProyecto.create(proyecto_id, current_user.id, tipo_autor, 'estado', 
                                     estado_anterior, nuevo_estado)
            
            return jsonify({
                'status': 'success',
                'message': 'Estado actualizado correctamente',
                'proyecto': proyecto.to_dict()
            })
        else:
            return jsonify({'status': 'error', 'message': 'No se pudo actualizar el estado'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/delete_proyecto/<int:proyecto_id>', methods=['POST'])
@login_required
def delete_proyecto(proyecto_id):
    if is_cliente(current_user):
        return jsonify({'status': 'error', 'message': 'No tienes permisos para eliminar proyectos'})
    
    proyecto = Proyecto.get_by_id(proyecto_id)
    if not proyecto:
        return jsonify({'status': 'error', 'message': 'Proyecto no encontrado'})
    
    proyecto_nombre = proyecto.nombre
    try:
        result = Proyecto.delete(proyecto_id)
        if result:
            log_user_action("Eliminar Proyecto", f"Proyecto '{proyecto_nombre}' eliminado", {'proyecto_id': proyecto_id})
            return jsonify({'status': 'success', 'message': 'Proyecto eliminado correctamente'})
        else:
            return jsonify({'status': 'error', 'message': 'No se pudo eliminar el proyecto'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/add_comentario', methods=['POST'])
@login_required
def add_comentario():
    proyecto_id = request.form.get('proyecto_id', type=int)
    comentario_texto = request.form.get('comentario', '').strip()
    comentario_padre_id = request.form.get('comentario_padre_id', type=int)
    
    if not proyecto_id:
        return jsonify({'status': 'error', 'message': 'Proyecto no especificado'})
    
    if not comentario_texto:
        return jsonify({'status': 'error', 'message': 'El comentario no puede estar vacío'})
    
    # Verificar que el proyecto existe
    proyecto = Proyecto.get_by_id(proyecto_id)
    if not proyecto:
        return jsonify({'status': 'error', 'message': 'Proyecto no encontrado'})
    
    # Si es una respuesta, verificar que el comentario padre existe
    if comentario_padre_id:
        comentario_padre = Comentario.get_by_id(comentario_padre_id)
        if not comentario_padre or comentario_padre.proyecto_id != proyecto_id:
            return jsonify({'status': 'error', 'message': 'Comentario padre no encontrado'})
    
    # Verificar permisos: el usuario debe estar asignado al proyecto o ser admin
    is_admin_user = is_admin(current_user)
    tiene_acceso = False
    
    if is_admin_user:
        tiene_acceso = True
    else:
        # Verificar si el usuario está asignado al proyecto
        conn = get_db_connection()
        cur = conn.cursor()
        if is_cliente(current_user):
            cur.execute("""
                SELECT COUNT(*) FROM proyecto_asignaciones 
                WHERE proyecto_id = %s AND asignado_id = %s AND tipo_asignado = 'cliente'
            """, (proyecto_id, current_user.id))
        else:
            cur.execute("""
                SELECT COUNT(*) FROM proyecto_asignaciones 
                WHERE proyecto_id = %s AND asignado_id = %s AND tipo_asignado = 'user'
            """, (proyecto_id, current_user.id))
        count = cur.fetchone()[0]
        cur.close()
        conn.close()
        tiene_acceso = count > 0
    
    if not tiene_acceso:
        return jsonify({'status': 'error', 'message': 'No tienes permisos para comentar en este proyecto'})
    
    # Determinar tipo de autor
    tipo_autor = 'cliente' if is_cliente(current_user) else 'user'
    
    # Crear el comentario o respuesta
    result = Comentario.create(proyecto_id, current_user.id, tipo_autor, comentario_texto, comentario_padre_id)
    
    if isinstance(result, Comentario):
        return jsonify({
            'status': 'success',
            'message': 'Comentario agregado correctamente',
            'comentario': result.to_dict()
        })
    else:
        return jsonify({'status': 'error', 'message': f'Error al crear comentario: {result}'})

@app.route('/delete_comentario/<int:comentario_id>', methods=['POST'])
@login_required
def delete_comentario(comentario_id):
    comentario = Comentario.get_by_id(comentario_id)
    if not comentario:
        return jsonify({'status': 'error', 'message': 'Comentario no encontrado'})
    
    # Verificar permisos: solo el autor o admin puede eliminar
    is_admin_user = is_admin(current_user)
    tipo_autor = 'cliente' if is_cliente(current_user) else 'user'
    es_autor = (comentario.autor_id == current_user.id and comentario.tipo_autor == tipo_autor)
    
    if not (is_admin_user or es_autor):
        return jsonify({'status': 'error', 'message': 'No tienes permisos para eliminar este comentario'})
    
    result = Comentario.delete(comentario_id)
    if result:
        return jsonify({'status': 'success', 'message': 'Comentario eliminado correctamente'})
    else:
        return jsonify({'status': 'error', 'message': 'Error al eliminar comentario'})

@app.route('/get_comentarios/<int:proyecto_id>', methods=['GET'])
@login_required
def get_comentarios(proyecto_id):
    # Verificar que el proyecto existe
    proyecto = Proyecto.get_by_id(proyecto_id)
    if not proyecto:
        return jsonify({'status': 'error', 'message': 'Proyecto no encontrado'})
    
    # Verificar permisos
    is_admin_user = is_admin(current_user)
    tiene_acceso = False
    
    if is_admin_user:
        tiene_acceso = True
    else:
        conn = get_db_connection()
        cur = conn.cursor()
        if is_cliente(current_user):
            cur.execute("""
                SELECT COUNT(*) FROM proyecto_asignaciones 
                WHERE proyecto_id = %s AND asignado_id = %s AND tipo_asignado = 'cliente'
            """, (proyecto_id, current_user.id))
        else:
            cur.execute("""
                SELECT COUNT(*) FROM proyecto_asignaciones 
                WHERE proyecto_id = %s AND asignado_id = %s AND tipo_asignado = 'user'
            """, (proyecto_id, current_user.id))
        count = cur.fetchone()[0]
        cur.close()
        conn.close()
        tiene_acceso = count > 0
    
    if not tiene_acceso:
        return jsonify({'status': 'error', 'message': 'No tienes permisos para ver comentarios de este proyecto'})
    
    comentarios = Comentario.get_by_proyecto(proyecto_id)
    comentarios_dict = [c.to_dict() for c in comentarios]
    
    return jsonify({
        'status': 'success',
        'comentarios': comentarios_dict
    })

@app.route('/create_or_update_presupuesto', methods=['POST'])
@login_required
def create_or_update_presupuesto():
    if is_cliente(current_user):
        return jsonify({'status': 'error', 'message': 'No tienes permisos para crear/editar presupuestos'})
    
    proyecto_id = request.form.get('proyecto_id', type=int)
    numero_presupuesto = request.form.get('numero_presupuesto')
    fecha = request.form.get('fecha')
    obra = request.form.get('obra')
    cliente_id = request.form.get('cliente_id', type=int)
    cliente_nombre = request.form.get('cliente_nombre')
    cliente_email = request.form.get('cliente_email')
    cliente_telefono = request.form.get('cliente_telefono')
    descuento = request.form.get('descuento', type=float)
    iva = request.form.get('iva', type=float)
    generalidades = request.form.get('generalidades')
    tipo_presupuesto = request.form.get('tipo_presupuesto', 'principal')
    incidencia_id = request.form.get('incidencia_id', type=int)
    visita_mantenimiento_id = request.form.get('visita_mantenimiento_id', type=int)
    presupuesto_id = request.form.get('presupuesto_id', type=int)  # Para actualizar un presupuesto específico
    
    if not proyecto_id:
        return jsonify({'status': 'error', 'message': 'Proyecto no especificado'})
    
    # Si hay un presupuesto_id específico, actualizar ese presupuesto
    if presupuesto_id:
        presupuesto = Presupuesto.get_by_id(presupuesto_id)
        if not presupuesto:
            return jsonify({'status': 'error', 'message': 'Presupuesto no encontrado'})
        result = presupuesto.update(
            numero_presupuesto=numero_presupuesto,
            fecha=fecha,
            obra=obra,
            cliente_id=cliente_id,
            cliente_nombre=cliente_nombre,
            cliente_email=cliente_email,
            cliente_telefono=cliente_telefono,
            descuento=descuento,
            iva=iva,
            generalidades=generalidades,
            tipo_presupuesto=tipo_presupuesto,
            incidencia_id=incidencia_id,
            visita_mantenimiento_id=visita_mantenimiento_id
        )
        if result:
            return jsonify({
                'status': 'success',
                'message': 'Presupuesto actualizado correctamente',
                'presupuesto': presupuesto.to_dict()
            })
        else:
            return jsonify({'status': 'error', 'message': 'Error al actualizar presupuesto'})
    # Verificar si existe presupuesto principal (solo para presupuestos principales)
    elif tipo_presupuesto == 'principal':
        presupuesto = Presupuesto.get_by_proyecto(proyecto_id)
        if presupuesto and presupuesto.tipo_presupuesto == 'principal':
            # Actualizar presupuesto principal existente
            result = presupuesto.update(
                numero_presupuesto=numero_presupuesto,
                fecha=fecha,
                obra=obra,
                cliente_id=cliente_id,
                cliente_nombre=cliente_nombre,
                cliente_email=cliente_email,
                cliente_telefono=cliente_telefono,
                descuento=descuento,
                iva=iva,
                generalidades=generalidades,
                tipo_presupuesto=tipo_presupuesto,
                incidencia_id=incidencia_id,
                visita_mantenimiento_id=visita_mantenimiento_id
            )
            if result:
                return jsonify({
                    'status': 'success',
                    'message': 'Presupuesto actualizado correctamente',
                    'presupuesto': presupuesto.to_dict()
                })
            else:
                return jsonify({'status': 'error', 'message': 'Error al actualizar presupuesto'})
    
    # Crear nuevo presupuesto (principal o secundario)
    result = Presupuesto.create(
        proyecto_id=proyecto_id,
        numero_presupuesto=numero_presupuesto,
        fecha=fecha,
        obra=obra,
        cliente_id=cliente_id,
        cliente_nombre=cliente_nombre,
        cliente_email=cliente_email,
        cliente_telefono=cliente_telefono,
        descuento=descuento or 0,
        iva=iva or 19,
        generalidades=generalidades,
        tipo_presupuesto=tipo_presupuesto,
        incidencia_id=incidencia_id,
        visita_mantenimiento_id=visita_mantenimiento_id
    )
    if isinstance(result, Presupuesto):
        return jsonify({
            'status': 'success',
            'message': 'Presupuesto creado correctamente',
            'presupuesto': result.to_dict()
        })
    else:
        return jsonify({'status': 'error', 'message': f'Error al crear presupuesto: {result}'})

@app.route('/add_presupuesto_item', methods=['POST'])
@login_required
def add_presupuesto_item():
    if is_cliente(current_user):
        return jsonify({'status': 'error', 'message': 'No tienes permisos para agregar items'})
    
    proyecto_id = request.form.get('proyecto_id', type=int)
    presupuesto_id = request.form.get('presupuesto_id', type=int)
    referencia = request.form.get('referencia')
    cantidad = request.form.get('cantidad', type=float)
    ubicacion = request.form.get('ubicacion')
    tipologia = request.form.get('tipologia')
    tipo = request.form.get('tipo')
    caracteristicas = request.form.get('caracteristicas')
    valor_unitario = request.form.get('valor_unitario', type=float)
    
    # Si no hay presupuesto_id pero hay proyecto_id, crear presupuesto primero
    if not presupuesto_id and proyecto_id:
        proyecto = Proyecto.get_by_id(proyecto_id)
        if not proyecto:
            return jsonify({'status': 'error', 'message': 'Proyecto no encontrado'})
        
        # Obtener información del cliente del proyecto
        asignados = proyecto.get_asignados()
        cliente_nombre = asignados[0]['nombre'] if asignados else proyecto.nombre
        cliente_email = asignados[0]['email'] if asignados else ''
        
        presupuesto = Presupuesto.create(
            proyecto_id=proyecto_id,
            obra=proyecto.nombre,
            cliente_nombre=cliente_nombre,
            cliente_email=cliente_email
        )
        if isinstance(presupuesto, Presupuesto):
            presupuesto_id = presupuesto.id
        else:
            return jsonify({'status': 'error', 'message': f'Error al crear presupuesto: {presupuesto}'})
    
    if not presupuesto_id:
        return jsonify({'status': 'error', 'message': 'Presupuesto no especificado'})
    
    result = PresupuestoItem.create(
        presupuesto_id=presupuesto_id,
        referencia=referencia,
        cantidad=cantidad or 1,
        ubicacion=ubicacion,
        tipologia=tipologia,
        tipo=tipo,
        caracteristicas=caracteristicas,
        valor_unitario=valor_unitario or 0
    )
    
    if isinstance(result, PresupuestoItem):
        return jsonify({
            'status': 'success',
            'message': 'Item agregado correctamente',
            'item': result.to_dict()
        })
    else:
        return jsonify({'status': 'error', 'message': f'Error al agregar item: {result}'})

@app.route('/update_presupuesto_item/<int:item_id>', methods=['POST'])
@login_required
def update_presupuesto_item(item_id):
    if is_cliente(current_user):
        return jsonify({'status': 'error', 'message': 'No tienes permisos para editar items'})
    
    item = PresupuestoItem.get_by_id(item_id)
    
    if not item:
        return jsonify({'status': 'error', 'message': 'Item no encontrado'})
    
    referencia = request.form.get('referencia')
    cantidad = request.form.get('cantidad', type=float)
    ubicacion = request.form.get('ubicacion')
    tipologia = request.form.get('tipologia')
    tipo = request.form.get('tipo')
    caracteristicas = request.form.get('caracteristicas')
    valor_unitario = request.form.get('valor_unitario', type=float)
    
    result = item.update(
        referencia=referencia,
        cantidad=cantidad,
        ubicacion=ubicacion,
        tipologia=tipologia,
        tipo=tipo,
        caracteristicas=caracteristicas,
        valor_unitario=valor_unitario
    )
    
    if result:
        return jsonify({
            'status': 'success',
            'message': 'Item actualizado correctamente',
            'item': item.to_dict()
        })
    else:
        return jsonify({'status': 'error', 'message': 'Error al actualizar item'})

@app.route('/api/presupuesto/item/<int:item_id>', methods=['GET'])
@login_required
def api_presupuesto_item_get(item_id):
    """API para obtener un item del presupuesto"""
    item = PresupuestoItem.get_by_id(item_id)
    if not item:
        return jsonify({'status': 'error', 'message': 'Item no encontrado'}), 404
    return jsonify({'status': 'success', 'item': item.to_dict()})

@app.route('/delete_presupuesto_item/<int:item_id>', methods=['POST'])
@login_required
def delete_presupuesto_item(item_id):
    if is_cliente(current_user):
        return jsonify({'status': 'error', 'message': 'No tienes permisos para eliminar items'})
    
    result = PresupuestoItem.delete(item_id)
    if result:
        return jsonify({'status': 'success', 'message': 'Item eliminado correctamente'})
    else:
        return jsonify({'status': 'error', 'message': 'Error al eliminar item'})

# Rutas para gestión de activos
@app.route('/add_activo', methods=['POST'])
@login_required
def add_activo():
    if is_cliente(current_user):
        return jsonify({'status': 'error', 'message': 'No tienes permisos para agregar activos'})
    
    proyecto_id = request.form.get('proyecto_id')
    nombre = request.form.get('nombre')
    tipo = request.form.get('tipo')
    estado = request.form.get('estado')
    numero_serie = request.form.get('numero_serie')
    ubicacion = request.form.get('ubicacion')
    fecha_compra = request.form.get('fecha_compra')
    fecha_instalacion = request.form.get('fecha_instalacion')
    valor = request.form.get('valor')
    asignado = request.form.get('asignado')
    cuenta_vinculada = request.form.get('cuenta_vinculada')
    ip = request.form.get('ip')
    password = request.form.get('password')
    detalles = request.form.get('detalles')
    
    if not proyecto_id or not nombre:
        return jsonify({'status': 'error', 'message': 'Proyecto y nombre son obligatorios'})
    
    # Obtener creador_id y creador_tipo
    creador_id = current_user.id
    creador_tipo = 'user' if is_user(current_user) else 'cliente'
    
    result = Activo.create(
        proyecto_id=int(proyecto_id),
        nombre=nombre,
        tipo=tipo,
        estado=estado,
        numero_serie=numero_serie if numero_serie else None,
        ubicacion=ubicacion if ubicacion else None,
        fecha_compra=fecha_compra if fecha_compra else None,
        fecha_instalacion=fecha_instalacion if fecha_instalacion else None,
        valor=float(valor) if valor else None,
        asignado_id=None,
        asignado_tipo=None,
        asignado=asignado if asignado else None,
        cuenta_vinculada=cuenta_vinculada if cuenta_vinculada else None,
        ip=ip if ip else None,
        password=password if password else None,
        detalles=detalles if detalles else None,
        creador_id=creador_id,
        creador_tipo=creador_tipo
    )
    
    if isinstance(result, Activo):
        return jsonify({
            'status': 'success',
            'message': 'Activo creado correctamente',
            'activo': result.to_dict(
                current_user_id=creador_id,
                current_user_is_admin=is_admin(current_user),
                current_user_tipo=creador_tipo
            )
        })
    else:
        return jsonify({'status': 'error', 'message': f'Error al crear activo: {result}'})

@app.route('/update_activo/<int:activo_id>', methods=['POST'])
@login_required
def update_activo(activo_id):
    if is_cliente(current_user):
        return jsonify({'status': 'error', 'message': 'No tienes permisos para editar activos'})
    
    activo = Activo.get_by_id(activo_id)
    if not activo:
        return jsonify({'status': 'error', 'message': 'Activo no encontrado'})
    
    # Verificar permisos: solo el creador o admin puede editar
    is_admin_user = is_admin(current_user)
    current_user_id = current_user.id
    current_user_tipo = 'user' if is_user(current_user) else 'cliente'
    
    puede_editar = is_admin_user or (activo.creador_id == current_user_id and activo.creador_tipo == current_user_tipo)
    if not puede_editar:
        return jsonify({'status': 'error', 'message': 'No tienes permisos para editar este activo'})
    
    nombre = request.form.get('nombre')
    tipo = request.form.get('tipo')
    estado = request.form.get('estado')
    numero_serie = request.form.get('numero_serie')
    ubicacion = request.form.get('ubicacion')
    fecha_compra = request.form.get('fecha_compra')
    fecha_instalacion = request.form.get('fecha_instalacion')
    valor = request.form.get('valor')
    asignado = request.form.get('asignado')
    cuenta_vinculada = request.form.get('cuenta_vinculada')
    ip = request.form.get('ip')
    password = request.form.get('password')
    detalles = request.form.get('detalles')
    
    result = activo.update(
        nombre=nombre if nombre else None,
        tipo=tipo if tipo else None,
        estado=estado if estado else None,
        numero_serie=numero_serie if numero_serie else None,
        ubicacion=ubicacion if ubicacion else None,
        fecha_compra=fecha_compra if fecha_compra else None,
        fecha_instalacion=fecha_instalacion if fecha_instalacion else None,
        valor=float(valor) if valor else None,
        asignado_id=None,
        asignado_tipo=None,
        asignado=asignado if asignado is not None else None,
        cuenta_vinculada=cuenta_vinculada if cuenta_vinculada is not None else None,
        ip=ip if ip is not None else None,
        password=password if password is not None else None,
        detalles=detalles if detalles else None
    )
    
    if result:
        # Recargar activo actualizado
        activo_actualizado = Activo.get_by_id(activo_id)
        return jsonify({
            'status': 'success',
            'message': 'Activo actualizado correctamente',
            'activo': activo_actualizado.to_dict(
                current_user_id=current_user_id,
                current_user_is_admin=is_admin_user,
                current_user_tipo=current_user_tipo
            )
        })
    else:
        return jsonify({'status': 'error', 'message': 'Error al actualizar activo'})

@app.route('/delete_activo/<int:activo_id>', methods=['POST'])
@login_required
def delete_activo(activo_id):
    if is_cliente(current_user):
        return jsonify({'status': 'error', 'message': 'No tienes permisos para eliminar activos'})
    
    activo = Activo.get_by_id(activo_id)
    if not activo:
        return jsonify({'status': 'error', 'message': 'Activo no encontrado'})
    
    # Verificar permisos: solo el creador o admin puede eliminar
    is_admin_user = is_admin(current_user)
    current_user_id = current_user.id
    current_user_tipo = 'user' if is_user(current_user) else 'cliente'
    
    puede_eliminar = is_admin_user or (activo.creador_id == current_user_id and activo.creador_tipo == current_user_tipo)
    if not puede_eliminar:
        return jsonify({'status': 'error', 'message': 'No tienes permisos para eliminar este activo'})
    
    result = Activo.delete(activo_id)
    if result:
        return jsonify({'status': 'success', 'message': 'Activo eliminado correctamente'})
    else:
        return jsonify({'status': 'error', 'message': 'Error al eliminar activo'})

@app.route('/get_activo/<int:activo_id>', methods=['GET'])
@login_required
def get_activo(activo_id):
    if is_cliente(current_user):
        return jsonify({'status': 'error', 'message': 'No tienes permisos para ver activos'})
    
    activo = Activo.get_by_id(activo_id)
    if not activo:
        return jsonify({'status': 'error', 'message': 'Activo no encontrado'})
    
    is_admin_user = is_admin(current_user)
    current_user_id = current_user.id
    current_user_tipo = 'user' if is_user(current_user) else 'cliente'
    
    return jsonify({
        'status': 'success',
        'activo': activo.to_dict(
            current_user_id=current_user_id,
            current_user_is_admin=is_admin_user,
            current_user_tipo=current_user_tipo
        )
    })

@app.route('/search_activos_by_proyecto', methods=['GET'])
@login_required
def search_activos_by_proyecto():
    """Busca activos de un proyecto para vincular a visitas de mantenimiento"""
    proyecto_id = request.args.get('proyecto_id', type=int)
    query = request.args.get('q', '').strip()
    
    if not proyecto_id:
        return jsonify({'status': 'error', 'message': 'Proyecto no especificado'})
    
    # Obtener todos los activos del proyecto
    activos = Activo.get_by_proyecto(proyecto_id)
    
    # Filtrar por búsqueda si se proporciona
    if query:
        query_lower = query.lower()
        activos = [a for a in activos if query_lower in a.nombre.lower() or 
                   (a.tipo and query_lower in a.tipo.lower()) or
                   (a.ubicacion and query_lower in a.ubicacion.lower())]
    
    # Convertir a diccionarios
    activos_dict = []
    for activo in activos:
        activos_dict.append({
            'id': activo.id,
            'nombre': activo.nombre,
            'tipo': activo.tipo or '',
            'ubicacion': activo.ubicacion or '',
            'estado': activo.estado or ''
        })
    
    return jsonify({
        'status': 'success',
        'activos': activos_dict
    })

@app.route('/search_presupuesto_items', methods=['GET'])
@login_required
def search_presupuesto_items():
    """Busca items del presupuesto de un proyecto"""
    if is_cliente(current_user):
        return jsonify({'status': 'error', 'message': 'No tienes permisos para buscar items'})
    
    proyecto_id = request.args.get('proyecto_id', type=int)
    query = request.args.get('q', '').strip()
    
    if not proyecto_id:
        return jsonify({'status': 'error', 'message': 'Proyecto no especificado'})
    
    # Obtener presupuesto del proyecto
    presupuesto = Presupuesto.get_by_proyecto(proyecto_id)
    if not presupuesto:
        return jsonify({'status': 'success', 'results': []})
    
    # Obtener items del presupuesto
    items = PresupuestoItem.get_by_presupuesto(presupuesto.id)
    
    # Filtrar por query si existe
    results = []
    query_lower = query.lower() if query else ''
    
    for item in items:
        # Buscar en referencia, tipologia, ubicacion, caracteristicas
        match = False
        if query_lower:
            if (item.referencia and query_lower in item.referencia.lower()) or \
               (item.tipologia and query_lower in item.tipologia.lower()) or \
               (item.ubicacion and query_lower in item.ubicacion.lower()) or \
               (item.caracteristicas and query_lower in item.caracteristicas.lower()):
                match = True
        else:
            match = True
        
        if match:
            # Crear display name
            display_parts = []
            if item.referencia:
                display_parts.append(f"Ref: {item.referencia}")
            if item.tipologia:
                display_parts.append(item.tipologia)
            if item.ubicacion:
                display_parts.append(f"({item.ubicacion})")
            
            display = ' - '.join(display_parts) if display_parts else f"Item #{item.id}"
            
            results.append({
                'id': item.id,
                'display': display,
                'referencia': item.referencia,
                'tipologia': item.tipologia,
                'ubicacion': item.ubicacion,
                'tipo': item.tipo,
                'caracteristicas': item.caracteristicas,
                'valor_unitario': float(item.valor_unitario) if item.valor_unitario else 0,
                'cantidad': float(item.cantidad) if item.cantidad else 0
            })
    
    return jsonify({
        'status': 'success',
        'results': results
    })

# Las funciones is_user, is_cliente, is_admin ya están definidas arriba
# Estas son duplicadas, se mantienen las de arriba

# Inyectar current_user y funciones helper en todos los templates
@app.context_processor
def inject_user():
    
    # Obtener proyectos en curso para la sidebar
    proyectos_en_curso = []
    proyectos_con_presupuesto = []
    if current_user and current_user.is_authenticated:
        is_admin_user = is_admin(current_user)
        if is_cliente(current_user):
            proyectos_en_curso = Proyecto.get_en_curso_by_asignado(
                current_user.id, 'cliente', is_admin_user
            )
        elif is_user(current_user):
            proyectos_en_curso = Proyecto.get_en_curso_by_asignado(
                current_user.id, 'user', is_admin_user
            )
        
        # Obtener proyectos con presupuesto para el menú de Presupuestos
        if is_user(current_user) and not is_cliente(current_user):
            proyectos_con_presupuesto = Proyecto.get_con_presupuesto(is_admin_user)
    
    return dict(
        current_user=current_user,
        is_cliente=is_cliente,
        is_user=is_user,
        is_admin=is_admin,
        proyectos_en_curso=proyectos_en_curso,
        proyectos_con_presupuesto=proyectos_con_presupuesto
    )

@app.route('/soporte/incidencias')
@login_required
def soporte_incidencias():
    """Vista de incidencias para administradores"""
    from datetime import datetime
    is_admin_user = is_admin(current_user)
    
    if not is_admin_user:
        flash('No tienes permisos para acceder a esta página', 'error')
        return redirect(url_for('projects'))
    
    # Obtener todas las incidencias abiertas
    incidencias = Incidencia.get_all_abiertas()
    incidencias_dict = []
    for incidencia in incidencias:
        incidencia_dict = incidencia.to_dict()
        # Obtener comentarios de la incidencia
        comentarios_incidencia = ComentarioIncidencia.get_by_incidencia(incidencia.id)
        incidencia_dict['comentarios'] = [c.to_dict() for c in comentarios_incidencia]
        incidencias_dict.append(incidencia_dict)
    
    return render_template('soporte_incidencias.html', 
                         now=datetime.now(), 
                         incidencias=incidencias_dict,
                         is_admin_user=is_admin_user)

@app.route('/add_incidencia', methods=['POST'])
@login_required
def add_incidencia():
    """Crea una nueva incidencia"""
    proyecto_id = request.form.get('proyecto_id', type=int)
    activo_id = request.form.get('activo_id', type=int)
    titulo = request.form.get('titulo')
    descripcion = request.form.get('descripcion')
    
    if not proyecto_id or not titulo:
        return jsonify({'status': 'error', 'message': 'Proyecto y título son obligatorios'})
    
    # Verificar permisos: solo clientes pueden crear incidencias desde project_detail
    if not is_cliente(current_user):
        return jsonify({'status': 'error', 'message': 'Solo los clientes pueden reportar incidencias'})
    
    creador_id = current_user.id
    creador_tipo = 'cliente'
    
    result = Incidencia.create(
        proyecto_id=proyecto_id,
        activo_id=activo_id if activo_id else None,
        titulo=titulo,
        descripcion=descripcion,
        creador_id=creador_id,
        creador_tipo=creador_tipo
    )
    
    if isinstance(result, Incidencia):
        return jsonify({
            'status': 'success',
            'message': 'Incidencia reportada correctamente',
            'incidencia': result.to_dict()
        })
    else:
        return jsonify({'status': 'error', 'message': f'Error al crear incidencia: {result}'})

@app.route('/update_incidencia_estado/<int:incidencia_id>', methods=['POST'])
@login_required
def update_incidencia_estado(incidencia_id):
    """Actualiza el estado de una incidencia (administradores y equipo asignado)"""
    incidencia = Incidencia.get_by_id(incidencia_id)
    if not incidencia:
        return jsonify({'status': 'error', 'message': 'Incidencia no encontrada'})
    
    # Verificar permisos: admin o usuario asignado al proyecto
    is_admin_user = is_admin(current_user)
    tiene_acceso = False
    
    if is_admin_user:
        tiene_acceso = True
    else:
        # Verificar si el usuario está asignado al proyecto
        conn = get_db_connection()
        cur = conn.cursor()
        if is_user(current_user):
            cur.execute("""
                SELECT COUNT(*) FROM proyecto_asignaciones 
                WHERE proyecto_id = %s AND asignado_id = %s AND tipo_asignado = 'user'
            """, (incidencia.proyecto_id, current_user.id))
            count = cur.fetchone()[0]
            tiene_acceso = count > 0
        cur.close()
        conn.close()
    
    if not tiene_acceso:
        return jsonify({'status': 'error', 'message': 'No tienes permisos para realizar esta acción'})
    
    nuevo_estado = request.form.get('estado')
    if not nuevo_estado:
        return jsonify({'status': 'error', 'message': 'Estado no especificado'})
    
    result = incidencia.update_estado(nuevo_estado)
    
    if result:
        return jsonify({
            'status': 'success',
            'message': 'Estado actualizado correctamente',
            'incidencia': incidencia.to_dict()
        })
    else:
        return jsonify({'status': 'error', 'message': 'Error al actualizar el estado'})

@app.route('/resolver_incidencia/<int:incidencia_id>', methods=['POST'])
@login_required
def resolver_incidencia(incidencia_id):
    """Resuelve una incidencia con opciones de solución (reemplazar, reparar, etc.)"""
    incidencia = Incidencia.get_by_id(incidencia_id)
    if not incidencia:
        return jsonify({'status': 'error', 'message': 'Incidencia no encontrada'})
    
    # Verificar permisos: admin o usuario asignado al proyecto
    is_admin_user = is_admin(current_user)
    tiene_acceso = False
    
    if is_admin_user:
        tiene_acceso = True
    else:
        # Verificar si el usuario está asignado al proyecto
        conn = get_db_connection()
        cur = conn.cursor()
        if is_user(current_user):
            cur.execute("""
                SELECT COUNT(*) FROM proyecto_asignaciones 
                WHERE proyecto_id = %s AND asignado_id = %s AND tipo_asignado = 'user'
            """, (incidencia.proyecto_id, current_user.id))
            count = cur.fetchone()[0]
            tiene_acceso = count > 0
        cur.close()
        conn.close()
    
    if not tiene_acceso:
        return jsonify({'status': 'error', 'message': 'No tienes permisos para resolver esta incidencia'})
    
    solucion = request.form.get('solucion', 'resuelta')  # resuelta, reemplazado, reparado, etc.
    comentario_resolucion = request.form.get('comentario_resolucion', '')
    
    # Actualizar estado de la incidencia
    result = incidencia.update_estado('resuelta')
    
    if result:
        # Actualizar estado del activo según la solución
        if incidencia.activo_id:
            activo = Activo.get_by_id(incidencia.activo_id)
            if activo:
                if solucion == 'reemplazado':
                    activo.update(estado='retirado')
                    # Opcional: crear un nuevo activo reemplazado
                elif solucion == 'reparado':
                    activo.update(estado='operativo')
                elif solucion == 'resuelta':
                    activo.update(estado='operativo')
                else:
                    activo.update(estado='operativo')
        
        # Agregar comentario de resolución si se proporciona
        if comentario_resolucion:
            autor_id = current_user.id
            tipo_autor = 'user'
            ComentarioIncidencia.create(
                incidencia_id=incidencia_id,
                autor_id=autor_id,
                tipo_autor=tipo_autor,
                comentario=f"[RESUELTO - {solucion.upper()}] {comentario_resolucion}"
            )
        
        return jsonify({
            'status': 'success',
            'message': f'Incidencia resuelta. Solución aplicada: {solucion}',
            'incidencia': incidencia.to_dict()
        })
    else:
        return jsonify({'status': 'error', 'message': 'Error al resolver la incidencia'})

@app.route('/add_comentario_incidencia', methods=['POST'])
@login_required
def add_comentario_incidencia():
    """Agrega un comentario a una incidencia"""
    incidencia_id = request.form.get('incidencia_id', type=int)
    comentario = request.form.get('comentario')
    
    if not incidencia_id or not comentario:
        return jsonify({'status': 'error', 'message': 'Incidencia y comentario son obligatorios'})
    
    incidencia = Incidencia.get_by_id(incidencia_id)
    if not incidencia:
        return jsonify({'status': 'error', 'message': 'Incidencia no encontrada'})
    
    # Verificar permisos: el usuario debe estar relacionado con el proyecto
    proyecto = Proyecto.get_by_id(incidencia.proyecto_id)
    if not proyecto:
        return jsonify({'status': 'error', 'message': 'Proyecto no encontrado'})
    
    # Verificar acceso al proyecto
    tiene_acceso = False
    if is_admin(current_user):
        tiene_acceso = True
    else:
        conn = get_db_connection()
        cur = conn.cursor()
        if is_cliente(current_user):
            cur.execute("""
                SELECT COUNT(*) FROM proyecto_asignaciones 
                WHERE proyecto_id = %s AND asignado_id = %s AND tipo_asignado = 'cliente'
            """, (incidencia.proyecto_id, current_user.id))
            count_asignado = cur.fetchone()[0]
            cur.execute("""
                SELECT COUNT(*) FROM presupuestos 
                WHERE proyecto_id = %s AND cliente_id = %s
            """, (incidencia.proyecto_id, current_user.id))
            count_presupuesto = cur.fetchone()[0]
            tiene_acceso = count_asignado > 0 or count_presupuesto > 0
        else:
            cur.execute("""
                SELECT COUNT(*) FROM proyecto_asignaciones 
                WHERE proyecto_id = %s AND asignado_id = %s AND tipo_asignado = 'user'
            """, (incidencia.proyecto_id, current_user.id))
            count = cur.fetchone()[0]
            tiene_acceso = count > 0
        cur.close()
        conn.close()
    
    if not tiene_acceso:
        return jsonify({'status': 'error', 'message': 'No tienes permisos para comentar en esta incidencia'})
    
    autor_id = current_user.id
    tipo_autor = 'cliente' if is_cliente(current_user) else 'user'
    
    result = ComentarioIncidencia.create(
        incidencia_id=incidencia_id,
        autor_id=autor_id,
        tipo_autor=tipo_autor,
        comentario=comentario
    )
    
    if isinstance(result, ComentarioIncidencia):
        return jsonify({
            'status': 'success',
            'message': 'Comentario agregado correctamente',
            'comentario': result.to_dict()
        })
    else:
        return jsonify({'status': 'error', 'message': f'Error al agregar comentario: {result}'})

@app.route('/get_incidencias/<int:proyecto_id>', methods=['GET'])
@login_required
def get_incidencias(proyecto_id):
    """Obtiene todas las incidencias de un proyecto"""
    # Verificar permisos
    proyecto = Proyecto.get_by_id(proyecto_id)
    if not proyecto:
        return jsonify({'status': 'error', 'message': 'Proyecto no encontrado'})
    
    is_admin_user = is_admin(current_user)
    tiene_acceso = False
    
    if is_admin_user:
        tiene_acceso = True
    else:
        conn = get_db_connection()
        cur = conn.cursor()
        if is_cliente(current_user):
            cur.execute("""
                SELECT COUNT(*) FROM proyecto_asignaciones 
                WHERE proyecto_id = %s AND asignado_id = %s AND tipo_asignado = 'cliente'
            """, (proyecto_id, current_user.id))
            count_asignado = cur.fetchone()[0]
            cur.execute("""
                SELECT COUNT(*) FROM presupuestos 
                WHERE proyecto_id = %s AND cliente_id = %s
            """, (proyecto_id, current_user.id))
            count_presupuesto = cur.fetchone()[0]
            tiene_acceso = count_asignado > 0 or count_presupuesto > 0
        else:
            cur.execute("""
                SELECT COUNT(*) FROM proyecto_asignaciones 
                WHERE proyecto_id = %s AND asignado_id = %s AND tipo_asignado = 'user'
            """, (proyecto_id, current_user.id))
            count = cur.fetchone()[0]
            tiene_acceso = count > 0
        cur.close()
        conn.close()
    
    if not tiene_acceso:
        return jsonify({'status': 'error', 'message': 'No tienes permisos para ver las incidencias de este proyecto'})
    
    incidencias = Incidencia.get_by_proyecto(proyecto_id)
    incidencias_dict = []
    for incidencia in incidencias:
        incidencia_dict = incidencia.to_dict()
        comentarios_incidencia = ComentarioIncidencia.get_by_incidencia(incidencia.id)
        incidencia_dict['comentarios'] = [c.to_dict() for c in comentarios_incidencia]
        incidencias_dict.append(incidencia_dict)
    
    return jsonify({'status': 'success', 'incidencias': incidencias_dict})

@app.route('/get_incidencia/<int:incidencia_id>', methods=['GET'])
@login_required
def get_incidencia(incidencia_id):
    """Obtiene una incidencia específica con todos sus detalles"""
    is_admin_user = is_admin(current_user)
    if not is_admin_user:
        return jsonify({'status': 'error', 'message': 'No tienes permisos para ver esta incidencia'})
    
    incidencia = Incidencia.get_by_id(incidencia_id)
    if not incidencia:
        return jsonify({'status': 'error', 'message': 'Incidencia no encontrada'})
    
    incidencia_dict = incidencia.to_dict()
    comentarios_incidencia = ComentarioIncidencia.get_by_incidencia(incidencia.id)
    incidencia_dict['comentarios'] = [c.to_dict() for c in comentarios_incidencia]
    
    return jsonify({'status': 'success', 'incidencia': incidencia_dict})

@app.route('/aprobar_proyecto/<int:proyecto_id>', methods=['POST'])
@login_required
def aprobar_proyecto(proyecto_id):
    """Permite a un cliente aprobar un presupuesto"""
    if not is_cliente(current_user):
        return jsonify({'status': 'error', 'message': 'Solo los clientes pueden aprobar presupuestos'})
    
    proyecto = Proyecto.get_by_id(proyecto_id)
    if not proyecto:
        return jsonify({'status': 'error', 'message': 'Proyecto no encontrado'})
    
    # Verificar que el proyecto esté en estado espera_aprobacion
    if proyecto.estado != 'espera_aprobacion':
        return jsonify({'status': 'error', 'message': 'El proyecto no está en estado de espera de aprobación'})
    
    # Verificar que el cliente tenga acceso al proyecto (asignado o cliente del presupuesto)
    tiene_acceso = False
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Verificar si está asignado como parte del equipo
    cur.execute("""
        SELECT COUNT(*) FROM proyecto_asignaciones 
        WHERE proyecto_id = %s AND asignado_id = %s AND tipo_asignado = 'cliente'
    """, (proyecto_id, current_user.id))
    count_asignado = cur.fetchone()[0]
    
    # Verificar si es el cliente del presupuesto
    cur.execute("""
        SELECT COUNT(*) FROM presupuestos 
        WHERE proyecto_id = %s AND cliente_id = %s
    """, (proyecto_id, current_user.id))
    count_presupuesto = cur.fetchone()[0]
    
    tiene_acceso = count_asignado > 0 or count_presupuesto > 0
    cur.close()
    conn.close()
    
    if not tiene_acceso:
        return jsonify({'status': 'error', 'message': 'No tienes permisos para aprobar este proyecto'})
    
    # Actualizar estado del proyecto a "espera_pago"
    result = proyecto.update(estado='espera_pago')
    
    if result:
        log_user_action("Aprobar Proyecto", f"Cliente aprobó el proyecto '{proyecto.nombre}' - Estado: espera_pago", {'proyecto_id': proyecto_id, 'estado_anterior': 'espera_aprobacion', 'estado_nuevo': 'espera_pago'})
        return jsonify({
            'status': 'success',
            'message': 'Presupuesto aprobado correctamente. El proyecto ha pasado a estado "Espera de Pago".'
        })
    else:
        return jsonify({'status': 'error', 'message': 'Error al aprobar el presupuesto'})

@app.route('/rechazar_proyecto/<int:proyecto_id>', methods=['POST'])
@login_required
def rechazar_proyecto(proyecto_id):
    """Permite a un cliente rechazar un presupuesto"""
    if not is_cliente(current_user):
        return jsonify({'status': 'error', 'message': 'Solo los clientes pueden rechazar presupuestos'})
    
    proyecto = Proyecto.get_by_id(proyecto_id)
    if not proyecto:
        return jsonify({'status': 'error', 'message': 'Proyecto no encontrado'})
    
    # Verificar que el proyecto esté en estado espera_aprobacion
    if proyecto.estado != 'espera_aprobacion':
        return jsonify({'status': 'error', 'message': 'El proyecto no está en estado de espera de aprobación'})
    
    # Verificar que el cliente tenga acceso al proyecto (asignado o cliente del presupuesto)
    tiene_acceso = False
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Verificar si está asignado como parte del equipo
    cur.execute("""
        SELECT COUNT(*) FROM proyecto_asignaciones 
        WHERE proyecto_id = %s AND asignado_id = %s AND tipo_asignado = 'cliente'
    """, (proyecto_id, current_user.id))
    count_asignado = cur.fetchone()[0]
    
    # Verificar si es el cliente del presupuesto
    cur.execute("""
        SELECT COUNT(*) FROM presupuestos 
        WHERE proyecto_id = %s AND cliente_id = %s
    """, (proyecto_id, current_user.id))
    count_presupuesto = cur.fetchone()[0]
    
    tiene_acceso = count_asignado > 0 or count_presupuesto > 0
    cur.close()
    conn.close()
    
    if not tiene_acceso:
        return jsonify({'status': 'error', 'message': 'No tienes permisos para rechazar este proyecto'})
    
    motivo = request.form.get('motivo', '')
    
    # Actualizar estado del proyecto a "espera_ppto" (espera presupuesto, para que se pueda modificar)
    result = proyecto.update(estado='espera_ppto')
    
    if result:
        # Opcional: Agregar un comentario con el motivo del rechazo
        if motivo:
            Comentario.create(
                proyecto_id=proyecto_id,
                autor_id=current_user.id,
                tipo_autor='cliente',
                comentario=f'[RECHAZADO] Motivo: {motivo}'
            )
        
        return jsonify({
            'status': 'success',
            'message': 'Presupuesto rechazado correctamente. El proyecto ha pasado a estado "Espera PPTO" para su revisión.'
        })
    else:
        return jsonify({'status': 'error', 'message': 'Error al rechazar el presupuesto'})

@app.route('/aprobar_presupuesto_secundario/<int:presupuesto_id>', methods=['POST'])
@login_required
def aprobar_presupuesto_secundario(presupuesto_id):
    """Aprobar un presupuesto secundario"""
    if not is_cliente(current_user):
        return jsonify({'status': 'error', 'message': 'Solo los clientes pueden aprobar presupuestos'})
    
    presupuesto = Presupuesto.get_by_id(presupuesto_id)
    if not presupuesto:
        return jsonify({'status': 'error', 'message': 'Presupuesto no encontrado'})
    
    if presupuesto.tipo_presupuesto != 'secundario':
        return jsonify({'status': 'error', 'message': 'Este endpoint solo aplica para presupuestos secundarios'})
    
    # Verificar que el cliente es el dueño del presupuesto
    if presupuesto.cliente_id != current_user.id:
        return jsonify({'status': 'error', 'message': 'No tienes permisos para aprobar este presupuesto'})
    
    result = presupuesto.update(estado_presupuesto='aprobado')
    if result:
        log_user_action("Aprobar Presupuesto Secundario", f"Cliente aprobó presupuesto secundario #{presupuesto.numero_presupuesto}", {'presupuesto_id': presupuesto_id, 'proyecto_id': presupuesto.proyecto_id})
        return jsonify({
            'status': 'success',
            'message': 'Presupuesto aprobado correctamente'
        })
    else:
        return jsonify({'status': 'error', 'message': 'Error al aprobar presupuesto'})

@app.route('/rechazar_presupuesto_secundario/<int:presupuesto_id>', methods=['POST'])
@login_required
def rechazar_presupuesto_secundario(presupuesto_id):
    """Rechazar un presupuesto secundario"""
    if not is_cliente(current_user):
        return jsonify({'status': 'error', 'message': 'Solo los clientes pueden rechazar presupuestos'})
    
    presupuesto = Presupuesto.get_by_id(presupuesto_id)
    if not presupuesto:
        return jsonify({'status': 'error', 'message': 'Presupuesto no encontrado'})
    
    if presupuesto.tipo_presupuesto != 'secundario':
        return jsonify({'status': 'error', 'message': 'Este endpoint solo aplica para presupuestos secundarios'})
    
    # Verificar que el cliente es el dueño del presupuesto
    if presupuesto.cliente_id != current_user.id:
        return jsonify({'status': 'error', 'message': 'No tienes permisos para rechazar este presupuesto'})
    
    motivo = request.form.get('motivo', '')
    result = presupuesto.update(estado_presupuesto='rechazado')
    if result:
        log_user_action("Rechazar Presupuesto Secundario", f"Cliente rechazó presupuesto secundario #{presupuesto.numero_presupuesto}" + (f" - Motivo: {motivo}" if motivo else ""), {'presupuesto_id': presupuesto_id, 'proyecto_id': presupuesto.proyecto_id})
        return jsonify({
            'status': 'success',
            'message': 'Presupuesto rechazado correctamente'
        })
    else:
        return jsonify({'status': 'error', 'message': 'Error al rechazar presupuesto'})

# Rutas para mantenimiento
@app.route('/save_mantenimiento_config', methods=['POST'])
@login_required
def save_mantenimiento_config():
    """Guarda o actualiza la configuración de mantenimiento de un proyecto"""
    if is_cliente(current_user):
        return jsonify({'status': 'error', 'message': 'No tienes permisos para modificar la configuración de mantenimiento'})
    
    proyecto_id = request.form.get('proyecto_id', type=int)
    periodo_visita = request.form.get('periodo_visita', '1 visita mensual')
    # El checkbox puede venir como '1', 'on', o '0' si no está marcado (gracias al JS)
    incluye_emergencia_val = request.form.get('incluye_emergencia', '0')
    incluye_emergencia = incluye_emergencia_val == '1' or incluye_emergencia_val == 'on'
    periodo_emergencia = request.form.get('periodo_emergencia') if incluye_emergencia else None
    
    if not proyecto_id:
        return jsonify({'status': 'error', 'message': 'Proyecto no especificado'})
    
    # Verificar que el proyecto existe y tiene mantenimiento habilitado
    proyecto = Proyecto.get_by_id(proyecto_id)
    if not proyecto:
        return jsonify({'status': 'error', 'message': 'Proyecto no encontrado'})
    
    if not (hasattr(proyecto, 'incluye_mantenimiento') and proyecto.incluye_mantenimiento):
        return jsonify({'status': 'error', 'message': 'Este proyecto no tiene mantenimiento habilitado'})
    
    result = MantenimientoConfig.create_or_update(proyecto_id, periodo_visita, incluye_emergencia, periodo_emergencia)
    
    if isinstance(result, MantenimientoConfig):
        return jsonify({
            'status': 'success',
            'message': 'Configuración de mantenimiento guardada correctamente',
            'config': result.to_dict()
        })
    else:
        return jsonify({'status': 'error', 'message': f'Error al guardar configuración: {result}'})

@app.route('/get_mantenimiento_config/<int:proyecto_id>', methods=['GET'])
@login_required
def get_mantenimiento_config(proyecto_id):
    """Obtiene la configuración de mantenimiento de un proyecto"""
    config = MantenimientoConfig.get_by_proyecto(proyecto_id)
    if config:
        return jsonify({'status': 'success', 'config': config.to_dict()})
    else:
        return jsonify({'status': 'success', 'config': None})

@app.route('/add_mantenimiento_visita', methods=['POST'])
@login_required
def add_mantenimiento_visita():
    """Crea una nueva visita de mantenimiento"""
    proyecto_id = request.form.get('proyecto_id', type=int)
    fecha_visita = request.form.get('fecha_visita')
    tipo_visita = request.form.get('tipo_visita', 'programada')
    incidencia_id = request.form.get('incidencia_id', type=int)
    comentarios = request.form.get('comentarios')
    sugerencias = request.form.get('sugerencias')
    observaciones = request.form.get('observaciones')
    
    if not proyecto_id or not fecha_visita:
        return jsonify({'status': 'error', 'message': 'Proyecto y fecha de visita son obligatorios'})
    
    # Verificar permisos
    proyecto = Proyecto.get_by_id(proyecto_id)
    if not proyecto:
        return jsonify({'status': 'error', 'message': 'Proyecto no encontrado'})
    
    # Verificar que la incidencia existe y pertenece al proyecto si se proporciona
    if incidencia_id:
        incidencia = Incidencia.get_by_id(incidencia_id)
        if not incidencia or incidencia.proyecto_id != proyecto_id:
            return jsonify({'status': 'error', 'message': 'Incidencia no válida para este proyecto'})
    
    creador_id = current_user.id
    creador_tipo = 'user' if is_user(current_user) else 'cliente'
    
    # Obtener activos seleccionados
    activos_ids = request.form.getlist('activos[]')
    activos_ids = [int(aid) for aid in activos_ids if aid and aid.isdigit()]
    
    # Verificar que los activos pertenecen al proyecto
    if activos_ids:
        for activo_id in activos_ids:
            activo = Activo.get_by_id(activo_id)
            if not activo or activo.proyecto_id != proyecto_id:
                return jsonify({'status': 'error', 'message': f'Activo {activo_id} no válido para este proyecto'})
    
    result = MantenimientoVisita.create(
        proyecto_id=proyecto_id,
        fecha_visita=fecha_visita,
        tipo_visita=tipo_visita,
        incidencia_id=incidencia_id if incidencia_id else None,
        comentarios=comentarios,
        sugerencias=sugerencias,
        observaciones=observaciones,
        creador_id=creador_id,
        creador_tipo=creador_tipo
    )
    
    # Vincular activos si se proporcionaron
    if isinstance(result, MantenimientoVisita) and activos_ids:
        result.vincular_activos(activos_ids)
    
    # Guardar respuestas de checklist si se proporcionaron
    if isinstance(result, MantenimientoVisita):
        checklist_respuestas = request.form.getlist('checklist_respuestas[]')
        for respuesta_data in checklist_respuestas:
            try:
                respuesta_dict = json.loads(respuesta_data) if isinstance(respuesta_data, str) else respuesta_data
                item_id = respuesta_dict.get('item_id')
                completado = respuesta_dict.get('completado', False)
                comentario = respuesta_dict.get('comentario')
                
                if item_id:
                    MantenimientoChecklistRespuesta.create_or_update(
                        visita_id=result.id,
                        checklist_item_id=int(item_id),
                        completado=completado,
                        comentario=comentario
                    )
            except (json.JSONDecodeError, ValueError, TypeError) as e:
                print(f"Error al procesar respuesta de checklist: {e}")
                continue
    
    if isinstance(result, MantenimientoVisita):
        return jsonify({
            'status': 'success',
            'message': 'Visita de mantenimiento creada correctamente',
            'visita': result.to_dict()
        })
    else:
        return jsonify({'status': 'error', 'message': f'Error al crear visita: {result}'})

@app.route('/update_mantenimiento_visita/<int:visita_id>', methods=['POST'])
@login_required
def update_mantenimiento_visita(visita_id):
    """Actualiza una visita de mantenimiento"""
    if is_cliente(current_user):
        return jsonify({'status': 'error', 'message': 'No tienes permisos para editar visitas'})
    
    visita = MantenimientoVisita.get_by_id(visita_id)
    if not visita:
        return jsonify({'status': 'error', 'message': 'Visita no encontrada'})
    
    fecha_visita = request.form.get('fecha_visita')
    tipo_visita = request.form.get('tipo_visita')
    incidencia_id = request.form.get('incidencia_id', type=int)
    comentarios = request.form.get('comentarios')
    sugerencias = request.form.get('sugerencias')
    observaciones = request.form.get('observaciones')
    
    # Verificar que la incidencia existe y pertenece al proyecto si se proporciona
    if incidencia_id:
        incidencia = Incidencia.get_by_id(incidencia_id)
        if not incidencia or incidencia.proyecto_id != visita.proyecto_id:
            return jsonify({'status': 'error', 'message': 'Incidencia no válida para este proyecto'})
    
    # Obtener activos seleccionados
    activos_ids = request.form.getlist('activos[]')
    activos_ids = [int(aid) for aid in activos_ids if aid and aid.isdigit()]
    
    result = visita.update(
        fecha_visita=fecha_visita if fecha_visita else None,
        tipo_visita=tipo_visita if tipo_visita else None,
        incidencia_id=incidencia_id if incidencia_id is not None else None,
        comentarios=comentarios if comentarios else None,
        sugerencias=sugerencias if sugerencias else None,
        observaciones=observaciones if observaciones else None
    )
    
    # Actualizar vinculaciones con activos
    if result and activos_ids is not None:
        visita.vincular_activos(activos_ids)
    
    # Guardar respuestas de checklist si se proporcionaron
    if result:
        checklist_respuestas = request.form.getlist('checklist_respuestas[]')
        for respuesta_data in checklist_respuestas:
            try:
                respuesta_dict = json.loads(respuesta_data) if isinstance(respuesta_data, str) else respuesta_data
                item_id = respuesta_dict.get('item_id')
                completado = respuesta_dict.get('completado', False)
                comentario = respuesta_dict.get('comentario')
                
                if item_id:
                    MantenimientoChecklistRespuesta.create_or_update(
                        visita_id=visita_id,
                        checklist_item_id=int(item_id),
                        completado=completado,
                        comentario=comentario
                    )
            except (json.JSONDecodeError, ValueError, TypeError) as e:
                print(f"Error al procesar respuesta de checklist: {e}")
                continue
    
    if result:
        return jsonify({
            'status': 'success',
            'message': 'Visita actualizada correctamente',
            'visita': visita.to_dict()
        })
    else:
        return jsonify({'status': 'error', 'message': 'Error al actualizar visita'})

@app.route('/delete_mantenimiento_visita/<int:visita_id>', methods=['POST'])
@login_required
def delete_mantenimiento_visita(visita_id):
    """Elimina una visita de mantenimiento"""
    if is_cliente(current_user):
        return jsonify({'status': 'error', 'message': 'No tienes permisos para eliminar visitas'})
    
    result = MantenimientoVisita.delete(visita_id)
    if result:
        return jsonify({'status': 'success', 'message': 'Visita eliminada correctamente'})
    else:
        return jsonify({'status': 'error', 'message': 'Error al eliminar visita'})

@app.route('/get_mantenimiento_visitas/<int:proyecto_id>', methods=['GET'])
@login_required
def get_mantenimiento_visitas(proyecto_id):
    """Obtiene todas las visitas de mantenimiento de un proyecto"""
    visitas = MantenimientoVisita.get_by_proyecto(proyecto_id)
    visitas_dict = []
    for visita in visitas:
        visita_dic = visita.to_dict()
        # Agregar respuestas de checklist con los items completos
        respuestas = MantenimientoChecklistRespuesta.get_by_visita(visita.id)
        checklist_dict = {}
        for respuesta in respuestas:
            item = MantenimientoChecklistItem.get_by_id(respuesta.checklist_item_id)
            if item:
                checklist_dict[respuesta.checklist_item_id] = {
                    'item': item.to_dict(),
                    'respuesta': respuesta.to_dict()
                }
        visita_dic['checklist_respuestas'] = checklist_dict
        visitas_dict.append(visita_dic)
    return jsonify({'status': 'success', 'visitas': visitas_dict})

@app.route('/get_checklist_items/<int:proyecto_id>', methods=['GET'])
@login_required
def get_checklist_items(proyecto_id):
    """Obtiene los items de checklist de un proyecto"""
    items = MantenimientoChecklistItem.get_by_proyecto(proyecto_id, solo_activos=True)
    items_dict = [item.to_dict() for item in items]
    return jsonify({'status': 'success', 'items': items_dict})

@app.route('/add_checklist_item', methods=['POST'])
@login_required
def add_checklist_item():
    """Agrega un item a la checklist de un proyecto"""
    if is_cliente(current_user):
        return jsonify({'status': 'error', 'message': 'No tienes permisos para modificar la checklist'})
    
    proyecto_id = request.form.get('proyecto_id', type=int)
    titulo = request.form.get('titulo')
    descripcion = request.form.get('descripcion')
    categoria = request.form.get('categoria')
    orden = request.form.get('orden', type=int) or 0
    
    if not proyecto_id or not titulo:
        return jsonify({'status': 'error', 'message': 'Proyecto y título son obligatorios'})
    
    result = MantenimientoChecklistItem.create(proyecto_id, titulo, descripcion, categoria, orden)
    
    if isinstance(result, MantenimientoChecklistItem):
        return jsonify({
            'status': 'success',
            'message': 'Item de checklist agregado correctamente',
            'item': result.to_dict()
        })
    else:
        return jsonify({'status': 'error', 'message': f'Error al agregar item: {result}'})

@app.route('/update_checklist_item/<int:item_id>', methods=['POST'])
@login_required
def update_checklist_item(item_id):
    """Actualiza un item de checklist"""
    if is_cliente(current_user):
        return jsonify({'status': 'error', 'message': 'No tienes permisos para modificar la checklist'})
    
    item = MantenimientoChecklistItem.get_by_id(item_id)
    if not item:
        return jsonify({'status': 'error', 'message': 'Item no encontrado'})
    
    titulo = request.form.get('titulo')
    descripcion = request.form.get('descripcion')
    categoria = request.form.get('categoria')
    orden = request.form.get('orden', type=int)
    activo = request.form.get('activo') == '1' if request.form.get('activo') else None
    
    result = item.update(
        titulo=titulo if titulo else None,
        descripcion=descripcion if descripcion else None,
        categoria=categoria if categoria else None,
        orden=orden if orden is not None else None,
        activo=activo if activo is not None else None
    )
    
    if result:
        return jsonify({
            'status': 'success',
            'message': 'Item actualizado correctamente',
            'item': item.to_dict()
        })
    else:
        return jsonify({'status': 'error', 'message': 'Error al actualizar item'})

@app.route('/delete_checklist_item/<int:item_id>', methods=['POST'])
@login_required
def delete_checklist_item(item_id):
    """Elimina un item de checklist"""
    if is_cliente(current_user):
        return jsonify({'status': 'error', 'message': 'No tienes permisos para eliminar items de checklist'})
    
    result = MantenimientoChecklistItem.delete(item_id)
    if result:
        return jsonify({'status': 'success', 'message': 'Item eliminado correctamente'})
    else:
        return jsonify({'status': 'error', 'message': 'Error al eliminar item'})

@app.route('/get_sesiones_instalacion/<int:proyecto_id>', methods=['GET'])
@login_required
def get_sesiones_instalacion(proyecto_id):
    """Obtiene todas las sesiones de instalación de un proyecto"""
    sesiones = InstalacionSesion.get_by_proyecto(proyecto_id)
    sesiones_dict = []
    for sesion in sesiones:
        sesion_dic = sesion.to_dict()
        # Agregar items completados
        completados = InstalacionChecklistCompletado.get_by_sesion(sesion.id)
        sesion_dic['items_completados'] = {c.checklist_item_id: c.to_dict() for c in completados}
        sesiones_dict.append(sesion_dic)
    return jsonify({'status': 'success', 'sesiones': sesiones_dict})

@app.route('/get_instalacion_checklist_items/<int:proyecto_id>', methods=['GET'])
@login_required
def get_instalacion_checklist_items(proyecto_id):
    """Obtiene los items del checklist de instalación de un proyecto"""
    items = InstalacionChecklistItem.get_by_proyecto(proyecto_id, solo_activos=True)
    items_dict = [item.to_dict() for item in items]
    return jsonify({'status': 'success', 'items': items_dict})

@app.route('/add_sesion_instalacion', methods=['POST'])
@login_required
def add_sesion_instalacion():
    """Crea una nueva sesión de instalación"""
    proyecto_id = request.form.get('proyecto_id', type=int)
    fecha = request.form.get('fecha')
    instalador_id = request.form.get('instalador_id', type=int)
    hora_llegada = request.form.get('hora_llegada')
    hora_salida = request.form.get('hora_salida')
    observaciones = request.form.get('observaciones')
    
    if not proyecto_id or not fecha or not instalador_id:
        return jsonify({'status': 'error', 'message': 'Proyecto, fecha e instalador son obligatorios'})
    
    result = InstalacionSesion.create(
        proyecto_id=proyecto_id,
        fecha=fecha,
        instalador_id=instalador_id,
        hora_llegada=hora_llegada if hora_llegada else None,
        hora_salida=hora_salida if hora_salida else None,
        observaciones=observaciones if observaciones else None
    )
    
    if isinstance(result, InstalacionSesion):
        # Guardar items completados del checklist
        sesion_id = result.id
        checklist_completados = request.form.getlist('checklist_completados[]')
        for item_data in checklist_completados:
            try:
                import json
                item_dict = json.loads(item_data) if isinstance(item_data, str) else item_data
                item_id = item_dict.get('item_id')
                hora_completado = item_dict.get('hora_completado')
                observaciones_item = item_dict.get('observaciones')
                
                if item_id:
                    InstalacionChecklistCompletado.create_or_update(
                        sesion_id=sesion_id,
                        checklist_item_id=int(item_id),
                        hora_completado=hora_completado if hora_completado else None,
                        observaciones=observaciones_item if observaciones_item else None
                    )
            except (json.JSONDecodeError, ValueError, TypeError) as e:
                print(f"Error al procesar item completado: {e}")
                continue
        
        return jsonify({
            'status': 'success',
            'message': 'Sesión de instalación creada correctamente',
            'sesion': result.to_dict()
        })
    else:
        return jsonify({'status': 'error', 'message': f'Error al crear sesión: {result}'})

@app.route('/update_sesion_instalacion/<int:sesion_id>', methods=['POST'])
@login_required
def update_sesion_instalacion(sesion_id):
    """Actualiza una sesión de instalación"""
    sesion = InstalacionSesion.get_by_id(sesion_id)
    if not sesion:
        return jsonify({'status': 'error', 'message': 'Sesión no encontrada'})
    
    fecha = request.form.get('fecha')
    hora_llegada = request.form.get('hora_llegada')
    hora_salida = request.form.get('hora_salida')
    observaciones = request.form.get('observaciones')
    
    result = sesion.update(
        fecha=fecha if fecha else None,
        hora_llegada=hora_llegada if hora_llegada else None,
        hora_salida=hora_salida if hora_salida else None,
        observaciones=observaciones if observaciones else None
    )
    
    if result:
        # Actualizar items completados
        import json
        checklist_completados = request.form.getlist('checklist_completados[]')
        # Primero eliminar todos los completados existentes para esta sesión
        items_existentes = InstalacionChecklistCompletado.get_by_sesion(sesion_id)
        items_ids_nuevos = set()
        for item_data in checklist_completados:
            try:
                item_dict = json.loads(item_data) if isinstance(item_data, str) else item_data
                item_id = item_dict.get('item_id')
                if item_id:
                    items_ids_nuevos.add(int(item_id))
            except:
                continue
        
        # Eliminar los que ya no están marcados
        for item_existente in items_existentes:
            if item_existente.checklist_item_id not in items_ids_nuevos:
                InstalacionChecklistCompletado.delete(sesion_id, item_existente.checklist_item_id)
        
        # Crear o actualizar los nuevos
        for item_data in checklist_completados:
            try:
                item_dict = json.loads(item_data) if isinstance(item_data, str) else item_data
                item_id = item_dict.get('item_id')
                hora_completado = item_dict.get('hora_completado')
                observaciones_item = item_dict.get('observaciones')
                
                if item_id:
                    InstalacionChecklistCompletado.create_or_update(
                        sesion_id=sesion_id,
                        checklist_item_id=int(item_id),
                        hora_completado=hora_completado if hora_completado else None,
                        observaciones=observaciones_item if observaciones_item else None
                    )
            except (json.JSONDecodeError, ValueError, TypeError) as e:
                print(f"Error al procesar item completado: {e}")
                continue
        
        return jsonify({
            'status': 'success',
            'message': 'Sesión actualizada correctamente',
            'sesion': sesion.to_dict()
        })
    else:
        return jsonify({'status': 'error', 'message': 'Error al actualizar sesión'})

@app.route('/delete_sesion_instalacion/<int:sesion_id>', methods=['POST'])
@login_required
def delete_sesion_instalacion(sesion_id):
    """Elimina una sesión de instalación"""
    result = InstalacionSesion.delete(sesion_id)
    if result:
        return jsonify({'status': 'success', 'message': 'Sesión eliminada correctamente'})
    else:
        return jsonify({'status': 'error', 'message': 'Error al eliminar sesión'})

@app.route('/add_instalacion_checklist_item', methods=['POST'])
@login_required
def add_instalacion_checklist_item():
    """Agrega un item al checklist de instalación"""
    proyecto_id = request.form.get('proyecto_id', type=int)
    titulo = request.form.get('titulo')
    descripcion = request.form.get('descripcion')
    activo_id = request.form.get('activo_id', type=int) if request.form.get('activo_id') else None
    presupuesto_item_id = request.form.get('presupuesto_item_id', type=int) if request.form.get('presupuesto_item_id') else None
    orden = request.form.get('orden', type=int) or 0
    
    if not proyecto_id or not titulo:
        return jsonify({'status': 'error', 'message': 'Proyecto y título son obligatorios'})
    
    result = InstalacionChecklistItem.create(
        proyecto_id=proyecto_id,
        titulo=titulo,
        descripcion=descripcion,
        activo_id=activo_id,
        presupuesto_item_id=presupuesto_item_id,
        orden=orden
    )
    
    if isinstance(result, InstalacionChecklistItem):
        return jsonify({
            'status': 'success',
            'message': 'Item agregado correctamente',
            'item': result.to_dict()
        })
    else:
        return jsonify({'status': 'error', 'message': f'Error al agregar item: {result}'})

@app.route('/update_instalacion_checklist_item/<int:item_id>', methods=['POST'])
@login_required
def update_instalacion_checklist_item(item_id):
    """Actualiza un item del checklist de instalación"""
    item = InstalacionChecklistItem.get_by_id(item_id)
    if not item:
        return jsonify({'status': 'error', 'message': 'Item no encontrado'})
    
    titulo = request.form.get('titulo')
    descripcion = request.form.get('descripcion')
    activo_id = request.form.get('activo_id', type=int) if request.form.get('activo_id') else None
    presupuesto_item_id = request.form.get('presupuesto_item_id', type=int) if request.form.get('presupuesto_item_id') else None
    orden = request.form.get('orden', type=int)
    activo = request.form.get('activo') == '1' if request.form.get('activo') else None
    
    result = item.update(
        titulo=titulo if titulo else None,
        descripcion=descripcion if descripcion else None,
        activo_id=activo_id,
        presupuesto_item_id=presupuesto_item_id,
        orden=orden if orden is not None else None,
        activo=activo if activo is not None else None
    )
    
    if result:
        return jsonify({
            'status': 'success',
            'message': 'Item actualizado correctamente',
            'item': item.to_dict()
        })
    else:
        return jsonify({'status': 'error', 'message': 'Error al actualizar item'})

@app.route('/delete_instalacion_checklist_item/<int:item_id>', methods=['POST'])
@login_required
def delete_instalacion_checklist_item(item_id):
    """Elimina un item del checklist de instalación"""
    result = InstalacionChecklistItem.delete(item_id)
    if result:
        return jsonify({'status': 'success', 'message': 'Item eliminado correctamente'})
    else:
        return jsonify({'status': 'error', 'message': 'Error al eliminar item'})

@app.route('/cargar_items_instalacion_desde_presupuesto/<int:proyecto_id>', methods=['POST'])
@login_required
def cargar_items_instalacion_desde_presupuesto(proyecto_id):
    """Carga items del presupuesto como checklist de instalación"""
    proyecto = Proyecto.get_by_id(proyecto_id)
    if not proyecto:
        return jsonify({'status': 'error', 'message': 'Proyecto no encontrado'})
    
    # Obtener presupuesto del proyecto
    presupuesto = Presupuesto.get_by_proyecto(proyecto_id)
    if not presupuesto:
        return jsonify({'status': 'error', 'message': 'No hay presupuesto asociado a este proyecto'})
    
    # Obtener items del presupuesto
    items_presupuesto = PresupuestoItem.get_by_presupuesto(presupuesto.id)
    items_creados = []
    errores = []
    
    for presupuesto_item in items_presupuesto:
        # Verificar si ya existe
        items_existentes = InstalacionChecklistItem.get_by_proyecto(proyecto_id, solo_activos=False)
        existe = False
        for item_existente in items_existentes:
            if item_existente.presupuesto_item_id == presupuesto_item.id:
                existe = True
                break
        
        if not existe:
            result = InstalacionChecklistItem.create(
                proyecto_id=proyecto_id,
                titulo=presupuesto_item.caracteristicas or f"Item {presupuesto_item.id}",
                descripcion=f"Desde presupuesto: {presupuesto_item.referencia or 'N/A'}",
                presupuesto_item_id=presupuesto_item.id,
                orden=len(items_existentes) + 1
            )
            if isinstance(result, InstalacionChecklistItem):
                items_creados.append(result.to_dict())
            else:
                errores.append(f"Error al crear item: {result}")
    
    return jsonify({
        'status': 'success',
        'message': f'Items cargados. {len(items_creados)} items creados.',
        'items_creados': items_creados,
        'errores': errores if errores else None
    })

@app.route('/cargar_checklist_default/<int:proyecto_id>', methods=['POST'])
@login_required
def cargar_checklist_default(proyecto_id):
    """Carga la checklist default de motores y portones para un proyecto"""
    if is_cliente(current_user):
        return jsonify({'status': 'error', 'message': 'No tienes permisos para cargar checklist default'})
    
    # Verificar que el proyecto existe
    proyecto = Proyecto.get_by_id(proyecto_id)
    if not proyecto:
        return jsonify({'status': 'error', 'message': 'Proyecto no encontrado'})
    
    # Checklist default para motores y portones
    checklist_default = [
        # Motores
        {'titulo': 'Verificar funcionamiento del motor', 'descripcion': 'Probar apertura y cierre del motor', 'categoria': 'Motores', 'orden': 1},
        {'titulo': 'Revisar estado de los cables', 'descripcion': 'Inspeccionar cables de alimentación y conexiones', 'categoria': 'Motores', 'orden': 2},
        {'titulo': 'Lubricar mecanismo del motor', 'descripcion': 'Aplicar lubricante a piezas móviles según especificaciones', 'categoria': 'Motores', 'orden': 3},
        {'titulo': 'Verificar límites de apertura y cierre', 'descripcion': 'Ajustar límites si es necesario', 'categoria': 'Motores', 'orden': 4},
        {'titulo': 'Revisar sensores de seguridad', 'descripcion': 'Comprobar funcionamiento de sensores fotoeléctricos y cortes', 'categoria': 'Motores', 'orden': 5},
        {'titulo': 'Limpiar y revisar control remoto', 'descripcion': 'Verificar baterías y funcionamiento de controles', 'categoria': 'Motores', 'orden': 6},
        
        # Portones
        {'titulo': 'Inspeccionar estado físico del portón', 'descripcion': 'Revisar daños, óxido, pintura', 'categoria': 'Portones', 'orden': 1},
        {'titulo': 'Verificar funcionamiento de bisagras', 'descripcion': 'Revisar desgaste y lubricar si es necesario', 'categoria': 'Portones', 'orden': 2},
        {'titulo': 'Revisar sistema de guías y rieles', 'descripcion': 'Limpiar y verificar alineación', 'categoria': 'Portones', 'orden': 3},
        {'titulo': 'Comprobar cierre hermético', 'descripcion': 'Verificar que el portón cierre correctamente', 'categoria': 'Portones', 'orden': 4},
        {'titulo': 'Revisar pestillos y cerraduras', 'descripcion': 'Verificar funcionamiento de sistemas de seguridad', 'categoria': 'Portones', 'orden': 5},
        {'titulo': 'Verificar sistema de contrapeso', 'descripcion': 'Revisar tensión de resortes o contrapesos', 'categoria': 'Portones', 'orden': 6},
        {'titulo': 'Inspeccionar pintura y protección anticorrosiva', 'descripcion': 'Identificar áreas que requieran mantenimiento', 'categoria': 'Portones', 'orden': 7},
    ]
    
    items_creados = []
    errores = []
    
    for item_data in checklist_default:
        # Verificar si ya existe un item similar (mismo título y categoría)
        items_existentes = MantenimientoChecklistItem.get_by_proyecto(proyecto_id, solo_activos=False)
        existe = False
        for item_existente in items_existentes:
            if item_existente.titulo.lower() == item_data['titulo'].lower() and item_existente.categoria == item_data['categoria']:
                existe = True
                break
        
        if not existe:
            result = MantenimientoChecklistItem.create(
                proyecto_id=proyecto_id,
                titulo=item_data['titulo'],
                descripcion=item_data.get('descripcion'),
                categoria=item_data.get('categoria'),
                orden=item_data.get('orden', 0)
            )
            if isinstance(result, MantenimientoChecklistItem):
                items_creados.append(result.to_dict())
            else:
                errores.append(f"Error al crear '{item_data['titulo']}': {result}")
    
    return jsonify({
        'status': 'success',
        'message': f'Checklist default cargada. {len(items_creados)} items creados.',
        'items_creados': items_creados,
        'errores': errores if errores else None
    })

@app.route('/upload_mantenimiento_foto', methods=['POST'])
@login_required
def upload_mantenimiento_foto():
    """Sube una foto para una visita de mantenimiento"""
    from werkzeug.utils import secure_filename
    import uuid
    
    visita_id = request.form.get('visita_id', type=int)
    descripcion = request.form.get('descripcion', '')
    
    if not visita_id or 'foto' not in request.files:
        return jsonify({'status': 'error', 'message': 'Visita y foto son obligatorios'})
    
    file = request.files['foto']
    if file.filename == '':
        return jsonify({'status': 'error', 'message': 'No se seleccionó ningún archivo'})
    
    # Verificar que la visita existe
    visita = MantenimientoVisita.get_by_id(visita_id)
    if not visita:
        return jsonify({'status': 'error', 'message': 'Visita no encontrada'})
    
    # Guardar archivo
    if file:
        filename = secure_filename(file.filename)
        # Generar nombre único
        unique_filename = f"{uuid.uuid4()}_{filename}"
        upload_folder = os.path.join('static', 'uploads', 'mantenimiento')
        os.makedirs(upload_folder, exist_ok=True)
        filepath = os.path.join(upload_folder, unique_filename)
        file.save(filepath)
        
        # Guardar ruta relativa en la base de datos
        ruta_relativa = f"/static/uploads/mantenimiento/{unique_filename}"
        
        result = MantenimientoFoto.create(visita_id, ruta_relativa, descripcion)
        
        if isinstance(result, MantenimientoFoto):
            return jsonify({
                'status': 'success',
                'message': 'Foto subida correctamente',
                'foto': result.to_dict()
            })
        else:
            return jsonify({'status': 'error', 'message': f'Error al guardar foto: {result}'})
    
    return jsonify({'status': 'error', 'message': 'Error al procesar archivo'})

@app.route('/delete_mantenimiento_foto/<int:foto_id>', methods=['POST'])
@login_required
def delete_mantenimiento_foto(foto_id):
    """Elimina una foto de mantenimiento"""
    if is_cliente(current_user):
        return jsonify({'status': 'error', 'message': 'No tienes permisos para eliminar fotos'})
    
    # Obtener foto para eliminar archivo físico
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT ruta_archivo FROM proyecto_mantenimiento_fotos WHERE id = %s", (foto_id,))
    foto_row = cur.fetchone()
    cur.close()
    conn.close()
    
    if foto_row:
        ruta_archivo = foto_row[0]
        # Eliminar archivo físico si existe
        if ruta_archivo.startswith('/'):
            ruta_archivo = ruta_archivo[1:]  # Remover / inicial
        filepath = os.path.join(ruta_archivo)
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
            except Exception as e:
                print(f"Error al eliminar archivo: {e}")
    
    result = MantenimientoFoto.delete(foto_id)
    if result:
        return jsonify({'status': 'success', 'message': 'Foto eliminada correctamente'})
    else:
        return jsonify({'status': 'error', 'message': 'Error al eliminar foto'})

@app.route('/upload_proyecto_documento', methods=['POST'])
@login_required
def upload_proyecto_documento():
    """Sube un documento para un proyecto"""
    from werkzeug.utils import secure_filename
    import uuid
    
    proyecto_id = request.form.get('proyecto_id', type=int)
    nombre_display = request.form.get('nombre_display', '').strip()
    descripcion = request.form.get('descripcion', '').strip()
    
    if not proyecto_id or 'archivo' not in request.files:
        return jsonify({'status': 'error', 'message': 'Proyecto y archivo son obligatorios'})
    
    file = request.files['archivo']
    if file.filename == '':
        return jsonify({'status': 'error', 'message': 'No se seleccionó ningún archivo'})
    
    # Verificar que el proyecto existe
    proyecto = Proyecto.get_by_id(proyecto_id)
    if not proyecto:
        return jsonify({'status': 'error', 'message': 'Proyecto no encontrado'})
    
    # Verificar permisos (solo usuarios/admin pueden subir)
    if is_cliente(current_user):
        return jsonify({'status': 'error', 'message': 'No tienes permisos para subir documentos'})
    
    # Guardar archivo
    if file:
        filename = secure_filename(file.filename)
        # Generar nombre único
        unique_filename = f"{uuid.uuid4()}_{filename}"
        upload_folder = os.path.join('static', 'uploads', 'documentos')
        os.makedirs(upload_folder, exist_ok=True)
        filepath = os.path.join(upload_folder, unique_filename)
        file.save(filepath)
        
        # Obtener información del archivo
        file_size = os.path.getsize(filepath)
        file_type = filename.split('.')[-1] if '.' in filename else 'unknown'
        
        # Usar nombre_display si se proporciona, sino usar el nombre del archivo
        if not nombre_display:
            nombre_display = filename
        
        # Guardar ruta relativa en la base de datos
        ruta_relativa = f"/static/uploads/documentos/{unique_filename}"
        
        # Determinar tipo de creador
        creador_id = current_user.id
        creador_tipo = 'user' if is_user(current_user) else 'cliente'
        
        result = DocumentoProyecto.create(
            proyecto_id, 
            filename, 
            nombre_display, 
            ruta_relativa, 
            file_type, 
            file_size, 
            creador_id, 
            creador_tipo, 
            descripcion
        )
        
        if isinstance(result, DocumentoProyecto):
            log_user_action("Subir Documento", f"Documento '{nombre_display}' subido al proyecto {proyecto_id}", {'proyecto_id': proyecto_id, 'documento_id': result.id, 'nombre': nombre_display})
            return jsonify({
                'status': 'success',
                'message': 'Documento subido correctamente',
                'documento': result.to_dict()
            })
        else:
            return jsonify({'status': 'error', 'message': f'Error al guardar documento: {result}'})
    
    return jsonify({'status': 'error', 'message': 'Error al procesar archivo'})

@app.route('/download_proyecto_documento/<int:documento_id>', methods=['GET'])
@login_required
def download_proyecto_documento(documento_id):
    """Descarga un documento del proyecto"""
    from flask import send_file
    
    documento = DocumentoProyecto.get_by_id(documento_id)
    if not documento:
        return jsonify({'status': 'error', 'message': 'Documento no encontrado'}), 404
    
    # Verificar que el usuario tiene acceso al proyecto
    proyecto = Proyecto.get_by_id(documento.proyecto_id)
    if not proyecto:
        return jsonify({'status': 'error', 'message': 'Proyecto no encontrado'}), 404
    
    # Verificar permisos (el usuario debe estar asignado al proyecto o ser admin)
    if is_cliente(current_user):
        # Cliente: verificar que está asignado al proyecto O es el cliente del presupuesto
        asignados = proyecto.get_asignados()
        cliente_asignado = any(a.get('id') == f"cliente_{current_user.id}" for a in asignados)
        
        # Si no está asignado, verificar si es el cliente del presupuesto
        if not cliente_asignado:
            presupuesto = Presupuesto.get_by_proyecto(documento.proyecto_id)
            if presupuesto and presupuesto.cliente_id == current_user.id:
                cliente_asignado = True
        
        if not cliente_asignado:
            return jsonify({'status': 'error', 'message': 'No tienes acceso a este documento'}), 403
    else:
        # Usuario: verificar que está asignado o es admin
        asignados = proyecto.get_asignados()
        user_asignado = any(a.get('id') == f"user_{current_user.id}" for a in asignados)
        is_admin_user = hasattr(current_user, 'username') and current_user.username == 'Olmeiri'
        if not user_asignado and not is_admin_user:
            return jsonify({'status': 'error', 'message': 'No tienes acceso a este documento'}), 403
    
    # Obtener la ruta completa del archivo
    file_path = documento.ruta_archivo.lstrip('/')
    if not os.path.exists(file_path):
        return jsonify({'status': 'error', 'message': 'Archivo no encontrado'}), 404
    
    # Registrar descarga
    log_user_action("Descargar Documento", f"Documento '{documento.nombre_display}' descargado del proyecto {documento.proyecto_id}", {'proyecto_id': documento.proyecto_id, 'documento_id': documento_id})
    
    # Asegurar que el nombre de descarga tenga la extensión correcta
    download_name = documento.nombre_display
    # Extraer extensión del nombre original del archivo
    if documento.nombre_archivo and '.' in documento.nombre_archivo:
        extension = documento.nombre_archivo.split('.')[-1]
        if '.' not in download_name:
            download_name = f"{download_name}.{extension}"
    elif documento.tipo_archivo and '.' not in download_name:
        download_name = f"{download_name}.{documento.tipo_archivo}"
    
    return send_file(file_path, as_attachment=True, download_name=download_name)

@app.route('/delete_proyecto_documento/<int:documento_id>', methods=['POST'])
@login_required
def delete_proyecto_documento(documento_id):
    """Elimina un documento del proyecto"""
    documento = DocumentoProyecto.get_by_id(documento_id)
    if not documento:
        return jsonify({'status': 'error', 'message': 'Documento no encontrado'})
    
    # Verificar permisos (solo usuarios/admin pueden eliminar)
    if is_cliente(current_user):
        return jsonify({'status': 'error', 'message': 'No tienes permisos para eliminar documentos'})
    
    # Eliminar archivo físico
    file_path = documento.ruta_archivo.lstrip('/')
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
        except Exception as e:
            print(f"Error al eliminar archivo: {e}")
    
    documento_nombre = documento.nombre_display
    documento_proyecto_id = documento.proyecto_id
    result = DocumentoProyecto.delete(documento_id)
    if result:
        log_user_action("Eliminar Documento", f"Documento '{documento_nombre}' eliminado del proyecto {documento_proyecto_id}", {'proyecto_id': documento_proyecto_id, 'documento_id': documento_id})
        return jsonify({'status': 'success', 'message': 'Documento eliminado correctamente'})
    else:
        return jsonify({'status': 'error', 'message': 'Error al eliminar documento'})

@app.route('/save_valoracion', methods=['POST'])
@login_required
def save_valoracion():
    """Guarda o actualiza la valoración de un cliente sobre un proyecto"""
    if not is_cliente(current_user):
        return jsonify({'status': 'error', 'message': 'Solo los clientes pueden valorar proyectos'})
    
    proyecto_id = request.form.get('proyecto_id', type=int)
    calificacion = request.form.get('calificacion', type=int)
    comentarios = request.form.get('comentarios', '').strip()
    sugerencias = request.form.get('sugerencias', '').strip()
    aspectos_positivos = request.form.get('aspectos_positivos', '').strip()
    aspectos_mejora = request.form.get('aspectos_mejora', '').strip()
    
    if not proyecto_id or not calificacion:
        return jsonify({'status': 'error', 'message': 'Proyecto y calificación son obligatorios'})
    
    if calificacion < 1 or calificacion > 5:
        return jsonify({'status': 'error', 'message': 'La calificación debe estar entre 1 y 5'})
    
    # Verificar que el cliente tiene acceso al proyecto
    proyecto = Proyecto.get_by_id(proyecto_id)
    if not proyecto:
        return jsonify({'status': 'error', 'message': 'Proyecto no encontrado'})
    
    # Verificar acceso del cliente
    conn = get_db_connection()
    cur = conn.cursor()
    tiene_acceso = False
    
    # Verificar si está asignado
    cur.execute("""
        SELECT COUNT(*) FROM proyecto_asignaciones 
        WHERE proyecto_id = %s AND asignado_id = %s AND tipo_asignado = 'cliente'
    """, (proyecto_id, current_user.id))
    count_asignado = cur.fetchone()[0]
    
    # Verificar si es el cliente del presupuesto
    cur.execute("""
        SELECT COUNT(*) FROM presupuestos 
        WHERE proyecto_id = %s AND cliente_id = %s
    """, (proyecto_id, current_user.id))
    count_presupuesto = cur.fetchone()[0]
    
    tiene_acceso = count_asignado > 0 or count_presupuesto > 0
    cur.close()
    conn.close()
    
    if not tiene_acceso:
        return jsonify({'status': 'error', 'message': 'No tienes acceso a este proyecto'})
    
    # Guardar valoración
    result = ProyectoValoracion.create(
        proyecto_id=proyecto_id,
        cliente_id=current_user.id,
        calificacion=calificacion,
        comentarios=comentarios if comentarios else None,
        sugerencias=sugerencias if sugerencias else None,
        aspectos_positivos=aspectos_positivos if aspectos_positivos else None,
        aspectos_mejora=aspectos_mejora if aspectos_mejora else None
    )
    
    if isinstance(result, ProyectoValoracion):
        cliente_nombre = current_user.nombre_empresa if current_user.tipo_cliente == 'empresa' else f"{current_user.nombre} {current_user.apellido}"
        log_user_action("Valorar Proyecto", f"Cliente '{cliente_nombre}' valoró el proyecto '{proyecto.nombre}' con {calificacion} estrellas", {'proyecto_id': proyecto_id, 'calificacion': calificacion, 'cliente_id': current_user.id})
        return jsonify({
            'status': 'success',
            'message': 'Valoración guardada correctamente',
            'valoracion': result.to_dict()
        })
    else:
        return jsonify({'status': 'error', 'message': f'Error al guardar valoración: {result}'})

@app.route('/valoraciones')
@login_required
def valoraciones():
    """Vista de valoraciones del sistema (solo para administradores)"""
    from datetime import datetime
    
    # Verificar que es administrador
    is_admin_user = hasattr(current_user, 'username') and current_user.username == 'Olmeiri'
    if not is_admin_user:
        flash('No tienes permisos para acceder a esta sección', 'error')
        return redirect(url_for('dashboard'))
    
    # Obtener parámetros de filtrado
    page = request.args.get('page', 1, type=int)
    per_page = 50
    offset = (page - 1) * per_page
    
    proyecto_id = request.args.get('proyecto_id', type=int)
    cliente_id = request.args.get('cliente_id', type=int)
    
    # Obtener valoraciones
    valoraciones_list = ProyectoValoracion.get_all(limit=per_page, offset=offset, proyecto_id=proyecto_id, cliente_id=cliente_id)
    total_valoraciones = ProyectoValoracion.get_count(proyecto_id=proyecto_id, cliente_id=cliente_id)
    
    valoraciones_dict = [v.to_dict() for v in valoraciones_list]
    
    # Obtener proyectos para filtro
    proyectos = Proyecto.get_all()
    proyectos_dict = [p.to_dict() for p in proyectos]
    
    log_user_action("Acceso Valoraciones", "Administrador accedió a la sección de valoraciones")
    
    return render_template('valoraciones.html', 
                         now=datetime.now(), 
                         valoraciones=valoraciones_dict,
                         total_valoraciones=total_valoraciones,
                         page=page,
                         per_page=per_page,
                         proyecto_id=proyecto_id,
                         cliente_id=cliente_id,
                         proyectos=proyectos_dict)

def generate_project_pdf(proyecto_id):
    """Genera un PDF completo del proyecto con todas sus secciones"""
    if not REPORTLAB_AVAILABLE:
        return None, "La librería reportlab no está instalada. Por favor, instala reportlab: pip install reportlab"
    
    # Obtener datos del proyecto
    proyecto = Proyecto.get_by_id(proyecto_id)
    if not proyecto:
        return None, "Proyecto no encontrado"
    
    proyecto_dict = proyecto.to_dict()
    
    # Crear buffer para el PDF
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
    story = []
    
    # Estilos
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#2d4154'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor('#2d4154'),
        spaceAfter=12,
        spaceBefore=20
    )
    
    subheading_style = ParagraphStyle(
        'CustomSubHeading',
        parent=styles['Heading3'],
        fontSize=12,
        textColor=colors.HexColor('#555'),
        spaceAfter=8,
        spaceBefore=12
    )
    
    normal_style = styles['Normal']
    normal_style.fontSize = 10
    
    # Título del documento
    story.append(Paragraph("REPORTE COMPLETO DEL PROYECTO", title_style))
    story.append(Spacer(1, 0.3*inch))
    
    # Información General del Proyecto
    story.append(Paragraph("INFORMACIÓN GENERAL", heading_style))
    story.append(Spacer(1, 0.1*inch))
    
    info_data = [
        ['Nombre del Proyecto:', proyecto_dict.get('nombre', 'N/A')],
        ['Estado:', proyecto_dict.get('estado', 'N/A').upper()],
        ['Progreso:', f"{proyecto_dict.get('progreso', 0)}%"],
        ['Fecha de Inicio:', proyecto_dict.get('fecha_inicio', 'N/A')],
        ['Fecha de Fin:', proyecto_dict.get('fecha_fin', 'N/A') or 'En curso'],
        ['Descripción:', proyecto_dict.get('descripcion', 'Sin descripción')]
    ]
    
    info_table = Table(info_data, colWidths=[2*inch, 4*inch])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f0f0f0')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 0.2*inch))
    
    # Presupuesto
    presupuesto = Presupuesto.get_by_proyecto(proyecto_id)
    if presupuesto:
        story.append(PageBreak())
        story.append(Paragraph("PRESUPUESTO", heading_style))
        story.append(Spacer(1, 0.1*inch))
        
        presupuesto_dict = presupuesto.to_dict()
        presupuesto_info = [
            ['Número de Presupuesto:', presupuesto_dict.get('numero_presupuesto', 'N/A')],
            ['Fecha:', presupuesto_dict.get('fecha', 'N/A')],
            ['Cliente:', presupuesto_dict.get('cliente_nombre', 'N/A')],
            ['Email:', presupuesto_dict.get('cliente_email', 'N/A')],
            ['Teléfono:', presupuesto_dict.get('cliente_telefono', 'N/A')],
            ['Descuento:', f"{presupuesto_dict.get('descuento', 0)}%"],
            ['IVA:', f"{presupuesto_dict.get('iva', 19)}%"]
        ]
        
        if presupuesto_dict.get('generalidades'):
            presupuesto_info.append(['Generalidades:', presupuesto_dict.get('generalidades')])
        
        presupuesto_table = Table(presupuesto_info, colWidths=[2*inch, 4*inch])
        presupuesto_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f0f0f0')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        story.append(presupuesto_table)
        story.append(Spacer(1, 0.2*inch))
        
        # Items del presupuesto
        items = PresupuestoItem.get_by_presupuesto(presupuesto.id)
        if items:
            story.append(Paragraph("Items del Presupuesto", subheading_style))
            
            items_data = [['Cantidad', 'Descripción', 'Precio Unitario', 'Total']]
            subtotal = 0
            for item in items:
                item_dict = item.to_dict()
                cantidad = item_dict.get('cantidad', 0)
                precio_unitario = item_dict.get('precio_unitario', 0)
                total_item = cantidad * precio_unitario
                subtotal += total_item
                items_data.append([
                    str(cantidad),
                    item_dict.get('descripcion', ''),
                    f"${precio_unitario:,.0f}",
                    f"${total_item:,.0f}"
                ])
            
            descuento = presupuesto_dict.get('descuento', 0)
            iva = presupuesto_dict.get('iva', 19)
            descuento_monto = subtotal * (descuento / 100)
            subtotal_con_descuento = subtotal - descuento_monto
            iva_monto = subtotal_con_descuento * (iva / 100)
            total = subtotal_con_descuento + iva_monto
            
            items_data.append(['', '', 'Subtotal:', f"${subtotal:,.0f}"])
            if descuento > 0:
                items_data.append(['', '', f'Descuento ({descuento}%):', f"-${descuento_monto:,.0f}"])
            items_data.append(['', '', f'IVA ({iva}%):', f"${iva_monto:,.0f}"])
            items_data.append(['', '', '<b>TOTAL:</b>', f"<b>${total:,.0f}</b>"])
            
            items_table = Table(items_data, colWidths=[0.8*inch, 3*inch, 1.2*inch, 1*inch])
            items_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2d4154')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('ALIGN', (2, 0), (-1, -1), 'RIGHT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTNAME', (0, 1), (-1, -2), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.HexColor('#f9f9f9')]),
            ]))
            story.append(items_table)
            story.append(Spacer(1, 0.2*inch))
    
    # Activos
    activos = Activo.get_by_proyecto(proyecto_id)
    if activos:
        story.append(PageBreak())
        story.append(Paragraph("ACTIVOS DEL PROYECTO", heading_style))
        story.append(Spacer(1, 0.1*inch))
        
        activos_data = [['Nombre', 'Tipo', 'Estado', 'Ubicación', 'Valor']]
        for activo in activos:
            activo_dict = activo.to_dict()
            activos_data.append([
                activo_dict.get('nombre', 'N/A'),
                activo_dict.get('tipo', 'N/A'),
                activo_dict.get('estado', 'N/A'),
                activo_dict.get('ubicacion', 'N/A'),
                f"${activo_dict.get('valor', 0):,.0f}" if activo_dict.get('valor') else 'N/A'
            ])
        
        activos_table = Table(activos_data, colWidths=[1.5*inch, 1*inch, 1*inch, 1.5*inch, 1*inch])
        activos_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2d4154')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (4, 0), (4, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9f9f9')]),
        ]))
        story.append(activos_table)
        story.append(Spacer(1, 0.2*inch))
    
    # Incidencias
    incidencias = Incidencia.get_by_proyecto(proyecto_id)
    if incidencias:
        story.append(PageBreak())
        story.append(Paragraph("INCIDENCIAS", heading_style))
        story.append(Spacer(1, 0.1*inch))
        
        for incidencia in incidencias:
            incidencia_dict = incidencia.to_dict()
            story.append(Paragraph(f"Incidencia #{incidencia_dict.get('id', 'N/A')}", subheading_style))
            
            incidencia_info = [
                ['Título:', incidencia_dict.get('titulo', 'N/A')],
                ['Estado:', incidencia_dict.get('estado', 'N/A').upper()],
                ['Prioridad:', incidencia_dict.get('prioridad', 'N/A').upper()],
                ['Fecha de Creación:', incidencia_dict.get('created_at_display', 'N/A')],
                ['Descripción:', incidencia_dict.get('descripcion', 'Sin descripción')]
            ]
            
            if incidencia_dict.get('solucion'):
                incidencia_info.append(['Solución:', incidencia_dict.get('solucion')])
            
            incidencia_table = Table(incidencia_info, colWidths=[1.5*inch, 4.5*inch])
            incidencia_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f0f0f0')),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                ('ALIGN', (1, 0), (1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ]))
            story.append(incidencia_table)
            story.append(Spacer(1, 0.15*inch))
    
    # Mantenimiento
    if proyecto_dict.get('incluye_mantenimiento'):
        mantenimiento_config = MantenimientoConfig.get_by_proyecto(proyecto_id)
        if mantenimiento_config:
            story.append(PageBreak())
            story.append(Paragraph("MANTENIMIENTO", heading_style))
            story.append(Spacer(1, 0.1*inch))
            
            config_dict = mantenimiento_config.to_dict()
            mantenimiento_info = [
                ['Período de Visita:', config_dict.get('periodo_visita', 'N/A')],
                ['Incluye Emergencia:', 'Sí' if config_dict.get('incluye_emergencia') else 'No']
            ]
            
            if config_dict.get('incluye_emergencia') and config_dict.get('periodo_emergencia'):
                mantenimiento_info.append(['Período de Emergencia:', config_dict.get('periodo_emergencia')])
            
            mantenimiento_table = Table(mantenimiento_info, colWidths=[2*inch, 4*inch])
            mantenimiento_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f0f0f0')),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                ('ALIGN', (1, 0), (1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ]))
            story.append(mantenimiento_table)
            story.append(Spacer(1, 0.2*inch))
            
            # Visitas de mantenimiento
            visitas = MantenimientoVisita.get_by_proyecto(proyecto_id)
            if visitas:
                story.append(Paragraph("Visitas de Mantenimiento", subheading_style))
                
                for visita in visitas:
                    visita_dict = visita.to_dict()
                    story.append(Paragraph(f"Visita del {visita_dict.get('fecha_visita_display', 'N/A')}", ParagraphStyle(
                        'VisitaTitle',
                        parent=normal_style,
                        fontSize=11,
                        textColor=colors.HexColor('#2d4154'),
                        spaceAfter=6,
                        spaceBefore=10
                    )))
                    
                    visita_info = [
                        ['Tipo de Visita:', visita_dict.get('tipo_visita', 'N/A').upper()],
                        ['Fecha:', visita_dict.get('fecha_visita_display', 'N/A')],
                        ['Creado por:', visita_dict.get('creador_nombre', 'N/A')]
                    ]
                    
                    if visita_dict.get('comentarios'):
                        visita_info.append(['Comentarios:', visita_dict.get('comentarios')])
                    if visita_dict.get('sugerencias'):
                        visita_info.append(['Sugerencias:', visita_dict.get('sugerencias')])
                    if visita_dict.get('observaciones'):
                        visita_info.append(['Observaciones:', visita_dict.get('observaciones')])
                    
                    visita_table = Table(visita_info, colWidths=[1.5*inch, 4.5*inch])
                    visita_table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f9f9f9')),
                        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
                        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
                        ('FONTSIZE', (0, 0), (-1, -1), 8),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                        ('TOPPADDING', (0, 0), (-1, -1), 4),
                        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                    ]))
                    story.append(visita_table)
                    story.append(Spacer(1, 0.1*inch))
    
    # Documentos
    documentos = DocumentoProyecto.get_by_proyecto(proyecto_id)
    if documentos:
        story.append(PageBreak())
        story.append(Paragraph("DOCUMENTOS DEL PROYECTO", heading_style))
        story.append(Spacer(1, 0.1*inch))
        
        documentos_data = [['Nombre', 'Tipo', 'Tamaño', 'Fecha de Subida']]
        for documento in documentos:
            documento_dict = documento.to_dict()
            documentos_data.append([
                documento_dict.get('nombre_display', 'N/A'),
                documento_dict.get('tipo_archivo', 'N/A'),
                documento_dict.get('tamaño_display', 'N/A'),
                documento_dict.get('created_at_display', 'N/A')
            ])
        
        documentos_table = Table(documentos_data, colWidths=[2.5*inch, 1*inch, 1*inch, 1.5*inch])
        documentos_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2d4154')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9f9f9')]),
        ]))
        story.append(documentos_table)
        story.append(Spacer(1, 0.2*inch))
    
    # Pie de página con fecha de generación
    story.append(Spacer(1, 0.3*inch))
    fecha_generacion = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
    story.append(Paragraph(f"<i>Reporte generado el {fecha_generacion}</i>", 
                          ParagraphStyle('Footer', parent=normal_style, fontSize=8, alignment=TA_CENTER, textColor=colors.grey)))
    
    # Construir PDF
    doc.build(story)
    buffer.seek(0)
    
    return buffer, None

@app.route('/download_project_report/<int:proyecto_id>')
@login_required
def download_project_report(proyecto_id):
    """Genera y descarga el reporte PDF completo del proyecto"""
    # Verificar acceso al proyecto
    proyecto = Proyecto.get_by_id(proyecto_id)
    if not proyecto:
        flash('Proyecto no encontrado', 'error')
        return redirect(url_for('projects'))
    
    # Verificar permisos
    if is_cliente(current_user):
        # Cliente solo puede ver proyectos asignados o del presupuesto
        conn = get_db_connection()
        cur = conn.cursor()
        tiene_acceso = False
        
        cur.execute("""
            SELECT COUNT(*) FROM proyecto_asignaciones 
            WHERE proyecto_id = %s AND asignado_id = %s AND tipo_asignado = 'cliente'
        """, (proyecto_id, current_user.id))
        count_asignado = cur.fetchone()[0]
        
        cur.execute("""
            SELECT COUNT(*) FROM presupuestos 
            WHERE proyecto_id = %s AND cliente_id = %s
        """, (proyecto_id, current_user.id))
        count_presupuesto = cur.fetchone()[0]
        
        tiene_acceso = count_asignado > 0 or count_presupuesto > 0
        cur.close()
        conn.close()
        
        if not tiene_acceso:
            flash('No tienes acceso a este proyecto', 'error')
            return redirect(url_for('projects'))
    
    # Generar PDF
    buffer, error = generate_project_pdf(proyecto_id)
    
    if error:
        flash(error, 'error')
        return redirect(url_for('project_detail', proyecto_id=proyecto_id))
    
    # Log de la acción
    log_user_action("Descargar Reporte PDF", f"Reporte PDF descargado del proyecto '{proyecto.nombre}'", {'proyecto_id': proyecto_id})
    
    # Nombre del archivo
    nombre_archivo = f"Reporte_{proyecto.nombre.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    
    return send_file(buffer, as_attachment=True, download_name=nombre_archivo, mimetype='application/pdf')

@app.route('/logs')
@login_required
def logs():
    """Vista de logs del sistema (solo para administradores)"""
    from datetime import datetime
    
    # Verificar que es administrador
    is_admin_user = hasattr(current_user, 'username') and current_user.username == 'Olmeiri'
    if not is_admin_user:
        flash('No tienes permisos para acceder a esta sección', 'error')
        return redirect(url_for('dashboard'))
    
    # Obtener parámetros de filtrado
    page = request.args.get('page', 1, type=int)
    per_page = 100
    offset = (page - 1) * per_page
    
    usuario_id = request.args.get('usuario_id', type=int)
    usuario_tipo = request.args.get('usuario_tipo', '')
    accion_filter = request.args.get('accion', '')
    
    # Obtener logs
    logs_list = UserLog.get_all(limit=per_page, offset=offset, usuario_id=usuario_id, usuario_tipo=usuario_tipo, accion=accion_filter)
    total_logs = UserLog.get_count(usuario_id=usuario_id, usuario_tipo=usuario_tipo, accion=accion_filter)
    
    logs_dict = [log.to_dict() for log in logs_list]
    
    log_user_action("Acceso Logs", "Administrador accedió a la sección de logs del sistema")
    
    return render_template('logs.html', 
                         now=datetime.now(), 
                         logs=logs_dict,
                         total_logs=total_logs,
                         page=page,
                         per_page=per_page,
                         usuario_id=usuario_id,
                         usuario_tipo=usuario_tipo,
                         accion_filter=accion_filter)

@app.route('/portal_pago/<int:proyecto_id>')
@login_required
def portal_pago(proyecto_id):
    """Portal de pago para el proyecto"""
    # Verificar que es cliente
    if not is_cliente(current_user):
        flash('Solo los clientes pueden acceder al portal de pago', 'error')
        return redirect(url_for('projects'))
    
    # Verificar acceso al proyecto
    proyecto = Proyecto.get_by_id(proyecto_id)
    if not proyecto:
        flash('Proyecto no encontrado', 'error')
        return redirect(url_for('projects'))
    
    # Verificar que el proyecto esté en estado espera_pago
    if proyecto.estado != 'espera_pago':
        flash('Este proyecto no está en estado de espera de pago', 'error')
        return redirect(url_for('projects'))
    
    # Verificar acceso del cliente
    conn = get_db_connection()
    cur = conn.cursor()
    tiene_acceso = False
    
    cur.execute("""
        SELECT COUNT(*) FROM proyecto_asignaciones 
        WHERE proyecto_id = %s AND asignado_id = %s AND tipo_asignado = 'cliente'
    """, (proyecto_id, current_user.id))
    count_asignado = cur.fetchone()[0]
    
    cur.execute("""
        SELECT COUNT(*) FROM presupuestos 
        WHERE proyecto_id = %s AND cliente_id = %s
    """, (proyecto_id, current_user.id))
    count_presupuesto = cur.fetchone()[0]
    
    tiene_acceso = count_asignado > 0 or count_presupuesto > 0
    cur.close()
    conn.close()
    
    if not tiene_acceso:
        flash('No tienes acceso a este proyecto', 'error')
        return redirect(url_for('projects'))
    
    # Obtener información del presupuesto para calcular el monto
    presupuesto = Presupuesto.get_by_proyecto(proyecto_id)
    monto_total = 0
    if presupuesto:
        items = PresupuestoItem.get_by_presupuesto(presupuesto.id)
        subtotal = sum(item.cantidad * item.valor_unitario for item in items)
        descuento = subtotal * (presupuesto.descuento / 100) if presupuesto.descuento else 0
        subtotal_con_descuento = subtotal - descuento
        iva = subtotal_con_descuento * (presupuesto.iva / 100) if presupuesto.iva else 0
        monto_total = subtotal_con_descuento + iva
    
    log_user_action("Acceso Portal Pago", f"Cliente accedió al portal de pago del proyecto '{proyecto.nombre}'", {'proyecto_id': proyecto_id, 'monto': monto_total})
    
    # Aquí puedes renderizar una página de pago o redirigir a un gateway externo
    # Por ahora, redirigimos a una página simple con información
    # En producción, esto debería integrarse con un gateway de pago real (Flow, Webpay, Stripe, etc.)
    return render_template('portal_pago.html', 
                         now=datetime.now(),
                         proyecto=proyecto.to_dict(),
                         monto_total=monto_total,
                         presupuesto=presupuesto.to_dict() if presupuesto else None)

# ========== RUTAS DE MARKETING ==========

@app.route('/marketing/dashboard')
@login_required
def marketing_dashboard():
    """Dashboard principal de marketing"""
    if is_cliente(current_user):
        flash('No tienes acceso a esta sección.', 'error')
        return redirect('/projects')
    
    from models import MarketingCampana, ClienteSegmento, Cliente
    
    # Obtener estadísticas
    campanas = MarketingCampana.get_all()
    campanas_activas = [c for c in campanas if c.estado == 'activa']
    total_presupuesto = sum(c.presupuesto for c in campanas)
    total_gastado = sum(c.presupuesto_gastado for c in campanas)
    
    # Clientes por segmento
    clientes_recurrentes = ClienteSegmento.get_by_segmento('recurrente') if hasattr(ClienteSegmento, 'get_by_segmento') else []
    clientes_nuevos = ClienteSegmento.get_by_segmento('nuevo') if hasattr(ClienteSegmento, 'get_by_segmento') else []
    clientes_perdidos = ClienteSegmento.get_by_segmento('perdido') if hasattr(ClienteSegmento, 'get_by_segmento') else []
    
    # Mes actual para cumpleaños
    mes_actual = datetime.now().month
    cumpleanos_mes = ClienteSegmento.get_cumpleanos_mes(mes_actual) if hasattr(ClienteSegmento, 'get_cumpleanos_mes') else []
    
    campanas_dict = [c.to_dict() for c in campanas[:5]]  # Últimas 5
    
    return render_template('marketing/dashboard.html',
                         now=datetime.now(),
                         campanas=campanas_dict,
                         campanas_activas_count=len(campanas_activas),
                         total_presupuesto=total_presupuesto,
                         total_gastado=total_gastado,
                         clientes_recurrentes_count=len(clientes_recurrentes),
                         clientes_nuevos_count=len(clientes_nuevos),
                         clientes_perdidos_count=len(clientes_perdidos),
                         cumpleanos_mes_count=len(cumpleanos_mes))

@app.route('/marketing/campanas')
@login_required
def marketing_campanas():
    """Lista todas las campañas"""
    if is_cliente(current_user):
        flash('No tienes acceso a esta sección.', 'error')
        return redirect('/projects')
    
    from models import MarketingCampana
    campanas = MarketingCampana.get_all()
    campanas_dict = [c.to_dict() for c in campanas]
    
    return render_template('marketing/campanas.html',
                         now=datetime.now(),
                         campanas=campanas_dict)

@app.route('/marketing/campanas/nueva', methods=['GET', 'POST'])
@login_required
def marketing_campana_nueva():
    """Crear nueva campaña"""
    if is_cliente(current_user):
        flash('No tienes acceso a esta sección.', 'error')
        return redirect('/projects')
    
    from models import MarketingCampana
    
    if request.method == 'POST':
        nombre = request.form.get('nombre')
        descripcion = request.form.get('descripcion')
        tipo = request.form.get('tipo')
        plataforma = request.form.get('plataforma')
        presupuesto = float(request.form.get('presupuesto', 0) or 0)
        fecha_inicio = request.form.get('fecha_inicio')
        fecha_fin = request.form.get('fecha_fin')
        objetivo = request.form.get('objetivo')
        publico_objetivo = request.form.get('publico_objetivo')
        
        campana = MarketingCampana.create(
            nombre=nombre,
            tipo=tipo,
            plataforma=plataforma,
            created_by=current_user.id,
            descripcion=descripcion,
            presupuesto=presupuesto,
            fecha_inicio=datetime.strptime(fecha_inicio, '%Y-%m-%d').date() if fecha_inicio else None,
            fecha_fin=datetime.strptime(fecha_fin, '%Y-%m-%d').date() if fecha_fin else None,
            objetivo=objetivo,
            publico_objetivo=publico_objetivo
        )
        
        if campana:
            flash('Campaña creada exitosamente', 'success')
            return redirect('/marketing/campanas')
        else:
            flash('Error al crear la campaña', 'error')
    
    return render_template('marketing/campana_nueva.html', now=datetime.now())

@app.route('/marketing/clientes/base-datos')
@login_required
def marketing_clientes_base_datos():
    """Base de datos de clientes optimizada para marketing"""
    if is_cliente(current_user):
        flash('No tienes acceso a esta sección.', 'error')
        return redirect('/projects')
    
    from models import Cliente, ClienteSegmento
    
    clientes = Cliente.get_all()
    clientes_dict = []
    
    for cliente in clientes:
        cliente_data = cliente.to_dict()
        segmento = ClienteSegmento.get_by_cliente_id(cliente.id)
        if segmento:
            cliente_data['segmento'] = segmento.to_dict()
        else:
            cliente_data['segmento'] = None
        clientes_dict.append(cliente_data)
    
    return render_template('marketing/clientes_base_datos.html',
                         now=datetime.now(),
                         clientes=clientes_dict)

@app.route('/marketing/clientes/clasificacion')
@login_required
def marketing_clientes_clasificacion():
    """Clasificación de clientes (recurrente, nuevo, perdido, cumpleaños)"""
    if is_cliente(current_user):
        flash('No tienes acceso a esta sección.', 'error')
        return redirect('/projects')
    
    from models import ClienteSegmento, Cliente
    
    segmentos_data = {}
    for segmento_tipo in ['recurrente', 'nuevo', 'perdido']:
        segmentos = ClienteSegmento.get_by_segmento(segmento_tipo)
        segmentos_data[segmento_tipo] = [s.to_dict() for s in segmentos]
    
    # Cumpleaños del mes actual
    mes_actual = datetime.now().month
    cumpleanos = ClienteSegmento.get_cumpleanos_mes(mes_actual)
    segmentos_data['cumpleanos'] = [s.to_dict() for s in cumpleanos]
    
    # Obtener datos de clientes para mostrar información completa
    clientes = Cliente.get_all()
    clientes_dict = {c.id: c.to_dict() for c in clientes}
    
    return render_template('marketing/clientes_clasificacion.html',
                         now=datetime.now(),
                         segmentos=segmentos_data,
                         clientes=clientes_dict)

@app.route('/marketing/integraciones/meta-pixel')
@login_required
def marketing_integraciones_meta_pixel():
    """Configuración de Meta Pixel (Facebook Ads)"""
    if is_cliente(current_user):
        flash('No tienes acceso a esta sección.', 'error')
        return redirect('/projects')
    
    from models import get_db_connection
    import json
    
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, tipo, nombre, activa, configuracion, estado_conexion
        FROM marketing_integraciones
        WHERE tipo = 'meta_pixel'
        LIMIT 1
    """)
    integracion = cur.fetchone()
    cur.close()
    conn.close()
    
    configuracion = None
    if integracion:
        configuracion = {
            'id': integracion[0],
            'tipo': integracion[1],
            'nombre': integracion[2],
            'activa': integracion[3],
            'configuracion': integracion[4],
            'estado_conexion': integracion[5]
        }
    
    return render_template('marketing/integraciones_meta_pixel.html',
                         now=datetime.now(),
                         configuracion=configuracion)

@app.route('/marketing/integraciones/whatsapp')
@login_required
def marketing_integraciones_whatsapp():
    """Configuración de WhatsApp Business"""
    if is_cliente(current_user):
        flash('No tienes acceso a esta sección.', 'error')
        return redirect('/projects')
    
    from models import get_db_connection
    import json
    
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, tipo, nombre, activa, configuracion, estado_conexion
        FROM marketing_integraciones
        WHERE tipo = 'whatsapp'
        LIMIT 1
    """)
    integracion = cur.fetchone()
    cur.close()
    conn.close()
    
    configuracion = None
    if integracion:
        # PostgreSQL JSONB puede devolver dict directamente o string
        config_raw = integracion[4]
        if isinstance(config_raw, dict):
            config_dict = config_raw
        elif isinstance(config_raw, str):
            try:
                config_dict = json.loads(config_raw) if config_raw else {}
            except:
                config_dict = {}
        else:
            config_dict = {}
        
        configuracion = {
            'id': integracion[0],
            'tipo': integracion[1],
            'nombre': integracion[2],
            'activa': integracion[3],
            'configuracion': config_dict,
            'estado_conexion': integracion[5]
        }
    
    return render_template('marketing/integraciones_whatsapp.html',
                         now=datetime.now(),
                         configuracion=configuracion)

# Rutas adicionales para acciones
@app.route('/marketing/integraciones/meta-pixel/guardar', methods=['POST'])
@login_required
def marketing_meta_pixel_guardar():
    """Guardar configuración de Meta Pixel"""
    if is_cliente(current_user):
        flash('No tienes acceso a esta sección.', 'error')
        return redirect('/projects')
    
    from models import get_db_connection
    import json
    
    pixel_id = request.form.get('pixel_id')
    access_token = request.form.get('access_token')
    activa = request.form.get('activa') == 'on'
    
    config = {
        'pixel_id': pixel_id,
        'access_token': access_token
    }
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # Verificar si ya existe
        cur.execute("SELECT id FROM marketing_integraciones WHERE tipo = 'meta_pixel'")
        existe = cur.fetchone()
        
        if existe:
            cur.execute("""
                UPDATE marketing_integraciones
                SET configuracion = %s, activa = %s, updated_at = CURRENT_TIMESTAMP
                WHERE tipo = 'meta_pixel'
            """, (json.dumps(config), activa))
        else:
            cur.execute("""
                INSERT INTO marketing_integraciones (tipo, nombre, activa, configuracion)
                VALUES ('meta_pixel', 'Meta Pixel (Facebook Ads)', %s, %s)
            """, (activa, json.dumps(config)))
        
        conn.commit()
        flash('Configuración de Meta Pixel guardada exitosamente', 'success')
    except Exception as e:
        conn.rollback()
        flash(f'Error al guardar configuración: {str(e)}', 'error')
    finally:
        cur.close()
        conn.close()
    
    return redirect('/marketing/integraciones/meta-pixel')

@app.route('/marketing/integraciones/whatsapp/guardar', methods=['POST'])
@login_required
def marketing_whatsapp_guardar():
    """Guardar configuración de WhatsApp Business"""
    if is_cliente(current_user):
        flash('No tienes acceso a esta sección.', 'error')
        return redirect('/projects')
    
    from models import get_db_connection
    import json
    
    tipo_integracion = request.form.get('tipo_integracion')
    activa = request.form.get('activa') == 'on'
    
    config = {
        'tipo_integracion': tipo_integracion
    }
    
    # Configuración según el tipo de integración
    if tipo_integracion == 'evolution_api':
        config['evolution_api_url'] = request.form.get('evolution_api_url', '').strip()
        config['evolution_api_key'] = request.form.get('evolution_api_key', '').strip()
        config['evolution_instance_id'] = request.form.get('evolution_instance_id', '').strip()
        config['evolution_number'] = request.form.get('evolution_number', '').strip()
    else:
        config['phone_number'] = request.form.get('phone_number', '').strip()
        config['api_key'] = request.form.get('api_key', '').strip()
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # Verificar si ya existe
        cur.execute("SELECT id FROM marketing_integraciones WHERE tipo = 'whatsapp'")
        existe = cur.fetchone()
        
        if existe:
            cur.execute("""
                UPDATE marketing_integraciones
                SET configuracion = %s, activa = %s, updated_at = CURRENT_TIMESTAMP
                WHERE tipo = 'whatsapp'
            """, (json.dumps(config), activa))
        else:
            cur.execute("""
                INSERT INTO marketing_integraciones (tipo, nombre, activa, configuracion)
                VALUES ('whatsapp', 'WhatsApp Business', %s, %s)
            """, (activa, json.dumps(config)))
        
        conn.commit()
        flash('Configuración de WhatsApp Business guardada exitosamente', 'success')
    except Exception as e:
        conn.rollback()
        flash(f'Error al guardar configuración: {str(e)}', 'error')
    finally:
        cur.close()
        conn.close()
    
    return redirect('/marketing/integraciones/whatsapp')

@app.route('/marketing/integraciones/whatsapp/probar-evolution', methods=['POST'])
@login_required
def marketing_whatsapp_probar_evolution():
    """Probar conexión con Evolution API usando UUID"""
    if is_cliente(current_user):
        return jsonify({'success': False, 'message': 'No tienes acceso'}), 403
    
    import requests
    import json
    
    data = request.get_json()
    api_url = data.get('evolution_api_url', '').rstrip('/')
    api_key = data.get('evolution_api_key')
    instance_id = data.get('evolution_instance_id', '').strip()
    
    if not api_url or not api_key or not instance_id:
        return jsonify({'success': False, 'message': 'Faltan parámetros requeridos'}), 400
    
    try:
        # Probar obteniendo información de la instancia específica usando UUID
        headers = {
            'apikey': api_key,
            'Content-Type': 'application/json'
        }
        
        # Primero intentar obtener todas las instancias para verificar que existe
        # Evolution API a veces requiere usar el nombre en lugar del UUID para algunos endpoints
        url_all = f"{api_url}/instance/fetchInstances"
        response_all = requests.get(url_all, headers=headers, timeout=10)
        
        if response_all.status_code == 200:
            instances = response_all.json()
            # Normalizar el instance_id para comparación
            instance_id_normalized = instance_id.strip().lower()
            
            instance_found = False
            found_instance_name = None
            
            # Evolution API puede devolver las instancias como array o como objeto
            if isinstance(instances, list):
                instances_to_check = instances
            elif isinstance(instances, dict) and 'data' in instances:
                instances_to_check = instances['data']
            else:
                instances_to_check = [instances] if isinstance(instances, dict) else []
            
            for inst in instances_to_check:
                if isinstance(inst, dict):
                    inst_name = inst.get('instanceName', '') or inst.get('name', '')
                    # Evolution API puede devolver el ID en diferentes campos
                    inst_id = inst.get('instanceId') or inst.get('id') or inst.get('key', '') or inst.get('instanceKey', '')
                    inst_id_str = str(inst_id).strip().lower() if inst_id else ''
                    
                    # Comparar UUID (case-insensitive)
                    if inst_id_str == instance_id_normalized:
                        instance_found = True
                        found_instance_name = inst_name or inst_id
                        break
                    # Comparación parcial por si hay diferencias de formato
                    elif inst_id_str and (instance_id_normalized in inst_id_str or inst_id_str in instance_id_normalized):
                        instance_found = True
                        found_instance_name = inst_name or inst_id
                        break
                    # Comparar por nombre también
                    elif inst_name and inst_name.lower().strip() == instance_id_normalized:
                        instance_found = True
                        found_instance_name = inst_name
                        break
            
                if instance_found:
                    # La instancia existe, la conexión es válida
                    # No necesitamos hacer fetchInstance si ya sabemos que existe
                    # Evolution API requiere el nombre de la instancia (no el UUID) para enviar mensajes
                    instance_name_to_use = found_instance_name if found_instance_name else instance_id
                    return jsonify({
                        'success': True, 
                        'message': f'Conexión exitosa. Instancia encontrada: {instance_name_to_use}. Usando nombre de instancia para envío.',
                        'data': {
                            'instance_id': instance_id, 
                            'instance_name': found_instance_name,
                            'instance_name_to_use': instance_name_to_use
                        }
                })
        
        # Si no la encontramos en la lista, intentar el endpoint específico
        url = f"{api_url}/instance/fetchInstance/{instance_id}"
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            instance_data = response.json()
            # Si obtenemos datos de la instancia, la conexión es exitosa
            instance_name = instance_data.get('instanceName') or instance_data.get('instance', {}).get('instanceName') or instance_data.get('instanceName', 'Instancia')
            instance_status = instance_data.get('instance', {}).get('status') or instance_data.get('status', 'unknown')
            return jsonify({
                'success': True, 
                'message': f'Conexión exitosa con instancia: {instance_name or instance_id} (Estado: {instance_status})',
                'data': instance_data
            })
        elif response.status_code == 404:
            # Si no encuentra por UUID directamente, intentar obtener todas las instancias para verificar
            try:
                url_all = f"{api_url}/instance/fetchInstances"
                response_all = requests.get(url_all, headers=headers, timeout=5)
                if response_all.status_code == 200:
                    instances = response_all.json()
                    # Normalizar el instance_id para comparación (sin espacios, en minúsculas)
                    instance_id_normalized = instance_id.strip().lower()
                    
                    instance_list = []
                    instance_found = False
                    found_instance_name = None
                    found_instance_id = None
                    
                    # Evolution API puede devolver las instancias como array o como objeto
                    if isinstance(instances, list):
                        instances_to_check = instances
                    elif isinstance(instances, dict):
                        instances_to_check = instances.get('data', [instances])
                    else:
                        instances_to_check = [instances]
                    
                    for inst in instances_to_check:
                        if isinstance(inst, dict):
                            inst_name = inst.get('instanceName', '') or inst.get('name', '')
                            # Evolution API puede devolver el ID en diferentes campos
                            inst_id = inst.get('instanceId') or inst.get('id') or inst.get('key', '') or inst.get('instanceKey', '')
                            inst_id_str = str(inst_id).strip().lower() if inst_id else ''
                            
                            instance_list.append(f"{inst_name or 'Sin nombre'} ({inst_id})")
                            
                            # Comparar tanto el UUID completo como parcial, y también el nombre
                            # Comparación exacta (case-insensitive)
                            if inst_id_str == instance_id_normalized:
                                instance_found = True
                                found_instance_name = inst_name or inst_id
                                found_instance_id = inst_id
                                break
                            # Comparación parcial (por si hay diferencias de formato)
                            elif instance_id_normalized in inst_id_str or inst_id_str in instance_id_normalized:
                                instance_found = True
                                found_instance_name = inst_name or inst_id
                                found_instance_id = inst_id
                                break
                            # Comparar por nombre también
                            elif inst_name and inst_name.lower().strip() == instance_id_normalized:
                                instance_found = True
                                found_instance_name = inst_name
                                found_instance_id = inst_id
                                break
                    
                    if instance_found:
                        # La instancia existe en la lista, aunque el endpoint específico devolvió 404
                        # Esto puede pasar si Evolution API requiere el nombre en lugar del UUID para fetchInstance
                        # Pero el UUID funciona para sendText, así que lo consideramos válido
                        return jsonify({
                            'success': True, 
                            'message': f'Instancia encontrada: {found_instance_name or found_instance_id or instance_id}. El UUID es válido y puede usarse para enviar mensajes.',
                            'data': {'instance_id': found_instance_id or instance_id, 'instance_name': found_instance_name}
                        })
                    else:
                        return jsonify({
                            'success': False, 
                            'message': f'Instancia "{instance_id}" no encontrada. Instancias disponibles: {", ".join(instance_list) if instance_list else "ninguna"}'
                        })
                else:
                    return jsonify({'success': False, 'message': f'Instancia "{instance_id}" no encontrada. Error al listar instancias: HTTP {response_all.status_code}'})
            except Exception as e:
                return jsonify({'success': False, 'message': f'Instancia "{instance_id}" no encontrada. Error al verificar: {str(e)}'})
        elif response.status_code == 401:
            return jsonify({'success': False, 'message': 'API Key inválida o no autorizada'})
        elif response.status_code == 403:
            return jsonify({'success': False, 'message': 'Acceso denegado. Verifica la API Key y permisos.'})
        else:
            try:
                error_data = response.json()
                error_msg = error_data.get('message') or error_data.get('error', f'Error {response.status_code}')
                return jsonify({'success': False, 'message': f'Error al conectar: {error_msg}'})
            except:
                return jsonify({'success': False, 'message': f'Error al conectar: HTTP {response.status_code}'})
            
    except requests.exceptions.ConnectionError:
        return jsonify({'success': False, 'message': 'No se pudo conectar al servidor. Verifica la URL y que Evolution API esté corriendo.'})
    except requests.exceptions.Timeout:
        return jsonify({'success': False, 'message': 'Timeout al conectar con el servidor. Verifica que Evolution API esté disponible.'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error inesperado: {str(e)}'})

def reemplazar_variables_mensaje(mensaje, destinatario_tipo, destinatario_id, recordatorio_id=None):
    """
    Reemplaza variables dinámicas en el mensaje según el destinatario
    
    Variables disponibles:
    - {nombre_cliente}, {apellido_cliente}, {nombre_completo}
    - {email}, {telefono}, {rut}
    - {empresa_nombre}
    - {proyecto_nombre}, {presupuesto_numero}, {monto}
    - {fecha}, {fecha_hoy}
    - {nombre_usuario}, {apellido_usuario}, {username}
    """
    from models import get_db_connection
    from datetime import datetime
    
    mensaje_resultado = str(mensaje)
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Reemplazar fecha_hoy siempre
        fecha_hoy = datetime.now().strftime('%d/%m/%Y')
        mensaje_resultado = mensaje_resultado.replace('{fecha_hoy}', fecha_hoy)
        
        if destinatario_tipo == 'cliente':
            # Obtener datos del cliente
            cur.execute("""
                SELECT nombre, apellido, correo, telefono, rut, nombre_empresa, tipo_cliente
                FROM clientes
                WHERE id = %s
            """, (destinatario_id,))
            cliente = cur.fetchone()
            
            if cliente:
                nombre, apellido, email, telefono, rut, empresa, tipo_cliente = cliente
                
                mensaje_resultado = mensaje_resultado.replace('{nombre_cliente}', nombre or '')
                mensaje_resultado = mensaje_resultado.replace('{apellido_cliente}', apellido or '')
                mensaje_resultado = mensaje_resultado.replace('{nombre_completo}', f"{nombre or ''} {apellido or ''}".strip())
                mensaje_resultado = mensaje_resultado.replace('{email}', email or '')
                mensaje_resultado = mensaje_resultado.replace('{telefono}', telefono or '')
                mensaje_resultado = mensaje_resultado.replace('{rut}', rut or '')
                mensaje_resultado = mensaje_resultado.replace('{empresa_nombre}', empresa or '')
                
                # Buscar proyecto activo del cliente a través de presupuestos
                cur.execute("""
                    SELECT p.id, p.nombre, pr.numero_presupuesto, p.estado
                    FROM proyectos p
                    LEFT JOIN presupuestos pr ON pr.proyecto_id = p.id
                    WHERE pr.cliente_id = %s
                    ORDER BY p.created_at DESC
                    LIMIT 1
                """, (destinatario_id,))
                proyecto = cur.fetchone()
                
                if proyecto:
                    proj_id, proj_nombre, presup_num, proj_estado = proyecto
                    mensaje_resultado = mensaje_resultado.replace('{proyecto_nombre}', proj_nombre or '')
                    mensaje_resultado = mensaje_resultado.replace('{presupuesto_numero}', str(presup_num) if presup_num else '')
                    mensaje_resultado = mensaje_resultado.replace('{proyecto_estado}', proj_estado or '')
                    
                    # Buscar monto del presupuesto
                    if proj_id:
                        cur.execute("""
                            SELECT SUM(pi.precio * pi.cantidad)
                            FROM presupuesto_items pi
                            JOIN presupuestos p ON p.id = pi.presupuesto_id
                            WHERE p.proyecto_id = %s
                        """, (proj_id,))
                        monto_row = cur.fetchone()
                        if monto_row and monto_row[0]:
                            monto = int(monto_row[0])
                            mensaje_resultado = mensaje_resultado.replace('{monto}', f"${monto:,}")
        
        elif destinatario_tipo == 'usuario':
            # Obtener datos del usuario
            cur.execute("""
                SELECT nombre, apellido, email, username
                FROM users
                WHERE id = %s
            """, (destinatario_id,))
            usuario = cur.fetchone()
            
            if usuario:
                nombre, apellido, email, username = usuario
                mensaje_resultado = mensaje_resultado.replace('{nombre_usuario}', nombre or '')
                mensaje_resultado = mensaje_resultado.replace('{apellido_usuario}', apellido or '')
                mensaje_resultado = mensaje_resultado.replace('{email}', email or '')
                mensaje_resultado = mensaje_resultado.replace('{username}', username or '')
        
        # Reemplazar {fecha} con la fecha programada del recordatorio si existe
        if recordatorio_id:
            cur.execute("SELECT fecha_programada FROM marketing_recordatorios WHERE id = %s", (recordatorio_id,))
            fecha_row = cur.fetchone()
            if fecha_row and fecha_row[0]:
                fecha_obj = fecha_row[0]
                if isinstance(fecha_obj, datetime):
                    fecha_str = fecha_obj.strftime('%d/%m/%Y %H:%M')
                else:
                    fecha_str = str(fecha_obj)
                mensaje_resultado = mensaje_resultado.replace('{fecha}', fecha_str)
        
        # Si {fecha} no fue reemplazado, usar fecha_hoy
        if '{fecha}' in mensaje_resultado:
            mensaje_resultado = mensaje_resultado.replace('{fecha}', fecha_hoy)
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"Error al reemplazar variables: {str(e)}")
        # Si hay error, dejar el mensaje original pero reemplazar al menos fechas
        mensaje_resultado = mensaje_resultado.replace('{fecha_hoy}', fecha_hoy)
        if '{fecha}' in mensaje_resultado:
            mensaje_resultado = mensaje_resultado.replace('{fecha}', fecha_hoy)
    
    return mensaje_resultado

def enviar_mensaje_whatsapp(numero_destino, mensaje, tipo='text'):
    """
    Envía un mensaje de WhatsApp usando la integración configurada
    
    Args:
        numero_destino: Número de teléfono destino (formato: 56912345678)
        mensaje: Contenido del mensaje
        tipo: Tipo de mensaje ('text', 'image', etc.)
    
    Returns:
        dict: {'success': bool, 'message': str, 'data': dict}
    """
    from models import get_db_connection
    import json
    import requests
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # Obtener configuración de WhatsApp
        cur.execute("""
            SELECT configuracion, activa
            FROM marketing_integraciones
            WHERE tipo = 'whatsapp' AND activa = TRUE
            LIMIT 1
        """)
        resultado = cur.fetchone()
        
        if not resultado:
            return {'success': False, 'message': 'WhatsApp no está configurado o no está activo'}
        
        # PostgreSQL JSONB puede devolver dict directamente o string
        config_raw = resultado[0]
        if isinstance(config_raw, dict):
            config = config_raw
        elif isinstance(config_raw, str):
            config = json.loads(config_raw) if config_raw else {}
        else:
            config = {}
        
        tipo_integracion = config.get('tipo_integracion')
        
        if tipo_integracion == 'evolution_api':
            return enviar_mensaje_evolution_api(
                numero_destino=numero_destino,
                mensaje=mensaje,
                tipo=tipo,
                config=config
            )
        else:
            return {'success': False, 'message': f'Tipo de integración "{tipo_integracion}" no implementado aún'}
            
    except Exception as e:
        return {'success': False, 'message': f'Error al enviar mensaje: {str(e)}'}
    finally:
        cur.close()
        conn.close()

def enviar_mensaje_evolution_api(numero_destino, mensaje, tipo='text', config=None):
    """
    Envía un mensaje usando Evolution API
    
    Args:
        numero_destino: Número destino (56912345678)
        mensaje: Texto del mensaje
        tipo: Tipo de mensaje
        config: Configuración de Evolution API
    
    Returns:
        dict con resultado del envío
    """
    import requests
    import json
    
    if not config:
        return {'success': False, 'message': 'Configuración no proporcionada'}
    
    api_url = config.get('evolution_api_url', '').rstrip('/')
    api_key = config.get('evolution_api_key')
    instance_id = config.get('evolution_instance_id')
    
    if not all([api_url, api_key, instance_id]):
        return {'success': False, 'message': 'Configuración incompleta de Evolution API'}
    
    # Evolution API requiere el nombre de la instancia para enviar mensajes, no el UUID
    # Si tenemos el UUID, necesitamos obtener el nombre de la instancia
    instance_name = config.get('evolution_instance_name')
    
    # Si no tenemos el nombre guardado, intentar obtenerlo usando el UUID
    if not instance_name:
        instance_name = instance_id  # Usar el ID como fallback
        try:
            import requests
            headers = {
                'apikey': api_key,
                'Content-Type': 'application/json'
            }
            # Intentar obtener el nombre de la instancia
            url_fetch = f"{api_url}/instance/fetchInstances"
            response_fetch = requests.get(url_fetch, headers=headers, timeout=10)
            print(f"[Evolution API] Fetch instances status: {response_fetch.status_code}")
            
            if response_fetch.status_code == 200:
                instances = response_fetch.json()
                instance_id_normalized = str(instance_id).strip().lower()
                
                print(f"[Evolution API] Tipo de respuesta fetchInstances: {type(instances)}")
                if isinstance(instances, dict):
                    print(f"[Evolution API] Claves en respuesta: {list(instances.keys())[:10]}")
                
                # Manejar diferentes formatos de respuesta
                instances_to_check = []
                if isinstance(instances, list):
                    instances_to_check = instances
                    print(f"[Evolution API] Lista con {len(instances)} instancias")
                elif isinstance(instances, dict):
                    # Intentar diferentes posibles claves
                    if 'data' in instances:
                        data = instances['data']
                        instances_to_check = data if isinstance(data, list) else [data]
                    elif 'instances' in instances:
                        data = instances['instances']
                        instances_to_check = data if isinstance(data, list) else [data]
                    else:
                        instances_to_check = [instances]
                else:
                    instances_to_check = []
                
                print(f"[Evolution API] Verificando {len(instances_to_check)} instancias para UUID: {instance_id_normalized}")
                
                for idx, inst in enumerate(instances_to_check):
                    if isinstance(inst, dict):
                        # Buscar el nombre en diferentes campos posibles
                        inst_name = (inst.get('instanceName') or 
                                   inst.get('name') or 
                                   inst.get('instance_name') or
                                   inst.get('instance', {}).get('instanceName', '') or
                                   '')
                        # Buscar el ID en diferentes campos posibles
                        inst_id = (inst.get('instanceId') or 
                                 inst.get('id') or 
                                 inst.get('key') or 
                                 inst.get('instanceKey') or
                                 inst.get('instance', {}).get('instanceId', '') or
                                 '')
                        inst_id_str = str(inst_id).strip().lower() if inst_id else ''
                        
                        print(f"[Evolution API] Instancia {idx}: name='{inst_name}', id='{inst_id}' (normalized: '{inst_id_str}')")
                        
                        # Comparar UUID (case-insensitive) - comparación exacta primero
                        if inst_id_str == instance_id_normalized:
                            if inst_name:
                                instance_name = inst_name
                                print(f"[Evolution API] ✓ Nombre encontrado (exacto): '{instance_name}' para UUID: {instance_id}")
                                break
                        # Comparación parcial
                        elif inst_id_str and (instance_id_normalized in inst_id_str or inst_id_str in instance_id_normalized):
                            if inst_name:
                                instance_name = inst_name
                                print(f"[Evolution API] ✓ Nombre encontrado (parcial): '{instance_name}' para UUID: {instance_id}")
                                break
                
                if instance_name == instance_id:
                    print(f"[Evolution API] ✗ No se encontró nombre. UUID buscado: '{instance_id_normalized}'")
        except Exception as e:
            import traceback
            print(f"[Evolution API] Error al obtener nombre de instancia: {str(e)}")
            print(f"[Evolution API] Traceback: {traceback.format_exc()}")
        
        # Si aún no tenemos un nombre válido (diferente del UUID), el endpoint no funcionará
        if instance_name == instance_id:
            print(f"[Evolution API] ADVERTENCIA: No se pudo obtener el nombre de la instancia. Intentando usar UUID directamente, pero puede fallar.")
    
    # Formatear número (asegurar formato internacional sin +)
    numero = str(numero_destino).replace('+', '').replace(' ', '').replace('-', '')
    if not numero.startswith('55'):  # Si no empieza con código de país, asumir que es chileno
        if numero.startswith('9'):
            numero = '56' + numero  # Agregar código de país Chile
        elif not numero.startswith('56'):
            numero = '56' + numero
    
    try:
        headers = {
            'apikey': api_key,
            'Content-Type': 'application/json'
        }
        
        # Preparar payload según tipo de mensaje
        payload = {
            'number': numero,
            'text': mensaje
        }
        
        # Endpoint de Evolution API para enviar mensaje de texto
        # Evolution API requiere el NOMBRE de la instancia, no el UUID
        url = f"{api_url}/message/sendText/{instance_name}"
        
        # Log para debug (en producción, comentar o usar logger)
        print(f"[Evolution API] Enviando mensaje a {numero}")
        print(f"[Evolution API] UUID de instancia: {instance_id}")
        print(f"[Evolution API] Nombre de instancia a usar: {instance_name}")
        print(f"[Evolution API] URL: {url}")
        print(f"[Evolution API] Payload: {payload}")
        
        response = requests.post(
            url,
            headers=headers,
            json=payload,
            timeout=30
        )
        
        print(f"[Evolution API] Response status: {response.status_code}")
        print(f"[Evolution API] Response body: {response.text[:500]}")
        
        # Evolution API puede retornar 200, 201 o 204 para éxito
        if response.status_code in [200, 201, 204]:
            try:
                data = response.json()
                return {
                    'success': True,
                    'message': 'Mensaje enviado exitosamente',
                    'data': data
                }
            except:
                # Si no hay JSON, igual es éxito si el código HTTP es correcto
                return {
                    'success': True,
                    'message': 'Mensaje enviado exitosamente',
                    'data': {'status': 'sent'}
                }
        elif response.status_code == 404:
            return {
                'success': False,
                'message': f'Instancia "{instance_id}" no encontrada. Verifica que el UUID sea correcto y que la instancia esté conectada.',
                'status_code': response.status_code
            }
        elif response.status_code == 401:
            return {
                'success': False,
                'message': 'API Key inválida o no autorizada. Verifica la API Key en la configuración.',
                'status_code': response.status_code
            }
        elif response.status_code == 403:
            return {
                'success': False,
                'message': 'Acceso denegado. Verifica la API Key y permisos de la instancia.',
                'status_code': response.status_code
            }
        elif response.status_code == 500:
            # Error 500 suele indicar problemas de conexión con la instancia
            error_msg = f'Error HTTP {response.status_code}'
            error_detail = None
            try:
                error_json = response.json()
                error_detail = error_json.get('response', {}).get('message') or error_json.get('message') or error_json.get('error')
                if isinstance(error_detail, dict):
                    error_detail = str(error_detail)
                error_msg = error_detail or error_msg
            except:
                # Intentar leer el texto de respuesta
                try:
                    error_text = response.text[:500] if response.text else ''
                    error_msg = error_text if error_text else error_msg
                except:
                    pass
            
            # Mensaje específico para "Connection Closed"
            if error_detail and ('Connection Closed' in str(error_detail) or 'connection closed' in str(error_detail).lower()):
                return {
                    'success': False,
                    'message': 'La conexión de WhatsApp está cerrada. Por favor, verifica que la instancia esté conectada en Evolution API. Necesitas escanear el código QR o reconectar la instancia.',
                    'error_detail': 'Connection Closed - La instancia de WhatsApp no está conectada',
                    'status_code': response.status_code,
                    'suggestion': 'Verifica el estado de la instancia en Evolution API y reconéctala si es necesario'
                }
            else:
                return {
                    'success': False,
                    'message': f'Error del servidor al enviar mensaje: {error_msg}',
                    'status_code': response.status_code
                }
        else:
            error_msg = f'Error HTTP {response.status_code}'
            try:
                error_json = response.json()
                error_msg = error_json.get('message') or error_json.get('error') or error_msg
                if isinstance(error_msg, dict):
                    error_msg = str(error_msg)
            except:
                # Intentar leer el texto de respuesta
                try:
                    error_msg = response.text[:200] if response.text else error_msg
                except:
                    pass
            
            return {
                'success': False,
                'message': f'Error al enviar mensaje: {error_msg}',
                'status_code': response.status_code
            }
            
    except requests.exceptions.ConnectionError as e:
        print(f"[Evolution API] ConnectionError: {str(e)}")
        return {'success': False, 'message': f'No se pudo conectar al servidor Evolution API. Verifica que la URL sea correcta y que el servidor esté corriendo: {api_url}'}
    except requests.exceptions.Timeout as e:
        print(f"[Evolution API] Timeout: {str(e)}")
        return {'success': False, 'message': 'Timeout al enviar mensaje. El servidor tardó demasiado en responder.'}
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"[Evolution API] Error inesperado: {str(e)}")
        print(f"[Evolution API] Traceback: {error_trace}")
        return {'success': False, 'message': f'Error inesperado al enviar mensaje: {str(e)}'}

@app.route('/marketing/integraciones/whatsapp/enviar-prueba', methods=['POST'])
@login_required
def marketing_whatsapp_enviar_prueba():
    """Enviar mensaje de prueba"""
    if is_cliente(current_user):
        return jsonify({'success': False, 'message': 'No tienes acceso'}), 403
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'Datos no proporcionados'}), 400
        
        numero = data.get('numero', '').strip()
        mensaje = data.get('mensaje', 'Este es un mensaje de prueba desde el sistema de marketing.').strip()
        
        if not numero:
            return jsonify({'success': False, 'message': 'Número de destino requerido'}), 400
        
        if not mensaje:
            mensaje = 'Este es un mensaje de prueba desde el sistema de marketing.'
        
        resultado = enviar_mensaje_whatsapp(numero, mensaje)
        
        # Asegurar que siempre devolvemos un JSON válido
        if not isinstance(resultado, dict):
            return jsonify({'success': False, 'message': 'Error desconocido al enviar mensaje'}), 500
        
        # Si hay un status_code de error, devolver código HTTP apropiado
        status_code = resultado.get('status_code', 200 if resultado.get('success') else 500)
        
        return jsonify(resultado), status_code if status_code != 200 else 200
        
    except Exception as e:
        import traceback
        print(f"Error en enviar-prueba: {str(e)}")
        print(traceback.format_exc())
        return jsonify({
            'success': False, 
            'message': f'Error inesperado: {str(e)}'
        }), 500

@app.route('/marketing/integraciones/whatsapp/enviar-campana', methods=['POST'])
@login_required
def marketing_whatsapp_enviar_campana():
    """Enviar mensajes de campaña a múltiples destinatarios"""
    if is_cliente(current_user):
        return jsonify({'success': False, 'message': 'No tienes acceso'}), 403
    
    data = request.get_json()
    numeros = data.get('numeros', [])  # Lista de números
    mensaje = data.get('mensaje')
    campana_id = data.get('campana_id')
    
    if not numeros or not mensaje:
        return jsonify({'success': False, 'message': 'Números y mensaje requeridos'}), 400
    
    resultados = []
    exitosos = 0
    fallidos = 0
    
    for numero in numeros:
        resultado = enviar_mensaje_whatsapp(numero, mensaje)
        resultados.append({
            'numero': numero,
            'success': resultado.get('success', False),
            'message': resultado.get('message', '')
        })
        if resultado.get('success'):
            exitosos += 1
        else:
            fallidos += 1
    
    # Registrar resultados si hay campana_id
    if campana_id:
        try:
            from models import get_db_connection
            import json
            conn = get_db_connection()
            cur = conn.cursor()
            
            # Actualizar estadísticas de la campaña
            cur.execute("""
                UPDATE marketing_campanas
                SET updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (campana_id,))
            
            conn.commit()
            cur.close()
            conn.close()
        except:
            pass
    
    return jsonify({
        'success': True,
        'message': f'Enviados: {exitosos}, Fallidos: {fallidos}',
        'exitosos': exitosos,
        'fallidos': fallidos,
        'resultados': resultados
    })

@app.route('/marketing/agendas/personal')
@login_required
def marketing_agendas_personal():
    """Agenda personal de marketing"""
    if is_cliente(current_user):
        flash('No tienes acceso a esta sección.', 'error')
        return redirect('/projects')
    
    from models import get_db_connection
    
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, usuario_id, cliente_id, negocio_sucursal, fecha, tipo_evento,
               titulo, descripcion, estado
        FROM marketing_agendas
        WHERE usuario_id = %s OR created_by = %s
        ORDER BY fecha DESC
        LIMIT 50
    """, (current_user.id, current_user.id))
    agendas = cur.fetchall()
    cur.close()
    conn.close()
    
    agendas_dict = []
    for agenda in agendas:
        agendas_dict.append({
            'id': agenda[0],
            'usuario_id': agenda[1],
            'cliente_id': agenda[2],
            'negocio_sucursal': agenda[3],
            'fecha': agenda[4].strftime('%Y-%m-%d %H:%M:%S') if agenda[4] else '',
            'tipo_evento': agenda[5],
            'titulo': agenda[6],
            'descripcion': agenda[7],
            'estado': agenda[8]
        })
    
    return render_template('marketing/agendas_personal.html',
                         now=datetime.now(),
                         agendas=agendas_dict)

@app.route('/marketing/recordatorios')
@login_required
def marketing_recordatorios():
    """Configuración de recordatorios"""
    if is_cliente(current_user):
        flash('No tienes acceso a esta sección.', 'error')
        return redirect('/projects')
    
    from models import get_db_connection
    
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, nombre, tipo, destinatario_tipo, destinatario_id, mensaje, canal,
               fecha_programada, fecha_envio, estado, activo, enviado
        FROM marketing_recordatorios
        ORDER BY created_at DESC
        LIMIT 100
    """)
    recordatorios = cur.fetchall()
    cur.close()
    conn.close()
    
    recordatorios_dict = []
    for rec in recordatorios:
        recordatorios_dict.append({
            'id': rec[0],
            'nombre': rec[1],
            'tipo': rec[2],
            'destinatario_tipo': rec[3],
            'destinatario_id': rec[4],
            'mensaje': rec[5],
            'canal': rec[6],
            'fecha_programada': rec[7].strftime('%Y-%m-%d %H:%M:%S') if rec[7] else '',
            'fecha_envio': rec[8].strftime('%Y-%m-%d %H:%M:%S') if rec[8] else '',
            'estado': rec[9],
            'activo': rec[10] if len(rec) > 10 else True,
            'enviado': rec[11] if len(rec) > 11 else False
        })
    
    return render_template('marketing/recordatorios.html',
                         now=datetime.now(),
                         recordatorios=recordatorios_dict)

@app.route('/marketing/recordatorios/nuevo', methods=['POST'])
@login_required
def marketing_recordatorios_nuevo():
    """Crear nuevo recordatorio"""
    if is_cliente(current_user):
        flash('No tienes acceso a esta sección.', 'error')
        return redirect('/projects')
    
    from models import get_db_connection
    
    nombre = request.form.get('nombre')
    tipo = request.form.get('tipo')
    destinatario_tipo = request.form.get('destinatario_tipo')
    destinatario_id = request.form.get('destinatario_id', type=int)
    mensaje = request.form.get('mensaje')
    canal = request.form.get('canal')
    fecha_programada = request.form.get('fecha_programada')
    activo = request.form.get('activo') == '1'
    
    if not all([tipo, destinatario_tipo, destinatario_id, mensaje, canal, fecha_programada]):
        flash('Todos los campos requeridos deben estar completos', 'error')
        return redirect('/marketing/recordatorios')
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # Convertir fecha
        fecha_dt = datetime.strptime(fecha_programada, '%Y-%m-%dT%H:%M')
        
        cur.execute("""
            INSERT INTO marketing_recordatorios 
            (nombre, tipo, destinatario_tipo, destinatario_id, mensaje, canal, fecha_programada, activo, created_by)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (nombre, tipo, destinatario_tipo, destinatario_id, mensaje, canal, fecha_dt, activo, current_user.id))
        
        recordatorio_id = cur.fetchone()[0]
        conn.commit()
        flash('Recordatorio creado exitosamente', 'success')
    except Exception as e:
        conn.rollback()
        flash(f'Error al crear recordatorio: {str(e)}', 'error')
    finally:
        cur.close()
        conn.close()
    
    return redirect('/marketing/recordatorios')

@app.route('/marketing/recordatorios/<int:recordatorio_id>/toggle', methods=['POST'])
@login_required
def marketing_recordatorios_toggle(recordatorio_id):
    """Habilitar o deshabilitar un recordatorio"""
    if is_cliente(current_user):
        return jsonify({'success': False, 'message': 'No tienes acceso'}), 403
    
    from models import get_db_connection
    import json
    
    data = request.get_json()
    activo = data.get('activo', False)
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        estado = 'pendiente' if activo else 'deshabilitado'
        cur.execute("""
            UPDATE marketing_recordatorios
            SET activo = %s, estado = %s
            WHERE id = %s
        """, (activo, estado, recordatorio_id))
        
        conn.commit()
        return jsonify({'success': True, 'message': 'Recordatorio actualizado'})
    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        cur.close()
        conn.close()

@app.route('/marketing/recordatorios/<int:recordatorio_id>/cancelar', methods=['POST'])
@login_required
def marketing_recordatorios_cancelar(recordatorio_id):
    """Cancelar un recordatorio"""
    if is_cliente(current_user):
        return jsonify({'success': False, 'message': 'No tienes acceso'}), 403
    
    from models import get_db_connection
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute("""
            UPDATE marketing_recordatorios
            SET estado = 'cancelado', activo = FALSE
            WHERE id = %s AND enviado = FALSE
        """, (recordatorio_id,))
        
        conn.commit()
        if cur.rowcount > 0:
            return jsonify({'success': True, 'message': 'Recordatorio cancelado'})
        else:
            return jsonify({'success': False, 'message': 'Recordatorio no encontrado o ya fue enviado'})
    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        cur.close()
        conn.close()

@app.route('/marketing/recordatorios/<int:recordatorio_id>')
@login_required
def marketing_recordatorios_ver(recordatorio_id):
    """Obtener detalles de un recordatorio"""
    if is_cliente(current_user):
        return jsonify({'success': False, 'message': 'No tienes acceso'}), 403
    
    from models import get_db_connection
    
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, nombre, tipo, destinatario_tipo, destinatario_id, mensaje, canal,
               fecha_programada, fecha_envio, estado, activo, enviado
        FROM marketing_recordatorios
        WHERE id = %s
    """, (recordatorio_id,))
    rec = cur.fetchone()
    cur.close()
    conn.close()
    
    if rec:
        return jsonify({
            'success': True,
            'recordatorio': {
                'id': rec[0],
                'nombre': rec[1],
                'tipo': rec[2],
                'destinatario_tipo': rec[3],
                'destinatario_id': rec[4],
                'mensaje': rec[5],
                'canal': rec[6],
                'fecha_programada': rec[7].strftime('%Y-%m-%d %H:%M:%S') if rec[7] else '',
                'fecha_envio': rec[8].strftime('%Y-%m-%d %H:%M:%S') if rec[8] else '',
                'estado': rec[9],
                'activo': rec[10],
                'enviado': rec[11]
            }
        })
    else:
        return jsonify({'success': False, 'message': 'Recordatorio no encontrado'}), 404

@app.route('/marketing/recordatorios/procesar', methods=['POST'])
@login_required
def marketing_recordatorios_procesar():
    """Procesar recordatorios pendientes y enviarlos"""
    if is_cliente(current_user):
        return jsonify({'success': False, 'message': 'No tienes acceso'}), 403
    
    from models import get_db_connection
    from datetime import datetime
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # Obtener recordatorios pendientes cuya fecha ya pasó
        cur.execute("""
            SELECT id, tipo, destinatario_tipo, destinatario_id, mensaje, canal, fecha_programada
            FROM marketing_recordatorios
            WHERE estado = 'pendiente'
            AND activo = TRUE
            AND enviado = FALSE
            AND fecha_programada <= CURRENT_TIMESTAMP
            ORDER BY fecha_programada ASC
            LIMIT 100
        """)
        recordatorios = cur.fetchall()
        
        procesados = 0
        exitosos = 0
        fallidos = 0
        
        for rec in recordatorios:
            rec_id, tipo, destinatario_tipo, destinatario_id, mensaje, canal, fecha_programada = rec
            
            try:
                # Obtener número de teléfono según el tipo de destinatario
                numero = None
                
                if destinatario_tipo == 'cliente':
                    cur.execute("SELECT telefono FROM clientes WHERE id = %s", (destinatario_id,))
                    cliente = cur.fetchone()
                    if cliente:
                        numero = cliente[0]
                elif destinatario_tipo == 'usuario':
                    cur.execute("SELECT telefono FROM users WHERE id = %s", (destinatario_id,))
                    usuario = cur.fetchone()
                    if usuario and usuario[0]:
                        numero = usuario[0]
                
                if not numero:
                    # Marcar como fallido
                    cur.execute("""
                        UPDATE marketing_recordatorios
                        SET estado = 'fallido', enviado = FALSE
                        WHERE id = %s
                    """, (rec_id,))
                    fallidos += 1
                    continue
                
                # Limpiar número de teléfono
                numero = str(numero).replace('+', '').replace(' ', '').replace('-', '')
                
                # Reemplazar variables dinámicas en el mensaje
                mensaje_personalizado = reemplazar_variables_mensaje(
                    mensaje,
                    destinatario_tipo,
                    destinatario_id,
                    rec_id
                )
                
                # Enviar mensaje según el canal
                if canal == 'whatsapp':
                    resultado = enviar_mensaje_whatsapp(numero, mensaje_personalizado)
                    
                    if resultado.get('success'):
                        cur.execute("""
                            UPDATE marketing_recordatorios
                            SET estado = 'enviado', enviado = TRUE, fecha_envio = CURRENT_TIMESTAMP
                            WHERE id = %s
                        """, (rec_id,))
                        exitosos += 1
                    else:
                        cur.execute("""
                            UPDATE marketing_recordatorios
                            SET estado = 'fallido', enviado = FALSE
                            WHERE id = %s
                        """, (rec_id,))
                        fallidos += 1
                else:
                    # Para otros canales (email, sms) implementar más adelante
                    cur.execute("""
                        UPDATE marketing_recordatorios
                        SET estado = 'pendiente_otro_canal', enviado = FALSE
                        WHERE id = %s
                    """, (rec_id,))
                    fallidos += 1
                
                procesados += 1
                
            except Exception as e:
                # Marcar como fallido en caso de error
                cur.execute("""
                    UPDATE marketing_recordatorios
                    SET estado = 'fallido', enviado = FALSE
                    WHERE id = %s
                """, (rec_id,))
                fallidos += 1
                print(f"Error procesando recordatorio {rec_id}: {str(e)}")
        
        conn.commit()
        
        return jsonify({
            'success': True,
            'message': f'Procesados: {procesados}, Exitosos: {exitosos}, Fallidos: {fallidos}',
            'procesados': procesados,
            'exitosos': exitosos,
            'fallidos': fallidos
        })
        
    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500
    finally:
        cur.close()
        conn.close()

# ========== RUTAS FALTANTES DE MARKETING ==========

# Integraciones
@app.route('/marketing/integraciones/google-ads')
@login_required
def marketing_integraciones_google_ads():
    """Configuración de Google Ads"""
    if is_cliente(current_user):
        flash('No tienes acceso a esta sección.', 'error')
        return redirect('/projects')
    
    from models import get_db_connection
    import json
    
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, tipo, nombre, activa, configuracion, estado_conexion
        FROM marketing_integraciones
        WHERE tipo = 'google_ads'
        LIMIT 1
    """)
    integracion = cur.fetchone()
    cur.close()
    conn.close()
    
    configuracion = None
    if integracion:
        configuracion = {
            'id': integracion[0],
            'tipo': integracion[1],
            'nombre': integracion[2],
            'activa': integracion[3],
            'configuracion': integracion[4],
            'estado_conexion': integracion[5]
        }
    
    return render_template('marketing/integraciones_google_ads.html',
                         now=datetime.now(),
                         configuracion=configuracion)

@app.route('/marketing/integraciones/email')
@login_required
def marketing_integraciones_email():
    """Configuración de Email Marketing"""
    if is_cliente(current_user):
        flash('No tienes acceso a esta sección.', 'error')
        return redirect('/projects')
    
    from models import get_db_connection
    import json
    
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, tipo, nombre, activa, configuracion, estado_conexion
        FROM marketing_integraciones
        WHERE tipo = 'email_marketing'
        LIMIT 1
    """)
    integracion = cur.fetchone()
    cur.close()
    conn.close()
    
    configuracion = None
    if integracion:
        # PostgreSQL JSONB puede devolver dict directamente o string
        config_raw = integracion[4]
        if isinstance(config_raw, dict):
            config_dict = config_raw
        elif isinstance(config_raw, str):
            try:
                config_dict = json.loads(config_raw) if config_raw else {}
            except:
                config_dict = {}
        else:
            config_dict = {}
        
        configuracion = {
            'id': integracion[0],
            'tipo': integracion[1],
            'nombre': integracion[2],
            'activa': integracion[3],
            'configuracion': config_dict,
            'estado_conexion': integracion[5]
        }
    
    return render_template('marketing/integraciones_email.html',
                         now=datetime.now(),
                         configuracion=configuracion)

# Campañas
@app.route('/marketing/campanas/activas')
@login_required
def marketing_campanas_activas():
    """Campañas activas"""
    if is_cliente(current_user):
        flash('No tienes acceso a esta sección.', 'error')
        return redirect('/projects')
    
    from models import MarketingCampana
    campanas = MarketingCampana.get_all()
    campanas_activas = [c for c in campanas if c.estado == 'activa']
    campanas_dict = [c.to_dict() for c in campanas_activas]
    
    return render_template('marketing/campanas_activas.html',
                         now=datetime.now(),
                         campanas=campanas_dict)

@app.route('/marketing/campanas/resultados')
@login_required
def marketing_campanas_resultados():
    """Resultados y métricas de campañas"""
    if is_cliente(current_user):
        flash('No tienes acceso a esta sección.', 'error')
        return redirect('/projects')
    
    from models import MarketingCampana, get_db_connection
    import json
    
    campanas = MarketingCampana.get_all()
    campanas_dict = []
    
    # Obtener resultados de cada campaña
    conn = get_db_connection()
    cur = conn.cursor()
    
    for campana in campanas:
        campana_data = campana.to_dict()
        
        # Obtener resultados de la campaña
        cur.execute("""
            SELECT SUM(impresiones), SUM(clicks), SUM(conversiones), SUM(costo), SUM(ingresos),
                   AVG(ctr), AVG(cpc), AVG(roi)
            FROM marketing_resultados
            WHERE campana_id = %s
        """, (campana.id,))
        resultado = cur.fetchone()
        
        if resultado and resultado[0]:
            campana_data['resultados'] = {
                'impresiones': int(resultado[0]) if resultado[0] else 0,
                'clicks': int(resultado[1]) if resultado[1] else 0,
                'conversiones': int(resultado[2]) if resultado[2] else 0,
                'costo': float(resultado[3]) if resultado[3] else 0,
                'ingresos': float(resultado[4]) if resultado[4] else 0,
                'ctr': float(resultado[5]) if resultado[5] else 0,
                'cpc': float(resultado[6]) if resultado[6] else 0,
                'roi': float(resultado[7]) if resultado[7] else 0
            }
        else:
            campana_data['resultados'] = None
        
        campanas_dict.append(campana_data)
    
    cur.close()
    conn.close()
    
    return render_template('marketing/campanas_resultados.html',
                         now=datetime.now(),
                         campanas=campanas_dict)

@app.route('/marketing/campanas/presupuesto')
@login_required
def marketing_campanas_presupuesto():
    """Presupuesto y gastos de campañas"""
    if is_cliente(current_user):
        flash('No tienes acceso a esta sección.', 'error')
        return redirect('/projects')
    
    from models import MarketingCampana
    campanas = MarketingCampana.get_all()
    campanas_dict = []
    
    total_presupuesto = 0
    total_gastado = 0
    
    for campana in campanas:
        campana_data = campana.to_dict()
        total_presupuesto += campana.presupuesto
        total_gastado += campana.presupuesto_gastado
        campana_data['porcentaje_gastado'] = (campana.presupuesto_gastado / campana.presupuesto * 100) if campana.presupuesto > 0 else 0
        campanas_dict.append(campana_data)
    
    return render_template('marketing/campanas_presupuesto.html',
                         now=datetime.now(),
                         campanas=campanas_dict,
                         total_presupuesto=total_presupuesto,
                         total_gastado=total_gastado,
                         disponible=total_presupuesto - total_gastado)

# Clientes
@app.route('/marketing/clientes/segmentos')
@login_required
def marketing_clientes_segmentos():
    """Segmentos y audiencias de clientes"""
    if is_cliente(current_user):
        flash('No tienes acceso a esta sección.', 'error')
        return redirect('/projects')
    
    from models import ClienteSegmento, Cliente
    
    segmentos_data = {}
    for segmento_tipo in ['recurrente', 'nuevo', 'perdido']:
        segmentos = ClienteSegmento.get_by_segmento(segmento_tipo)
        segmentos_data[segmento_tipo] = len(segmentos)
    
    # Mes actual para cumpleaños
    mes_actual = datetime.now().month
    cumpleanos = ClienteSegmento.get_cumpleanos_mes(mes_actual)
    segmentos_data['cumpleanos'] = len(cumpleanos)
    
    # Obtener todos los clientes con sus segmentos
    clientes = Cliente.get_all()
    clientes_segmentados = []
    for cliente in clientes:
        cliente_data = cliente.to_dict()
        segmento = ClienteSegmento.get_by_cliente_id(cliente.id)
        if segmento:
            cliente_data['segmento'] = segmento.to_dict()
        else:
            cliente_data['segmento'] = None
        clientes_segmentados.append(cliente_data)
    
    return render_template('marketing/clientes_segmentos.html',
                         now=datetime.now(),
                         segmentos_count=segmentos_data,
                         clientes=clientes_segmentados)

@app.route('/marketing/clientes/exportar')
@login_required
def marketing_clientes_exportar():
    """Exportar clientes para Meta/Google"""
    if is_cliente(current_user):
        flash('No tienes acceso a esta sección.', 'error')
        return redirect('/projects')
    
    from models import Cliente, ClienteSegmento
    
    clientes = Cliente.get_all()
    
    # Preparar datos para exportación
    clientes_export = []
    for cliente in clientes:
        segmento = ClienteSegmento.get_by_cliente_id(cliente.id)
        clientes_export.append({
            'email': cliente.correo,
            'telefono': cliente.telefono.replace('+', '').replace(' ', '').replace('-', '') if cliente.telefono else '',
            'nombre': cliente.nombre or '',
            'apellido': cliente.apellido or '',
            'segmento': segmento.segmento if segmento else 'sin_segmento'
        })
    
    return render_template('marketing/clientes_exportar.html',
                         now=datetime.now(),
                         clientes=clientes_export,
                         total_clientes=len(clientes_export))

@app.route('/marketing/clientes/cumpleanos')
@login_required
def marketing_clientes_cumpleanos():
    """Cumpleaños del mes"""
    if is_cliente(current_user):
        flash('No tienes acceso a esta sección.', 'error')
        return redirect('/projects')
    
    from models import ClienteSegmento, Cliente
    
    mes_actual = datetime.now().month
    cumpleanos = ClienteSegmento.get_cumpleanos_mes(mes_actual)
    
    clientes_dict = {c.id: c.to_dict() for c in Cliente.get_all()}
    
    cumpleanos_dict = []
    for segmento in cumpleanos:
        cliente = clientes_dict.get(segmento.cliente_id)
        if cliente:
            cumpleanos_dict.append({
                'cliente': cliente,
                'segmento': segmento.to_dict(),
                'fecha_nacimiento': segmento.fecha_nacimiento
            })
    
    return render_template('marketing/clientes_cumpleanos.html',
                         now=datetime.now(),
                         cumpleanos=cumpleanos_dict,
                         mes_actual=mes_actual)

# Agendas
@app.route('/marketing/agendas/negocio')
@login_required
def marketing_agendas_negocio():
    """Agenda por negocio/sucursal"""
    if is_cliente(current_user):
        flash('No tienes acceso a esta sección.', 'error')
        return redirect('/projects')
    
    from models import get_db_connection
    
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, usuario_id, cliente_id, negocio_sucursal, fecha, tipo_evento,
               titulo, descripcion, estado
        FROM marketing_agendas
        WHERE negocio_sucursal IS NOT NULL
        ORDER BY fecha DESC
        LIMIT 100
    """)
    agendas = cur.fetchall()
    cur.close()
    conn.close()
    
    agendas_dict = []
    for agenda in agendas:
        agendas_dict.append({
            'id': agenda[0],
            'usuario_id': agenda[1],
            'cliente_id': agenda[2],
            'negocio_sucursal': agenda[3],
            'fecha': agenda[4].strftime('%Y-%m-%d %H:%M:%S') if agenda[4] else '',
            'tipo_evento': agenda[5],
            'titulo': agenda[6],
            'descripcion': agenda[7],
            'estado': agenda[8]
        })
    
    return render_template('marketing/agendas_negocio.html',
                         now=datetime.now(),
                         agendas=agendas_dict)

# Recordatorios
@app.route('/marketing/recordatorios/plantillas')
@login_required
def marketing_recordatorios_plantillas():
    """Plantillas de recordatorios"""
    if is_cliente(current_user):
        flash('No tienes acceso a esta sección.', 'error')
        return redirect('/projects')
    
    from models import get_db_connection
    
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, nombre, tipo, canal, asunto, contenido, activa, uso_count, created_at
        FROM marketing_plantillas
        ORDER BY uso_count DESC, created_at DESC
    """)
    plantillas = cur.fetchall()
    cur.close()
    conn.close()
    
    plantillas_dict = []
    for plant in plantillas:
        plantillas_dict.append({
            'id': plant[0],
            'nombre': plant[1],
            'tipo': plant[2],
            'canal': plant[3],
            'asunto': plant[4],
            'contenido': plant[5],
            'activa': plant[6],
            'uso_count': plant[7],
            'created_at': plant[8].strftime('%Y-%m-%d %H:%M:%S') if plant[8] else ''
        })
    
    return render_template('marketing/recordatorios_plantillas.html',
                         now=datetime.now(),
                         plantillas=plantillas_dict)

@app.route('/marketing/recordatorios/historial')
@login_required
def marketing_recordatorios_historial():
    """Historial de envíos de recordatorios"""
    if is_cliente(current_user):
        flash('No tienes acceso a esta sección.', 'error')
        return redirect('/projects')
    
    from models import get_db_connection
    
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, nombre, tipo, destinatario_tipo, destinatario_id, mensaje, canal,
               fecha_programada, fecha_envio, estado, enviado
        FROM marketing_recordatorios
        WHERE enviado = TRUE OR estado = 'enviado'
        ORDER BY fecha_envio DESC
        LIMIT 100
    """)
    recordatorios = cur.fetchall()
    cur.close()
    conn.close()
    
    recordatorios_dict = []
    for rec in recordatorios:
        recordatorios_dict.append({
            'id': rec[0],
            'nombre': rec[1],
            'tipo': rec[2],
            'destinatario_tipo': rec[3],
            'destinatario_id': rec[4],
            'mensaje': rec[5][:100] + '...' if rec[5] and len(rec[5]) > 100 else rec[5],
            'canal': rec[6],
            'fecha_programada': rec[7].strftime('%Y-%m-%d %H:%M:%S') if rec[7] else '',
            'fecha_envio': rec[8].strftime('%Y-%m-%d %H:%M:%S') if rec[8] else '',
            'estado': rec[9],
            'enviado': rec[10]
        })
    
    return render_template('marketing/recordatorios_historial.html',
                         now=datetime.now(),
                         recordatorios=recordatorios_dict)

# Remarketing
@app.route('/marketing/remarketing/whatsapp')
@login_required
def marketing_remarketing_whatsapp():
    """Campañas de remarketing por WhatsApp"""
    if is_cliente(current_user):
        flash('No tienes acceso a esta sección.', 'error')
        return redirect('/projects')
    
    from models import MarketingCampana
    campanas = MarketingCampana.get_all()
    campanas_remarketing = [c for c in campanas if 'remarketing' in c.tipo.lower() or 'whatsapp' in c.plataforma.lower()]
    campanas_dict = [c.to_dict() for c in campanas_remarketing]
    
    return render_template('marketing/remarketing_whatsapp.html',
                         now=datetime.now(),
                         campanas=campanas_dict)

@app.route('/marketing/remarketing/email')
@login_required
def marketing_remarketing_email():
    """Campañas de remarketing por Email"""
    if is_cliente(current_user):
        flash('No tienes acceso a esta sección.', 'error')
        return redirect('/projects')
    
    from models import MarketingCampana
    campanas = MarketingCampana.get_all()
    campanas_remarketing = [c for c in campanas if 'remarketing' in c.tipo.lower() or 'email' in c.plataforma.lower()]
    campanas_dict = [c.to_dict() for c in campanas_remarketing]
    
    return render_template('marketing/remarketing_email.html',
                         now=datetime.now(),
                         campanas=campanas_dict)

@app.route('/marketing/remarketing/segmentos')
@login_required
def marketing_remarketing_segmentos():
    """Segmentos para remarketing"""
    if is_cliente(current_user):
        flash('No tienes acceso a esta sección.', 'error')
        return redirect('/projects')
    
    from models import ClienteSegmento, Cliente
    
    # Segmentos comunes para remarketing
    clientes_perdidos = ClienteSegmento.get_by_segmento('perdido')
    clientes_dict = {c.id: c.to_dict() for c in Cliente.get_all()}
    
    segmentos_remarketing = []
    for segmento in clientes_perdidos:
        cliente = clientes_dict.get(segmento.cliente_id)
        if cliente:
            segmentos_remarketing.append({
                'cliente': cliente,
                'segmento': segmento.to_dict(),
                'dias_sin_visita': None  # Calcular según última visita
            })
    
    return render_template('marketing/remarketing_segmentos.html',
                         now=datetime.now(),
                         segmentos=segmentos_remarketing)

# Análisis y Reportes
@app.route('/marketing/analisis/roi')
@login_required
def marketing_analisis_roi():
    """ROI y Conversiones"""
    if is_cliente(current_user):
        flash('No tienes acceso a esta sección.', 'error')
        return redirect('/projects')
    
    from models import MarketingCampana, get_db_connection
    
    campanas = MarketingCampana.get_all()
    
    # Calcular ROI por campaña
    conn = get_db_connection()
    cur = conn.cursor()
    
    campanas_roi = []
    for campana in campanas:
        cur.execute("""
            SELECT SUM(costo) as total_costo, SUM(ingresos) as total_ingresos, SUM(conversiones) as total_conversiones
            FROM marketing_resultados
            WHERE campana_id = %s
        """, (campana.id,))
        resultado = cur.fetchone()
        
        if resultado and resultado[0]:
            costo = float(resultado[0]) if resultado[0] else 0
            ingresos = float(resultado[1]) if resultado[1] else 0
            conversiones = int(resultado[2]) if resultado[2] else 0
            
            roi = ((ingresos - costo) / costo * 100) if costo > 0 else 0
            costo_por_conversion = costo / conversiones if conversiones > 0 else 0
            valor_por_conversion = ingresos / conversiones if conversiones > 0 else 0
            
            campanas_roi.append({
                'campana': campana.to_dict(),
                'costo': costo,
                'ingresos': ingresos,
                'conversiones': conversiones,
                'roi': roi,
                'costo_por_conversion': costo_por_conversion,
                'valor_por_conversion': valor_por_conversion
            })
    
    cur.close()
    conn.close()
    
    return render_template('marketing/analisis_roi.html',
                         now=datetime.now(),
                         campanas_roi=campanas_roi)

@app.route('/marketing/analisis/embudo')
@login_required
def marketing_analisis_embudo():
    """Embudo de Conversión"""
    if is_cliente(current_user):
        flash('No tienes acceso a esta sección.', 'error')
        return redirect('/projects')
    
    from models import MarketingCampana, get_db_connection
    
    campanas = MarketingCampana.get_all()
    
    # Calcular métricas del embudo
    conn = get_db_connection()
    cur = conn.cursor()
    
    embudo_global = {
        'impresiones': 0,
        'clicks': 0,
        'conversiones': 0,
        'tasa_clic': 0,
        'tasa_conversion': 0
    }
    
    for campana in campanas:
        cur.execute("""
            SELECT SUM(impresiones), SUM(clicks), SUM(conversiones)
            FROM marketing_resultados
            WHERE campana_id = %s
        """, (campana.id,))
        resultado = cur.fetchone()
        
        if resultado and resultado[0]:
            embudo_global['impresiones'] += int(resultado[0]) if resultado[0] else 0
            embudo_global['clicks'] += int(resultado[1]) if resultado[1] else 0
            embudo_global['conversiones'] += int(resultado[2]) if resultado[2] else 0
    
    if embudo_global['impresiones'] > 0:
        embudo_global['tasa_clic'] = (embudo_global['clicks'] / embudo_global['impresiones']) * 100
    if embudo_global['clicks'] > 0:
        embudo_global['tasa_conversion'] = (embudo_global['conversiones'] / embudo_global['clicks']) * 100
    
    cur.close()
    conn.close()
    
    return render_template('marketing/analisis_embudo.html',
                         now=datetime.now(),
                         embudo=embudo_global)

@app.route('/marketing/analisis/atribucion')
@login_required
def marketing_analisis_atribucion():
    """Atribución de Ventas"""
    if is_cliente(current_user):
        flash('No tienes acceso a esta sección.', 'error')
        return redirect('/projects')
    
    from models import MarketingCampana, get_db_connection
    
    campanas = MarketingCampana.get_all()
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    atribucion = []
    for campana in campanas:
        cur.execute("""
            SELECT SUM(conversiones) as total_conversiones, SUM(ingresos) as total_ingresos
            FROM marketing_resultados
            WHERE campana_id = %s
        """, (campana.id,))
        resultado = cur.fetchone()
        
        if resultado and resultado[0]:
            atribucion.append({
                'campana': campana.to_dict(),
                'conversiones': int(resultado[0]) if resultado[0] else 0,
                'ingresos': float(resultado[1]) if resultado[1] else 0
            })
    
    # Ordenar por ingresos
    atribucion.sort(key=lambda x: x['ingresos'], reverse=True)
    
    cur.close()
    conn.close()
    
    return render_template('marketing/analisis_atribucion.html',
                         now=datetime.now(),
                         atribucion=atribucion)

@app.route('/marketing/analisis/reportes')
@login_required
def marketing_analisis_reportes():
    """Reportes Personalizados"""
    if is_cliente(current_user):
        flash('No tienes acceso a esta sección.', 'error')
        return redirect('/projects')
    
    return render_template('marketing/analisis_reportes.html',
                         now=datetime.now())

# Automatización
@app.route('/marketing/automatizacion/flujos')
@login_required
def marketing_automatizacion_flujos():
    """Flujos de Marketing"""
    if is_cliente(current_user):
        flash('No tienes acceso a esta sección.', 'error')
        return redirect('/projects')
    
    from models import get_db_connection
    
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, nombre, descripcion, activo, trigger_tipo, ejecuciones_count, created_at
        FROM marketing_flujos
        ORDER BY created_at DESC
    """)
    flujos = cur.fetchall()
    cur.close()
    conn.close()
    
    flujos_dict = []
    for flujo in flujos:
        flujos_dict.append({
            'id': flujo[0],
            'nombre': flujo[1],
            'descripcion': flujo[2],
            'activo': flujo[3],
            'trigger_tipo': flujo[4],
            'ejecuciones_count': flujo[5],
            'created_at': flujo[6].strftime('%Y-%m-%d %H:%M:%S') if flujo[6] else ''
        })
    
    return render_template('marketing/automatizacion_flujos.html',
                         now=datetime.now(),
                         flujos=flujos_dict)

@app.route('/marketing/automatizacion/triggers')
@login_required
def marketing_automatizacion_triggers():
    """Triggers y Condiciones"""
    if is_cliente(current_user):
        flash('No tienes acceso a esta sección.', 'error')
        return redirect('/projects')
    
    return render_template('marketing/automatizacion_triggers.html',
                         now=datetime.now())

@app.route('/marketing/automatizacion/abandonos')
@login_required
def marketing_automatizacion_abandonos():
    """Recuperación de Abandonos"""
    if is_cliente(current_user):
        flash('No tienes acceso a esta sección.', 'error')
        return redirect('/projects')
    
    return render_template('marketing/automatizacion_abandonos.html',
                         now=datetime.now())

# Configuración
@app.route('/marketing/configuracion')
@login_required
def marketing_configuracion():
    """Configuración general de Marketing"""
    if is_cliente(current_user):
        flash('No tienes acceso a esta sección.', 'error')
        return redirect('/projects')
    
    from models import get_db_connection
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Obtener todas las integraciones
    cur.execute("""
        SELECT tipo, nombre, activa, estado_conexion
        FROM marketing_integraciones
        ORDER BY tipo
    """)
    integraciones = cur.fetchall()
    
    integraciones_dict = []
    for integ in integraciones:
        integraciones_dict.append({
            'tipo': integ[0],
            'nombre': integ[1],
            'activa': integ[2],
            'estado_conexion': integ[3]
        })
    
    cur.close()
    conn.close()
    
    return render_template('marketing/configuracion.html',
                         now=datetime.now(),
                         integraciones=integraciones_dict)

# Rutas adicionales para guardar configuraciones
@app.route('/marketing/integraciones/google-ads/guardar', methods=['POST'])
@login_required
def marketing_google_ads_guardar():
    """Guardar configuración de Google Ads"""
    if is_cliente(current_user):
        flash('No tienes acceso a esta sección.', 'error')
        return redirect('/projects')
    
    from models import get_db_connection
    import json
    
    customer_id = request.form.get('customer_id', '').strip()
    developer_token = request.form.get('developer_token', '').strip()
    client_id = request.form.get('client_id', '').strip()
    client_secret = request.form.get('client_secret', '').strip()
    activa = request.form.get('activa') == 'on'
    
    config = {
        'customer_id': customer_id,
        'developer_token': developer_token,
        'client_id': client_id,
        'client_secret': client_secret
    }
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute("SELECT id FROM marketing_integraciones WHERE tipo = 'google_ads'")
        existe = cur.fetchone()
        
        if existe:
            cur.execute("""
                UPDATE marketing_integraciones
                SET configuracion = %s, activa = %s, updated_at = CURRENT_TIMESTAMP
                WHERE tipo = 'google_ads'
            """, (json.dumps(config), activa))
        else:
            cur.execute("""
                INSERT INTO marketing_integraciones (tipo, nombre, activa, configuracion)
                VALUES ('google_ads', 'Google Ads', %s, %s)
            """, (activa, json.dumps(config)))
        
        conn.commit()
        flash('Configuración de Google Ads guardada exitosamente', 'success')
    except Exception as e:
        conn.rollback()
        flash(f'Error al guardar configuración: {str(e)}', 'error')
    finally:
        cur.close()
        conn.close()
    
    return redirect('/marketing/integraciones/google-ads')

@app.route('/marketing/integraciones/email/guardar', methods=['POST'])
@login_required
def marketing_email_guardar():
    """Guardar configuración de Email Marketing"""
    if is_cliente(current_user):
        flash('No tienes acceso a esta sección.', 'error')
        return redirect('/projects')
    
    from models import get_db_connection
    import json
    
    tipo_servicio = request.form.get('tipo_servicio', '').strip()
    smtp_host = request.form.get('smtp_host', '').strip()
    smtp_port = request.form.get('smtp_port', '').strip()
    smtp_user = request.form.get('smtp_user', '').strip()
    smtp_password = request.form.get('smtp_password', '').strip()
    email_remitente = request.form.get('email_remitente', '').strip()
    activa = request.form.get('activa') == 'on'
    
    config = {
        'tipo_servicio': tipo_servicio,
        'smtp_host': smtp_host,
        'smtp_port': smtp_port,
        'smtp_user': smtp_user,
        'smtp_password': smtp_password,
        'email_remitente': email_remitente
    }
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute("SELECT id FROM marketing_integraciones WHERE tipo = 'email_marketing'")
        existe = cur.fetchone()
        
        if existe:
            cur.execute("""
                UPDATE marketing_integraciones
                SET configuracion = %s, activa = %s, updated_at = CURRENT_TIMESTAMP
                WHERE tipo = 'email_marketing'
            """, (json.dumps(config), activa))
        else:
            cur.execute("""
                INSERT INTO marketing_integraciones (tipo, nombre, activa, configuracion)
                VALUES ('email_marketing', 'Email Marketing', %s, %s)
            """, (activa, json.dumps(config)))
        
        conn.commit()
        flash('Configuración de Email Marketing guardada exitosamente', 'success')
    except Exception as e:
        conn.rollback()
        flash(f'Error al guardar configuración: {str(e)}', 'error')
    finally:
        cur.close()
        conn.close()
    
    return redirect('/marketing/integraciones/email')

@app.route('/marketing/integraciones/email/enviar-prueba', methods=['POST'])
@login_required
def marketing_email_enviar_prueba():
    """Enviar email de prueba"""
    if is_cliente(current_user):
        return jsonify({'success': False, 'message': 'No tienes acceso'}), 403
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'Datos no proporcionados'}), 400
        
        email_destino = data.get('email_destino', '').strip()
        asunto = data.get('asunto', 'Prueba de Email Marketing').strip()
        mensaje = data.get('mensaje', 'Este es un mensaje de prueba desde el sistema de email marketing.').strip()
        
        if not email_destino:
            return jsonify({'success': False, 'message': 'Email destino requerido'}), 400
        
        # Validar formato de email
        import re
        email_pattern = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'
        if not re.match(email_pattern, email_destino):
            return jsonify({'success': False, 'message': 'Formato de email inválido'}), 400
        
        resultado = enviar_email_marketing(
            email_destino=email_destino,
            asunto=asunto,
            mensaje=mensaje
        )
        
        # Si hay un status_code de error, devolver código HTTP apropiado
        status_code = resultado.get('status_code', 200 if resultado.get('success') else 500)
        
        return jsonify(resultado), status_code if status_code != 200 else 200
        
    except Exception as e:
        import traceback
        print(f"Error en enviar-prueba-email: {str(e)}")
        print(traceback.format_exc())
        return jsonify({
            'success': False, 
            'message': f'Error inesperado: {str(e)}'
        }), 500

def enviar_email_marketing(email_destino, asunto, mensaje, config=None):
    """
    Envía un email usando la configuración de Email Marketing
    
    Args:
        email_destino: Email destino
        asunto: Asunto del email
        mensaje: Cuerpo del mensaje (texto plano)
        config: Configuración opcional (si no se proporciona, se obtiene de la BD)
    
    Returns:
        dict con resultado del envío
    """
    from models import get_db_connection
    import json
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    
    # Si no se proporciona config, obtenerla de la BD
    if not config:
        conn = get_db_connection()
        cur = conn.cursor()
        
        try:
            cur.execute("""
                SELECT configuracion, activa
                FROM marketing_integraciones
                WHERE tipo = 'email_marketing' AND activa = TRUE
                LIMIT 1
            """)
            resultado = cur.fetchone()
            
            if not resultado:
                return {'success': False, 'message': 'Email Marketing no está configurado o no está activo'}
            
            # PostgreSQL JSONB puede devolver dict directamente o string
            config_raw = resultado[0]
            if isinstance(config_raw, dict):
                config = config_raw
            elif isinstance(config_raw, str):
                config = json.loads(config_raw) if config_raw else {}
            else:
                config = {}
                
        finally:
            cur.close()
            conn.close()
    
    if not config:
        return {'success': False, 'message': 'Configuración no proporcionada'}
    
    tipo_servicio = config.get('tipo_servicio', 'smtp')
    smtp_host = config.get('smtp_host', '').strip()
    smtp_port = config.get('smtp_port', '').strip()
    smtp_user = config.get('smtp_user', '').strip()
    smtp_password = config.get('smtp_password', '').strip()
    email_remitente = config.get('email_remitente', '').strip() or smtp_user
    
    if not all([smtp_host, smtp_port, smtp_user, smtp_password, email_remitente]):
        return {'success': False, 'message': 'Configuración incompleta de Email Marketing. Verifica que todos los campos estén completos.'}
    
    try:
        # Crear mensaje
        msg = MIMEMultipart()
        msg['From'] = email_remitente
        msg['To'] = email_destino
        msg['Subject'] = asunto
        
        # Agregar cuerpo del mensaje
        msg.attach(MIMEText(mensaje, 'plain'))
        
        # Convertir puerto a entero
        try:
            port = int(smtp_port)
        except:
            port = 587  # Puerto por defecto
        
        print(f"[Email Marketing] Enviando email a {email_destino}")
        print(f"[Email Marketing] Servidor: {smtp_host}:{port}")
        print(f"[Email Marketing] Remitente: {email_remitente}")
        
        # Conectar al servidor SMTP y enviar
        if tipo_servicio == 'smtp' or not tipo_servicio:
            # SMTP estándar con TLS
            server = smtplib.SMTP(smtp_host, port)
            server.starttls()  # Habilitar TLS
            server.login(smtp_user, smtp_password)
            text = msg.as_string()
            server.sendmail(email_remitente, email_destino, text)
            server.quit()
            
            print(f"[Email Marketing] ✓ Email enviado exitosamente")
            return {
                'success': True,
                'message': f'Email enviado exitosamente a {email_destino}'
            }
        else:
            return {
                'success': False,
                'message': f'Tipo de servicio "{tipo_servicio}" no implementado aún. Solo SMTP está disponible.'
            }
            
    except smtplib.SMTPAuthenticationError as e:
        print(f"[Email Marketing] Error de autenticación: {str(e)}")
        return {
            'success': False,
            'message': 'Error de autenticación. Verifica el usuario y contraseña/API Key.'
        }
    except smtplib.SMTPRecipientsRefused as e:
        print(f"[Email Marketing] Destinatario rechazado: {str(e)}")
        return {
            'success': False,
            'message': f'El email destino "{email_destino}" fue rechazado. Verifica que sea válido.'
        }
    except smtplib.SMTPException as e:
        print(f"[Email Marketing] Error SMTP: {str(e)}")
        return {
            'success': False,
            'message': f'Error SMTP: {str(e)}'
        }
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"[Email Marketing] Error inesperado: {str(e)}")
        print(f"[Email Marketing] Traceback: {error_trace}")
        return {
            'success': False,
            'message': f'Error al enviar email: {str(e)}'
        }

@app.route('/marketing/clientes/exportar/csv')
@login_required
def marketing_clientes_exportar_csv():
    """Exportar clientes en formato CSV"""
    if is_cliente(current_user):
        flash('No tienes acceso a esta sección.', 'error')
        return redirect('/projects')
    
    from models import Cliente, ClienteSegmento
    from io import StringIO, BytesIO
    from flask import send_file
    import csv
    
    formato = request.args.get('formato', 'meta')
    clientes = Cliente.get_all()
    
    output = StringIO()
    
    if formato == 'meta':
        # Formato para Meta (Facebook/Instagram)
        writer = csv.writer(output)
        writer.writerow(['email', 'phone', 'fn', 'ln', 'external_id'])
        
        for cliente in clientes:
            segmento = ClienteSegmento.get_by_cliente_id(cliente.id)
            telefono = cliente.telefono.replace('+', '').replace(' ', '').replace('-', '') if cliente.telefono else ''
            writer.writerow([
                cliente.correo,
                telefono,
                cliente.nombre or '',
                cliente.apellido or '',
                str(cliente.id)
            ])
    else:
        # Formato para Google Ads
        writer = csv.writer(output)
        writer.writerow(['Email', 'Phone', 'First Name', 'Last Name', 'Country Code'])
        
        for cliente in clientes:
            telefono = cliente.telefono.replace('+', '').replace(' ', '').replace('-', '') if cliente.telefono else ''
            writer.writerow([
                cliente.correo,
                telefono,
                cliente.nombre or '',
                cliente.apellido or '',
                'CL'  # Chile
            ])
    
    output.seek(0)
    filename = f'clientes_{formato}_{datetime.now().strftime("%Y%m%d")}.csv'
    
    return send_file(
        BytesIO(output.getvalue().encode('utf-8-sig')),
        mimetype='text/csv',
        as_attachment=True,
        download_name=filename
    )

@app.route('/marketing/agendas/negocio/nueva', methods=['POST'])
@login_required
def marketing_agendas_negocio_nueva():
    """Crear nuevo evento de negocio/sucursal"""
    if is_cliente(current_user):
        flash('No tienes acceso a esta sección.', 'error')
        return redirect('/projects')
    
    from models import get_db_connection
    
    titulo = request.form.get('titulo')
    negocio_sucursal = request.form.get('negocio_sucursal')
    tipo_evento = request.form.get('tipo_evento')
    fecha = request.form.get('fecha')
    descripcion = request.form.get('descripcion')
    
    if not all([titulo, negocio_sucursal, tipo_evento, fecha]):
        flash('Todos los campos requeridos deben estar completos', 'error')
        return redirect('/marketing/agendas/negocio')
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        fecha_dt = datetime.strptime(fecha, '%Y-%m-%dT%H:%M')
        
        cur.execute("""
            INSERT INTO marketing_agendas 
            (titulo, negocio_sucursal, tipo_evento, fecha, descripcion, created_by)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (titulo, negocio_sucursal, tipo_evento, fecha_dt, descripcion, current_user.id))
        
        conn.commit()
        flash('Evento creado exitosamente', 'success')
    except Exception as e:
        conn.rollback()
        flash(f'Error al crear evento: {str(e)}', 'error')
    finally:
        cur.close()
        conn.close()
    
    return redirect('/marketing/agendas/negocio')

@app.route('/marketing/recordatorios/plantillas/nueva', methods=['POST'])
@login_required
def marketing_recordatorios_plantillas_nueva():
    """Crear nueva plantilla"""
    if is_cliente(current_user):
        flash('No tienes acceso a esta sección.', 'error')
        return redirect('/projects')
    
    from models import get_db_connection
    
    nombre = request.form.get('nombre')
    tipo = request.form.get('tipo')
    canal = request.form.get('canal')
    asunto = request.form.get('asunto')
    contenido = request.form.get('contenido')
    
    if not all([nombre, tipo, canal, contenido]):
        flash('Todos los campos requeridos deben estar completos', 'error')
        return redirect('/marketing/recordatorios/plantillas')
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute("""
            INSERT INTO marketing_plantillas 
            (nombre, tipo, canal, asunto, contenido, created_by)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (nombre, tipo, canal, asunto, contenido, current_user.id))
        
        conn.commit()
        flash('Plantilla creada exitosamente', 'success')
    except Exception as e:
        conn.rollback()
        flash(f'Error al crear plantilla: {str(e)}', 'error')
    finally:
        cur.close()
        conn.close()
    
    return redirect('/marketing/recordatorios/plantillas')

if __name__ == '__main__':
    app.run(debug=True)