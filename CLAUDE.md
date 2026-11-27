# Organizy

Single-user personal productivity app (only me): spaces → departments → tasks → steps, a Today planner, recurring tasks, an ideas inbox and a People book. It covers Horizon's Club, Yacine Academy (Instagram, Club), my studies, my career and personal contacts. It is also a DevOps portfolio project.

- Spec (source of truth): @docs/SPEC.md
- Approved proposal (data model, API, UI plan, decisions 1–31, phase plan): docs/PROPOSAL.md. Read the relevant section before starting a feature.
- Ask before deviating from either.

## Stack
- Backend: FastAPI · Python 3.12 · SQLAlchemy 2.0 (sync, psycopg 3) · Pydantic v2 · Alembic · PostgreSQL 17 · uv
- Frontend: Next.js App Router (TypeScript) · Tailwind · shadcn/ui · lucide-react · Motion · dnd-kit · cmdk · sonner · TanStack Query
- Monorepo: `backend/`, `frontend/`, `docker-compose*.yml`, `.github/workflows/`

## Commands
- DB (dev): `docker compose -f docker-compose.dev.yml up -d`
- Backend: `cd backend && uv run fastapi dev app/main.py`
  - tests: `uv run pytest`
  - lint: `uv run ruff check . && uv run black --check .`
  - migrations: `uv run alembic revision --autogenerate -m "..."`, then `uv run alembic upgrade head`
- Frontend: `cd frontend && npm run dev`
  - checks: `npm run lint` · `npm run typecheck` · `npm test`
  - regenerate API types: `npm run gen:api`
- Full stack (Phase 3+): `docker compose up --build`

## Android-first
- Organizy is mainly an Android phone app, delivered as an installable PWA (Chrome WebAPK). It is not a native app.
- Design every screen at phone size first (412×915), then adapt it for desktop.
- Android details:
  - the back gesture closes sheets
  - safe areas and theme-color
  - manifest shortcuts and a share target into Ideas
  - haptics
  - touch targets of at least 48dp
- Live preview while building: `npm run dev` (hot reload), the `/dev/preview` phone frames, and the real phone through chrome://inspect port forwarding. Show a phone-size screenshot after each screen.

## Architecture rules
- Business rules live in `backend/app/services`, never in routers or the frontend.
- "Today" and all dates come from `app/core/clock.py` (TZ from env, default Africa/Algiers). Never call `date.today()` or `datetime.now()` directly.
- Progress is computed server-side only (round-half-up). Clients never send it.
  - Auto-done fires only when checking a step takes progress from below 100 to 100.
- Pin "done" is derived from its task or step. Recurring occurrences are computed; a row is written only when one is checked.
- Status and kind fields are text + CHECK constraints, not Postgres enums.
- The frontend calls the API only through `src/lib/api` with generated OpenAPI types. Mutations are optimistic (TanStack Query).
- UI:
  - no tables, grids or admin-panel look; use cards and lists
  - design tokens only (no raw hex), with both themes designed properly
  - respect reduced motion
  - red only for overdue / late nudges, amber for waiting, green for done

## Privacy
- People data is real personal data. Never put real names, emails or phones in code, seeds, tests, fixtures, screenshots or commit messages. Fake people only (example.com).
- Never read or print `.env` files or secrets.

## Workflow
- I'm learning Claude Code: briefly explain each decision and name the Claude Code feature we're using.
- One feature per branch, small Conventional Commits (`feat(tasks): ...`). Show me the diff before committing.
- After committing: push, open the PR and merge it yourself (squash, delete the branch), then switch to `main` and pull. Don't ask or tell me first. Only merge when tests and lint pass (and CI is green, once CI exists).
- Write failing tests first for business rules, then implement.
- Stop at the end of each phase (and each feature) so I can test. End each phase with a recap: "Claude Code features used" + one tip.
- Ask before adding a dependency or changing the stack.
