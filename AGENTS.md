# AGENTS — Dashboard NexSecure

Dashboard Flask (Jinja + PyMySQL/MariaDB). No es la landing web.

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
source .venv/bin/activate
python app.py   # :5000
```

Config en `.env` (no commitear). No desplegar a prod a mano desde el agente.
