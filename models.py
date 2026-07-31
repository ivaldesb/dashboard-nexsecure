import os
import pymysql
from pymysql.err import IntegrityError
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.environ.get("DB_HOST", "147.124.195.34")
DB_NAME = os.environ.get("DB_NAME", "nexsecur_nexsecure")
DB_USER = os.environ.get("DB_USER", "nexsecur_backend_dashboard")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "")
DB_PORT = int(os.environ.get("DB_PORT", "3306"))

# Conexión a la base de datos MariaDB

def get_db_connection():
    conn = pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        port=DB_PORT,
        charset="utf8mb4",
        cursorclass=pymysql.cursors.Cursor,
        autocommit=False,
    )
    return conn

# Crear tabla de usuarios si no existe

def create_users_table():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INT AUTO_INCREMENT PRIMARY KEY,
        email VARCHAR(120) UNIQUE NOT NULL,
        password VARCHAR(200) NOT NULL,
        nombre VARCHAR(100),
        apellido VARCHAR(100),
        username VARCHAR(100) UNIQUE,
        tag VARCHAR(50) DEFAULT 'Usuario',
        is_admin BOOLEAN DEFAULT FALSE,
        estado VARCHAR(20) DEFAULT 'habilitado',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_login TIMESTAMP
    );
    """)
    conn.commit()
    
    # Migración: agregar columna tag si no existe
    try:
        cur.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='users' AND column_name='tag'
        """)
        if not cur.fetchone():
            cur.execute("ALTER TABLE users ADD COLUMN tag VARCHAR(50) DEFAULT 'Usuario'")
            conn.commit()
            print("Migración exitosa: columna 'tag' agregada a 'users'")
    except Exception as e:
        conn.rollback()
        print(f"Error durante migración para 'tag': {e}")
    
    # Migración: agregar columna is_admin si no existe
    try:
        cur.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='users' AND column_name='is_admin'
        """)
        if not cur.fetchone():
            cur.execute("ALTER TABLE users ADD COLUMN is_admin BOOLEAN DEFAULT FALSE")
            conn.commit()
            print("Migración exitosa: columna 'is_admin' agregada a 'users'")
    except Exception as e:
        conn.rollback()
        print(f"Error durante migración para 'is_admin': {e}")
    
    cur.close()
    conn.close()

def create_clientes_table():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS clientes (
        id INT AUTO_INCREMENT PRIMARY KEY,
        nombre VARCHAR(100),
        apellido VARCHAR(100),
        tipo_cliente VARCHAR(50) NOT NULL,
        rut VARCHAR(20),
        nombre_empresa VARCHAR(200),
        rut_empresa VARCHAR(20),
        giro VARCHAR(120),
        telefono VARCHAR(30) NOT NULL,
        correo VARCHAR(120) NOT NULL,
        usuario_referidor_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
        estado VARCHAR(20) DEFAULT 'habilitado',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_login TIMESTAMP
    );
    """)
    conn.commit()
    
    # Migración: agregar columna usuario_referidor_id si no existe
    try:
        cur.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='clientes' AND column_name='usuario_referidor_id'
        """)
        if not cur.fetchone():
            cur.execute("ALTER TABLE clientes ADD COLUMN usuario_referidor_id INTEGER REFERENCES users(id) ON DELETE SET NULL")
            conn.commit()
            print("Migración exitosa: columna 'usuario_referidor_id' agregada a 'clientes'")
    except Exception as e:
        conn.rollback()
        print(f"Error durante migración para 'usuario_referidor_id': {e}")
    
    cur.close()
    conn.close()

class User:
    def __init__(self, id, email, password_hash, nombre, apellido, username, estado, created_at, last_login, tag=None, is_admin=False):
        self.id = id
        self.email = email
        self.password_hash = password_hash
        self.nombre = nombre
        self.apellido = apellido
        self.username = username
        self.estado = estado
        self.created_at = created_at
        self.last_login = last_login
        self.tag = tag if tag else 'Usuario'
        self.is_admin = is_admin if isinstance(is_admin, bool) else (is_admin == True or is_admin == 't' or is_admin == 'true')

    @staticmethod
    def get_by_email(email):
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, email, password, nombre, apellido, username, estado, created_at, last_login, COALESCE(tag, 'Usuario'), COALESCE(is_admin, FALSE) FROM users WHERE email = %s", (email,))
        user = cur.fetchone()
        cur.close()
        conn.close()
        if user:
            return User(*user)
        return None

    @staticmethod
    def get_by_id(user_id):
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, email, password, nombre, apellido, username, estado, created_at, last_login, COALESCE(tag, 'Usuario'), COALESCE(is_admin, FALSE) FROM users WHERE id = %s", (user_id,))
        user = cur.fetchone()
        cur.close()
        conn.close()
        if user:
            return User(*user)
        return None
    
    @staticmethod
    def get_all():
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, email, password, nombre, apellido, username, estado, created_at, last_login, COALESCE(tag, 'Usuario'), COALESCE(is_admin, FALSE) FROM users ORDER BY id ASC")
        users = cur.fetchall()
        cur.close()
        conn.close()
        return [User(*user) for user in users]
    
    def set_estado(self, nuevo_estado):
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("UPDATE users SET estado = %s WHERE id = %s", (nuevo_estado, self.id))
            conn.commit()
            self.estado = nuevo_estado
            return True
        except Exception as e:
            conn.rollback()
            return False
        finally:
            cur.close()
            conn.close()

    @staticmethod
    def get_by_username(username):
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, email, password, nombre, apellido, username, estado, created_at, last_login, COALESCE(tag, 'Usuario'), COALESCE(is_admin, FALSE) FROM users WHERE username = %s", (username,))
        user = cur.fetchone()
        cur.close()
        conn.close()
        if user:
            return User(*user)
        return None

    @staticmethod
    def create(email, password, nombre, apellido, username, tag='Usuario', is_admin=False):
        conn = get_db_connection()
        cur = conn.cursor()
        password_hash = generate_password_hash(password)
        try:
            cur.execute("""
                INSERT INTO users (email, password, nombre, apellido, username, tag, is_admin)
                VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id, email, password, nombre, apellido, username, estado, created_at, last_login, COALESCE(tag, 'Usuario'), COALESCE(is_admin, FALSE)
            """, (email, password_hash, nombre, apellido, username, tag, is_admin))
            user_row = cur.fetchone()
            conn.commit()
            return User(*user_row)
        except Exception as e:
            conn.rollback()
            return str(e) if str(e) else "Error desconocido al crear usuario."
        finally:
            cur.close()
            conn.close()


    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    # Métodos requeridos por Flask-Login
    def get_id(self):
        return str(self.id)
    @property
    def is_authenticated(self):
        return True
    @property
    def is_active(self):
        return self.estado == 'habilitado'
    @property
    def is_anonymous(self):
        return False

    def update_last_login(self):
        conn = get_db_connection()
        cur = conn.cursor()
        now = datetime.now()
        cur.execute("UPDATE users SET last_login = %s WHERE id = %s", (now, self.id))
        conn.commit()
        cur.close()
        conn.close()
        self.last_login = now 

    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'nombre': self.nombre,
            'apellido': self.apellido,
            'username': self.username,
            'tag': self.tag,
            'is_admin': self.is_admin,
            'estado': self.estado,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else '',
            'last_login': self.last_login.strftime('%Y-%m-%d %H:%M:%S') if self.last_login else ''
        }

    @staticmethod
    def delete(user_id):
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("DELETE FROM users WHERE id = %s", (user_id,))
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            return False
        finally:
            cur.close()
            conn.close()

    def edit(self, nombre=None, apellido=None, username=None, email=None, estado=None, tag=None, is_admin=None):
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            updates = []
            params = []
            if nombre is not None:
                updates.append("nombre=%s")
                params.append(nombre)
            if apellido is not None:
                updates.append("apellido=%s")
                params.append(apellido)
            if username is not None:
                updates.append("username=%s")
                params.append(username)
            if email is not None:
                updates.append("email=%s")
                params.append(email)
            if estado is not None:
                updates.append("estado=%s")
                params.append(estado)
            if tag is not None:
                updates.append("tag=%s")
                params.append(tag)
            if is_admin is not None:
                updates.append("is_admin=%s")
                params.append(is_admin)
            
            params.append(self.id)
            cur.execute(f"""
                UPDATE users SET {', '.join(updates)} WHERE id=%s
            """, params)
            conn.commit()
            # Actualizar atributos del objeto
            if nombre is not None:
                self.nombre = nombre
            if apellido is not None:
                self.apellido = apellido
            if username is not None:
                self.username = username
            if email is not None:
                self.email = email
            if estado is not None:
                self.estado = estado
            if tag is not None:
                self.tag = tag
            if is_admin is not None:
                self.is_admin = is_admin if isinstance(is_admin, bool) else (is_admin == True or is_admin == 't' or is_admin == 'true')
            return True
        except Exception as e:
            conn.rollback()
            return False
        finally:
            cur.close()
            conn.close()

class Cliente:
    def __init__(self, id, tipo_cliente, nombre, apellido, rut, correo, telefono, nombre_empresa, rut_empresa, giro, estado, created_at, last_login, usuario_referidor_id=None):
        self.id = id
        self.tipo_cliente = tipo_cliente
        self.nombre = nombre
        self.apellido = apellido
        self.rut = rut
        self.correo = correo
        self.telefono = telefono
        self.nombre_empresa = nombre_empresa
        self.rut_empresa = rut_empresa
        self.giro = giro
        self.estado = estado
        self.created_at = created_at
        self.last_login = last_login
        self.usuario_referidor_id = usuario_referidor_id

    @staticmethod
    def get_all():
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT id, tipo_cliente, nombre, apellido, rut, correo, telefono, nombre_empresa, rut_empresa, giro, estado, created_at, last_login, COALESCE(usuario_referidor_id, NULL)
            FROM clientes ORDER BY id ASC
        """)
        clientes = cur.fetchall()
        cur.close()
        conn.close()
        return [Cliente(*c) for c in clientes]

    @staticmethod
    def create(tipo_cliente, nombre, apellido, rut, correo, telefono, nombre_empresa=None, rut_empresa=None, giro=None, usuario_referidor_id=None):
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                INSERT INTO clientes (tipo_cliente, nombre, apellido, rut, correo, telefono, nombre_empresa, rut_empresa, giro, usuario_referidor_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id, tipo_cliente, nombre, apellido, rut, correo, telefono, nombre_empresa, rut_empresa, giro, estado, created_at, last_login, COALESCE(usuario_referidor_id, NULL)
            """, (tipo_cliente, nombre, apellido, rut, correo, telefono, nombre_empresa, rut_empresa, giro, usuario_referidor_id))
            cliente_row = cur.fetchone()
            conn.commit()
            return Cliente(*cliente_row)
        except Exception as e:
            conn.rollback()
            return str(e) if str(e) else "Error desconocido al crear cliente."
        finally:
            cur.close()
            conn.close()

    @staticmethod
    def get_by_id(cliente_id):
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT id, tipo_cliente, nombre, apellido, rut, correo, telefono, nombre_empresa, rut_empresa, giro, estado, created_at, last_login, COALESCE(usuario_referidor_id, NULL)
            FROM clientes WHERE id = %s
        """, (cliente_id,))
        cliente = cur.fetchone()
        cur.close()
        conn.close()
        if cliente:
            return Cliente(*cliente)
        return None

    def set_estado(self, nuevo_estado):
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("UPDATE clientes SET estado = %s WHERE id = %s", (nuevo_estado, self.id))
            conn.commit()
            self.estado = nuevo_estado
            return True
        except Exception as e:
            conn.rollback()
            return False
        finally:
            cur.close()
            conn.close()

    def update_last_login(self):
        conn = get_db_connection()
        cur = conn.cursor()
        now = datetime.now()
        cur.execute("UPDATE clientes SET last_login = %s WHERE id = %s", (now, self.id))
        conn.commit()
        cur.close()
        conn.close()
        self.last_login = now 

    @staticmethod
    def get_by_correo(correo):
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT id, tipo_cliente, nombre, apellido, rut, correo, telefono, nombre_empresa, rut_empresa, giro, estado, created_at, last_login
            FROM clientes WHERE correo = %s
        """, (correo,))
        cliente = cur.fetchone()
        cur.close()
        conn.close()
        if cliente:
            return Cliente(*cliente)
        return None

    @staticmethod
    def get_by_rut(rut):
        """Busca cliente por RUT (normalizado, sin puntos ni guiones)"""
        conn = get_db_connection()
        cur = conn.cursor()
        # Normalizar RUT: quitar puntos y guiones
        rut_normalizado = rut.replace('.', '').replace('-', '').upper()
        cur.execute("""
            SELECT id, tipo_cliente, nombre, apellido, rut, correo, telefono, nombre_empresa, rut_empresa, giro, estado, created_at, last_login, COALESCE(usuario_referidor_id, NULL)
            FROM clientes WHERE REPLACE(REPLACE(UPPER(rut), '.', ''), '-', '') = %s
        """, (rut_normalizado,))
        cliente = cur.fetchone()
        cur.close()
        conn.close()
        if cliente:
            return Cliente(*cliente)
        return None

    def check_rut_password(self, rut_input):
        """Verifica si el RUT ingresado coincide con el RUT del cliente"""
        # Normalizar ambos RUTs: quitar puntos, guiones y convertir a mayúsculas
        rut_cliente = self.rut.replace('.', '').replace('-', '').upper() if self.rut else ''
        rut_input_normalizado = rut_input.replace('.', '').replace('-', '').upper()
        return rut_cliente == rut_input_normalizado

    # Métodos requeridos por Flask-Login
    def get_id(self):
        # Usar prefijo 'cliente_' para diferenciar de usuarios
        return f'cliente_{self.id}'
    
    @property
    def is_authenticated(self):
        return True
    
    @property
    def is_active(self):
        return self.estado == 'habilitado'
    
    @property
    def is_anonymous(self):
        return False

    def to_dict(self):
        # Obtener información del usuario referidor si existe
        usuario_referidor_nombre = None
        if self.usuario_referidor_id:
            usuario_referidor = User.get_by_id(self.usuario_referidor_id)
            if usuario_referidor:
                usuario_referidor_nombre = f"{usuario_referidor.nombre} {usuario_referidor.apellido}" if usuario_referidor.nombre and usuario_referidor.apellido else usuario_referidor.username
        
        return {
            'id': self.id,
            'tipo_cliente': self.tipo_cliente,
            'nombre': self.nombre,
            'apellido': self.apellido,
            'rut': self.rut,
            'correo': self.correo,
            'telefono': self.telefono,
            'nombre_empresa': self.nombre_empresa,
            'rut_empresa': self.rut_empresa,
            'giro': self.giro,
            'estado': self.estado,
            'usuario_referidor_id': self.usuario_referidor_id,
            'usuario_referidor_nombre': usuario_referidor_nombre,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else '',
            'last_login': self.last_login.strftime('%Y-%m-%d %H:%M:%S') if self.last_login else ''
        }

    @staticmethod
    def delete(cliente_id):
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("DELETE FROM clientes WHERE id = %s", (cliente_id,))
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            return False
        finally:
            cur.close()
            conn.close()

    def edit(self, tipo_cliente=None, nombre=None, apellido=None, rut=None, correo=None, telefono=None, nombre_empresa=None, rut_empresa=None, giro=None, estado=None, usuario_referidor_id=None):
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                UPDATE clientes SET tipo_cliente=%s, nombre=%s, apellido=%s, rut=%s, correo=%s, telefono=%s, nombre_empresa=%s, rut_empresa=%s, giro=%s, estado=%s, usuario_referidor_id=%s WHERE id=%s
            """, (tipo_cliente, nombre, apellido, rut, correo, telefono, nombre_empresa, rut_empresa, giro, estado, usuario_referidor_id, self.id))
            conn.commit()
            # Actualizar atributos del objeto
            self.tipo_cliente = tipo_cliente
            self.nombre = nombre
            self.apellido = apellido
            self.rut = rut
            self.correo = correo
            self.telefono = telefono
            self.nombre_empresa = nombre_empresa
            self.rut_empresa = rut_empresa
            self.giro = giro
            self.estado = estado
            self.usuario_referidor_id = usuario_referidor_id
            return True
        except Exception as e:
            conn.rollback()
            return False
        finally:
            cur.close()
            conn.close()

def create_proyectos_table():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS proyectos (
        id INT AUTO_INCREMENT PRIMARY KEY,
        nombre VARCHAR(200) NOT NULL,
        descripcion TEXT,
        estado VARCHAR(50) DEFAULT 'en_desarrollo',
        progreso INTEGER DEFAULT 0,
        incluye_mantenimiento BOOLEAN DEFAULT FALSE,
        es_solo_mantenimiento BOOLEAN DEFAULT FALSE,
        ciclo_pago_mensual DECIMAL(12,2) DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    # Migraciones para tablas existentes
    for col, ddl in (
        ("incluye_mantenimiento", "ALTER TABLE proyectos ADD COLUMN incluye_mantenimiento BOOLEAN DEFAULT FALSE"),
        ("es_solo_mantenimiento", "ALTER TABLE proyectos ADD COLUMN es_solo_mantenimiento BOOLEAN DEFAULT FALSE"),
        ("ciclo_pago_mensual", "ALTER TABLE proyectos ADD COLUMN ciclo_pago_mensual DECIMAL(12,2) DEFAULT 0"),
    ):
        try:
            cur.execute(
                "SELECT column_name FROM information_schema.columns WHERE table_name='proyectos' AND column_name=%s",
                (col,),
            )
            if not cur.fetchone():
                cur.execute(ddl)
                conn.commit()
                print(f"Migración exitosa: columna '{col}' agregada a 'proyectos'")
        except Exception as e:
            conn.rollback()
            print(f"Error durante migración para '{col}': {e}")
    conn.commit()
    cur.close()
    conn.close()

def create_proyecto_asignaciones_table():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS proyecto_asignaciones (
        id INT AUTO_INCREMENT PRIMARY KEY,
        proyecto_id INTEGER NOT NULL REFERENCES proyectos(id) ON DELETE CASCADE,
        asignado_id INTEGER NOT NULL,
        tipo_asignado VARCHAR(20) NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(proyecto_id, asignado_id, tipo_asignado)
    );
    """)
    conn.commit()
    cur.close()
    conn.close()

def create_proyecto_comentarios_table():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS proyecto_comentarios (
        id INT AUTO_INCREMENT PRIMARY KEY,
        proyecto_id INTEGER NOT NULL REFERENCES proyectos(id) ON DELETE CASCADE,
        autor_id INTEGER NOT NULL,
        tipo_autor VARCHAR(20) NOT NULL,
        comentario TEXT NOT NULL,
        comentario_padre_id INTEGER REFERENCES proyecto_comentarios(id) ON DELETE CASCADE,
        is_deleted BOOLEAN DEFAULT FALSE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    conn.commit()
    
    # Migración: agregar columna comentario_padre_id si no existe
    try:
        cur.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='proyecto_comentarios' AND column_name='comentario_padre_id'
        """)
        if not cur.fetchone():
            cur.execute("ALTER TABLE proyecto_comentarios ADD COLUMN comentario_padre_id INTEGER REFERENCES proyecto_comentarios(id) ON DELETE CASCADE")
            conn.commit()
            print("Migración exitosa: columna 'comentario_padre_id' agregada a 'proyecto_comentarios'")
    except Exception as e:
        conn.rollback()
        print(f"Error durante migración para 'comentario_padre_id': {e}")
    
    # Migración: agregar columna is_deleted si no existe
    try:
        cur.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='proyecto_comentarios' AND column_name='is_deleted'
        """)
        if not cur.fetchone():
            cur.execute("ALTER TABLE proyecto_comentarios ADD COLUMN is_deleted BOOLEAN DEFAULT FALSE")
            conn.commit()
            print("Migración exitosa: columna 'is_deleted' agregada a 'proyecto_comentarios'")
    except Exception as e:
        conn.rollback()
        print(f"Error durante migración para 'is_deleted': {e}")
    
    cur.close()
    conn.close()

def create_proyecto_cambios_table():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS proyecto_cambios (
        id INT AUTO_INCREMENT PRIMARY KEY,
        proyecto_id INTEGER NOT NULL REFERENCES proyectos(id) ON DELETE CASCADE,
        autor_id INTEGER NOT NULL,
        tipo_autor VARCHAR(20) NOT NULL,
        campo_cambiado VARCHAR(50) NOT NULL,
        valor_anterior TEXT,
        valor_nuevo TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    conn.commit()
    cur.close()
    conn.close()

def create_presupuestos_table():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS presupuestos (
        id INT AUTO_INCREMENT PRIMARY KEY,
        proyecto_id INTEGER NOT NULL REFERENCES proyectos(id) ON DELETE CASCADE,
        numero_presupuesto VARCHAR(50) UNIQUE,
        fecha DATE DEFAULT CURRENT_DATE,
        obra VARCHAR(200),
        cliente_id INTEGER,
        cliente_nombre VARCHAR(200),
        cliente_email VARCHAR(120),
        cliente_telefono VARCHAR(30),
        descuento DECIMAL(5,2) DEFAULT 0,
        iva DECIMAL(5,2) DEFAULT 19,
        generalidades TEXT,
        tipo_presupuesto VARCHAR(20) DEFAULT 'principal',
        estado_presupuesto VARCHAR(50) DEFAULT 'pendiente_aprobacion',
        incidencia_id INTEGER REFERENCES incidencias(id) ON DELETE SET NULL,
        visita_mantenimiento_id INTEGER REFERENCES proyecto_mantenimiento_visitas(id) ON DELETE SET NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    conn.commit()
    
    # Migración: agregar columna estado_presupuesto si no existe
    try:
        cur.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='presupuestos' AND column_name='estado_presupuesto'
        """)
        if not cur.fetchone():
            cur.execute("ALTER TABLE presupuestos ADD COLUMN estado_presupuesto VARCHAR(50) DEFAULT 'pendiente_aprobacion'")
            # Establecer estado aprobado para presupuestos principales existentes
            cur.execute("UPDATE presupuestos SET estado_presupuesto = 'aprobado' WHERE tipo_presupuesto = 'principal'")
            conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"Error al agregar columna estado_presupuesto: {e}")
    
    # Migración: agregar columna incidencia_id si no existe
    try:
        cur.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='presupuestos' AND column_name='incidencia_id'
        """)
        if not cur.fetchone():
            cur.execute("ALTER TABLE presupuestos ADD COLUMN incidencia_id INTEGER REFERENCES incidencias(id) ON DELETE SET NULL")
            conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"Error al agregar columna incidencia_id: {e}")
    
    # Migración: agregar columna visita_mantenimiento_id si no existe
    try:
        cur.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='presupuestos' AND column_name='visita_mantenimiento_id'
        """)
        if not cur.fetchone():
            cur.execute("ALTER TABLE presupuestos ADD COLUMN visita_mantenimiento_id INTEGER REFERENCES proyecto_mantenimiento_visitas(id) ON DELETE SET NULL")
            conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"Error al agregar columna visita_mantenimiento_id: {e}")
    
    # Migración: agregar columna cliente_id si no existe
    try:
        cur.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='presupuestos' AND column_name='cliente_id'
        """)
        if not cur.fetchone():
            cur.execute("ALTER TABLE presupuestos ADD COLUMN cliente_id INTEGER")
            conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"Error al agregar columna cliente_id: {e}")
    
    # Migración: agregar columna porcentaje_empresa si no existe
    try:
        cur.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='presupuestos' AND column_name='porcentaje_empresa'
        """)
        if not cur.fetchone():
            cur.execute("ALTER TABLE presupuestos ADD COLUMN porcentaje_empresa DECIMAL(5,2) DEFAULT 0")
            conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"Error al agregar columna porcentaje_empresa: {e}")
    
    # Migración: agregar columna tipo_presupuesto si no existe
    try:
        cur.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='presupuestos' AND column_name='tipo_presupuesto'
        """)
        if not cur.fetchone():
            cur.execute("ALTER TABLE presupuestos ADD COLUMN tipo_presupuesto VARCHAR(20) DEFAULT 'principal'")
            conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"Error al agregar columna tipo_presupuesto: {e}")
    
    cur.close()
    conn.close()

def create_presupuesto_items_table():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS presupuesto_items (
        id INT AUTO_INCREMENT PRIMARY KEY,
        presupuesto_id INTEGER NOT NULL REFERENCES presupuestos(id) ON DELETE CASCADE,
        referencia VARCHAR(50),
        cantidad DECIMAL(10,2) DEFAULT 1,
        ubicacion VARCHAR(200),
        tipologia VARCHAR(200),
        tipo VARCHAR(50),
        caracteristicas TEXT,
        valor_unitario DECIMAL(12,2) DEFAULT 0,
        orden INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    conn.commit()
    cur.close()
    conn.close()

def create_presupuesto_costos_table():
    """Crea la tabla para almacenar los costos detallados de cada item del presupuesto"""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS presupuesto_costos (
        id INT AUTO_INCREMENT PRIMARY KEY,
        presupuesto_item_id INTEGER NOT NULL REFERENCES presupuesto_items(id) ON DELETE CASCADE,
        insumos DECIMAL(12,2) DEFAULT 0,
        maquila DECIMAL(12,2) DEFAULT 0,
        instalacion DECIMAL(12,2) DEFAULT 0,
        desinstalacion DECIMAL(12,2) DEFAULT 0,
        materiales_ferreteria DECIMAL(12,2) DEFAULT 0,
        gastos_generales DECIMAL(12,2) DEFAULT 0,
        utilidad_porcentaje DECIMAL(5,2) DEFAULT 0,
        flete DECIMAL(12,2) DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    conn.commit()
    cur.close()
    conn.close()

def create_presupuesto_facturas_table():
    """Crea la tabla para almacenar facturas/boletas del proyecto"""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS presupuesto_facturas (
        id INT AUTO_INCREMENT PRIMARY KEY,
        presupuesto_id INTEGER NOT NULL REFERENCES presupuestos(id) ON DELETE CASCADE,
        tipo_documento VARCHAR(20) NOT NULL DEFAULT 'factura',
        numero_documento VARCHAR(100),
        proveedor VARCHAR(255),
        fecha_emision DATE,
        fecha_vencimiento DATE,
        total DECIMAL(12,2),
        iva DECIMAL(12,2) DEFAULT 0,
        neto DECIMAL(12,2),
        archivo_ruta VARCHAR(500),
        texto_extraido TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    try:
        cur.execute(
            "SELECT column_name FROM information_schema.columns WHERE table_name='presupuesto_gastos' AND column_name='factura_id'"
        )
        if not cur.fetchone():
            cur.execute(
                "ALTER TABLE presupuesto_gastos ADD COLUMN factura_id INTEGER REFERENCES presupuesto_facturas(id) ON DELETE SET NULL"
            )
            conn.commit()
            print("Migración exitosa: columna 'factura_id' agregada a 'presupuesto_gastos'")
    except Exception as e:
        conn.rollback()
        print(f"Error durante migración para 'factura_id': {e}")
    conn.commit()
    cur.close()
    conn.close()

def create_presupuesto_gastos_table():
    """Crea la tabla para almacenar gastos adicionales del proyecto"""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS presupuesto_gastos (
        id INT AUTO_INCREMENT PRIMARY KEY,
        presupuesto_id INTEGER NOT NULL REFERENCES presupuestos(id) ON DELETE CASCADE,
        descripcion VARCHAR(500) NOT NULL,
        monto DECIMAL(12,2) NOT NULL,
        tipo VARCHAR(50) DEFAULT 'general',
        pagado_por_id INTEGER REFERENCES users(id),
        pagado_por_tipo VARCHAR(20) DEFAULT 'user',
        fecha DATE DEFAULT CURRENT_DATE,
        factura_id INTEGER REFERENCES presupuesto_facturas(id) ON DELETE SET NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    conn.commit()
    cur.close()
    conn.close()

def create_presupuesto_pagos_empleados_table():
    """Crea la tabla para asignar porcentajes de pago a empleados y anticipos"""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS presupuesto_pagos_empleados (
        id INT AUTO_INCREMENT PRIMARY KEY,
        presupuesto_id INTEGER NOT NULL REFERENCES presupuestos(id) ON DELETE CASCADE,
        empleado_id INTEGER NOT NULL REFERENCES users(id),
        porcentaje_pago DECIMAL(5,2) DEFAULT 0,
        anticipo DECIMAL(12,2) DEFAULT 0,
        quien_pago_anticipo_id INTEGER REFERENCES users(id),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(presupuesto_id, empleado_id)
    );
    """)
    conn.commit()
    
    # Migración: cambiar gastos_personales por anticipo si existe
    try:
        cur.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='presupuesto_pagos_empleados' AND column_name='gastos_personales'
        """)
        if cur.fetchone():
            # Renombrar columna
            cur.execute("ALTER TABLE presupuesto_pagos_empleados RENAME COLUMN gastos_personales TO anticipo")
            conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"Error al renombrar columna gastos_personales: {e}")
    
    # Migración: agregar columna quien_pago_anticipo_id si no existe
    try:
        cur.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='presupuesto_pagos_empleados' AND column_name='quien_pago_anticipo_id'
        """)
        if not cur.fetchone():
            cur.execute("ALTER TABLE presupuesto_pagos_empleados ADD COLUMN quien_pago_anticipo_id INTEGER REFERENCES users(id)")
            conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"Error al agregar columna quien_pago_anticipo_id: {e}")
    
    cur.close()
    conn.close()

class Proyecto:
    def __init__(self, id, nombre, descripcion, estado, progreso, created_at, updated_at, incluye_mantenimiento=False, es_solo_mantenimiento=False, ciclo_pago_mensual=0):
        self.id = id
        self.nombre = nombre
        self.descripcion = descripcion
        self.estado = estado
        self.progreso = progreso
        self.incluye_mantenimiento = incluye_mantenimiento
        self.es_solo_mantenimiento = es_solo_mantenimiento if isinstance(es_solo_mantenimiento, bool) else (es_solo_mantenimiento == True or es_solo_mantenimiento == 't' or es_solo_mantenimiento == 'true')
        self.ciclo_pago_mensual = float(ciclo_pago_mensual) if ciclo_pago_mensual else 0
        self.created_at = created_at
        self.updated_at = updated_at

    @staticmethod
    def create(nombre, descripcion=None, estado='en_desarrollo', progreso=0, incluye_mantenimiento=False, es_solo_mantenimiento=False, ciclo_pago_mensual=0):
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                INSERT INTO proyectos (nombre, descripcion, estado, progreso, incluye_mantenimiento, es_solo_mantenimiento, ciclo_pago_mensual)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id, nombre, descripcion, estado, progreso, created_at, updated_at, COALESCE(incluye_mantenimiento, FALSE) as incluye_mantenimiento, COALESCE(es_solo_mantenimiento, FALSE) as es_solo_mantenimiento, COALESCE(ciclo_pago_mensual, 0) as ciclo_pago_mensual
            """, (nombre, descripcion, estado, progreso, incluye_mantenimiento, es_solo_mantenimiento, ciclo_pago_mensual))
            proyecto_row = cur.fetchone()
            conn.commit()
            return Proyecto(*proyecto_row)
        except Exception as e:
            conn.rollback()
            return str(e) if str(e) else "Error desconocido al crear proyecto."
        finally:
            cur.close()
            conn.close()

    @staticmethod
    def get_all():
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT id, nombre, descripcion, estado, progreso, created_at, updated_at, COALESCE(incluye_mantenimiento, FALSE) as incluye_mantenimiento, COALESCE(es_solo_mantenimiento, FALSE) as es_solo_mantenimiento, COALESCE(ciclo_pago_mensual, 0) as ciclo_pago_mensual
            FROM proyectos ORDER BY created_at DESC
        """)
        proyectos = cur.fetchall()
        cur.close()
        conn.close()
        return [Proyecto(*p) for p in proyectos]

    @staticmethod
    def get_by_id(proyecto_id):
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT id, nombre, descripcion, estado, progreso, created_at, updated_at, COALESCE(incluye_mantenimiento, FALSE) as incluye_mantenimiento, COALESCE(es_solo_mantenimiento, FALSE) as es_solo_mantenimiento, COALESCE(ciclo_pago_mensual, 0) as ciclo_pago_mensual
            FROM proyectos WHERE id = %s
        """, (proyecto_id,))
        proyecto = cur.fetchone()
        cur.close()
        conn.close()
        if proyecto:
            return Proyecto(*proyecto)
        return None

    @staticmethod
    def get_by_asignado(asignado_id, tipo_asignado, is_admin=False):
        """Obtiene proyectos asignados a un usuario o cliente. Si is_admin=True, devuelve todos.
        Para clientes, también incluye proyectos donde son el cliente del presupuesto."""
        conn = get_db_connection()
        cur = conn.cursor()
        if is_admin:
            cur.execute("""
                SELECT DISTINCT p.id, p.nombre, p.descripcion, p.estado, p.progreso, p.created_at, p.updated_at, COALESCE(p.incluye_mantenimiento, FALSE) as incluye_mantenimiento, COALESCE(p.es_solo_mantenimiento, FALSE) as es_solo_mantenimiento, COALESCE(p.ciclo_pago_mensual, 0) as ciclo_pago_mensual
                FROM proyectos p
                ORDER BY p.created_at DESC
            """)
        else:
            if tipo_asignado == 'cliente':
                # Para clientes: proyectos asignados O proyectos donde son el cliente del presupuesto
                cur.execute("""
                    SELECT DISTINCT p.id, p.nombre, p.descripcion, p.estado, p.progreso, p.created_at, p.updated_at, COALESCE(p.incluye_mantenimiento, FALSE) as incluye_mantenimiento, COALESCE(p.es_solo_mantenimiento, FALSE) as es_solo_mantenimiento, COALESCE(p.ciclo_pago_mensual, 0) as ciclo_pago_mensual
                    FROM proyectos p
                    LEFT JOIN proyecto_asignaciones pa ON p.id = pa.proyecto_id AND pa.asignado_id = %s AND pa.tipo_asignado = 'cliente'
                    LEFT JOIN presupuestos pr ON p.id = pr.proyecto_id AND pr.cliente_id = %s
                    WHERE pa.asignado_id IS NOT NULL OR pr.cliente_id IS NOT NULL
                    ORDER BY p.created_at DESC
                """, (asignado_id, asignado_id))
            else:
                # Para usuarios: solo proyectos asignados
                cur.execute("""
                    SELECT DISTINCT p.id, p.nombre, p.descripcion, p.estado, p.progreso, p.created_at, p.updated_at, COALESCE(p.incluye_mantenimiento, FALSE) as incluye_mantenimiento, COALESCE(p.es_solo_mantenimiento, FALSE) as es_solo_mantenimiento, COALESCE(p.ciclo_pago_mensual, 0) as ciclo_pago_mensual
                    FROM proyectos p
                    INNER JOIN proyecto_asignaciones pa ON p.id = pa.proyecto_id
                    WHERE pa.asignado_id = %s AND pa.tipo_asignado = %s
                    ORDER BY p.created_at DESC
                """, (asignado_id, tipo_asignado))
        proyectos = cur.fetchall()
        cur.close()
        conn.close()
        return [Proyecto(*p) for p in proyectos]

    @staticmethod
    def get_en_curso_by_asignado(asignado_id, tipo_asignado, is_admin=False):
        """Obtiene proyectos en curso asignados a un usuario o cliente.
        Para clientes, también incluye proyectos donde son el cliente del presupuesto."""
        conn = get_db_connection()
        cur = conn.cursor()
        if is_admin:
            cur.execute("""
                SELECT DISTINCT p.id, p.nombre, p.descripcion, p.estado, p.progreso, p.created_at, p.updated_at, COALESCE(p.incluye_mantenimiento, FALSE) as incluye_mantenimiento, COALESCE(p.es_solo_mantenimiento, FALSE) as es_solo_mantenimiento, COALESCE(p.ciclo_pago_mensual, 0) as ciclo_pago_mensual
                FROM proyectos p
                WHERE p.estado IN ('en_desarrollo', 'espera_aprobacion', 'espera_ppto')
                ORDER BY p.created_at DESC
                LIMIT 5
            """)
        else:
            if tipo_asignado == 'cliente':
                # Para clientes: proyectos asignados O proyectos donde son el cliente del presupuesto
                cur.execute("""
                    SELECT DISTINCT p.id, p.nombre, p.descripcion, p.estado, p.progreso, p.created_at, p.updated_at, COALESCE(p.incluye_mantenimiento, FALSE) as incluye_mantenimiento, COALESCE(p.es_solo_mantenimiento, FALSE) as es_solo_mantenimiento, COALESCE(p.ciclo_pago_mensual, 0) as ciclo_pago_mensual
                    FROM proyectos p
                    LEFT JOIN proyecto_asignaciones pa ON p.id = pa.proyecto_id AND pa.asignado_id = %s AND pa.tipo_asignado = 'cliente'
                    LEFT JOIN presupuestos pr ON p.id = pr.proyecto_id AND pr.cliente_id = %s
                    WHERE (pa.asignado_id IS NOT NULL OR pr.cliente_id IS NOT NULL)
                    AND p.estado IN ('en_desarrollo', 'espera_aprobacion', 'espera_ppto')
                    ORDER BY p.created_at DESC
                    LIMIT 5
                """, (asignado_id, asignado_id))
            else:
                # Para usuarios: solo proyectos asignados
                cur.execute("""
                    SELECT DISTINCT p.id, p.nombre, p.descripcion, p.estado, p.progreso, p.created_at, p.updated_at, COALESCE(p.incluye_mantenimiento, FALSE) as incluye_mantenimiento, COALESCE(p.es_solo_mantenimiento, FALSE) as es_solo_mantenimiento, COALESCE(p.ciclo_pago_mensual, 0) as ciclo_pago_mensual
                    FROM proyectos p
                    INNER JOIN proyecto_asignaciones pa ON p.id = pa.proyecto_id
                    WHERE pa.asignado_id = %s AND pa.tipo_asignado = %s
                    AND p.estado IN ('en_desarrollo', 'espera_aprobacion', 'espera_ppto')
                    ORDER BY p.created_at DESC
                    LIMIT 5
                """, (asignado_id, tipo_asignado))
        proyectos = cur.fetchall()
        cur.close()
        conn.close()
        return [Proyecto(*p) for p in proyectos]

    @staticmethod
    def get_con_presupuesto(is_admin=False):
        """Obtiene proyectos que tienen presupuesto asociado"""
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT DISTINCT p.id, p.nombre, p.descripcion, p.estado, p.progreso, p.created_at, p.updated_at, COALESCE(p.incluye_mantenimiento, FALSE) as incluye_mantenimiento, COALESCE(p.es_solo_mantenimiento, FALSE) as es_solo_mantenimiento, COALESCE(p.ciclo_pago_mensual, 0) as ciclo_pago_mensual
            FROM proyectos p
            INNER JOIN presupuestos pr ON p.id = pr.proyecto_id
            ORDER BY p.created_at DESC
            LIMIT 10
        """)
        proyectos = cur.fetchall()
        cur.close()
        conn.close()
        return [Proyecto(*p) for p in proyectos]

    def asignar(self, asignado_id, tipo_asignado):
        """Asigna el proyecto a un usuario o cliente"""
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                INSERT IGNORE INTO proyecto_asignaciones (proyecto_id, asignado_id, tipo_asignado)
                VALUES (%s, %s, %s)
            """, (self.id, asignado_id, tipo_asignado))
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            return False
        finally:
            cur.close()
            conn.close()

    def update(self, nombre=None, descripcion=None, estado=None, progreso=None, incluye_mantenimiento=None, es_solo_mantenimiento=None, ciclo_pago_mensual=None):
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            updates = []
            params = []
            if nombre is not None:
                updates.append("nombre = %s")
                params.append(nombre)
            if descripcion is not None:
                updates.append("descripcion = %s")
                params.append(descripcion)
            if estado is not None:
                updates.append("estado = %s")
                params.append(estado)
            if progreso is not None:
                updates.append("progreso = %s")
                params.append(progreso)
            if incluye_mantenimiento is not None:
                updates.append("incluye_mantenimiento = %s")
                params.append(incluye_mantenimiento)
            if es_solo_mantenimiento is not None:
                updates.append("es_solo_mantenimiento = %s")
                params.append(es_solo_mantenimiento)
            if ciclo_pago_mensual is not None:
                updates.append("ciclo_pago_mensual = %s")
                params.append(ciclo_pago_mensual)
            
            updates.append("updated_at = CURRENT_TIMESTAMP")
            params.append(self.id)
            
            cur.execute(f"""
                UPDATE proyectos SET {', '.join(updates)}
                WHERE id = %s
            """, params)
            conn.commit()
            # Actualizar atributos
            if nombre is not None: self.nombre = nombre
            if descripcion is not None: self.descripcion = descripcion
            if estado is not None: self.estado = estado
            if progreso is not None: self.progreso = progreso
            if incluye_mantenimiento is not None: self.incluye_mantenimiento = incluye_mantenimiento
            if es_solo_mantenimiento is not None: self.es_solo_mantenimiento = es_solo_mantenimiento
            if ciclo_pago_mensual is not None: self.ciclo_pago_mensual = ciclo_pago_mensual
            return True
        except Exception as e:
            conn.rollback()
            return False
        finally:
            cur.close()
            conn.close()

    @staticmethod
    def delete(proyecto_id):
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("DELETE FROM proyectos WHERE id = %s", (proyecto_id,))
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            return False
        finally:
            cur.close()
            conn.close()

    def get_asignados(self):
        """Obtiene todos los usuarios y clientes asignados a este proyecto"""
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT asignado_id, tipo_asignado
            FROM proyecto_asignaciones
            WHERE proyecto_id = %s
        """, (self.id,))
        asignaciones = cur.fetchall()
        cur.close()
        conn.close()
        
        asignados = []
        for asignado_id, tipo_asignado in asignaciones:
            if tipo_asignado == 'user':
                user = User.get_by_id(asignado_id)
                if user:
                    asignados.append({
                        'id': asignado_id,
                        'tipo': 'user',
                        'nombre': f"{user.nombre} {user.apellido}",
                        'email': user.email,
                        'username': user.username,
                        'tag': user.tag if hasattr(user, 'tag') else 'Usuario'
                    })
            elif tipo_asignado == 'cliente':
                cliente = Cliente.get_by_id(asignado_id)
                if cliente:
                    if cliente.tipo_cliente == 'empresa':
                        nombre = cliente.nombre_empresa
                        representante_nombre = f"{cliente.nombre} {cliente.apellido}" if cliente.nombre and cliente.apellido else None
                    else:
                        nombre = f"{cliente.nombre} {cliente.apellido}"
                        representante_nombre = None
                    asignados.append({
                        'id': asignado_id,
                        'tipo': 'cliente',
                        'nombre': nombre,
                        'email': cliente.correo,
                        'tipo_cliente': cliente.tipo_cliente,
                        'nombre_empresa': cliente.nombre_empresa if cliente.tipo_cliente == 'empresa' else None,
                        'representante_nombre': representante_nombre,
                        'representante_rut': cliente.rut_empresa if cliente.tipo_cliente == 'empresa' and cliente.rut_empresa else None
                    })
        return asignados

    def to_dict(self, include_asignados=False):
        dict_data = {
            'id': self.id,
            'nombre': self.nombre,
            'descripcion': self.descripcion,
            'estado': self.estado,
            'progreso': self.progreso,
            'incluye_mantenimiento': self.incluye_mantenimiento if hasattr(self, 'incluye_mantenimiento') else False,
            'es_solo_mantenimiento': self.es_solo_mantenimiento if hasattr(self, 'es_solo_mantenimiento') else False,
            'ciclo_pago_mensual': float(self.ciclo_pago_mensual) if hasattr(self, 'ciclo_pago_mensual') else 0,
            'created_at': self.created_at.strftime('%Y-%m-%d') if self.created_at else '',
            'updated_at': self.updated_at.strftime('%Y-%m-%d') if self.updated_at else ''
        }
        if include_asignados:
            dict_data['asignados'] = self.get_asignados()
        return dict_data

class Comentario:
    def __init__(self, id, proyecto_id, autor_id, tipo_autor, comentario, created_at, comentario_padre_id=None, is_deleted=False):
        self.id = id
        self.proyecto_id = proyecto_id
        self.autor_id = autor_id
        self.tipo_autor = tipo_autor
        self.comentario = comentario
        self.created_at = created_at
        self.comentario_padre_id = comentario_padre_id
        self.is_deleted = is_deleted if isinstance(is_deleted, bool) else (is_deleted == True or is_deleted == 't' or is_deleted == 'true')

    @staticmethod
    def create(proyecto_id, autor_id, tipo_autor, comentario, comentario_padre_id=None):
        """Crea un nuevo comentario o respuesta"""
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                INSERT INTO proyecto_comentarios (proyecto_id, autor_id, tipo_autor, comentario, comentario_padre_id, is_deleted)
                VALUES (%s, %s, %s, %s, %s, FALSE)
                RETURNING id, proyecto_id, autor_id, tipo_autor, comentario, created_at, comentario_padre_id, is_deleted
            """, (proyecto_id, autor_id, tipo_autor, comentario, comentario_padre_id))
            comentario_row = cur.fetchone()
            conn.commit()
            return Comentario(*comentario_row)
        except Exception as e:
            conn.rollback()
            return str(e) if str(e) else "Error desconocido al crear comentario."
        finally:
            cur.close()
            conn.close()

    @staticmethod
    def get_by_id(comentario_id):
        """Obtiene un comentario por su ID"""
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT id, proyecto_id, autor_id, tipo_autor, comentario, created_at, comentario_padre_id, is_deleted
            FROM proyecto_comentarios
            WHERE id = %s
        """, (comentario_id,))
        comentario = cur.fetchone()
        cur.close()
        conn.close()
        if comentario:
            return Comentario(*comentario)
        return None

    @staticmethod
    def get_by_proyecto(proyecto_id, include_deleted=False):
        """Obtiene todos los comentarios de un proyecto ordenados por fecha, con respuestas anidadas.
        Si include_deleted=True, incluye comentarios eliminados."""
        conn = get_db_connection()
        cur = conn.cursor()
        if include_deleted:
            # Obtener todos los comentarios, incluyendo eliminados
            cur.execute("""
                SELECT id, proyecto_id, autor_id, tipo_autor, comentario, created_at, comentario_padre_id, is_deleted
                FROM proyecto_comentarios
                WHERE proyecto_id = %s
                ORDER BY 
                    COALESCE(comentario_padre_id, id) ASC,
                    created_at ASC
            """, (proyecto_id,))
        else:
            # Obtener solo comentarios no eliminados
            cur.execute("""
                SELECT id, proyecto_id, autor_id, tipo_autor, comentario, created_at, comentario_padre_id, is_deleted
                FROM proyecto_comentarios
                WHERE proyecto_id = %s AND (is_deleted = FALSE OR is_deleted IS NULL)
                ORDER BY 
                    COALESCE(comentario_padre_id, id) ASC,
                    created_at ASC
            """, (proyecto_id,))
        comentarios = cur.fetchall()
        cur.close()
        conn.close()
        return [Comentario(*c) for c in comentarios]

    @staticmethod
    def delete(comentario_id):
        """Marca un comentario como eliminado (soft delete) y también marca sus respuestas"""
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            # Marcar el comentario como eliminado
            cur.execute("""
                UPDATE proyecto_comentarios 
                SET is_deleted = TRUE 
                WHERE id = %s
            """, (comentario_id,))
            
            # Marcar también todas las respuestas como eliminadas
            cur.execute("""
                UPDATE proyecto_comentarios 
                SET is_deleted = TRUE 
                WHERE comentario_padre_id = %s
            """, (comentario_id,))
            
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            return False
        finally:
            cur.close()
            conn.close()

    def to_dict(self):
        """Convierte el comentario a diccionario con información del autor"""
        # Obtener información del autor
        autor_nombre = "Usuario desconocido"
        autor_email = ""
        autor_tag = None
        
        if self.tipo_autor == 'user':
            user = User.get_by_id(self.autor_id)
            if user:
                autor_nombre = f"{user.nombre} {user.apellido}"
                autor_email = user.email
                autor_tag = user.tag if hasattr(user, 'tag') else 'Usuario'
            else:
                autor_tag = 'Usuario'
        elif self.tipo_autor == 'cliente':
            cliente = Cliente.get_by_id(self.autor_id)
            if cliente:
                if cliente.tipo_cliente == 'empresa':
                    autor_nombre = cliente.nombre_empresa
                else:
                    autor_nombre = f"{cliente.nombre} {cliente.apellido}"
                autor_email = cliente.correo
        
        return {
            'id': self.id,
            'proyecto_id': self.proyecto_id,
            'autor_id': self.autor_id,
            'tipo_autor': self.tipo_autor,
            'autor_nombre': autor_nombre,
            'autor_email': autor_email,
            'autor_tag': autor_tag,
            'comentario': self.comentario,
            'comentario_padre_id': self.comentario_padre_id,
            'is_deleted': self.is_deleted,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else '',
            'created_at_date': self.created_at.strftime('%d') if self.created_at else '',
            'created_at_month': self.created_at.strftime('%b') if self.created_at else '',
            'created_at_year': self.created_at.strftime('%Y') if self.created_at else ''
        }

class CambioProyecto:
    def __init__(self, id, proyecto_id, autor_id, tipo_autor, campo_cambiado, valor_anterior, valor_nuevo, created_at):
        self.id = id
        self.proyecto_id = proyecto_id
        self.autor_id = autor_id
        self.tipo_autor = tipo_autor
        self.campo_cambiado = campo_cambiado
        self.valor_anterior = valor_anterior
        self.valor_nuevo = valor_nuevo
        self.created_at = created_at

    @staticmethod
    def create(proyecto_id, autor_id, tipo_autor, campo_cambiado, valor_anterior=None, valor_nuevo=None):
        """Registra un cambio en un proyecto"""
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                INSERT INTO proyecto_cambios (proyecto_id, autor_id, tipo_autor, campo_cambiado, valor_anterior, valor_nuevo)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id, proyecto_id, autor_id, tipo_autor, campo_cambiado, valor_anterior, valor_nuevo, created_at
            """, (proyecto_id, autor_id, tipo_autor, campo_cambiado, valor_anterior, valor_nuevo))
            cambio_row = cur.fetchone()
            conn.commit()
            return CambioProyecto(*cambio_row)
        except Exception as e:
            conn.rollback()
            return str(e) if str(e) else "Error desconocido al registrar cambio."
        finally:
            cur.close()
            conn.close()

    @staticmethod
    def get_by_proyecto(proyecto_id, limit=10):
        """Obtiene los cambios recientes de un proyecto ordenados por fecha descendente"""
        conn = get_db_connection()
        cur = conn.cursor()
        if limit is None:
            cur.execute("""
                SELECT id, proyecto_id, autor_id, tipo_autor, campo_cambiado, valor_anterior, valor_nuevo, created_at
                FROM proyecto_cambios
                WHERE proyecto_id = %s
                ORDER BY created_at DESC
            """, (proyecto_id,))
        else:
            cur.execute("""
                SELECT id, proyecto_id, autor_id, tipo_autor, campo_cambiado, valor_anterior, valor_nuevo, created_at
                FROM proyecto_cambios
                WHERE proyecto_id = %s
                ORDER BY created_at DESC
                LIMIT %s
            """, (proyecto_id, limit))
        cambios = cur.fetchall()
        cur.close()
        conn.close()
        return [CambioProyecto(*c) for c in cambios]

    def to_dict(self):
        """Convierte el cambio a diccionario con información del autor"""
        # Obtener información del autor
        autor_nombre = "Usuario desconocido"
        
        if self.tipo_autor == 'user':
            user = User.get_by_id(self.autor_id)
            if user:
                autor_nombre = f"{user.nombre} {user.apellido}"
        elif self.tipo_autor == 'cliente':
            cliente = Cliente.get_by_id(self.autor_id)
            if cliente:
                if cliente.tipo_cliente == 'empresa':
                    autor_nombre = cliente.nombre_empresa
                else:
                    autor_nombre = f"{cliente.nombre} {cliente.apellido}"
        
        # Mapear nombres de campos a español
        campos_espanol = {
            'nombre': 'Nombre',
            'descripcion': 'Descripción',
            'estado': 'Estado',
            'progreso': 'Progreso',
            'asignados': 'Asignados'
        }
        campo_display = campos_espanol.get(self.campo_cambiado, self.campo_cambiado)
        
        # Formatear valores según el campo
        valor_anterior_display = self.valor_anterior if self.valor_anterior else '(sin valor)'
        valor_nuevo_display = self.valor_nuevo if self.valor_nuevo else '(sin valor)'
        
        if self.campo_cambiado == 'progreso':
            valor_anterior_display = f"{self.valor_anterior}%" if self.valor_anterior else '(sin valor)'
            valor_nuevo_display = f"{self.valor_nuevo}%" if self.valor_nuevo else '(sin valor)'
        elif self.campo_cambiado == 'estado':
            estados_espanol = {
                'finalizado': 'Finalizado',
                'en_desarrollo': 'En desarrollo',
                'espera_aprobacion': 'Espera Aprobación',
                'espera_ppto': 'Espera PPTO',
                'soporte': 'Soporte'
            }
            valor_anterior_display = estados_espanol.get(self.valor_anterior, self.valor_anterior) if self.valor_anterior else '(sin valor)'
            valor_nuevo_display = estados_espanol.get(self.valor_nuevo, self.valor_nuevo) if self.valor_nuevo else '(sin valor)'
        
        return {
            'id': self.id,
            'proyecto_id': self.proyecto_id,
            'autor_id': self.autor_id,
            'tipo_autor': self.tipo_autor,
            'autor_nombre': autor_nombre,
            'campo_cambiado': self.campo_cambiado,
            'campo_display': campo_display,
            'valor_anterior': self.valor_anterior,
            'valor_anterior_display': valor_anterior_display,
            'valor_nuevo': self.valor_nuevo,
            'valor_nuevo_display': valor_nuevo_display,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else '',
            'created_at_short': self.created_at.strftime('%d/%m/%Y %H:%M') if self.created_at else ''
        }

class Presupuesto:
    def __init__(self, id, proyecto_id, numero_presupuesto, fecha, obra, cliente_id, cliente_nombre, cliente_email, cliente_telefono, descuento, iva, generalidades, created_at, updated_at, porcentaje_empresa=None, tipo_presupuesto='principal', incidencia_id=None, visita_mantenimiento_id=None, estado_presupuesto='pendiente_aprobacion'):
        self.id = id
        self.proyecto_id = proyecto_id
        self.numero_presupuesto = numero_presupuesto
        self.fecha = fecha
        self.obra = obra
        self.cliente_id = cliente_id
        self.cliente_nombre = cliente_nombre
        self.cliente_email = cliente_email
        self.cliente_telefono = cliente_telefono
        self.descuento = float(descuento) if descuento else 0
        self.iva = float(iva) if iva else 19
        self.porcentaje_empresa = float(porcentaje_empresa) if porcentaje_empresa else 0
        self.tipo_presupuesto = tipo_presupuesto if tipo_presupuesto else 'principal'
        self.estado_presupuesto = estado_presupuesto if estado_presupuesto else 'pendiente_aprobacion'
        self.incidencia_id = incidencia_id if incidencia_id else None
        self.visita_mantenimiento_id = visita_mantenimiento_id if visita_mantenimiento_id else None
        self.generalidades = generalidades
        self.created_at = created_at
        self.updated_at = updated_at

    @staticmethod
    def create(proyecto_id, numero_presupuesto=None, fecha=None, obra=None, cliente_id=None, cliente_nombre=None, cliente_email=None, cliente_telefono=None, descuento=0, iva=19, generalidades=None, tipo_presupuesto='principal', incidencia_id=None, visita_mantenimiento_id=None, estado_presupuesto=None):
        """Crea un nuevo presupuesto"""
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            if not numero_presupuesto:
                # Generar número automático
                cur.execute("SELECT COALESCE(MAX(CAST(SUBSTRING(numero_presupuesto FROM '[0-9]+') AS INTEGER)), 0) + 1 FROM presupuestos WHERE numero_presupuesto ~ '^[0-9]+$'")
                next_num = cur.fetchone()[0]
                numero_presupuesto = str(next_num)
            
            # Establecer estado por defecto según tipo
            if estado_presupuesto is None:
                if tipo_presupuesto == 'principal':
                    estado_presupuesto = 'aprobado'  # Los principales vienen aprobados por defecto
                else:
                    estado_presupuesto = 'pendiente_aprobacion'  # Los secundarios requieren aprobación
            
            cur.execute("""
                INSERT INTO presupuestos (proyecto_id, numero_presupuesto, fecha, obra, cliente_id, cliente_nombre, cliente_email, cliente_telefono, descuento, iva, generalidades, porcentaje_empresa, tipo_presupuesto, incidencia_id, visita_mantenimiento_id, estado_presupuesto)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id, proyecto_id, numero_presupuesto, fecha, obra, cliente_id, cliente_nombre, cliente_email, cliente_telefono, descuento, iva, generalidades, created_at, updated_at, COALESCE(porcentaje_empresa, 0), COALESCE(tipo_presupuesto, 'principal'), incidencia_id, visita_mantenimiento_id, COALESCE(estado_presupuesto, 'pendiente_aprobacion')
            """, (proyecto_id, numero_presupuesto, fecha, obra, cliente_id, cliente_nombre, cliente_email, cliente_telefono, descuento, iva, generalidades, 0, tipo_presupuesto, incidencia_id, visita_mantenimiento_id, estado_presupuesto))
            presupuesto_row = cur.fetchone()
            conn.commit()
            return Presupuesto(*presupuesto_row)
        except Exception as e:
            conn.rollback()
            return str(e) if str(e) else "Error desconocido al crear presupuesto."
        finally:
            cur.close()
            conn.close()

    @staticmethod
    def get_by_id(presupuesto_id):
        """Obtiene un presupuesto por su ID"""
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT id, proyecto_id, numero_presupuesto, fecha, obra, cliente_id, cliente_nombre, cliente_email, cliente_telefono, descuento, iva, generalidades, created_at, updated_at, COALESCE(porcentaje_empresa, 0), COALESCE(tipo_presupuesto, 'principal'), incidencia_id, visita_mantenimiento_id, COALESCE(estado_presupuesto, 'pendiente_aprobacion')
            FROM presupuestos
            WHERE id = %s
        """, (presupuesto_id,))
        presupuesto = cur.fetchone()
        cur.close()
        conn.close()
        if presupuesto:
            return Presupuesto(*presupuesto)
        return None

    @staticmethod
    def get_by_proyecto(proyecto_id):
        """Obtiene el presupuesto principal de un proyecto (el más reciente)"""
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT id, proyecto_id, numero_presupuesto, fecha, obra, cliente_id, cliente_nombre, cliente_email, cliente_telefono, descuento, iva, generalidades, created_at, updated_at, COALESCE(porcentaje_empresa, 0), COALESCE(tipo_presupuesto, 'principal'), incidencia_id, visita_mantenimiento_id, COALESCE(estado_presupuesto, 'pendiente_aprobacion')
            FROM presupuestos
            WHERE proyecto_id = %s AND tipo_presupuesto = 'principal'
            ORDER BY created_at DESC
            LIMIT 1
        """, (proyecto_id,))
        presupuesto = cur.fetchone()
        cur.close()
        conn.close()
        if presupuesto:
            return Presupuesto(*presupuesto)
        return None

    @staticmethod
    def get_all_by_proyecto(proyecto_id):
        """Obtiene todos los presupuestos de un proyecto"""
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT id, proyecto_id, numero_presupuesto, fecha, obra, cliente_id, cliente_nombre, cliente_email, cliente_telefono, descuento, iva, generalidades, created_at, updated_at, COALESCE(porcentaje_empresa, 0), COALESCE(tipo_presupuesto, 'principal'), incidencia_id, visita_mantenimiento_id, COALESCE(estado_presupuesto, 'pendiente_aprobacion')
            FROM presupuestos
            WHERE proyecto_id = %s
            ORDER BY 
                CASE WHEN tipo_presupuesto = 'principal' THEN 0 ELSE 1 END,
                created_at DESC
        """, (proyecto_id,))
        presupuestos = cur.fetchall()
        cur.close()
        conn.close()
        return [Presupuesto(*p) for p in presupuestos]

    def update(self, numero_presupuesto=None, fecha=None, obra=None, cliente_id=None, cliente_nombre=None, cliente_email=None, cliente_telefono=None, descuento=None, iva=None, generalidades=None, porcentaje_empresa=None, tipo_presupuesto=None, incidencia_id=None, visita_mantenimiento_id=None, estado_presupuesto=None):
        """Actualiza un presupuesto"""
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            updates = []
            params = []
            if numero_presupuesto is not None:
                updates.append("numero_presupuesto = %s")
                params.append(numero_presupuesto)
            if fecha is not None:
                updates.append("fecha = %s")
                params.append(fecha)
            if obra is not None:
                updates.append("obra = %s")
                params.append(obra)
            if cliente_id is not None:
                updates.append("cliente_id = %s")
                params.append(cliente_id)
            if cliente_nombre is not None:
                updates.append("cliente_nombre = %s")
                params.append(cliente_nombre)
            if cliente_email is not None:
                updates.append("cliente_email = %s")
                params.append(cliente_email)
            if cliente_telefono is not None:
                updates.append("cliente_telefono = %s")
                params.append(cliente_telefono)
            if descuento is not None:
                updates.append("descuento = %s")
                params.append(descuento)
            if iva is not None:
                updates.append("iva = %s")
                params.append(iva)
            if generalidades is not None:
                updates.append("generalidades = %s")
                params.append(generalidades)
            if porcentaje_empresa is not None:
                updates.append("porcentaje_empresa = %s")
                params.append(porcentaje_empresa)
            if tipo_presupuesto is not None:
                updates.append("tipo_presupuesto = %s")
                params.append(tipo_presupuesto)
            if estado_presupuesto is not None:
                updates.append("estado_presupuesto = %s")
                params.append(estado_presupuesto)
            if incidencia_id is not None:
                updates.append("incidencia_id = %s")
                params.append(incidencia_id)
            if visita_mantenimiento_id is not None:
                updates.append("visita_mantenimiento_id = %s")
                params.append(visita_mantenimiento_id)
            
            updates.append("updated_at = CURRENT_TIMESTAMP")
            params.append(self.id)
            
            cur.execute(f"""
                UPDATE presupuestos SET {', '.join(updates)}
                WHERE id = %s
            """, params)
            conn.commit()
            # Actualizar atributos del objeto
            if cliente_id is not None:
                self.cliente_id = cliente_id
            if tipo_presupuesto is not None:
                self.tipo_presupuesto = tipo_presupuesto
            if estado_presupuesto is not None:
                self.estado_presupuesto = estado_presupuesto
            if incidencia_id is not None:
                self.incidencia_id = incidencia_id
            if visita_mantenimiento_id is not None:
                self.visita_mantenimiento_id = visita_mantenimiento_id
            return True
        except Exception as e:
            conn.rollback()
            return False
        finally:
            cur.close()
            conn.close()

    def to_dict(self):
        return {
            'id': self.id,
            'proyecto_id': self.proyecto_id,
            'numero_presupuesto': self.numero_presupuesto,
            'fecha': self.fecha.strftime('%d-%m-%Y') if self.fecha else '',
            'obra': self.obra,
            'cliente_id': self.cliente_id,
            'cliente_nombre': self.cliente_nombre,
            'cliente_email': self.cliente_email,
            'cliente_telefono': self.cliente_telefono,
            'descuento': self.descuento,
            'iva': self.iva,
            'porcentaje_empresa': self.porcentaje_empresa,
            'tipo_presupuesto': self.tipo_presupuesto if hasattr(self, 'tipo_presupuesto') else 'principal',
            'estado_presupuesto': self.estado_presupuesto if hasattr(self, 'estado_presupuesto') else 'pendiente_aprobacion',
            'incidencia_id': self.incidencia_id if hasattr(self, 'incidencia_id') else None,
            'visita_mantenimiento_id': self.visita_mantenimiento_id if hasattr(self, 'visita_mantenimiento_id') else None,
            'generalidades': self.generalidades
        }

class PresupuestoItem:
    def __init__(self, id, presupuesto_id, referencia, cantidad, ubicacion, tipologia, tipo, caracteristicas, valor_unitario, orden, created_at):
        self.id = id
        self.presupuesto_id = presupuesto_id
        self.referencia = referencia
        self.cantidad = float(cantidad) if cantidad else 0
        self.ubicacion = ubicacion
        self.tipologia = tipologia
        self.tipo = tipo
        self.caracteristicas = caracteristicas
        self.valor_unitario = float(valor_unitario) if valor_unitario else 0
        self.orden = orden
        self.created_at = created_at

    @property
    def importe_total(self):
        return self.cantidad * self.valor_unitario

    @staticmethod
    def get_by_id(item_id):
        """Obtiene un item por su ID"""
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT id, presupuesto_id, referencia, cantidad, ubicacion, tipologia, tipo, caracteristicas, valor_unitario, orden, created_at
            FROM presupuesto_items
            WHERE id = %s
        """, (item_id,))
        item = cur.fetchone()
        cur.close()
        conn.close()
        if item:
            return PresupuestoItem(*item)
        return None

    @staticmethod
    def create(presupuesto_id, referencia=None, cantidad=1, ubicacion=None, tipologia=None, tipo=None, caracteristicas=None, valor_unitario=0, orden=0):
        """Crea un nuevo item de presupuesto"""
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                INSERT INTO presupuesto_items (presupuesto_id, referencia, cantidad, ubicacion, tipologia, tipo, caracteristicas, valor_unitario, orden)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id, presupuesto_id, referencia, cantidad, ubicacion, tipologia, tipo, caracteristicas, valor_unitario, orden, created_at
            """, (presupuesto_id, referencia, cantidad, ubicacion, tipologia, tipo, caracteristicas, valor_unitario, orden))
            item_row = cur.fetchone()
            conn.commit()
            return PresupuestoItem(*item_row)
        except Exception as e:
            conn.rollback()
            return str(e) if str(e) else "Error desconocido al crear item."
        finally:
            cur.close()
            conn.close()

    @staticmethod
    def get_by_presupuesto(presupuesto_id):
        """Obtiene todos los items de un presupuesto ordenados por orden"""
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT id, presupuesto_id, referencia, cantidad, ubicacion, tipologia, tipo, caracteristicas, valor_unitario, orden, created_at
            FROM presupuesto_items
            WHERE presupuesto_id = %s
            ORDER BY orden ASC, id ASC
        """, (presupuesto_id,))
        items = cur.fetchall()
        cur.close()
        conn.close()
        return [PresupuestoItem(*item) for item in items]

    def update(self, referencia=None, cantidad=None, ubicacion=None, tipologia=None, tipo=None, caracteristicas=None, valor_unitario=None, orden=None):
        """Actualiza un item de presupuesto"""
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            updates = []
            params = []
            if referencia is not None:
                updates.append("referencia = %s")
                params.append(referencia)
            if cantidad is not None:
                updates.append("cantidad = %s")
                params.append(cantidad)
            if ubicacion is not None:
                updates.append("ubicacion = %s")
                params.append(ubicacion)
            if tipologia is not None:
                updates.append("tipologia = %s")
                params.append(tipologia)
            if tipo is not None:
                updates.append("tipo = %s")
                params.append(tipo)
            if caracteristicas is not None:
                updates.append("caracteristicas = %s")
                params.append(caracteristicas)
            if valor_unitario is not None:
                updates.append("valor_unitario = %s")
                params.append(valor_unitario)
            if orden is not None:
                updates.append("orden = %s")
                params.append(orden)
            
            params.append(self.id)
            
            cur.execute(f"""
                UPDATE presupuesto_items SET {', '.join(updates)}
                WHERE id = %s
            """, params)
            conn.commit()
            # Actualizar atributos
            if cantidad is not None:
                self.cantidad = float(cantidad)
            if valor_unitario is not None:
                self.valor_unitario = float(valor_unitario)
            return True
        except Exception as e:
            conn.rollback()
            return False
        finally:
            cur.close()
            conn.close()

    @staticmethod
    def delete(item_id):
        """Elimina un item de presupuesto"""
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("DELETE FROM presupuesto_items WHERE id = %s", (item_id,))
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            return False
        finally:
            cur.close()
            conn.close()

    def to_dict(self):
        return {
            'id': self.id,
            'presupuesto_id': self.presupuesto_id,
            'referencia': self.referencia,
            'cantidad': self.cantidad,
            'ubicacion': self.ubicacion,
            'tipologia': self.tipologia,
            'tipo': self.tipo,
            'caracteristicas': self.caracteristicas,
            'valor_unitario': self.valor_unitario,
            'importe_total': self.importe_total,
            'orden': self.orden
        }

class PresupuestoCosto:
    """Modelo para almacenar los costos detallados de cada item del presupuesto"""
    def __init__(self, id, presupuesto_item_id, insumos, maquila, instalacion, desinstalacion, materiales_ferreteria, gastos_generales, utilidad_porcentaje, flete, created_at, updated_at):
        self.id = id
        self.presupuesto_item_id = presupuesto_item_id
        self.insumos = float(insumos) if insumos else 0
        self.maquila = float(maquila) if maquila else 0
        self.instalacion = float(instalacion) if instalacion else 0
        self.desinstalacion = float(desinstalacion) if desinstalacion else 0
        self.materiales_ferreteria = float(materiales_ferreteria) if materiales_ferreteria else 0
        self.gastos_generales = float(gastos_generales) if gastos_generales else 0
        self.utilidad_porcentaje = float(utilidad_porcentaje) if utilidad_porcentaje else 0
        self.flete = float(flete) if flete else 0
        self.created_at = created_at
        self.updated_at = updated_at

    @property
    def costo_total(self):
        """Calcula el costo total sin utilidad"""
        return (self.insumos + self.maquila + self.instalacion + self.desinstalacion + 
                self.materiales_ferreteria + self.gastos_generales + self.flete)

    @property
    def valor_con_utilidad(self):
        """Calcula el valor con utilidad aplicada"""
        costo_base = self.costo_total
        utilidad_monto = costo_base * (self.utilidad_porcentaje / 100)
        return costo_base + utilidad_monto

    @staticmethod
    def get_by_item_id(item_id):
        """Obtiene el costo de un item"""
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT id, presupuesto_item_id, insumos, maquila, instalacion, desinstalacion, 
                   materiales_ferreteria, gastos_generales, utilidad_porcentaje, flete, created_at, updated_at
            FROM presupuesto_costos
            WHERE presupuesto_item_id = %s
        """, (item_id,))
        costo = cur.fetchone()
        cur.close()
        conn.close()
        if costo:
            return PresupuestoCosto(*costo)
        return None

    @staticmethod
    def create_or_update(item_id, insumos=0, maquila=0, instalacion=0, desinstalacion=0, 
                        materiales_ferreteria=0, gastos_generales=0, utilidad_porcentaje=0, flete=0):
        """Crea o actualiza el costo de un item"""
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            # Verificar si existe
            cur.execute("SELECT id FROM presupuesto_costos WHERE presupuesto_item_id = %s", (item_id,))
            existe = cur.fetchone()
            
            if existe:
                # Actualizar
                cur.execute("""
                    UPDATE presupuesto_costos 
                    SET insumos=%s, maquila=%s, instalacion=%s, desinstalacion=%s,
                        materiales_ferreteria=%s, gastos_generales=%s, utilidad_porcentaje=%s, flete=%s,
                        updated_at=CURRENT_TIMESTAMP
                    WHERE presupuesto_item_id=%s
                    RETURNING id, presupuesto_item_id, insumos, maquila, instalacion, desinstalacion,
                              materiales_ferreteria, gastos_generales, utilidad_porcentaje, flete, created_at, updated_at
                """, (insumos, maquila, instalacion, desinstalacion, materiales_ferreteria, 
                      gastos_generales, utilidad_porcentaje, flete, item_id))
            else:
                # Crear
                cur.execute("""
                    INSERT INTO presupuesto_costos (presupuesto_item_id, insumos, maquila, instalacion, desinstalacion,
                                                    materiales_ferreteria, gastos_generales, utilidad_porcentaje, flete)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id, presupuesto_item_id, insumos, maquila, instalacion, desinstalacion,
                              materiales_ferreteria, gastos_generales, utilidad_porcentaje, flete, created_at, updated_at
                """, (item_id, insumos, maquila, instalacion, desinstalacion, materiales_ferreteria,
                      gastos_generales, utilidad_porcentaje, flete))
            
            costo_row = cur.fetchone()
            conn.commit()
            return PresupuestoCosto(*costo_row)
        except Exception as e:
            conn.rollback()
            return str(e) if str(e) else "Error desconocido al crear/actualizar costo."
        finally:
            cur.close()
            conn.close()

    def to_dict(self):
        return {
            'id': self.id,
            'presupuesto_item_id': self.presupuesto_item_id,
            'insumos': self.insumos,
            'maquila': self.maquila,
            'instalacion': self.instalacion,
            'desinstalacion': self.desinstalacion,
            'materiales_ferreteria': self.materiales_ferreteria,
            'gastos_generales': self.gastos_generales,
            'utilidad_porcentaje': self.utilidad_porcentaje,
            'flete': self.flete,
            'costo_total': self.costo_total,
            'valor_con_utilidad': self.valor_con_utilidad
        }

class PresupuestoGasto:
    """Modelo para gastos adicionales del proyecto"""
    def __init__(self, id, presupuesto_id, descripcion, monto, tipo, pagado_por_id, pagado_por_tipo, fecha, created_at, updated_at, factura_id=None):
        self.id = id
        self.presupuesto_id = presupuesto_id
        self.descripcion = descripcion
        self.monto = float(monto) if monto else 0
        self.tipo = tipo
        self.pagado_por_id = pagado_por_id
        self.pagado_por_tipo = pagado_por_tipo
        self.fecha = fecha
        self.created_at = created_at
        self.updated_at = updated_at
        self.factura_id = factura_id

    @staticmethod
    def get_by_presupuesto(presupuesto_id):
        """Obtiene todos los gastos de un presupuesto"""
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT id, presupuesto_id, descripcion, monto, tipo, pagado_por_id, pagado_por_tipo, fecha, created_at, updated_at, COALESCE(factura_id, NULL)
            FROM presupuesto_gastos
            WHERE presupuesto_id = %s
            ORDER BY fecha DESC, created_at DESC
        """, (presupuesto_id,))
        gastos = cur.fetchall()
        cur.close()
        conn.close()
        return [PresupuestoGasto(*g) for g in gastos]

    @staticmethod
    def create(presupuesto_id, descripcion, monto, tipo='general', pagado_por_id=None, pagado_por_tipo='user', fecha=None, factura_id=None):
        """Crea un nuevo gasto"""
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            if not fecha:
                fecha = datetime.now().date()
            cur.execute("""
                INSERT INTO presupuesto_gastos (presupuesto_id, descripcion, monto, tipo, pagado_por_id, pagado_por_tipo, fecha, factura_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id, presupuesto_id, descripcion, monto, tipo, pagado_por_id, pagado_por_tipo, fecha, created_at, updated_at, factura_id
            """, (presupuesto_id, descripcion, monto, tipo, pagado_por_id, pagado_por_tipo, fecha, factura_id))
            gasto_row = cur.fetchone()
            conn.commit()
            return PresupuestoGasto(*gasto_row)
        except Exception as e:
            conn.rollback()
            return str(e) if str(e) else "Error desconocido al crear gasto."
        finally:
            cur.close()
            conn.close()

    @staticmethod
    def get_by_id(gasto_id):
        """Obtiene un gasto por su ID"""
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                SELECT id, presupuesto_id, descripcion, monto, tipo, pagado_por_id, pagado_por_tipo, fecha, created_at, updated_at, COALESCE(factura_id, NULL)
                FROM presupuesto_gastos
                WHERE id = %s
            """, (gasto_id,))
            gasto_row = cur.fetchone()
            if gasto_row:
                return PresupuestoGasto(*gasto_row)
            return None
        except Exception as e:
            return None
        finally:
            cur.close()
            conn.close()

    def update(self, descripcion=None, monto=None, tipo=None, pagado_por_id=None, pagado_por_tipo=None, fecha=None, factura_id=None, _update_pagado_por_id=False, _update_factura_id=False):
        """Actualiza un gasto
        _update_pagado_por_id: Si es True, actualiza pagado_por_id incluso si es None
        _update_factura_id: Si es True, actualiza factura_id incluso si es None
        """
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            updates = []
            params = []
            
            if descripcion is not None:
                updates.append("descripcion = %s")
                params.append(descripcion)
            if monto is not None:
                updates.append("monto = %s")
                params.append(monto)
            if tipo is not None:
                updates.append("tipo = %s")
                params.append(tipo)
            if pagado_por_id is not None or _update_pagado_por_id:
                updates.append("pagado_por_id = %s")
                params.append(pagado_por_id)
            if pagado_por_tipo is not None:
                updates.append("pagado_por_tipo = %s")
                params.append(pagado_por_tipo)
            if fecha is not None:
                updates.append("fecha = %s")
                params.append(fecha)
            if factura_id is not None or _update_factura_id:
                updates.append("factura_id = %s")
                params.append(factura_id)
            
            if not updates:
                return True
            
            updates.append("updated_at = CURRENT_TIMESTAMP")
            params.append(self.id)
            
            query = f"UPDATE presupuesto_gastos SET {', '.join(updates)} WHERE id = %s"
            cur.execute(query, params)
            conn.commit()
            
            # Actualizar los valores del objeto
            if descripcion is not None:
                self.descripcion = descripcion
            if monto is not None:
                self.monto = float(monto) if monto else 0
            if tipo is not None:
                self.tipo = tipo
            if pagado_por_id is not None or _update_pagado_por_id:
                self.pagado_por_id = pagado_por_id
            if pagado_por_tipo is not None:
                self.pagado_por_tipo = pagado_por_tipo
            if fecha is not None:
                self.fecha = fecha
            if factura_id is not None or _update_factura_id:
                self.factura_id = factura_id
            
            return True
        except Exception as e:
            conn.rollback()
            import traceback
            print(f"Error en update de PresupuestoGasto: {str(e)}")
            print(traceback.format_exc())
            return False
        finally:
            cur.close()
            conn.close()

    @staticmethod
    def delete(gasto_id):
        """Elimina un gasto"""
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("DELETE FROM presupuesto_gastos WHERE id = %s", (gasto_id,))
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            return False
        finally:
            cur.close()
            conn.close()

    def to_dict(self):
        # Convertir -1 a 'empresa' para el frontend
        pagado_por_id = self.pagado_por_id
        if pagado_por_id == -1:
            pagado_por_id = 'empresa'
        elif pagado_por_id and pagado_por_id > 0:
            pagado_por_id = pagado_por_id
        else:
            pagado_por_id = None
        
        # Manejar fecha que puede ser string o date
        fecha_str = None
        if self.fecha:
            if isinstance(self.fecha, str):
                fecha_str = self.fecha
            else:
                fecha_str = self.fecha.strftime('%Y-%m-%d')
        
        return {
            'id': self.id,
            'presupuesto_id': self.presupuesto_id,
            'descripcion': self.descripcion,
            'monto': self.monto,
            'tipo': self.tipo,
            'pagado_por_id': pagado_por_id,
            'pagado_por_tipo': self.pagado_por_tipo,
            'fecha': fecha_str,
            'factura_id': self.factura_id if hasattr(self, 'factura_id') else None
        }

class PresupuestoFactura:
    """Modelo para facturas/boletas del proyecto"""
    def __init__(self, id, presupuesto_id, tipo_documento, numero_documento, proveedor, fecha_emision, fecha_vencimiento, total, iva, neto, archivo_ruta, texto_extraido, created_at, updated_at):
        self.id = id
        self.presupuesto_id = presupuesto_id
        self.tipo_documento = tipo_documento
        self.numero_documento = numero_documento
        self.proveedor = proveedor
        self.fecha_emision = fecha_emision
        self.fecha_vencimiento = fecha_vencimiento
        self.total = float(total) if total else 0
        self.iva = float(iva) if iva else 0
        self.neto = float(neto) if neto else 0
        self.archivo_ruta = archivo_ruta
        self.texto_extraido = texto_extraido
        self.created_at = created_at
        self.updated_at = updated_at

    @staticmethod
    def create(presupuesto_id, tipo_documento='factura', numero_documento=None, proveedor=None, fecha_emision=None, fecha_vencimiento=None, total=None, iva=None, neto=None, archivo_ruta=None, texto_extraido=None):
        """Crea una nueva factura/boleta"""
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                INSERT INTO presupuesto_facturas (presupuesto_id, tipo_documento, numero_documento, proveedor, fecha_emision, fecha_vencimiento, total, iva, neto, archivo_ruta, texto_extraido)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id, presupuesto_id, tipo_documento, numero_documento, proveedor, fecha_emision, fecha_vencimiento, total, iva, neto, archivo_ruta, texto_extraido, created_at, updated_at
            """, (presupuesto_id, tipo_documento, numero_documento, proveedor, fecha_emision, fecha_vencimiento, total, iva, neto, archivo_ruta, texto_extraido))
            factura_row = cur.fetchone()
            conn.commit()
            return PresupuestoFactura(*factura_row)
        except Exception as e:
            conn.rollback()
            return str(e) if str(e) else "Error desconocido al crear factura."
        finally:
            cur.close()
            conn.close()

    @staticmethod
    def get_by_presupuesto(presupuesto_id):
        """Obtiene todas las facturas/boletas de un presupuesto"""
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT id, presupuesto_id, tipo_documento, numero_documento, proveedor, fecha_emision, fecha_vencimiento, total, iva, neto, archivo_ruta, texto_extraido, created_at, updated_at
            FROM presupuesto_facturas
            WHERE presupuesto_id = %s
            ORDER BY fecha_emision DESC, created_at DESC
        """, (presupuesto_id,))
        facturas = cur.fetchall()
        cur.close()
        conn.close()
        return [PresupuestoFactura(*f) for f in facturas]

    @staticmethod
    def get_by_id(factura_id):
        """Obtiene una factura por su ID"""
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                SELECT id, presupuesto_id, tipo_documento, numero_documento, proveedor, fecha_emision, fecha_vencimiento, total, iva, neto, archivo_ruta, texto_extraido, created_at, updated_at
                FROM presupuesto_facturas
                WHERE id = %s
            """, (factura_id,))
            factura_row = cur.fetchone()
            if factura_row:
                return PresupuestoFactura(*factura_row)
            return None
        except Exception as e:
            return None
        finally:
            cur.close()
            conn.close()

    @staticmethod
    def get_gastos_vinculados(factura_id):
        """Obtiene todos los gastos vinculados a una factura"""
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT id, presupuesto_id, descripcion, monto, tipo, pagado_por_id, pagado_por_tipo, fecha, created_at, updated_at, COALESCE(factura_id, NULL)
            FROM presupuesto_gastos
            WHERE factura_id = %s
            ORDER BY fecha DESC, created_at DESC
        """, (factura_id,))
        gastos = cur.fetchall()
        cur.close()
        conn.close()
        return [PresupuestoGasto(*g) for g in gastos]

    @staticmethod
    def delete(factura_id):
        """Elimina una factura/boleta"""
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            # Primero obtener la factura para eliminar el archivo si existe
            factura = PresupuestoFactura.get_by_id(factura_id)
            if factura and factura.archivo_ruta:
                import os
                filepath = factura.archivo_ruta.lstrip('/')
                if os.path.exists(filepath):
                    try:
                        os.remove(filepath)
                    except:
                        pass  # Si no se puede eliminar el archivo, continuar
            
            # Eliminar la factura (los gastos vinculados se desvinculan automáticamente por ON DELETE SET NULL)
            cur.execute("DELETE FROM presupuesto_facturas WHERE id = %s", (factura_id,))
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            return False
        finally:
            cur.close()
            conn.close()

    def to_dict(self):
        # Manejar fecha_emision que puede ser string o date
        fecha_emision_str = None
        if self.fecha_emision:
            if isinstance(self.fecha_emision, str):
                fecha_emision_str = self.fecha_emision
            else:
                fecha_emision_str = self.fecha_emision.strftime('%Y-%m-%d')
        
        # Manejar fecha_vencimiento que puede ser string o date
        fecha_vencimiento_str = None
        if self.fecha_vencimiento:
            if isinstance(self.fecha_vencimiento, str):
                fecha_vencimiento_str = self.fecha_vencimiento
            else:
                fecha_vencimiento_str = self.fecha_vencimiento.strftime('%Y-%m-%d')
        
        return {
            'id': self.id,
            'presupuesto_id': self.presupuesto_id,
            'tipo_documento': self.tipo_documento,
            'numero_documento': self.numero_documento,
            'proveedor': self.proveedor,
            'fecha_emision': fecha_emision_str,
            'fecha_vencimiento': fecha_vencimiento_str,
            'total': self.total,
            'iva': self.iva,
            'neto': self.neto,
            'archivo_ruta': self.archivo_ruta,
            'texto_extraido': self.texto_extraido[:500] + '...' if self.texto_extraido and len(self.texto_extraido) > 500 else self.texto_extraido,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M') if self.created_at else None
        }

class PresupuestoPagoEmpleado:
    """Modelo para asignar porcentajes de pago a empleados"""
    def __init__(self, id, presupuesto_id, empleado_id, porcentaje_pago, anticipo, created_at, updated_at, quien_pago_anticipo_id=None):
        self.id = id
        self.presupuesto_id = presupuesto_id
        self.empleado_id = empleado_id
        self.porcentaje_pago = float(porcentaje_pago) if porcentaje_pago else 0
        self.anticipo = float(anticipo) if anticipo else 0
        self.quien_pago_anticipo_id = quien_pago_anticipo_id
        self.created_at = created_at
        self.updated_at = updated_at

    @staticmethod
    def get_by_presupuesto(presupuesto_id):
        """Obtiene todos los pagos de empleados de un presupuesto"""
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT pp.id, pp.presupuesto_id, pp.empleado_id, pp.porcentaje_pago, COALESCE(pp.anticipo, 0), pp.created_at, pp.updated_at, pp.quien_pago_anticipo_id
            FROM presupuesto_pagos_empleados pp
            WHERE pp.presupuesto_id = %s
            ORDER BY pp.empleado_id
        """, (presupuesto_id,))
        pagos = cur.fetchall()
        cur.close()
        conn.close()
        return [PresupuestoPagoEmpleado(*p) for p in pagos]

    @staticmethod
    def create_or_update(presupuesto_id, empleado_id, porcentaje_pago=0, anticipo=0, quien_pago_anticipo_id=None):
        """Crea o actualiza el pago de un empleado"""
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                INSERT INTO presupuesto_pagos_empleados (presupuesto_id, empleado_id, porcentaje_pago, anticipo, quien_pago_anticipo_id)
                VALUES (%s, %s, %s, %s, %s) AS new
                ON DUPLICATE KEY UPDATE
                    porcentaje_pago = new.porcentaje_pago,
                    anticipo = new.anticipo,
                    quien_pago_anticipo_id = new.quien_pago_anticipo_id,
                    updated_at = CURRENT_TIMESTAMP
                RETURNING id, presupuesto_id, empleado_id, porcentaje_pago, COALESCE(anticipo, 0), created_at, updated_at, quien_pago_anticipo_id
            """, (presupuesto_id, empleado_id, porcentaje_pago, anticipo, quien_pago_anticipo_id))
            pago_row = cur.fetchone()
            conn.commit()
            return PresupuestoPagoEmpleado(*pago_row)
        except Exception as e:
            conn.rollback()
            return str(e) if str(e) else "Error desconocido al crear/actualizar pago."
        finally:
            cur.close()
            conn.close()

    @staticmethod
    def get_by_id(pago_id):
        """Obtiene un pago de empleado por su ID"""
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                SELECT pp.id, pp.presupuesto_id, pp.empleado_id, pp.porcentaje_pago, COALESCE(pp.anticipo, 0), pp.created_at, pp.updated_at, pp.quien_pago_anticipo_id
                FROM presupuesto_pagos_empleados pp
                WHERE pp.id = %s
            """, (pago_id,))
            pago = cur.fetchone()
            if pago:
                # Asegurar que quien_pago_anticipo_id sea None si es NULL en la BD
                pago_list = list(pago)
                if pago_list[7] is None:
                    pago_list[7] = None
                return PresupuestoPagoEmpleado(*pago_list)
            return None
        except Exception as e:
            print(f"Error en get_by_id: {e}")
            return None
        finally:
            cur.close()
            conn.close()

    @staticmethod
    def delete(pago_id):
        """Elimina un pago de empleado"""
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("DELETE FROM presupuesto_pagos_empleados WHERE id = %s", (pago_id,))
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            return False
        finally:
            cur.close()
            conn.close()

    def calcular_pago_total(self, total_presupuesto):
        """Calcula el pago total para este empleado (porcentaje - anticipo)"""
        pago_porcentaje = total_presupuesto * (self.porcentaje_pago / 100)
        return pago_porcentaje - self.anticipo

    def to_dict(self):
        # Convertir -1 a 'empresa' para el frontend
        quien_pago_id = self.quien_pago_anticipo_id
        if quien_pago_id == -1:
            quien_pago_id = 'empresa'
        elif quien_pago_id and quien_pago_id > 0:
            quien_pago_id = quien_pago_id
        else:
            quien_pago_id = None
        
        return {
            'id': self.id,
            'presupuesto_id': self.presupuesto_id,
            'empleado_id': self.empleado_id,
            'porcentaje_pago': self.porcentaje_pago,
            'anticipo': self.anticipo,
            'quien_pago_anticipo_id': quien_pago_id
        }

def create_activos_table():
    """Crea la tabla de activos si no existe"""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS activos (
        id INT AUTO_INCREMENT PRIMARY KEY,
        proyecto_id INTEGER NOT NULL,
        nombre VARCHAR(200) NOT NULL,
        tipo VARCHAR(50),
        estado VARCHAR(50),
        numero_serie VARCHAR(100),
        ubicacion VARCHAR(200),
        fecha_compra DATE,
        fecha_instalacion DATE,
        valor DECIMAL(12, 2),
        asignado_id INTEGER,
        asignado_tipo VARCHAR(20),
        asignado VARCHAR(200),
        cuenta_vinculada VARCHAR(200),
        ip VARCHAR(50),
        password VARCHAR(200),
        detalles TEXT,
        creador_id INTEGER NOT NULL,
        creador_tipo VARCHAR(20) NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (proyecto_id) REFERENCES proyectos(id) ON DELETE CASCADE
    );
    """)
    conn.commit()
    
    # Migración: agregar columna asignado si no existe
    try:
        cur.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='activos' AND column_name='asignado'
        """)
        if not cur.fetchone():
            cur.execute("ALTER TABLE activos ADD COLUMN asignado VARCHAR(200)")
            conn.commit()
            print("Migración exitosa: columna 'asignado' agregada a 'activos'")
    except Exception as e:
        conn.rollback()
        print(f"Error durante migración para 'asignado': {e}")
    
    # Migración: agregar columna cuenta_vinculada si no existe
    try:
        cur.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='activos' AND column_name='cuenta_vinculada'
        """)
        if not cur.fetchone():
            cur.execute("ALTER TABLE activos ADD COLUMN cuenta_vinculada VARCHAR(200)")
            conn.commit()
            print("Migración exitosa: columna 'cuenta_vinculada' agregada a 'activos'")
    except Exception as e:
        conn.rollback()
        print(f"Error durante migración para 'cuenta_vinculada': {e}")
    
    cur.close()
    conn.close()

class Activo:
    def __init__(self, id, proyecto_id, nombre, tipo, estado, numero_serie, ubicacion, fecha_compra, fecha_instalacion, valor, asignado_id, asignado_tipo, asignado, cuenta_vinculada, ip, password, detalles, creador_id, creador_tipo, created_at, updated_at):
        self.id = id
        self.proyecto_id = proyecto_id
        self.nombre = nombre
        self.tipo = tipo
        self.estado = estado
        self.numero_serie = numero_serie
        self.ubicacion = ubicacion
        self.fecha_compra = fecha_compra
        self.fecha_instalacion = fecha_instalacion
        self.valor = float(valor) if valor else 0
        self.asignado_id = asignado_id
        self.asignado_tipo = asignado_tipo
        self.asignado = asignado
        self.cuenta_vinculada = cuenta_vinculada
        self.ip = ip
        self.password = password
        self.detalles = detalles
        self.creador_id = creador_id
        self.creador_tipo = creador_tipo
        self.created_at = created_at
        self.updated_at = updated_at

    @staticmethod
    def create(proyecto_id, nombre, tipo=None, estado=None, numero_serie=None, ubicacion=None, fecha_compra=None, fecha_instalacion=None, valor=None, asignado_id=None, asignado_tipo=None, asignado=None, cuenta_vinculada=None, ip=None, password=None, detalles=None, creador_id=None, creador_tipo='user'):
        """Crea un nuevo activo"""
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                INSERT INTO activos (proyecto_id, nombre, tipo, estado, numero_serie, ubicacion, fecha_compra, fecha_instalacion, valor, asignado_id, asignado_tipo, asignado, cuenta_vinculada, ip, password, detalles, creador_id, creador_tipo)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id, proyecto_id, nombre, tipo, estado, numero_serie, ubicacion, fecha_compra, fecha_instalacion, valor, asignado_id, asignado_tipo, asignado, cuenta_vinculada, ip, password, detalles, creador_id, creador_tipo, created_at, updated_at
            """, (proyecto_id, nombre, tipo, estado, numero_serie, ubicacion, fecha_compra, fecha_instalacion, valor, asignado_id, asignado_tipo, asignado, cuenta_vinculada, ip, password, detalles, creador_id, creador_tipo))
            activo_row = cur.fetchone()
            conn.commit()
            return Activo(*activo_row)
        except Exception as e:
            conn.rollback()
            return str(e) if str(e) else "Error desconocido al crear activo."
        finally:
            cur.close()
            conn.close()

    @staticmethod
    def get_by_id(activo_id):
        """Obtiene un activo por su ID"""
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT id, proyecto_id, nombre, tipo, estado, numero_serie, ubicacion, fecha_compra, fecha_instalacion, valor, asignado_id, asignado_tipo, asignado, cuenta_vinculada, ip, password, detalles, creador_id, creador_tipo, created_at, updated_at
            FROM activos
            WHERE id = %s
        """, (activo_id,))
        activo = cur.fetchone()
        cur.close()
        conn.close()
        if activo:
            return Activo(*activo)
        return None

    @staticmethod
    def get_by_proyecto(proyecto_id):
        """Obtiene todos los activos de un proyecto"""
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT id, proyecto_id, nombre, tipo, estado, numero_serie, ubicacion, fecha_compra, fecha_instalacion, valor, asignado_id, asignado_tipo, asignado, cuenta_vinculada, ip, password, detalles, creador_id, creador_tipo, created_at, updated_at
            FROM activos
            WHERE proyecto_id = %s
            ORDER BY created_at DESC
        """, (proyecto_id,))
        activos = cur.fetchall()
        cur.close()
        conn.close()
        return [Activo(*a) for a in activos]

    def update(self, nombre=None, tipo=None, estado=None, numero_serie=None, ubicacion=None, fecha_compra=None, fecha_instalacion=None, valor=None, asignado_id=None, asignado_tipo=None, asignado=None, cuenta_vinculada=None, ip=None, password=None, detalles=None):
        """Actualiza un activo"""
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            updates = []
            params = []
            if nombre is not None:
                updates.append("nombre = %s")
                params.append(nombre)
            if tipo is not None:
                updates.append("tipo = %s")
                params.append(tipo)
            if estado is not None:
                updates.append("estado = %s")
                params.append(estado)
            if numero_serie is not None:
                updates.append("numero_serie = %s")
                params.append(numero_serie)
            if ubicacion is not None:
                updates.append("ubicacion = %s")
                params.append(ubicacion)
            if fecha_compra is not None:
                updates.append("fecha_compra = %s")
                params.append(fecha_compra)
            if fecha_instalacion is not None:
                updates.append("fecha_instalacion = %s")
                params.append(fecha_instalacion)
            if valor is not None:
                updates.append("valor = %s")
                params.append(valor)
            if asignado_id is not None:
                updates.append("asignado_id = %s")
                params.append(asignado_id)
            if asignado_tipo is not None:
                updates.append("asignado_tipo = %s")
                params.append(asignado_tipo)
            if asignado is not None:
                updates.append("asignado = %s")
                params.append(asignado)
            if cuenta_vinculada is not None:
                updates.append("cuenta_vinculada = %s")
                params.append(cuenta_vinculada)
            if ip is not None:
                updates.append("ip = %s")
                params.append(ip)
            if password is not None:
                updates.append("password = %s")
                params.append(password)
            if detalles is not None:
                updates.append("detalles = %s")
                params.append(detalles)
            
            updates.append("updated_at = CURRENT_TIMESTAMP")
            params.append(self.id)
            
            cur.execute(f"""
                UPDATE activos SET {', '.join(updates)}
                WHERE id = %s
            """, params)
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            return False
        finally:
            cur.close()
            conn.close()

    @staticmethod
    def delete(activo_id):
        """Elimina un activo"""
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("DELETE FROM activos WHERE id = %s", (activo_id,))
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            return False
        finally:
            cur.close()
            conn.close()

    def to_dict(self, current_user_id=None, current_user_is_admin=False, current_user_tipo='user'):
        """Convierte el activo a diccionario, ocultando IP y password si no es el creador o admin"""
        # Determinar si se puede ver IP y password
        puede_ver_credenciales = current_user_is_admin or (current_user_id == self.creador_id and current_user_tipo == self.creador_tipo)
        
        # Obtener información del asignado
        asignado_nombre = None
        if self.asignado_id and self.asignado_tipo:
            if self.asignado_tipo == 'user':
                user = User.get_by_id(self.asignado_id)
                if user:
                    asignado_nombre = f"{user.nombre} {user.apellido}"
            elif self.asignado_tipo == 'cliente':
                cliente = Cliente.get_by_id(self.asignado_id)
                if cliente:
                    if cliente.tipo_cliente == 'empresa':
                        asignado_nombre = cliente.nombre_empresa
                    else:
                        asignado_nombre = f"{cliente.nombre} {cliente.apellido}"
        
        return {
            'id': self.id,
            'proyecto_id': self.proyecto_id,
            'nombre': self.nombre,
            'tipo': self.tipo,
            'estado': self.estado,
            'numero_serie': self.numero_serie,
            'ubicacion': self.ubicacion,
            'fecha_compra': self.fecha_compra.strftime('%Y-%m-%d') if self.fecha_compra else None,
            'fecha_instalacion': self.fecha_instalacion.strftime('%Y-%m-%d') if self.fecha_instalacion else None,
            'valor': self.valor,
            'asignado_id': self.asignado_id,
            'asignado_tipo': self.asignado_tipo,
            'asignado': self.asignado,
            'asignado_nombre': asignado_nombre if asignado_nombre else self.asignado,
            'cuenta_vinculada': self.cuenta_vinculada,
            'ip': self.ip if puede_ver_credenciales else None,
            'password': self.password if puede_ver_credenciales else None,
            'puede_ver_credenciales': puede_ver_credenciales,
            'detalles': self.detalles,
            'creador_id': self.creador_id,
            'creador_tipo': self.creador_tipo,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else '',
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else ''
        }

def create_incidencias_table():
    """Crea la tabla de incidencias si no existe"""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS incidencias (
        id INT AUTO_INCREMENT PRIMARY KEY,
        proyecto_id INTEGER NOT NULL,
        activo_id INTEGER,
        titulo VARCHAR(200) NOT NULL,
        descripcion TEXT,
        estado VARCHAR(50) DEFAULT 'abierta',
        creador_id INTEGER NOT NULL,
        creador_tipo VARCHAR(20) NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (proyecto_id) REFERENCES proyectos(id) ON DELETE CASCADE,
        FOREIGN KEY (activo_id) REFERENCES activos(id) ON DELETE SET NULL
    );
    """)
    conn.commit()
    cur.close()
    conn.close()

def create_incidencia_comentarios_table():
    """Crea la tabla de comentarios de incidencias si no existe"""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS incidencia_comentarios (
        id INT AUTO_INCREMENT PRIMARY KEY,
        incidencia_id INTEGER NOT NULL,
        autor_id INTEGER NOT NULL,
        tipo_autor VARCHAR(20) NOT NULL,
        comentario TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (incidencia_id) REFERENCES incidencias(id) ON DELETE CASCADE
    );
    """)
    conn.commit()
    cur.close()
    conn.close()

def create_proyecto_mantenimiento_config_table():
    """Crea la tabla de configuración de mantenimiento para proyectos"""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS proyecto_mantenimiento_config (
        id INT AUTO_INCREMENT PRIMARY KEY,
        proyecto_id INTEGER NOT NULL UNIQUE REFERENCES proyectos(id) ON DELETE CASCADE,
        periodo_visita VARCHAR(200) DEFAULT '1 visita mensual',
        incluye_emergencia BOOLEAN DEFAULT FALSE,
        periodo_emergencia VARCHAR(200),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    conn.commit()
    cur.close()
    conn.close()

def create_proyecto_mantenimiento_visitas_table():
    """Crea la tabla de visitas de mantenimiento"""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS proyecto_mantenimiento_visitas (
        id INT AUTO_INCREMENT PRIMARY KEY,
        proyecto_id INTEGER NOT NULL REFERENCES proyectos(id) ON DELETE CASCADE,
        fecha_visita DATE NOT NULL,
        tipo_visita VARCHAR(50) DEFAULT 'programada',
        incidencia_id INTEGER REFERENCES incidencias(id) ON DELETE SET NULL,
        comentarios TEXT,
        sugerencias TEXT,
        observaciones TEXT,
        creador_id INTEGER NOT NULL,
        creador_tipo VARCHAR(20) NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    try:
        cur.execute(
            "SELECT column_name FROM information_schema.columns WHERE table_name='proyecto_mantenimiento_visitas' AND column_name='incidencia_id'"
        )
        if not cur.fetchone():
            cur.execute(
                "ALTER TABLE proyecto_mantenimiento_visitas ADD COLUMN incidencia_id INTEGER REFERENCES incidencias(id) ON DELETE SET NULL"
            )
            conn.commit()
            print("Migración exitosa: columna 'incidencia_id' agregada a 'proyecto_mantenimiento_visitas'")
    except Exception as e:
        conn.rollback()
        print(f"Error durante migración para 'incidencia_id': {e}")
    conn.commit()
    cur.close()
    conn.close()

def create_proyecto_mantenimiento_fotos_table():
    """Crea la tabla de fotos de visitas de mantenimiento"""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS proyecto_mantenimiento_fotos (
        id INT AUTO_INCREMENT PRIMARY KEY,
        visita_id INTEGER NOT NULL REFERENCES proyecto_mantenimiento_visitas(id) ON DELETE CASCADE,
        ruta_archivo VARCHAR(500) NOT NULL,
        descripcion TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    conn.commit()
    cur.close()
    conn.close()

def create_proyecto_mantenimiento_visitas_activos_table():
    """Crea la tabla intermedia para vincular visitas de mantenimiento con activos"""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS proyecto_mantenimiento_visitas_activos (
        id INT AUTO_INCREMENT PRIMARY KEY,
        visita_id INTEGER NOT NULL REFERENCES proyecto_mantenimiento_visitas(id) ON DELETE CASCADE,
        activo_id INTEGER NOT NULL REFERENCES activos(id) ON DELETE CASCADE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(visita_id, activo_id)
    );
    """)
    cur.execute("CREATE INDEX IF NOT EXISTS idx_visita_activo_visita ON proyecto_mantenimiento_visitas_activos(visita_id)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_visita_activo_activo ON proyecto_mantenimiento_visitas_activos(activo_id)")
    conn.commit()
    cur.close()
    conn.close()

def create_proyecto_mantenimiento_checklist_items_table():
    """Crea la tabla de items de checklist para proyectos"""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS proyecto_mantenimiento_checklist_items (
        id INT AUTO_INCREMENT PRIMARY KEY,
        proyecto_id INTEGER NOT NULL REFERENCES proyectos(id) ON DELETE CASCADE,
        titulo VARCHAR(500) NOT NULL,
        descripcion TEXT,
        categoria VARCHAR(200),
        orden INTEGER DEFAULT 0,
        activo BOOLEAN DEFAULT TRUE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    cur.execute("CREATE INDEX IF NOT EXISTS idx_checklist_items_proyecto ON proyecto_mantenimiento_checklist_items(proyecto_id)")
    conn.commit()
    cur.close()
    conn.close()

def create_proyecto_mantenimiento_checklist_respuestas_table():
    """Crea la tabla de respuestas de checklist por visita"""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS proyecto_mantenimiento_checklist_respuestas (
        id INT AUTO_INCREMENT PRIMARY KEY,
        visita_id INTEGER NOT NULL REFERENCES proyecto_mantenimiento_visitas(id) ON DELETE CASCADE,
        checklist_item_id INTEGER NOT NULL REFERENCES proyecto_mantenimiento_checklist_items(id) ON DELETE CASCADE,
        completado BOOLEAN DEFAULT FALSE,
        comentario TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(visita_id, checklist_item_id)
    );
    """)
    cur.execute("CREATE INDEX IF NOT EXISTS idx_checklist_respuestas_visita ON proyecto_mantenimiento_checklist_respuestas(visita_id)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_checklist_respuestas_item ON proyecto_mantenimiento_checklist_respuestas(checklist_item_id)")
    conn.commit()
    cur.close()
    conn.close()

def create_proyecto_instalacion_sesiones_table():
    """Crea la tabla de sesiones de instalación del proyecto"""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS proyecto_instalacion_sesiones (
        id INT AUTO_INCREMENT PRIMARY KEY,
        proyecto_id INTEGER NOT NULL REFERENCES proyectos(id) ON DELETE CASCADE,
        fecha DATE NOT NULL,
        hora_llegada TIME,
        hora_salida TIME,
        instalador_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        observaciones TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    cur.execute("CREATE INDEX IF NOT EXISTS idx_instalacion_sesiones_proyecto ON proyecto_instalacion_sesiones(proyecto_id)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_instalacion_sesiones_fecha ON proyecto_instalacion_sesiones(fecha)")
    conn.commit()
    cur.close()
    conn.close()

def create_proyecto_instalacion_checklist_items_table():
    """Crea la tabla de items del checklist de instalación por proyecto"""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS proyecto_instalacion_checklist_items (
        id INT AUTO_INCREMENT PRIMARY KEY,
        proyecto_id INTEGER NOT NULL REFERENCES proyectos(id) ON DELETE CASCADE,
        activo_id INTEGER REFERENCES activos(id) ON DELETE SET NULL,
        presupuesto_item_id INTEGER REFERENCES presupuesto_items(id) ON DELETE SET NULL,
        titulo VARCHAR(500) NOT NULL,
        descripcion TEXT,
        orden INTEGER DEFAULT 0,
        activo BOOLEAN DEFAULT TRUE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    cur.execute("CREATE INDEX IF NOT EXISTS idx_instalacion_checklist_proyecto ON proyecto_instalacion_checklist_items(proyecto_id)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_instalacion_checklist_activo ON proyecto_instalacion_checklist_items(activo_id)")
    conn.commit()
    cur.close()
    conn.close()

def create_proyecto_instalacion_checklist_completados_table():
    """Crea la tabla de items completados durante una sesión de instalación"""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS proyecto_instalacion_checklist_completados (
        id INT AUTO_INCREMENT PRIMARY KEY,
        sesion_id INTEGER NOT NULL REFERENCES proyecto_instalacion_sesiones(id) ON DELETE CASCADE,
        checklist_item_id INTEGER NOT NULL REFERENCES proyecto_instalacion_checklist_items(id) ON DELETE CASCADE,
        hora_completado TIME,
        observaciones TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(sesion_id, checklist_item_id)
    );
    """)
    cur.execute("CREATE INDEX IF NOT EXISTS idx_instalacion_completados_sesion ON proyecto_instalacion_checklist_completados(sesion_id)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_instalacion_completados_item ON proyecto_instalacion_checklist_completados(checklist_item_id)")
    conn.commit()
    cur.close()
    conn.close()

class Incidencia:
    def __init__(self, id, proyecto_id, activo_id, titulo, descripcion, estado, creador_id, creador_tipo, created_at, updated_at):
        self.id = id
        self.proyecto_id = proyecto_id
        self.activo_id = activo_id
        self.titulo = titulo
        self.descripcion = descripcion
        self.estado = estado
        self.creador_id = creador_id
        self.creador_tipo = creador_tipo
        self.created_at = created_at
        self.updated_at = updated_at

    @staticmethod
    def create(proyecto_id, activo_id=None, titulo=None, descripcion=None, creador_id=None, creador_tipo='cliente'):
        """Crea una nueva incidencia"""
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                INSERT INTO incidencias (proyecto_id, activo_id, titulo, descripcion, creador_id, creador_tipo)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id, proyecto_id, activo_id, titulo, descripcion, estado, creador_id, creador_tipo, created_at, updated_at
            """, (proyecto_id, activo_id, titulo, descripcion, creador_id, creador_tipo))
            incidencia_row = cur.fetchone()
            conn.commit()
            return Incidencia(*incidencia_row)
        except Exception as e:
            conn.rollback()
            return str(e) if str(e) else "Error desconocido al crear incidencia."
        finally:
            cur.close()
            conn.close()

    @staticmethod
    def get_by_id(incidencia_id):
        """Obtiene una incidencia por su ID"""
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT id, proyecto_id, activo_id, titulo, descripcion, estado, creador_id, creador_tipo, created_at, updated_at
            FROM incidencias
            WHERE id = %s
        """, (incidencia_id,))
        incidencia = cur.fetchone()
        cur.close()
        conn.close()
        if incidencia:
            return Incidencia(*incidencia)
        return None

    @staticmethod
    def get_by_proyecto(proyecto_id):
        """Obtiene todas las incidencias de un proyecto"""
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT id, proyecto_id, activo_id, titulo, descripcion, estado, creador_id, creador_tipo, created_at, updated_at
            FROM incidencias
            WHERE proyecto_id = %s
            ORDER BY created_at DESC
        """, (proyecto_id,))
        incidencias = cur.fetchall()
        cur.close()
        conn.close()
        return [Incidencia(*i) for i in incidencias]

    @staticmethod
    def get_all_abiertas():
        """Obtiene todas las incidencias abiertas (para administradores)"""
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT id, proyecto_id, activo_id, titulo, descripcion, estado, creador_id, creador_tipo, created_at, updated_at
            FROM incidencias
            WHERE estado IN ('abierta', 'en_proceso')
            ORDER BY created_at DESC
        """)
        incidencias = cur.fetchall()
        cur.close()
        conn.close()
        return [Incidencia(*i) for i in incidencias]

    def update_estado(self, nuevo_estado):
        """Actualiza el estado de una incidencia"""
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                UPDATE incidencias 
                SET estado = %s, updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (nuevo_estado, self.id))
            conn.commit()
            self.estado = nuevo_estado
            return True
        except Exception as e:
            conn.rollback()
            return False
        finally:
            cur.close()
            conn.close()

    def to_dict(self):
        """Convierte la incidencia a diccionario"""
        # Obtener información del creador
        creador_nombre = None
        creador_tag = None
        if self.creador_tipo == 'user':
            user = User.get_by_id(self.creador_id)
            if user:
                creador_nombre = f"{user.nombre} {user.apellido}"
                creador_tag = user.tag or 'Usuario'
        elif self.creador_tipo == 'cliente':
            cliente = Cliente.get_by_id(self.creador_id)
            if cliente:
                if cliente.tipo_cliente == 'empresa':
                    creador_nombre = cliente.nombre_empresa
                else:
                    creador_nombre = f"{cliente.nombre} {cliente.apellido}"
                creador_tag = 'Cliente'
        
        # Obtener información del activo si existe
        activo_nombre = None
        if self.activo_id:
            activo = Activo.get_by_id(self.activo_id)
            if activo:
                activo_nombre = activo.nombre
        
        # Obtener información del proyecto
        proyecto_nombre = None
        proyecto = Proyecto.get_by_id(self.proyecto_id)
        if proyecto:
            proyecto_nombre = proyecto.nombre
        
        # Mapear estado a display
        estado_display = {
            'abierta': 'Abierta',
            'en_proceso': 'En Proceso',
            'resuelta': 'Resuelta'
        }.get(self.estado, self.estado)
        
        return {
            'id': self.id,
            'proyecto_id': self.proyecto_id,
            'proyecto_nombre': proyecto_nombre,
            'activo_id': self.activo_id,
            'activo_nombre': activo_nombre,
            'titulo': self.titulo,
            'descripcion': self.descripcion,
            'estado': self.estado,
            'estado_display': estado_display,
            'creador_id': self.creador_id,
            'creador_tipo': self.creador_tipo,
            'creador_nombre': creador_nombre,
            'creador_tag': creador_tag,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else '',
            'created_at_date': self.created_at.strftime('%d') if self.created_at else '',
            'created_at_month': self.created_at.strftime('%b') if self.created_at else '',
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else ''
        }

class ComentarioIncidencia:
    def __init__(self, id, incidencia_id, autor_id, tipo_autor, comentario, created_at):
        self.id = id
        self.incidencia_id = incidencia_id
        self.autor_id = autor_id
        self.tipo_autor = tipo_autor
        self.comentario = comentario
        self.created_at = created_at

    @staticmethod
    def create(incidencia_id, autor_id, tipo_autor, comentario):
        """Crea un nuevo comentario para una incidencia"""
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                INSERT INTO incidencia_comentarios (incidencia_id, autor_id, tipo_autor, comentario)
                VALUES (%s, %s, %s, %s)
                RETURNING id, incidencia_id, autor_id, tipo_autor, comentario, created_at
            """, (incidencia_id, autor_id, tipo_autor, comentario))
            comentario_row = cur.fetchone()
            conn.commit()
            return ComentarioIncidencia(*comentario_row)
        except Exception as e:
            conn.rollback()
            return str(e) if str(e) else "Error desconocido al crear comentario."
        finally:
            cur.close()
            conn.close()

    @staticmethod
    def get_by_incidencia(incidencia_id):
        """Obtiene todos los comentarios de una incidencia"""
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT id, incidencia_id, autor_id, tipo_autor, comentario, created_at
            FROM incidencia_comentarios
            WHERE incidencia_id = %s
            ORDER BY created_at ASC
        """, (incidencia_id,))
        comentarios = cur.fetchall()
        cur.close()
        conn.close()
        return [ComentarioIncidencia(*c) for c in comentarios]

    def to_dict(self):
        """Convierte el comentario a diccionario"""
        # Obtener información del autor
        autor_nombre = None
        autor_tag = None
        if self.tipo_autor == 'user':
            user = User.get_by_id(self.autor_id)
            if user:
                autor_nombre = f"{user.nombre} {user.apellido}"
                autor_tag = user.tag or 'Usuario'
        elif self.tipo_autor == 'cliente':
            cliente = Cliente.get_by_id(self.autor_id)
            if cliente:
                if cliente.tipo_cliente == 'empresa':
                    autor_nombre = cliente.nombre_empresa
                else:
                    autor_nombre = f"{cliente.nombre} {cliente.apellido}"
                autor_tag = 'Cliente'
        
        return {
            'id': self.id,
            'incidencia_id': self.incidencia_id,
            'autor_id': self.autor_id,
            'tipo_autor': self.tipo_autor,
            'autor_nombre': autor_nombre,
            'autor_tag': autor_tag,
            'comentario': self.comentario,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else '',
            'created_at_date': self.created_at.strftime('%d') if self.created_at else '',
            'created_at_month': self.created_at.strftime('%b') if self.created_at else ''
        }

class MantenimientoConfig:
    def __init__(self, id, proyecto_id, periodo_visita, incluye_emergencia, periodo_emergencia, created_at, updated_at):
        self.id = id
        self.proyecto_id = proyecto_id
        self.periodo_visita = periodo_visita
        self.incluye_emergencia = incluye_emergencia
        self.periodo_emergencia = periodo_emergencia
        self.created_at = created_at
        self.updated_at = updated_at

    @staticmethod
    def get_by_proyecto(proyecto_id):
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT id, proyecto_id, periodo_visita, incluye_emergencia, periodo_emergencia, created_at, updated_at
            FROM proyecto_mantenimiento_config
            WHERE proyecto_id = %s
        """, (proyecto_id,))
        row = cur.fetchone()
        cur.close()
        conn.close()
        if row:
            return MantenimientoConfig(*row)
        return None

    @staticmethod
    def create_or_update(proyecto_id, periodo_visita, incluye_emergencia=False, periodo_emergencia=None):
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            # Verificar si existe
            cur.execute("SELECT id FROM proyecto_mantenimiento_config WHERE proyecto_id = %s", (proyecto_id,))
            exists = cur.fetchone()
            
            if exists:
                # Actualizar
                cur.execute("""
                    UPDATE proyecto_mantenimiento_config
                    SET periodo_visita = %s, incluye_emergencia = %s, periodo_emergencia = %s, updated_at = CURRENT_TIMESTAMP
                    WHERE proyecto_id = %s
                    RETURNING id, proyecto_id, periodo_visita, incluye_emergencia, periodo_emergencia, created_at, updated_at
                """, (periodo_visita, incluye_emergencia, periodo_emergencia, proyecto_id))
            else:
                # Crear
                cur.execute("""
                    INSERT INTO proyecto_mantenimiento_config (proyecto_id, periodo_visita, incluye_emergencia, periodo_emergencia)
                    VALUES (%s, %s, %s, %s)
                    RETURNING id, proyecto_id, periodo_visita, incluye_emergencia, periodo_emergencia, created_at, updated_at
                """, (proyecto_id, periodo_visita, incluye_emergencia, periodo_emergencia))
            
            row = cur.fetchone()
            conn.commit()
            return MantenimientoConfig(*row)
        except Exception as e:
            conn.rollback()
            return str(e)
        finally:
            cur.close()
            conn.close()

    def to_dict(self):
        return {
            'id': self.id,
            'proyecto_id': self.proyecto_id,
            'periodo_visita': self.periodo_visita,
            'incluye_emergencia': self.incluye_emergencia,
            'periodo_emergencia': self.periodo_emergencia,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else '',
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else ''
        }

class MantenimientoVisita:
    def __init__(self, id, proyecto_id, fecha_visita, tipo_visita, incidencia_id, comentarios, sugerencias, observaciones, creador_id, creador_tipo, created_at, updated_at):
        self.id = id
        self.proyecto_id = proyecto_id
        self.fecha_visita = fecha_visita
        self.tipo_visita = tipo_visita
        self.incidencia_id = incidencia_id
        self.comentarios = comentarios
        self.sugerencias = sugerencias
        self.observaciones = observaciones
        self.creador_id = creador_id
        self.creador_tipo = creador_tipo
        self.created_at = created_at
        self.updated_at = updated_at

    @staticmethod
    def create(proyecto_id, fecha_visita, tipo_visita='programada', incidencia_id=None, comentarios=None, sugerencias=None, observaciones=None, creador_id=None, creador_tipo='user'):
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                INSERT INTO proyecto_mantenimiento_visitas (proyecto_id, fecha_visita, tipo_visita, incidencia_id, comentarios, sugerencias, observaciones, creador_id, creador_tipo)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id, proyecto_id, fecha_visita, tipo_visita, COALESCE(incidencia_id, 0) as incidencia_id, comentarios, sugerencias, observaciones, creador_id, creador_tipo, created_at, updated_at
            """, (proyecto_id, fecha_visita, tipo_visita, incidencia_id, comentarios, sugerencias, observaciones, creador_id, creador_tipo))
            row = cur.fetchone()
            conn.commit()
            return MantenimientoVisita(*row)
        except Exception as e:
            conn.rollback()
            return str(e)
        finally:
            cur.close()
            conn.close()

    @staticmethod
    def get_by_proyecto(proyecto_id):
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT id, proyecto_id, fecha_visita, tipo_visita, COALESCE(incidencia_id, 0) as incidencia_id, comentarios, sugerencias, observaciones, creador_id, creador_tipo, created_at, updated_at
            FROM proyecto_mantenimiento_visitas
            WHERE proyecto_id = %s
            ORDER BY fecha_visita DESC, created_at DESC
        """, (proyecto_id,))
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return [MantenimientoVisita(*row) for row in rows]

    @staticmethod
    def get_by_id(visita_id):
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT id, proyecto_id, fecha_visita, tipo_visita, COALESCE(incidencia_id, 0) as incidencia_id, comentarios, sugerencias, observaciones, creador_id, creador_tipo, created_at, updated_at
            FROM proyecto_mantenimiento_visitas
            WHERE id = %s
        """, (visita_id,))
        row = cur.fetchone()
        cur.close()
        conn.close()
        if row:
            return MantenimientoVisita(*row)
        return None

    def update(self, fecha_visita=None, tipo_visita=None, incidencia_id=None, comentarios=None, sugerencias=None, observaciones=None):
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            updates = []
            params = []
            if fecha_visita is not None:
                updates.append("fecha_visita = %s")
                params.append(fecha_visita)
            if tipo_visita is not None:
                updates.append("tipo_visita = %s")
                params.append(tipo_visita)
            if comentarios is not None:
                updates.append("comentarios = %s")
                params.append(comentarios)
            if sugerencias is not None:
                updates.append("sugerencias = %s")
                params.append(sugerencias)
            if observaciones is not None:
                updates.append("observaciones = %s")
                params.append(observaciones)
            if incidencia_id is not None:
                updates.append("incidencia_id = %s")
                params.append(incidencia_id if incidencia_id != 0 else None)
            
            updates.append("updated_at = CURRENT_TIMESTAMP")
            params.append(self.id)
            
            cur.execute(f"""
                UPDATE proyecto_mantenimiento_visitas SET {', '.join(updates)}
                WHERE id = %s
                RETURNING id, proyecto_id, fecha_visita, tipo_visita, COALESCE(incidencia_id, 0) as incidencia_id, comentarios, sugerencias, observaciones, creador_id, creador_tipo, created_at, updated_at
            """, params)
            row = cur.fetchone()
            conn.commit()
            
            # Recargar datos desde la base de datos para asegurar tipos correctos
            if row:
                self.fecha_visita = row[2]  # fecha_visita desde la BD (tipo date)
                self.tipo_visita = row[3]
                self.incidencia_id = row[4] if row[4] != 0 else None
                self.comentarios = row[5]
                self.sugerencias = row[6]
                self.observaciones = row[7]
            
            return True
        except Exception as e:
            conn.rollback()
            return False
        finally:
            cur.close()
            conn.close()

    def get_activos_vinculados(self):
        """Obtiene los activos vinculados a esta visita"""
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                SELECT a.id, a.proyecto_id, a.nombre, a.tipo, a.estado, a.numero_serie, 
                       a.ubicacion, a.fecha_compra, a.fecha_instalacion, a.valor, 
                       a.asignado_id, a.asignado_tipo, a.asignado, a.cuenta_vinculada, 
                       a.ip, a.password, a.detalles, a.creador_id, a.creador_tipo, 
                       a.created_at, a.updated_at
                FROM activos a
                INNER JOIN proyecto_mantenimiento_visitas_activos pva ON a.id = pva.activo_id
                WHERE pva.visita_id = %s
                ORDER BY a.nombre
            """, (self.id,))
            rows = cur.fetchall()
            return [Activo(*row) for row in rows]
        finally:
            cur.close()
            conn.close()
    
    def vincular_activos(self, activo_ids):
        """Vincula uno o más activos a esta visita"""
        if not activo_ids:
            return True
        
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            # Eliminar vinculaciones existentes
            cur.execute("DELETE FROM proyecto_mantenimiento_visitas_activos WHERE visita_id = %s", (self.id,))
            
            # Agregar nuevas vinculaciones
            for activo_id in activo_ids:
                if activo_id:
                    try:
                        cur.execute("""
                            INSERT IGNORE INTO proyecto_mantenimiento_visitas_activos (visita_id, activo_id)
                            VALUES (%s, %s)
                        """, (self.id, int(activo_id)))
                    except (ValueError, TypeError):
                        continue
            
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            return False
        finally:
            cur.close()
            conn.close()
    
    @staticmethod
    def delete(visita_id):
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            # Eliminar vinculaciones con activos primero (CASCADE debería hacerlo, pero por si acaso)
            cur.execute("DELETE FROM proyecto_mantenimiento_visitas_activos WHERE visita_id = %s", (visita_id,))
            cur.execute("DELETE FROM proyecto_mantenimiento_visitas WHERE id = %s", (visita_id,))
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            return False
        finally:
            cur.close()
            conn.close()

    def to_dict(self):
        # Obtener información del creador
        creador_nombre = "Usuario desconocido"
        if self.creador_tipo == 'user':
            user = User.get_by_id(self.creador_id)
            if user:
                creador_nombre = f"{user.nombre} {user.apellido}"
        elif self.creador_tipo == 'cliente':
            cliente = Cliente.get_by_id(self.creador_id)
            if cliente:
                if cliente.tipo_cliente == 'empresa':
                    creador_nombre = cliente.nombre_empresa
                else:
                    creador_nombre = f"{cliente.nombre} {cliente.apellido}"
        
        # Obtener fotos de la visita
        fotos = MantenimientoFoto.get_by_visita(self.id)
        fotos_dict = [f.to_dict() for f in fotos]
        
        # Obtener información de la incidencia vinculada si existe
        incidencia_info = None
        if self.incidencia_id and self.incidencia_id != 0:
            incidencia = Incidencia.get_by_id(self.incidencia_id)
            if incidencia:
                incidencia_info = {
                    'id': incidencia.id,
                    'titulo': incidencia.titulo,
                    'estado': incidencia.estado
                }
        
        # Obtener activos vinculados a la visita
        activos_vinculados = self.get_activos_vinculados()
        activos_dict = [a.to_dict() for a in activos_vinculados]
        
        # Obtener respuestas de checklist con items completos
        checklist_respuestas = MantenimientoChecklistRespuesta.get_by_visita(self.id)
        checklist_respuestas_dict = {}
        for respuesta in checklist_respuestas:
            item = MantenimientoChecklistItem.get_by_id(respuesta.checklist_item_id)
            if item:
                checklist_respuestas_dict[respuesta.checklist_item_id] = {
                    'item': item.to_dict(),
                    'respuesta': respuesta.to_dict()
                }
        
        # Manejar fecha_visita que puede ser date o string
        if self.fecha_visita:
            if isinstance(self.fecha_visita, str):
                # Si es string, ya está en formato correcto o necesita parseo
                fecha_visita_str = self.fecha_visita
                # Intentar convertir a date para el display
                try:
                    from datetime import datetime
                    fecha_obj = datetime.strptime(self.fecha_visita, '%Y-%m-%d').date()
                    fecha_visita_display = fecha_obj.strftime('%d-%m-%Y')
                except (ValueError, AttributeError):
                    fecha_visita_display = self.fecha_visita
            else:
                # Si es date/datetime
                fecha_visita_str = self.fecha_visita.strftime('%Y-%m-%d')
                fecha_visita_display = self.fecha_visita.strftime('%d-%m-%Y')
        else:
            fecha_visita_str = ''
            fecha_visita_display = ''
        
        return {
            'id': self.id,
            'proyecto_id': self.proyecto_id,
            'fecha_visita': fecha_visita_str,
            'fecha_visita_display': fecha_visita_display,
            'tipo_visita': self.tipo_visita,
            'incidencia_id': self.incidencia_id if self.incidencia_id and self.incidencia_id != 0 else None,
            'incidencia': incidencia_info,
            'activos': activos_dict,
            'comentarios': self.comentarios,
            'sugerencias': self.sugerencias,
            'observaciones': self.observaciones,
            'creador_id': self.creador_id,
            'creador_tipo': self.creador_tipo,
            'creador_nombre': creador_nombre,
            'fotos': fotos_dict,
            'checklist_respuestas': checklist_respuestas_dict,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at and hasattr(self.created_at, 'strftime') else (str(self.created_at) if self.created_at else ''),
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at and hasattr(self.updated_at, 'strftime') else (str(self.updated_at) if self.updated_at else '')
        }

class MantenimientoFoto:
    def __init__(self, id, visita_id, ruta_archivo, descripcion, created_at):
        self.id = id
        self.visita_id = visita_id
        self.ruta_archivo = ruta_archivo
        self.descripcion = descripcion
        self.created_at = created_at

    @staticmethod
    def create(visita_id, ruta_archivo, descripcion=None):
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                INSERT INTO proyecto_mantenimiento_fotos (visita_id, ruta_archivo, descripcion)
                VALUES (%s, %s, %s)
                RETURNING id, visita_id, ruta_archivo, descripcion, created_at
            """, (visita_id, ruta_archivo, descripcion))
            row = cur.fetchone()
            conn.commit()
            return MantenimientoFoto(*row)
        except Exception as e:
            conn.rollback()
            return str(e)
        finally:
            cur.close()
            conn.close()

    @staticmethod
    def get_by_visita(visita_id):
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT id, visita_id, ruta_archivo, descripcion, created_at
            FROM proyecto_mantenimiento_fotos
            WHERE visita_id = %s
            ORDER BY created_at ASC
        """, (visita_id,))
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return [MantenimientoFoto(*row) for row in rows]

    @staticmethod
    def delete(foto_id):
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("DELETE FROM proyecto_mantenimiento_fotos WHERE id = %s", (foto_id,))
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            return False
        finally:
            cur.close()
            conn.close()

    def to_dict(self):
        return {
            'id': self.id,
            'visita_id': self.visita_id,
            'ruta_archivo': self.ruta_archivo,
            'descripcion': self.descripcion,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else ''
        }

class MantenimientoChecklistItem:
    def __init__(self, id, proyecto_id, titulo, descripcion, categoria, orden, activo, created_at, updated_at):
        self.id = id
        self.proyecto_id = proyecto_id
        self.titulo = titulo
        self.descripcion = descripcion
        self.categoria = categoria
        self.orden = orden if orden else 0
        self.activo = activo if isinstance(activo, bool) else (activo == True or activo == 't' or activo == 'true')
        self.created_at = created_at
        self.updated_at = updated_at

    @staticmethod
    def create(proyecto_id, titulo, descripcion=None, categoria=None, orden=0):
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                INSERT INTO proyecto_mantenimiento_checklist_items (proyecto_id, titulo, descripcion, categoria, orden, activo)
                VALUES (%s, %s, %s, %s, %s, TRUE)
                RETURNING id, proyecto_id, titulo, descripcion, categoria, orden, activo, created_at, updated_at
            """, (proyecto_id, titulo, descripcion, categoria, orden))
            row = cur.fetchone()
            conn.commit()
            return MantenimientoChecklistItem(*row)
        except Exception as e:
            conn.rollback()
            return str(e)
        finally:
            cur.close()
            conn.close()

    @staticmethod
    def get_by_proyecto(proyecto_id, solo_activos=True):
        conn = get_db_connection()
        cur = conn.cursor()
        query = """
            SELECT id, proyecto_id, titulo, descripcion, categoria, orden, activo, created_at, updated_at
            FROM proyecto_mantenimiento_checklist_items
            WHERE proyecto_id = %s
        """
        if solo_activos:
            query += " AND activo = TRUE"
        query += " ORDER BY categoria, orden, titulo"
        cur.execute(query, (proyecto_id,))
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return [MantenimientoChecklistItem(*row) for row in rows]

    @staticmethod
    def get_by_id(item_id):
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT id, proyecto_id, titulo, descripcion, categoria, orden, activo, created_at, updated_at
            FROM proyecto_mantenimiento_checklist_items
            WHERE id = %s
        """, (item_id,))
        row = cur.fetchone()
        cur.close()
        conn.close()
        if row:
            return MantenimientoChecklistItem(*row)
        return None

    def update(self, titulo=None, descripcion=None, categoria=None, orden=None, activo=None):
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            updates = []
            params = []
            if titulo is not None:
                updates.append("titulo = %s")
                params.append(titulo)
            if descripcion is not None:
                updates.append("descripcion = %s")
                params.append(descripcion)
            if categoria is not None:
                updates.append("categoria = %s")
                params.append(categoria)
            if orden is not None:
                updates.append("orden = %s")
                params.append(orden)
            if activo is not None:
                updates.append("activo = %s")
                params.append(activo)
            
            updates.append("updated_at = CURRENT_TIMESTAMP")
            params.append(self.id)
            
            cur.execute(f"""
                UPDATE proyecto_mantenimiento_checklist_items SET {', '.join(updates)}
                WHERE id = %s
            """, params)
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            return False
        finally:
            cur.close()
            conn.close()

    @staticmethod
    def delete(item_id):
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("DELETE FROM proyecto_mantenimiento_checklist_items WHERE id = %s", (item_id,))
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            return False
        finally:
            cur.close()
            conn.close()

    def to_dict(self):
        return {
            'id': self.id,
            'proyecto_id': self.proyecto_id,
            'titulo': self.titulo,
            'descripcion': self.descripcion,
            'categoria': self.categoria,
            'orden': self.orden,
            'activo': self.activo
        }

class MantenimientoChecklistRespuesta:
    def __init__(self, id, visita_id, checklist_item_id, completado, comentario, created_at, updated_at):
        self.id = id
        self.visita_id = visita_id
        self.checklist_item_id = checklist_item_id
        self.completado = completado if isinstance(completado, bool) else (completado == True or completado == 't' or completado == 'true')
        self.comentario = comentario
        self.created_at = created_at
        self.updated_at = updated_at

    @staticmethod
    def create_or_update(visita_id, checklist_item_id, completado=False, comentario=None):
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                INSERT INTO proyecto_mantenimiento_checklist_respuestas (visita_id, checklist_item_id, completado, comentario)
                VALUES (%s, %s, %s, %s) AS new
                ON DUPLICATE KEY UPDATE
                    completado = new.completado,
                    comentario = new.comentario,
                    updated_at = CURRENT_TIMESTAMP
                RETURNING id, visita_id, checklist_item_id, completado, comentario, created_at, updated_at
            """, (visita_id, checklist_item_id, completado, comentario))
            row = cur.fetchone()
            conn.commit()
            return MantenimientoChecklistRespuesta(*row)
        except Exception as e:
            conn.rollback()
            return str(e)
        finally:
            cur.close()
            conn.close()

    @staticmethod
    def get_by_visita(visita_id):
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT id, visita_id, checklist_item_id, completado, comentario, created_at, updated_at
            FROM proyecto_mantenimiento_checklist_respuestas
            WHERE visita_id = %s
        """, (visita_id,))
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return [MantenimientoChecklistRespuesta(*row) for row in rows]

    @staticmethod
    def get_by_visita_item(visita_id, checklist_item_id):
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT id, visita_id, checklist_item_id, completado, comentario, created_at, updated_at
            FROM proyecto_mantenimiento_checklist_respuestas
            WHERE visita_id = %s AND checklist_item_id = %s
        """, (visita_id, checklist_item_id))
        row = cur.fetchone()
        cur.close()
        conn.close()
        if row:
            return MantenimientoChecklistRespuesta(*row)
        return None

    def to_dict(self):
        return {
            'id': self.id,
            'visita_id': self.visita_id,
            'checklist_item_id': self.checklist_item_id,
            'completado': self.completado,
            'comentario': self.comentario
        }

class InstalacionSesion:
    """Modelo para sesiones de instalación del proyecto"""
    def __init__(self, id, proyecto_id, fecha, hora_llegada, hora_salida, instalador_id, observaciones, created_at, updated_at):
        self.id = id
        self.proyecto_id = proyecto_id
        self.fecha = fecha
        self.hora_llegada = hora_llegada
        self.hora_salida = hora_salida
        self.instalador_id = instalador_id
        self.observaciones = observaciones
        self.created_at = created_at
        self.updated_at = updated_at
    
    @staticmethod
    def create(proyecto_id, fecha, instalador_id, hora_llegada=None, hora_salida=None, observaciones=None):
        """Crea una nueva sesión de instalación"""
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                INSERT INTO proyecto_instalacion_sesiones (proyecto_id, fecha, hora_llegada, hora_salida, instalador_id, observaciones)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id, proyecto_id, fecha, hora_llegada, hora_salida, instalador_id, observaciones, created_at, updated_at
            """, (proyecto_id, fecha, hora_llegada, hora_salida, instalador_id, observaciones))
            row = cur.fetchone()
            conn.commit()
            return InstalacionSesion(*row)
        except Exception as e:
            conn.rollback()
            return str(e)
        finally:
            cur.close()
            conn.close()
    
    @staticmethod
    def get_by_proyecto(proyecto_id):
        """Obtiene todas las sesiones de un proyecto"""
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT id, proyecto_id, fecha, hora_llegada, hora_salida, instalador_id, observaciones, created_at, updated_at
            FROM proyecto_instalacion_sesiones
            WHERE proyecto_id = %s
            ORDER BY fecha DESC, hora_llegada DESC
        """, (proyecto_id,))
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return [InstalacionSesion(*row) for row in rows]
    
    @staticmethod
    def get_by_id(sesion_id):
        """Obtiene una sesión por su ID"""
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT id, proyecto_id, fecha, hora_llegada, hora_salida, instalador_id, observaciones, created_at, updated_at
            FROM proyecto_instalacion_sesiones
            WHERE id = %s
        """, (sesion_id,))
        row = cur.fetchone()
        cur.close()
        conn.close()
        if row:
            return InstalacionSesion(*row)
        return None
    
    def update(self, fecha=None, hora_llegada=None, hora_salida=None, observaciones=None):
        """Actualiza una sesión de instalación"""
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            updates = []
            params = []
            if fecha is not None:
                updates.append("fecha = %s")
                params.append(fecha)
            if hora_llegada is not None:
                updates.append("hora_llegada = %s")
                params.append(hora_llegada)
            if hora_salida is not None:
                updates.append("hora_salida = %s")
                params.append(hora_salida)
            if observaciones is not None:
                updates.append("observaciones = %s")
                params.append(observaciones)
            
            updates.append("updated_at = CURRENT_TIMESTAMP")
            params.append(self.id)
            
            cur.execute(f"""
                UPDATE proyecto_instalacion_sesiones SET {', '.join(updates)}
                WHERE id = %s
                RETURNING id, proyecto_id, fecha, hora_llegada, hora_salida, instalador_id, observaciones, created_at, updated_at
            """, params)
            row = cur.fetchone()
            conn.commit()
            
            if row:
                self.fecha = row[2]
                self.hora_llegada = row[3]
                self.hora_salida = row[4]
                self.observaciones = row[6]
            
            return True
        except Exception as e:
            conn.rollback()
            return False
        finally:
            cur.close()
            conn.close()
    
    @staticmethod
    def delete(sesion_id):
        """Elimina una sesión de instalación"""
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("DELETE FROM proyecto_instalacion_sesiones WHERE id = %s", (sesion_id,))
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            return False
        finally:
            cur.close()
            conn.close()
    
    def calcular_tiempo_total(self):
        """Calcula el tiempo total de la sesión en minutos"""
        if self.hora_llegada and self.hora_salida:
            from datetime import datetime, timedelta
            if isinstance(self.hora_llegada, str):
                hora_llegada = datetime.strptime(self.hora_llegada, '%H:%M:%S').time()
            else:
                hora_llegada = self.hora_llegada
            
            if isinstance(self.hora_salida, str):
                hora_salida = datetime.strptime(self.hora_salida, '%H:%M:%S').time()
            else:
                hora_salida = self.hora_salida
            
            llegada_dt = datetime.combine(self.fecha, hora_llegada)
            salida_dt = datetime.combine(self.fecha, hora_salida)
            if salida_dt < llegada_dt:
                salida_dt += timedelta(days=1)
            
            diff = salida_dt - llegada_dt
            return diff.total_seconds() / 60  # Retorna en minutos
        return 0
    
    def to_dict(self):
        """Convierte la sesión a diccionario"""
        instalador = User.get_by_id(self.instalador_id)
        instalador_nombre = ""
        if instalador:
            instalador_nombre = f"{instalador.nombre} {instalador.apellido}".strip() or instalador.username or instalador.email
        
        tiempo_total_minutos = self.calcular_tiempo_total()
        horas = int(tiempo_total_minutos // 60)
        minutos = int(tiempo_total_minutos % 60)
        
        hora_llegada_str = None
        hora_salida_str = None
        if self.hora_llegada:
            if isinstance(self.hora_llegada, str):
                hora_llegada_str = self.hora_llegada[:5] if len(self.hora_llegada) >= 5 else self.hora_llegada
            else:
                hora_llegada_str = self.hora_llegada.strftime('%H:%M')
        
        if self.hora_salida:
            if isinstance(self.hora_salida, str):
                hora_salida_str = self.hora_salida[:5] if len(self.hora_salida) >= 5 else self.hora_salida
            else:
                hora_salida_str = self.hora_salida.strftime('%H:%M')
        
        fecha_str = None
        if self.fecha:
            if isinstance(self.fecha, str):
                fecha_str = self.fecha
            else:
                fecha_str = self.fecha.strftime('%Y-%m-%d')
        
        return {
            'id': self.id,
            'proyecto_id': self.proyecto_id,
            'fecha': fecha_str,
            'hora_llegada': hora_llegada_str,
            'hora_salida': hora_salida_str,
            'instalador_id': self.instalador_id,
            'instalador_nombre': instalador_nombre,
            'observaciones': self.observaciones,
            'tiempo_total_minutos': tiempo_total_minutos,
            'tiempo_total_horas': horas,
            'tiempo_total_minutos_restantes': minutos,
            'tiempo_total_display': f"{horas}h {minutos}min" if horas > 0 else f"{minutos}min",
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at and hasattr(self.created_at, 'strftime') else (str(self.created_at) if self.created_at else ''),
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at and hasattr(self.updated_at, 'strftime') else (str(self.updated_at) if self.updated_at else '')
        }

class InstalacionChecklistItem:
    """Modelo para items del checklist de instalación"""
    def __init__(self, id, proyecto_id, activo_id, presupuesto_item_id, titulo, descripcion, orden, activo, created_at, updated_at):
        self.id = id
        self.proyecto_id = proyecto_id
        self.activo_id = activo_id
        self.presupuesto_item_id = presupuesto_item_id
        self.titulo = titulo
        self.descripcion = descripcion
        self.orden = orden
        self.activo = activo
        self.created_at = created_at
        self.updated_at = updated_at
    
    @staticmethod
    def create(proyecto_id, titulo, descripcion=None, activo_id=None, presupuesto_item_id=None, orden=0):
        """Crea un nuevo item del checklist"""
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                INSERT INTO proyecto_instalacion_checklist_items (proyecto_id, activo_id, presupuesto_item_id, titulo, descripcion, orden, activo)
                VALUES (%s, %s, %s, %s, %s, %s, TRUE)
                RETURNING id, proyecto_id, activo_id, presupuesto_item_id, titulo, descripcion, orden, activo, created_at, updated_at
            """, (proyecto_id, activo_id, presupuesto_item_id, titulo, descripcion, orden))
            row = cur.fetchone()
            conn.commit()
            return InstalacionChecklistItem(*row)
        except Exception as e:
            conn.rollback()
            return str(e)
        finally:
            cur.close()
            conn.close()
    
    @staticmethod
    def get_by_proyecto(proyecto_id, solo_activos=True):
        """Obtiene todos los items del checklist de un proyecto"""
        conn = get_db_connection()
        cur = conn.cursor()
        query = """
            SELECT id, proyecto_id, activo_id, presupuesto_item_id, titulo, descripcion, orden, activo, created_at, updated_at
            FROM proyecto_instalacion_checklist_items
            WHERE proyecto_id = %s
        """
        if solo_activos:
            query += " AND activo = TRUE"
        query += " ORDER BY orden, titulo"
        cur.execute(query, (proyecto_id,))
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return [InstalacionChecklistItem(*row) for row in rows]
    
    @staticmethod
    def get_by_id(item_id):
        """Obtiene un item por su ID"""
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT id, proyecto_id, activo_id, presupuesto_item_id, titulo, descripcion, orden, activo, created_at, updated_at
            FROM proyecto_instalacion_checklist_items
            WHERE id = %s
        """, (item_id,))
        row = cur.fetchone()
        cur.close()
        conn.close()
        if row:
            return InstalacionChecklistItem(*row)
        return None
    
    def update(self, titulo=None, descripcion=None, activo_id=None, presupuesto_item_id=None, orden=None, activo=None):
        """Actualiza un item del checklist"""
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            updates = []
            params = []
            if titulo is not None:
                updates.append("titulo = %s")
                params.append(titulo)
            if descripcion is not None:
                updates.append("descripcion = %s")
                params.append(descripcion)
            if activo_id is not None:
                updates.append("activo_id = %s")
                params.append(activo_id)
            if presupuesto_item_id is not None:
                updates.append("presupuesto_item_id = %s")
                params.append(presupuesto_item_id)
            if orden is not None:
                updates.append("orden = %s")
                params.append(orden)
            if activo is not None:
                updates.append("activo = %s")
                params.append(activo)
            
            updates.append("updated_at = CURRENT_TIMESTAMP")
            params.append(self.id)
            
            cur.execute(f"""
                UPDATE proyecto_instalacion_checklist_items SET {', '.join(updates)}
                WHERE id = %s
                RETURNING id, proyecto_id, activo_id, presupuesto_item_id, titulo, descripcion, orden, activo, created_at, updated_at
            """, params)
            row = cur.fetchone()
            conn.commit()
            
            if row:
                self.titulo = row[4]
                self.descripcion = row[5]
                self.activo_id = row[2]
                self.presupuesto_item_id = row[3]
                self.orden = row[6]
                self.activo = row[7]
            
            return True
        except Exception as e:
            conn.rollback()
            return False
        finally:
            cur.close()
            conn.close()
    
    @staticmethod
    def delete(item_id):
        """Elimina un item del checklist"""
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("DELETE FROM proyecto_instalacion_checklist_items WHERE id = %s", (item_id,))
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            return False
        finally:
            cur.close()
            conn.close()
    
    def to_dict(self):
        """Convierte el item a diccionario"""
        activo_info = None
        if self.activo_id:
            activo = Activo.get_by_id(self.activo_id)
            if activo:
                activo_info = activo.to_dict()
        
        presupuesto_item_info = None
        if self.presupuesto_item_id:
            presupuesto_item = PresupuestoItem.get_by_id(self.presupuesto_item_id)
            if presupuesto_item:
                presupuesto_item_info = presupuesto_item.to_dict()
        
        return {
            'id': self.id,
            'proyecto_id': self.proyecto_id,
            'activo_id': self.activo_id,
            'activo_info': activo_info,
            'presupuesto_item_id': self.presupuesto_item_id,
            'presupuesto_item_info': presupuesto_item_info,
            'titulo': self.titulo,
            'descripcion': self.descripcion,
            'orden': self.orden,
            'activo': self.activo,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at and hasattr(self.created_at, 'strftime') else (str(self.created_at) if self.created_at else ''),
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at and hasattr(self.updated_at, 'strftime') else (str(self.updated_at) if self.updated_at else '')
        }

class InstalacionChecklistCompletado:
    """Modelo para items completados durante una sesión"""
    def __init__(self, id, sesion_id, checklist_item_id, hora_completado, observaciones, created_at):
        self.id = id
        self.sesion_id = sesion_id
        self.checklist_item_id = checklist_item_id
        self.hora_completado = hora_completado
        self.observaciones = observaciones
        self.created_at = created_at
    
    @staticmethod
    def create_or_update(sesion_id, checklist_item_id, hora_completado=None, observaciones=None):
        """Crea o actualiza un item completado"""
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                INSERT INTO proyecto_instalacion_checklist_completados (sesion_id, checklist_item_id, hora_completado, observaciones)
                VALUES (%s, %s, %s, %s) AS new
                ON DUPLICATE KEY UPDATE
                    hora_completado = new.hora_completado,
                    observaciones = new.observaciones
                RETURNING id, sesion_id, checklist_item_id, hora_completado, observaciones, created_at
            """, (sesion_id, checklist_item_id, hora_completado, observaciones))
            row = cur.fetchone()
            conn.commit()
            return InstalacionChecklistCompletado(*row)
        except Exception as e:
            conn.rollback()
            return str(e)
        finally:
            cur.close()
            conn.close()
    
    @staticmethod
    def get_by_sesion(sesion_id):
        """Obtiene todos los items completados de una sesión"""
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT id, sesion_id, checklist_item_id, hora_completado, observaciones, created_at
            FROM proyecto_instalacion_checklist_completados
            WHERE sesion_id = %s
        """, (sesion_id,))
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return [InstalacionChecklistCompletado(*row) for row in rows]
    
    @staticmethod
    def delete(sesion_id, checklist_item_id):
        """Elimina un item completado"""
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                DELETE FROM proyecto_instalacion_checklist_completados 
                WHERE sesion_id = %s AND checklist_item_id = %s
            """, (sesion_id, checklist_item_id))
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            return False
        finally:
            cur.close()
            conn.close()
    
    def to_dict(self):
        """Convierte a diccionario"""
        hora_completado_str = None
        if self.hora_completado:
            if isinstance(self.hora_completado, str):
                hora_completado_str = self.hora_completado[:5] if len(self.hora_completado) >= 5 else self.hora_completado
            else:
                hora_completado_str = self.hora_completado.strftime('%H:%M')
        
        return {
            'id': self.id,
            'sesion_id': self.sesion_id,
            'checklist_item_id': self.checklist_item_id,
            'hora_completado': hora_completado_str,
            'observaciones': self.observaciones,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at and hasattr(self.created_at, 'strftime') else (str(self.created_at) if self.created_at else '')
        }

def create_proyecto_documentos_table():
    """Crea la tabla de documentos del proyecto"""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS proyecto_documentos (
        id INT AUTO_INCREMENT PRIMARY KEY,
        proyecto_id INTEGER NOT NULL REFERENCES proyectos(id) ON DELETE CASCADE,
        nombre_archivo VARCHAR(500) NOT NULL,
        nombre_display VARCHAR(500) NOT NULL,
        ruta_archivo VARCHAR(500) NOT NULL,
        tipo_archivo VARCHAR(100),
        tamano_archivo BIGINT,
        creador_id INTEGER NOT NULL,
        creador_tipo VARCHAR(20) NOT NULL,
        descripcion TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    conn.commit()
    cur.close()
    conn.close()

class DocumentoProyecto:
    def __init__(self, id, proyecto_id, nombre_archivo, nombre_display, ruta_archivo, tipo_archivo, tamano_archivo, creador_id, creador_tipo, descripcion, created_at):
        self.id = id
        self.proyecto_id = proyecto_id
        self.nombre_archivo = nombre_archivo
        self.nombre_display = nombre_display
        self.ruta_archivo = ruta_archivo
        self.tipo_archivo = tipo_archivo
        self.tamano_archivo = tamano_archivo
        self.creador_id = creador_id
        self.creador_tipo = creador_tipo
        self.descripcion = descripcion
        self.created_at = created_at

    @staticmethod
    def create(proyecto_id, nombre_archivo, nombre_display, ruta_archivo, tipo_archivo, tamano_archivo, creador_id, creador_tipo, descripcion=None):
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                INSERT INTO proyecto_documentos (proyecto_id, nombre_archivo, nombre_display, ruta_archivo, tipo_archivo, tamano_archivo, creador_id, creador_tipo, descripcion)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id, proyecto_id, nombre_archivo, nombre_display, ruta_archivo, tipo_archivo, tamano_archivo, creador_id, creador_tipo, descripcion, created_at
            """, (proyecto_id, nombre_archivo, nombre_display, ruta_archivo, tipo_archivo, tamano_archivo, creador_id, creador_tipo, descripcion))
            row = cur.fetchone()
            conn.commit()
            return DocumentoProyecto(*row)
        except Exception as e:
            conn.rollback()
            return str(e)
        finally:
            cur.close()
            conn.close()

    @staticmethod
    def get_by_proyecto(proyecto_id):
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT id, proyecto_id, nombre_archivo, nombre_display, ruta_archivo, tipo_archivo, tamano_archivo, creador_id, creador_tipo, descripcion, created_at
            FROM proyecto_documentos
            WHERE proyecto_id = %s
            ORDER BY created_at DESC
        """, (proyecto_id,))
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return [DocumentoProyecto(*row) for row in rows]

    @staticmethod
    def get_by_id(documento_id):
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT id, proyecto_id, nombre_archivo, nombre_display, ruta_archivo, tipo_archivo, tamano_archivo, creador_id, creador_tipo, descripcion, created_at
            FROM proyecto_documentos
            WHERE id = %s
        """, (documento_id,))
        row = cur.fetchone()
        cur.close()
        conn.close()
        if row:
            return DocumentoProyecto(*row)
        return None

    @staticmethod
    def delete(documento_id):
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("DELETE FROM proyecto_documentos WHERE id = %s", (documento_id,))
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            return False
        finally:
            cur.close()
            conn.close()

    def to_dict(self):
        # Obtener información del creador
        creador_nombre = 'Usuario desconocido'
        if self.creador_tipo == 'user':
            user = User.get_by_id(self.creador_id)
            if user:
                creador_nombre = f"{user.nombre} {user.apellido}".strip() or user.username or user.email
        elif self.creador_tipo == 'cliente':
            cliente = Cliente.get_by_id(self.creador_id)
            if cliente:
                if cliente.tipo_cliente == 'empresa':
                    creador_nombre = cliente.nombre_empresa or f"{cliente.nombre} {cliente.apellido}".strip()
                else:
                    creador_nombre = f"{cliente.nombre} {cliente.apellido}".strip()
        
        # Formatear tamaño del archivo
        tamano_display = self.format_file_size(self.tamano_archivo) if self.tamano_archivo else 'N/A'
        
        return {
            'id': self.id,
            'proyecto_id': self.proyecto_id,
            'nombre_archivo': self.nombre_archivo,
            'nombre_display': self.nombre_display,
            'ruta_archivo': self.ruta_archivo,
            'tipo_archivo': self.tipo_archivo,
            'tamano_archivo': self.tamano_archivo,
            'tamano_display': tamano_display,
            'creador_id': self.creador_id,
            'creador_tipo': self.creador_tipo,
            'creador_nombre': creador_nombre,
            'descripcion': self.descripcion,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else '',
            'created_at_display': self.created_at.strftime('%d/%m/%Y %H:%M') if self.created_at else ''
        }
    
    @staticmethod
    def format_file_size(size_bytes):
        """Formatea el tamaño del archivo en formato legible"""
        if size_bytes is None:
            return 'N/A'
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} TB"

def create_proyecto_valoraciones_table():
    """Crea la tabla de valoraciones/feedback de clientes sobre proyectos"""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS proyecto_valoraciones (
        id INT AUTO_INCREMENT PRIMARY KEY,
        proyecto_id INTEGER NOT NULL REFERENCES proyectos(id) ON DELETE CASCADE,
        cliente_id INTEGER NOT NULL,
        calificacion INTEGER NOT NULL CHECK (calificacion >= 1 AND calificacion <= 5),
        comentarios TEXT,
        sugerencias TEXT,
        aspectos_positivos TEXT,
        aspectos_mejora TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(proyecto_id, cliente_id)
    );
    """)
    cur.execute("CREATE INDEX IF NOT EXISTS idx_valoraciones_proyecto ON proyecto_valoraciones(proyecto_id)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_valoraciones_cliente ON proyecto_valoraciones(cliente_id)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_valoraciones_created_at ON proyecto_valoraciones(created_at DESC)")
    conn.commit()
    cur.close()
    conn.close()

class ProyectoValoracion:
    def __init__(self, id, proyecto_id, cliente_id, calificacion, comentarios, sugerencias, aspectos_positivos, aspectos_mejora, created_at, updated_at):
        self.id = id
        self.proyecto_id = proyecto_id
        self.cliente_id = cliente_id
        self.calificacion = calificacion
        self.comentarios = comentarios
        self.sugerencias = sugerencias
        self.aspectos_positivos = aspectos_positivos
        self.aspectos_mejora = aspectos_mejora
        self.created_at = created_at
        self.updated_at = updated_at

    @staticmethod
    def create(proyecto_id, cliente_id, calificacion, comentarios=None, sugerencias=None, aspectos_positivos=None, aspectos_mejora=None):
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                INSERT INTO proyecto_valoraciones (proyecto_id, cliente_id, calificacion, comentarios, sugerencias, aspectos_positivos, aspectos_mejora)
                VALUES (%s, %s, %s, %s, %s, %s, %s) AS new
                ON DUPLICATE KEY UPDATE
                    calificacion = new.calificacion,
                    comentarios = new.comentarios,
                    sugerencias = new.sugerencias,
                    aspectos_positivos = new.aspectos_positivos,
                    aspectos_mejora = new.aspectos_mejora,
                    updated_at = CURRENT_TIMESTAMP
                RETURNING id, proyecto_id, cliente_id, calificacion, comentarios, sugerencias, aspectos_positivos, aspectos_mejora, created_at, updated_at
            """, (proyecto_id, cliente_id, calificacion, comentarios, sugerencias, aspectos_positivos, aspectos_mejora))
            row = cur.fetchone()
            conn.commit()
            return ProyectoValoracion(*row)
        except Exception as e:
            conn.rollback()
            return str(e)
        finally:
            cur.close()
            conn.close()

    @staticmethod
    def get_by_proyecto(proyecto_id):
        """Obtiene todas las valoraciones de un proyecto"""
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT id, proyecto_id, cliente_id, calificacion, comentarios, sugerencias, aspectos_positivos, aspectos_mejora, created_at, updated_at
            FROM proyecto_valoraciones
            WHERE proyecto_id = %s
            ORDER BY created_at DESC
        """, (proyecto_id,))
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return [ProyectoValoracion(*row) for row in rows]

    @staticmethod
    def get_by_cliente_proyecto(proyecto_id, cliente_id):
        """Obtiene la valoración de un cliente específico para un proyecto"""
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT id, proyecto_id, cliente_id, calificacion, comentarios, sugerencias, aspectos_positivos, aspectos_mejora, created_at, updated_at
            FROM proyecto_valoraciones
            WHERE proyecto_id = %s AND cliente_id = %s
        """, (proyecto_id, cliente_id))
        row = cur.fetchone()
        cur.close()
        conn.close()
        if row:
            return ProyectoValoracion(*row)
        return None

    @staticmethod
    def get_all(limit=1000, offset=0, proyecto_id=None, cliente_id=None):
        """Obtiene todas las valoraciones con filtros opcionales"""
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            query = """
                SELECT id, proyecto_id, cliente_id, calificacion, comentarios, sugerencias, aspectos_positivos, aspectos_mejora, created_at, updated_at
                FROM proyecto_valoraciones
                WHERE 1=1
            """
            params = []
            
            if proyecto_id:
                query += " AND proyecto_id = %s"
                params.append(proyecto_id)
            if cliente_id:
                query += " AND cliente_id = %s"
                params.append(cliente_id)
            
            query += " ORDER BY created_at DESC LIMIT %s OFFSET %s"
            params.extend([limit, offset])
            
            cur.execute(query, params)
            rows = cur.fetchall()
            return [ProyectoValoracion(*row) for row in rows]
        finally:
            cur.close()
            conn.close()

    @staticmethod
    def get_count(proyecto_id=None, cliente_id=None):
        """Obtiene el conteo de valoraciones"""
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            query = "SELECT COUNT(*) FROM proyecto_valoraciones WHERE 1=1"
            params = []
            
            if proyecto_id:
                query += " AND proyecto_id = %s"
                params.append(proyecto_id)
            if cliente_id:
                query += " AND cliente_id = %s"
                params.append(cliente_id)
            
            cur.execute(query, params)
            count = cur.fetchone()[0]
            return count
        finally:
            cur.close()
            conn.close()

    def to_dict(self):
        # Obtener información del cliente
        cliente = Cliente.get_by_id(self.cliente_id)
        cliente_nombre = 'Cliente desconocido'
        if cliente:
            if cliente.tipo_cliente == 'empresa':
                cliente_nombre = cliente.nombre_empresa
            else:
                cliente_nombre = f"{cliente.nombre} {cliente.apellido}"
        
        # Obtener información del proyecto
        proyecto = Proyecto.get_by_id(self.proyecto_id)
        proyecto_nombre = proyecto.nombre if proyecto else 'Proyecto desconocido'
        
        return {
            'id': self.id,
            'proyecto_id': self.proyecto_id,
            'proyecto_nombre': proyecto_nombre,
            'cliente_id': self.cliente_id,
            'cliente_nombre': cliente_nombre,
            'calificacion': self.calificacion,
            'comentarios': self.comentarios,
            'sugerencias': self.sugerencias,
            'aspectos_positivos': self.aspectos_positivos,
            'aspectos_mejora': self.aspectos_mejora,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else '',
            'created_at_display': self.created_at.strftime('%d/%m/%Y %H:%M:%S') if self.created_at else '',
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else ''
        }

def create_user_logs_table():
    """Crea la tabla de logs de acciones de usuarios y clientes"""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS user_logs (
        id INT AUTO_INCREMENT PRIMARY KEY,
        usuario_id INTEGER,
        usuario_tipo VARCHAR(20) NOT NULL,
        usuario_nombre VARCHAR(200),
        accion VARCHAR(100) NOT NULL,
        descripcion TEXT,
        ruta VARCHAR(500),
        metodo VARCHAR(10),
        ip_address VARCHAR(50),
        user_agent TEXT,
        datos_adicionales JSON,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    cur.execute("CREATE INDEX IF NOT EXISTS idx_user_logs_usuario ON user_logs(usuario_id, usuario_tipo)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_user_logs_created_at ON user_logs(created_at DESC)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_user_logs_accion ON user_logs(accion)")
    conn.commit()
    cur.close()
    conn.close()

class UserLog:
    def __init__(self, id, usuario_id, usuario_tipo, usuario_nombre, accion, descripcion, ruta, metodo, ip_address, user_agent, datos_adicionales, created_at):
        self.id = id
        self.usuario_id = usuario_id
        self.usuario_tipo = usuario_tipo
        self.usuario_nombre = usuario_nombre
        self.accion = accion
        self.descripcion = descripcion
        self.ruta = ruta
        self.metodo = metodo
        self.ip_address = ip_address
        self.user_agent = user_agent
        self.datos_adicionales = datos_adicionales
        self.created_at = created_at

    @staticmethod
    def create(usuario_id, usuario_tipo, usuario_nombre, accion, descripcion=None, ruta=None, metodo=None, ip_address=None, user_agent=None, datos_adicionales=None):
        import json
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            datos_json = json.dumps(datos_adicionales) if datos_adicionales else None
            cur.execute("""
                INSERT INTO user_logs (usuario_id, usuario_tipo, usuario_nombre, accion, descripcion, ruta, metodo, ip_address, user_agent, datos_adicionales)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id, usuario_id, usuario_tipo, usuario_nombre, accion, descripcion, ruta, metodo, ip_address, user_agent, datos_adicionales, created_at
            """, (usuario_id, usuario_tipo, usuario_nombre, accion, descripcion, ruta, metodo, ip_address, user_agent, datos_json))
            row = cur.fetchone()
            conn.commit()
            return UserLog(*row)
        except Exception as e:
            conn.rollback()
            return str(e)
        finally:
            cur.close()
            conn.close()

    @staticmethod
    def get_all(limit=1000, offset=0, usuario_id=None, usuario_tipo=None, accion=None):
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            query = """
                SELECT id, usuario_id, usuario_tipo, usuario_nombre, accion, descripcion, ruta, metodo, ip_address, user_agent, datos_adicionales, created_at
                FROM user_logs
                WHERE 1=1
            """
            params = []
            
            if usuario_id:
                query += " AND usuario_id = %s"
                params.append(usuario_id)
            if usuario_tipo:
                query += " AND usuario_tipo = %s"
                params.append(usuario_tipo)
            if accion:
                query += " AND accion = %s"
                params.append(accion)
            
            query += " ORDER BY created_at DESC LIMIT %s OFFSET %s"
            params.extend([limit, offset])
            
            cur.execute(query, params)
            rows = cur.fetchall()
            return [UserLog(*row) for row in rows]
        finally:
            cur.close()
            conn.close()

    @staticmethod
    def get_count(usuario_id=None, usuario_tipo=None, accion=None):
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            query = "SELECT COUNT(*) FROM user_logs WHERE 1=1"
            params = []
            
            if usuario_id:
                query += " AND usuario_id = %s"
                params.append(usuario_id)
            if usuario_tipo:
                query += " AND usuario_tipo = %s"
                params.append(usuario_tipo)
            if accion:
                query += " AND accion = %s"
                params.append(accion)
            
            cur.execute(query, params)
            count = cur.fetchone()[0]
            return count
        finally:
            cur.close()
            conn.close()

    def to_dict(self):
        import json
        # PostgreSQL JSONB ya convierte automáticamente a diccionario Python
        # Verificar si es string o ya es dict
        datos_adicionales = None
        if self.datos_adicionales:
            if isinstance(self.datos_adicionales, dict):
                datos_adicionales = self.datos_adicionales
            elif isinstance(self.datos_adicionales, str):
                try:
                    datos_adicionales = json.loads(self.datos_adicionales)
                except (json.JSONDecodeError, TypeError):
                    datos_adicionales = None
            else:
                datos_adicionales = self.datos_adicionales
        
        return {
            'id': self.id,
            'usuario_id': self.usuario_id,
            'usuario_tipo': self.usuario_tipo,
            'usuario_nombre': self.usuario_nombre,
            'accion': self.accion,
            'descripcion': self.descripcion,
            'ruta': self.ruta,
            'metodo': self.metodo,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'datos_adicionales': datos_adicionales,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else '',
            'created_at_display': self.created_at.strftime('%d/%m/%Y %H:%M:%S') if self.created_at else ''
        }

# ========== MODELOS DE MARKETING ==========

def create_marketing_campanas_table():
    """Crea la tabla para almacenar las campañas de marketing"""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS marketing_campanas (
        id INT AUTO_INCREMENT PRIMARY KEY,
        nombre VARCHAR(200) NOT NULL,
        descripcion TEXT,
        tipo VARCHAR(50) NOT NULL,
        plataforma VARCHAR(50) NOT NULL,
        estado VARCHAR(20) DEFAULT 'borrador',
        presupuesto DECIMAL(12,2) DEFAULT 0,
        presupuesto_gastado DECIMAL(12,2) DEFAULT 0,
        fecha_inicio DATE,
        fecha_fin DATE,
        objetivo TEXT,
        publico_objetivo TEXT,
        configuracion JSON,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        created_by INTEGER REFERENCES users(id) ON DELETE SET NULL
    );
    """)
    conn.commit()
    cur.close()
    conn.close()

def create_marketing_resultados_table():
    """Crea la tabla para almacenar resultados diarios de campañas"""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS marketing_resultados (
        id INT AUTO_INCREMENT PRIMARY KEY,
        campana_id INTEGER REFERENCES marketing_campanas(id) ON DELETE CASCADE,
        fecha DATE NOT NULL,
        impresiones INTEGER DEFAULT 0,
        clicks INTEGER DEFAULT 0,
        conversiones INTEGER DEFAULT 0,
        costo DECIMAL(12,2) DEFAULT 0,
        ingresos DECIMAL(12,2) DEFAULT 0,
        ctr DECIMAL(5,2) DEFAULT 0,
        cpc DECIMAL(10,2) DEFAULT 0,
        cpm DECIMAL(10,2) DEFAULT 0,
        roi DECIMAL(5,2) DEFAULT 0,
        datos_adicionales JSON,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(campana_id, fecha)
    );
    """)
    conn.commit()
    cur.close()
    conn.close()

def create_marketing_clientes_segmentos_table():
    """Crea la tabla para clasificar y segmentar clientes"""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS marketing_clientes_segmentos (
        id INT AUTO_INCREMENT PRIMARY KEY,
        cliente_id INTEGER REFERENCES clientes(id) ON DELETE CASCADE,
        segmento VARCHAR(50) NOT NULL,
        subsegmento VARCHAR(100),
        ultima_visita DATE,
        frecuencia_visita INTEGER DEFAULT 0,
        frecuencia_semanas DECIMAL(4,2),
        valor_total DECIMAL(12,2) DEFAULT 0,
        ticket_promedio DECIMAL(12,2) DEFAULT 0,
        fecha_nacimiento DATE,
        mes_cumpleanos INTEGER,
        scoring INTEGER DEFAULT 0,
        notas TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(cliente_id)
    );
    """)
    conn.commit()
    cur.close()
    conn.close()

def create_marketing_recordatorios_table():
    """Crea la tabla para programar y gestionar recordatorios"""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS marketing_recordatorios (
        id INT AUTO_INCREMENT PRIMARY KEY,
        nombre VARCHAR(200),
        tipo VARCHAR(50) NOT NULL,
        destinatario_tipo VARCHAR(20) NOT NULL,
        destinatario_id INTEGER,
        mensaje TEXT NOT NULL,
        canal VARCHAR(20) NOT NULL,
        fecha_programada TIMESTAMP NOT NULL,
        fecha_envio TIMESTAMP,
        estado VARCHAR(20) DEFAULT 'pendiente',
        activo BOOLEAN DEFAULT TRUE,
        enviado BOOLEAN DEFAULT FALSE,
        respuesta_recibida BOOLEAN DEFAULT FALSE,
        es_recurrente BOOLEAN DEFAULT FALSE,
        recurrencia TEXT,
        metadata JSON,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        created_by INTEGER REFERENCES users(id) ON DELETE SET NULL
    );
    """)
    # Agregar columnas si no existen (migración)
    try:
        cur.execute("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name='marketing_recordatorios' AND column_name='nombre'
        """)
        if not cur.fetchone():
            cur.execute("ALTER TABLE marketing_recordatorios ADD COLUMN nombre VARCHAR(200)")
        cur.execute("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name='marketing_recordatorios' AND column_name='activo'
        """)
        if not cur.fetchone():
            cur.execute("ALTER TABLE marketing_recordatorios ADD COLUMN activo BOOLEAN DEFAULT TRUE")
        cur.execute("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name='marketing_recordatorios' AND column_name='es_recurrente'
        """)
        if not cur.fetchone():
            cur.execute("ALTER TABLE marketing_recordatorios ADD COLUMN es_recurrente BOOLEAN DEFAULT FALSE")
        cur.execute("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name='marketing_recordatorios' AND column_name='recurrencia'
        """)
        if not cur.fetchone():
            cur.execute("ALTER TABLE marketing_recordatorios ADD COLUMN recurrencia TEXT")
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"Error en migración de marketing_recordatorios: {e}")
    conn.commit()
    cur.close()
    conn.close()

def create_marketing_integraciones_table():
    """Crea la tabla para gestionar integraciones con plataformas externas"""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS marketing_integraciones (
        id INT AUTO_INCREMENT PRIMARY KEY,
        tipo VARCHAR(50) NOT NULL UNIQUE,
        nombre VARCHAR(200) NOT NULL,
        activa BOOLEAN DEFAULT FALSE,
        configuracion JSON NOT NULL,
        ultima_sincronizacion TIMESTAMP,
        estado_conexion VARCHAR(20) DEFAULT 'desconectado',
        notas TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    conn.commit()
    cur.close()
    conn.close()

def create_marketing_agendas_table():
    """Crea la tabla para gestionar agendas personales y de negocio"""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS marketing_agendas (
        id INT AUTO_INCREMENT PRIMARY KEY,
        usuario_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
        cliente_id INTEGER REFERENCES clientes(id) ON DELETE SET NULL,
        negocio_sucursal VARCHAR(200),
        fecha TIMESTAMP NOT NULL,
        tipo_evento VARCHAR(50) NOT NULL,
        titulo VARCHAR(200) NOT NULL,
        descripcion TEXT,
        duracion_minutos INTEGER,
        recordatorio_minutos INTEGER,
        recordatorio_enviado BOOLEAN DEFAULT FALSE,
        estado VARCHAR(20) DEFAULT 'programado',
        metadata JSON,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        created_by INTEGER REFERENCES users(id) ON DELETE SET NULL
    );
    """)
    conn.commit()
    cur.close()
    conn.close()

def create_marketing_plantillas_table():
    """Crea la tabla para almacenar plantillas de mensajes"""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS marketing_plantillas (
        id INT AUTO_INCREMENT PRIMARY KEY,
        nombre VARCHAR(200) NOT NULL,
        tipo VARCHAR(50) NOT NULL,
        canal VARCHAR(20) NOT NULL,
        asunto VARCHAR(200),
        contenido TEXT NOT NULL,
        variables TEXT,
        activa BOOLEAN DEFAULT TRUE,
        uso_count INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        created_by INTEGER REFERENCES users(id) ON DELETE SET NULL
    );
    """)
    conn.commit()
    cur.close()
    conn.close()

def create_all_marketing_tables():
    """Crea todas las tablas necesarias para el módulo de marketing"""
    create_marketing_campanas_table()
    create_marketing_resultados_table()
    create_marketing_clientes_segmentos_table()
    create_marketing_recordatorios_table()
    create_marketing_integraciones_table()
    create_marketing_agendas_table()
    create_marketing_plantillas_table()
    print("Todas las tablas de marketing han sido creadas exitosamente.")

class MarketingCampana:
    def __init__(self, id, nombre, descripcion, tipo, plataforma, estado, presupuesto, 
                 presupuesto_gastado, fecha_inicio, fecha_fin, objetivo, publico_objetivo, 
                 configuracion, created_at, updated_at, created_by):
        self.id = id
        self.nombre = nombre
        self.descripcion = descripcion
        self.tipo = tipo
        self.plataforma = plataforma
        self.estado = estado
        self.presupuesto = float(presupuesto) if presupuesto else 0
        self.presupuesto_gastado = float(presupuesto_gastado) if presupuesto_gastado else 0
        self.fecha_inicio = fecha_inicio
        self.fecha_fin = fecha_fin
        self.objetivo = objetivo
        self.publico_objetivo = publico_objetivo
        self.configuracion = configuracion
        self.created_at = created_at
        self.updated_at = updated_at
        self.created_by = created_by
    
    @staticmethod
    def get_all():
        """Obtiene todas las campañas"""
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT id, nombre, descripcion, tipo, plataforma, estado, presupuesto, 
                   presupuesto_gastado, fecha_inicio, fecha_fin, objetivo, publico_objetivo,
                   configuracion, created_at, updated_at, created_by
            FROM marketing_campanas
            ORDER BY created_at DESC
        """)
        campanas = cur.fetchall()
        cur.close()
        conn.close()
        return [MarketingCampana(*c) for c in campanas]
    
    @staticmethod
    def get_by_id(campana_id):
        """Obtiene una campaña por ID"""
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT id, nombre, descripcion, tipo, plataforma, estado, presupuesto,
                   presupuesto_gastado, fecha_inicio, fecha_fin, objetivo, publico_objetivo,
                   configuracion, created_at, updated_at, created_by
            FROM marketing_campanas
            WHERE id = %s
        """, (campana_id,))
        campana = cur.fetchone()
        cur.close()
        conn.close()
        if campana:
            return MarketingCampana(*campana)
        return None
    
    @staticmethod
    def create(nombre, tipo, plataforma, created_by, descripcion=None, presupuesto=0,
               fecha_inicio=None, fecha_fin=None, objetivo=None, publico_objetivo=None, 
               configuracion=None):
        """Crea una nueva campaña"""
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            import json
            config_json = json.dumps(configuracion) if configuracion else None
            cur.execute("""
                INSERT INTO marketing_campanas 
                (nombre, descripcion, tipo, plataforma, presupuesto, fecha_inicio, fecha_fin,
                 objetivo, publico_objetivo, configuracion, created_by)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id, nombre, descripcion, tipo, plataforma, estado, presupuesto,
                          presupuesto_gastado, fecha_inicio, fecha_fin, objetivo, publico_objetivo,
                          configuracion, created_at, updated_at, created_by
            """, (nombre, descripcion, tipo, plataforma, presupuesto, fecha_inicio, fecha_fin,
                  objetivo, publico_objetivo, config_json, created_by))
            campana_row = cur.fetchone()
            conn.commit()
            return MarketingCampana(*campana_row)
        except Exception as e:
            conn.rollback()
            return None
        finally:
            cur.close()
            conn.close()
    
    def to_dict(self):
        """Convierte la campaña a diccionario"""
        return {
            'id': self.id,
            'nombre': self.nombre,
            'descripcion': self.descripcion,
            'tipo': self.tipo,
            'plataforma': self.plataforma,
            'estado': self.estado,
            'presupuesto': self.presupuesto,
            'presupuesto_gastado': self.presupuesto_gastado,
            'fecha_inicio': self.fecha_inicio.strftime('%Y-%m-%d') if self.fecha_inicio else None,
            'fecha_fin': self.fecha_fin.strftime('%Y-%m-%d') if self.fecha_fin else None,
            'objetivo': self.objetivo,
            'publico_objetivo': self.publico_objetivo,
            'configuracion': self.configuracion,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else '',
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else '',
            'created_by': self.created_by
        }

class ClienteSegmento:
    def __init__(self, id, cliente_id, segmento, subsegmento, ultima_visita, frecuencia_visita,
                 frecuencia_semanas, valor_total, ticket_promedio, fecha_nacimiento, mes_cumpleanos,
                 scoring, notas, created_at, updated_at):
        self.id = id
        self.cliente_id = cliente_id
        self.segmento = segmento
        self.subsegmento = subsegmento
        self.ultima_visita = ultima_visita
        self.frecuencia_visita = frecuencia_visita
        self.frecuencia_semanas = float(frecuencia_semanas) if frecuencia_semanas else None
        self.valor_total = float(valor_total) if valor_total else 0
        self.ticket_promedio = float(ticket_promedio) if ticket_promedio else 0
        self.fecha_nacimiento = fecha_nacimiento
        self.mes_cumpleanos = mes_cumpleanos
        self.scoring = scoring
        self.notas = notas
        self.created_at = created_at
        self.updated_at = updated_at
    
    @staticmethod
    def get_by_cliente_id(cliente_id):
        """Obtiene el segmento de un cliente"""
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT id, cliente_id, segmento, subsegmento, ultima_visita, frecuencia_visita,
                   frecuencia_semanas, valor_total, ticket_promedio, fecha_nacimiento, mes_cumpleanos,
                   scoring, notas, created_at, updated_at
            FROM marketing_clientes_segmentos
            WHERE cliente_id = %s
        """, (cliente_id,))
        segmento = cur.fetchone()
        cur.close()
        conn.close()
        if segmento:
            return ClienteSegmento(*segmento)
        return None
    
    @staticmethod
    def get_by_segmento(segmento):
        """Obtiene todos los clientes de un segmento"""
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT id, cliente_id, segmento, subsegmento, ultima_visita, frecuencia_visita,
                   frecuencia_semanas, valor_total, ticket_promedio, fecha_nacimiento, mes_cumpleanos,
                   scoring, notas, created_at, updated_at
            FROM marketing_clientes_segmentos
            WHERE segmento = %s
            ORDER BY scoring DESC
        """, (segmento,))
        segmentos = cur.fetchall()
        cur.close()
        conn.close()
        return [ClienteSegmento(*s) for s in segmentos]
    
    @staticmethod
    def get_cumpleanos_mes(mes):
        """Obtiene clientes que cumplen años en un mes específico"""
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT id, cliente_id, segmento, subsegmento, ultima_visita, frecuencia_visita,
                   frecuencia_semanas, valor_total, ticket_promedio, fecha_nacimiento, mes_cumpleanos,
                   scoring, notas, created_at, updated_at
            FROM marketing_clientes_segmentos
            WHERE mes_cumpleanos = %s AND fecha_nacimiento IS NOT NULL
            ORDER BY fecha_nacimiento
        """, (mes,))
        segmentos = cur.fetchall()
        cur.close()
        conn.close()
        return [ClienteSegmento(*s) for s in segmentos]
    
    def to_dict(self):
        """Convierte el segmento a diccionario"""
        return {
            'id': self.id,
            'cliente_id': self.cliente_id,
            'segmento': self.segmento,
            'subsegmento': self.subsegmento,
            'ultima_visita': self.ultima_visita.strftime('%Y-%m-%d') if self.ultima_visita else None,
            'frecuencia_visita': self.frecuencia_visita,
            'frecuencia_semanas': self.frecuencia_semanas,
            'valortotal': self.valor_total,
            'ticket_promedio': self.ticket_promedio,
            'fecha_nacimiento': self.fecha_nacimiento.strftime('%Y-%m-%d') if self.fecha_nacimiento else None,
            'mes_cumpleanos': self.mes_cumpleanos,
            'scoring': self.scoring,
            'notas': self.notas,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else '',
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else ''
        }