# AGENTS — Dashboard NexSecure

CRM/Dashboard **Django** (templates Django + SQLite local / MariaDB opcional). No es la landing web. El código Flask antiguo vive en `legacy/` (solo referencia, no se ejecuta).

## Contexto del agente

- Rules: `.cursor/rules/` (`git-branching`, `git-identity`, `ponytail`, `subagentes-planes`, `dashboard-nexsecure-scope`)
- Skill: `.cursor/skills/dashboard-nexsecure/SKILL.md`

## Git

1. Actualizar `develop` (`fetch` + `pull`).
2. Rama feature/fix desde `develop` (kebab-case).
3. No commitear en `main`/`develop` directo.
4. PR → `develop` → (estable) `main`.
5. Si solo hay `master`, tratarla como legado y usar/crear `main`.
6. Autoría/firma: usuario + SSH 1Password; sin co-autoría del agente. Commit/push solo si se pide.

## Local

```bash
.venv\Scripts\activate        # Windows (source .venv/bin/activate en unix)
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver    # http://127.0.0.1:8000
```

Config en `.env` (no commitear). Smoke test: `python manage.py test core`. No desplegar a prod a mano desde el agente.
