# Dashboard NexSecure

CRM interno de NexSecure para gestionar clientes, proyectos, presupuestos (matriz de costos), activos, incidencias, documentos, mantenimiento, finanzas y calendario.

- **Stack:** Django 5 + templates (tema Gentelella) + SQLite local (MariaDB opcional)
- **No es** la landing web (vive en otro repo)
- **Acceso privado:** login obligatorio; sin registro público (las credenciales las crea un administrador)

El código Flask antiguo está en `legacy/` solo como referencia; no se ejecuta.

## Requisitos

- Python 3.12+ recomendado
- Windows / Linux / macOS

## Arranque local

```bash
# Clonar e entrar al repo
cd dashboard-nexsecure

# Entorno virtual
python -m venv .venv
.\.venv\Scripts\activate          # Windows
# source .venv/bin/activate       # Unix

pip install -r requirements.txt
copy .env.example .env            # Windows
# cp .env.example .env            # Unix

python manage.py migrate
python manage.py createsuperuser
python manage.py runserver        # http://127.0.0.1:8000
```

Configura `SECRET_KEY`, `DEBUG` y (si aplica) la base de datos en `.env`. **No commitees** `.env`.

### Base de datos

Por defecto usa SQLite (`db.sqlite3`).

Para MariaDB/MySQL en `.env`:

```env
DB_ENGINE=mysql
DB_HOST=127.0.0.1
DB_NAME=nexsecure
DB_USER=nexsecure
DB_PASSWORD=***
DB_PORT=3306
```

## Módulos

| App | Función |
|-----|---------|
| `accounts` | Usuarios, tags, roles/permisos; rol admin con acceso total |
| `clientes` | CRUD clientes + portal (solo proyectos/presupuestos vinculados) |
| `proyectos` | Núcleo: código auto, equipo/clientes, estados, detalle por pestañas, comentarios, timeline |
| `presupuestos` | Cotizaciones, matriz Material/Servicio, PDF, gastos vinculados a factura/boleta |
| `activos` | Inventario por proyecto + panel global |
| `incidencias` | Tickets con diagnóstico, fotos, comentarios |
| `documentos` | Repositorio con categorías, ACL y auditoría de vista/descarga |
| `mantenimiento` | Visitas, checklists por tipo de servicio, fotos |
| `finanzas` | IVA/PPM, flujo de caja, conciliación, import CSV/Excel (solo admin) |
| `calendario` | Eventos/tareas privados, capas, email (+ stub WhatsApp) |
| `marketing` | Stub reservado |
| `core` | Dashboard, PDFs (reportlab), helpers de UI/modal |

### Flujo de proyecto (resumen)

1. Se crea en estado **Borrador** (oculto al portal del cliente).
2. Detalle en pestaña nueva: General, Activos, Incidencias, Documentos, Mantenimiento, Presupuestos, Timeline, Descargas.
3. Las altas/ediciones simples se hacen en **modal** sin salir de la pantalla.
4. El cliente ve el último presupuesto **enviado** en General y puede aceptar o rechazar con comentario.
5. Matriz de costos: solo equipo/admin; el cliente ve cotización formal (neto) y PDF sin costos internos.

## Verificación

```bash
python manage.py check
python manage.py test core
python manage.py makemigrations --check --dry-run
```

## Estructura

```
manage.py
config/           # settings, urls, wsgi/asgi
accounts/ …       # apps Django
templates/        # base.html, includes/, módulos
static/           # Gentelella + css/nexsecure.css + js/
legacy/           # Flask histórico (solo lectura)
.env.example
```

## Git

```
feat/* | fix/*  →  PR → develop  →  (estable) main
```

Trabajar en rama feature/fix desde `develop`. No editar `main`/`develop` directo.

## Variables de entorno útiles

Ver [`.env.example`](.env.example):

- `EMAIL_*` — notificaciones de calendario (por defecto backend consola)
- `WHATSAPP_ENABLED` — stub de WhatsApp (`0` = no-op)
- `FINANZAS_IVA_RATE` / `FINANZAS_PPM_RATE` — tasas tributarias Chile

## Licencia / uso

Software interno NexSecure. No publicar credenciales ni datos de clientes en el repositorio.
