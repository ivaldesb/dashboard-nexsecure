---
name: dashboard-nexsecure
description: >-
  Guía del dashboard Flask NexSecure: stack, estructura, ramas git y arranque
  local. Usar al desarrollar features, fixes o cambios de UI/DB en este repo.
---

# Dashboard NexSecure

## Cuándo usarla

Trabajo en este repositorio: rutas Flask, modelos MariaDB, templates Jinja, static, auth Flask-Login, PDFs reportlab, o workflow git del dashboard.

## Stack y estructura

- **Stack:** Flask, Flask-Login, PyMySQL/MariaDB, reportlab, python-dotenv, Werkzeug
- **Entry:** `app.py`
- **DB / modelos:** `models.py`
- **UI:** `templates/`, `static/`
- **Config:** `.env` (no commitear secretos)

No es Next.js/Vercel. La landing vive en otro repo (`Proyectos/Web`).

## Workflow de ramas

```
feat/* | fix/*  →  PR → develop  →  (estable) main
```

1. `git fetch` + checkout `develop` + `pull`
2. Crear rama desde `develop` (kebab-case), p. ej. `feat/filtro-clientes`
3. Trabajar solo en esa rama
4. Push / PR solo si el usuario lo pide
5. Si no existe `develop`, crearla desde `main` y pushearla
6. Si solo existe `master`: legado → usar/crear `main` como producción

Identidad: ver `.cursor/rules/git-identity.mdc` (firma SSH 1Password del usuario).

## Arranque local

```bash
source .venv/bin/activate
python app.py
# http://127.0.0.1:5000
```

## No hacer

- No desplegar a producción a mano
- No incluir `.env` ni secretos en commits
- No tocar `git config` ni desactivar firma (`--no-gpg-sign`)
