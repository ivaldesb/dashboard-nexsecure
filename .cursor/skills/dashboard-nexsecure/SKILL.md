---
name: dashboard-nexsecure
description: >-
  Guía del CRM Django NexSecure: stack, apps, ramas git y arranque local.
  Usar al desarrollar features, fixes o cambios de UI/DB en este repo.
---

# Dashboard NexSecure

## Cuándo usarla

Trabajo en este repositorio: vistas/modelos Django, templates, static, auth con roles, PDFs reportlab, finanzas, o workflow git del dashboard.

## Stack y estructura

- **Stack:** Django 5.x, SQLite (default) / MariaDB con `DB_ENGINE=mysql` + PyMySQL, reportlab, openpyxl, python-dotenv
- **Entry:** `manage.py` (settings en `config/settings.py`)
- **Apps:** `accounts` (User custom + Role), `clientes`, `proyectos` (detalle por pestañas + timeline), `activos`, `documentos` (ACL + auditoría), `incidencias`, `presupuestos`, `finanzas` (IVA/PPM), `calendario`, `marketing` (stub), `core` (dashboard, sidebar, PDFs)
- **UI:** `templates/` (base `base.html` + `includes/sidebar.html`, tema Gentelella en `static/`)
- **Auth:** login obligatorio global (`accounts.middleware.LoginRequiredMiddleware`), sin registro público; permisos vía roles (`Role.is_admin`, `require_admin`, `require_perm`)
- **Legacy Flask:** `legacy/` (solo referencia)
- **Config:** `.env` (no commitear secretos)

No es Next.js/Vercel/Flask. La landing vive en otro repo (`Proyectos/Web`).

## Workflow de ramas

```
feat/* | fix/*  →  PR → develop  →  (estable) main
```

1. `git fetch` + checkout `develop` + `pull`
2. Crear rama desde `develop` (kebab-case), p. ej. `feat/filtro-clientes`
3. Trabajar solo en esa rama
4. Push / PR solo si el usuario lo pide
5. Si no existe `develop`, crearla desde `main` y pushearla

Identidad: ver `.cursor/rules/git-identity.mdc` (firma SSH 1Password del usuario).

## Arranque local

```bash
.venv\Scripts\activate            # Windows (source .venv/bin/activate en unix)
pip install -r requirements.txt
python manage.py migrate           # crea schema + seeds (rol admin, estados de proyecto)
python manage.py createsuperuser
python manage.py runserver         # http://127.0.0.1:8000
```

## Verificación

```bash
python manage.py test core         # smoke end-to-end (login wall, permisos, pestañas, PDF)
python manage.py check
python manage.py makemigrations --check --dry-run   # sin drift modelos↔migraciones
```

## No hacer

- No desplegar a producción a mano
- No incluir `.env` ni secretos en commits
- No tocar `git config` ni desactivar firma (`--no-gpg-sign`)
- No editar `legacy/` salvo pedido explícito
