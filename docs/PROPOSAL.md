# Organizy: Proposal (architecture, data model, API, UI, build plan)

## Context
Organizy is a single-user productivity app built around Space → Department → Task → Step, plus a People book, a Today planner, recurring tasks and an ideas inbox (full spec: `docs/SPEC.md`). It is also a DevOps portfolio piece and a way to learn Claude Code. The folder currently holds only `docs/SPEC.md` and a draft `CLAUDE.md`, and it is not a git repo yet. This document is the proposal the spec asks for ("How I want to work with you", step 1). No code gets written until you approve it.

> **Claude Code feature in use right now: Plan mode.** I can read files but I can't edit anything except this plan file. When I'm done I call `ExitPlanMode`, and you approve the plan or send feedback. Use it (Shift+Tab to cycle modes) whenever a change is big enough that you want to agree on a design before any file changes.

---

## ★ Update from your feedback: Organizy is an Android phone app

**Decided: an installable PWA on Android.** Chrome on Android installs it as a real app (a WebAPK): it has its own icon in the app drawer, runs full screen, and gets its own entry in recent apps. The phone is now the **primary target**. Desktop is the secondary layout.

**To remember this** (I'll do these as soon as plan mode ends, since plan mode only lets me edit this file):
- Save a memory: "Organizy = Android-first installable PWA; phone UI is the primary design target; the user wants a live phone preview while building."
- Add an "Android-first" rule to CLAUDE.md.
- Add a note to `docs/SPEC.md`.

**What changes in the plan**
- **Phone-first design.**
  - Every screen is designed first at **412 × 915 (Pixel-class Android)**, then widened for desktop.
  - The ui-reviewer subagent checks the phone layout first.
- **Android-specific features**, added in Phase 2 step 11:
  - The **Android back gesture closes open sheets and panels** instead of leaving the page (panels are tied to the URL, decision in §4).
  - **Safe-area padding**, and a status-bar color (`theme-color`) for each theme.
  - **App shortcuts**: long-press the app icon for "Today", "Quick add" or "New idea" (manifest `shortcuts`).
  - **Share target**: share text or a link from any Android app (WhatsApp, Chrome…) straight into the Ideas inbox (manifest `share_target`).
  - **Haptics**: a short vibration when you check a step or complete a task (`navigator.vibrate`, off when reduce-motion is on).
  - Tap-to-call, email and WhatsApp links open the native apps.
  - Swipe gestures, bottom sheets and ≥ 48 dp touch targets (Android's guideline, a bit bigger than the spec's 44 px).
- Installing the PWA needs HTTPS. For development, USB port forwarding (below) makes the phone treat the site as `localhost`, which Android allows without HTTPS. Real HTTPS comes with the Azure deployment.

## ★ Live preview: watching the phone UI while I build

The goal is the "edit an HTML page, see it in the browser" feeling. It's set up in **Phase 2 step 1**, before any screen is built:
1. **Hot reload.** `npm run dev` runs Next.js with Fast Refresh. Every file I save shows up within about a second, without a page reload.
2. **Device preview page `/dev/preview`** (dev only, not shipped in the production build). It shows several **Android phone frames side by side** (412 × 915), each running a live screen: Home, Today, Space, Task panel, People, Ideas. Each frame can switch between light and dark. Leave it open on your second screen and watch the screens change as I work. Next to it, **`/design`** shows every token and component.
3. **On your real Android phone (USB):**
   - turn on USB debugging
   - open `chrome://inspect` → *Port forwarding* (3000 → localhost:3000) on the PC
   - open `localhost:3000` on the phone
   You get the real app with hot reload, and you can even install it as a PWA. Same Wi-Fi without a cable also works (`http://<PC-IP>:3000`, with secure cookies relaxed in dev only), but it can't be installed that way.
4. **I check it visually too.** I'll use the Claude in Chrome tools to open the preview at phone size, take screenshots and fix what I see, then show you the screenshot after each screen. You can also paste your own phone screenshots (a Claude Code feature taught in Phase 2).
5. **Earlier visual check (optional).** Before Phase 2, I can publish a static, clickable HTML mockup of the main phone screens as a private page, so you can approve the look before the real frontend exists.

---

## 0. Decisions to make before we start

Each item has my recommendation **in bold**. Reply only on the ones you disagree with.

**Setup**
1. **Move the repo out of OneDrive** to something like `C:\dev\organizy`. OneDrive sync fights with `node_modules`, `.git` and Docker bind mounts: files get locked, sync is slow and you see phantom conflicts.
2. **Make the GitHub repo public** (it's a portfolio). That makes secret hygiene essential, see the permissions section.
3. **Split the seed in two.** The spec's seed mixes your real spaces and tasks with fake people. If it runs on your real database, the fake people end up in your real contacts book. Proposal: `seed base` (spaces, departments, tasks, the recurring task) runs once when the DB is empty. `seed demo` (the 3 fake people) runs only when `SEED_DEMO=true`, which is the case in dev and tests and never in prod.

**Task rules**
4. **Status when you check the first step.** The spec doesn't say. Recommended: a `todo` task moves to `in_progress` automatically. No other automatic changes.
5. **Deleting the last unchecked step.** This can push step progress to 100%. The spec says auto-done only fires on a step *check*, so **deleting a step does not auto-complete the task**. The card simply shows 100%.
6. **Auto-done on a `waiting` task.** If the last step gets checked while the task is waiting, **it becomes done** (the rule applies to every status). Its waiting fields are cleared.
7. **Leaving `waiting`.** Changing the status away from waiting **clears `waiting_on` and `nudge_on`**. Also, **`nudge_on` is optional**, so the seeded LabLabee and Metwork tasks start with nudge = seed date + 3 days.
8. **Reopen target status.** The Reopen button sets the task to **`in_progress` if any step is done, otherwise `todo`**. You can still pick any status from the status pill.
9. **Rounding.** Progress uses **round-half-up** (1/8 = 12.5% → 13%). Python's built-in `round()` would give 12 (banker's rounding), so this gets a test.
10. **Moving a task to another space.** The spec resets its department. **The move dialog also lets you pick a department in the target space** (default: "No department").

**Today, pins and recurring**
11. **A pin's "done" is derived, not stored.** It reflects the task's or step's own done state. A separate `done` column could drift: for example, you finish the task from its panel and the pin stays unchecked. So **pin done = target done**, and "unfinished pins" means pins whose target is not done.
12. **Recurring occurrences are computed, not pre-generated.** The backend calculates which dates a rule matches for the days being displayed. It only writes an `occurrence` row when you check or uncheck one. GET requests never write to the DB. The spec's intent (no pre-creation for the future) still holds.
13. **Ordering on Today:** events (by time), then recurring occurrences as a fixed "Routine" group, then your pinned items (drag to reorder). Recurring items are not draggable among pins in v1.
14. **Tasks due today but not pinned.** These show in a small **"Due today – pin?" suggestion tray** on Today, with one-click pinning. Home's "Today" section is about *due dates*. The Today page is about *pins*.
15. **Pinning a recurring template is not allowed.** Its occurrences already appear automatically.
16. **Archived spaces.** Their tasks, waiting items and recurring occurrences are hidden everywhere (Home, Today, Space list). **Explicit pins pointing at them still show on Today**, with an "archived" hint. Search includes archived items, with a badge.
17. **"Move unfinished to tomorrow"** works on whatever day you are viewing (it moves that day's pins to the next day). Today also shows a small banner if yesterday still has unfinished pins.
18. **Steps with due dates** also appear in Home's Overdue / Today / This week sections, displayed with their parent task.

**Home and dates**
19. **"This week"** means tomorrow through the last day of the current week (WEEK_START=Sunday, so the week ends Saturday). It excludes today and overdue items, so nothing appears twice.
20. **"Upcoming birthdays (next 7 days)"** means today through today+7. The age shown is the age they are turning.
21. **Space "average progress"** is the average across all of the space's tasks, with done tasks counting as 100% (recurring templates excluded). Averaging only open tasks would make the number *drop* every time you finish something.

**Events**
22. **Events get an optional end time.** The start time is required, as in the spec.

**People**
23. **Birthday is optional overall**, but if you enter one, day and month are required.
24. **Phones are stored as entered, plus a normalized E.164 copy** (via the `phonenumbers` library, default region DZ). That copy is what makes the tap-to-call and WhatsApp (`wa.me/213…`) links reliable.
25. **Photo uploads** are limited to 5 MB and jpeg/png/webp. They are re-encoded with Pillow, which also **strips EXIF/GPS metadata** (a privacy point) and resizes to 512 px.

**Ideas, Undo and small UI choices**
26. **Converting an idea to a task** marks the idea `converted` and links it to the new task. It disappears from the inbox, and the task links back to it.
27. **Undo on delete:** the delete is sent ~5 s later, after the toast's Undo window, and flushed if the tab closes. This is simpler than soft-deleting every table. Space and person deletes are permanent, so they keep the confirmation dialog the spec asks for.
28. **Phone navigation.** The bottom nav's centre "+" *is* the floating add button, so there's no second floating button. **Ideas lives at the top of the "Spaces" tab** (Ideas inbox row + space list), which keeps it within 2 taps.
29. **Swipe left on a task card** reveals two buttons, "Pin to today" and "Move", because the spec puts two actions on one gesture. Swipe right = done.
30. **Recently viewed** is stored in the browser's `localStorage` (per device) in v1. It's not auth data, so it doesn't conflict with the no-token-in-localStorage rule.
31. **Formatting.** The spec lists ruff + black. **Keep both** (ruff lints, black formats). Ruff's own formatter could replace black later, but we'll stick to the spec.

---

## 1. Folder structure

```
organizy/
├─ backend/
│  ├─ app/
│  │  ├─ main.py               # FastAPI app factory, routers, middleware
│  │  ├─ core/                 # config.py (pydantic-settings), db.py, security.py,
│  │  │                        # clock.py (today/now in TZ), ratelimit.py, storage.py
│  │  ├─ models/               # SQLAlchemy 2.0 models, one file per aggregate
│  │  ├─ schemas/              # Pydantic v2 request/response models
│  │  ├─ services/             # business rules: progress.py, recurrence.py, agenda.py,
│  │  │                        # dashboard.py, birthdays.py, people.py, spaces.py, …
│  │  ├─ api/routes/           # thin routers, one per resource
│  │  ├─ api/deps.py           # get_db, require_session, get_clock
│  │  └─ cli.py                # hash-password, seed base|demo
│  ├─ alembic/ + alembic.ini
│  ├─ tests/                   # unit/ (pure rules) + api/ (HTTP + real Postgres)
│  ├─ pyproject.toml + uv.lock # deps (uv), ruff, black, pytest config
│  ├─ Dockerfile + .dockerignore
├─ frontend/
│  ├─ src/app/                 # App Router: (auth)/login, (app)/page.tsx (Home), today/,
│  │                           # spaces/[id]/, people/, people/[id]/, ideas/, manifest.ts
│  ├─ src/components/ui/       # shadcn primitives (owned, editable)
│  ├─ src/components/          # app components (TaskCard, ProgressRing, …)
│  ├─ src/features/            # per-feature hooks + components (tasks/, people/, today/…)
│  ├─ src/lib/api/             # fetch client + generated OpenAPI types (schema.d.ts)
│  ├─ src/styles/              # globals.css with design tokens
│  ├─ public/icons/            # PWA icons
│  ├─ package.json, eslint, prettier, vitest config
│  ├─ Dockerfile + .dockerignore
├─ docs/                       # SPEC.md, architecture.md, screenshots/
├─ .claude/                    # settings.json, agents/, skills/, hooks/
├─ .github/workflows/ci.yml
├─ docker-compose.dev.yml      # Phase 1: Postgres only
├─ docker-compose.yml          # Phase 3: full stack
├─ .env.example, .gitignore, README.md, CLAUDE.md
```

**Why this structure:**
- **Layered backend (routes → services → models).** Routers only parse and validate. Every rule (progress, auto-done, recurrence, birthdays) lives in `services/` as plain functions you can unit-test without HTTP.
- **`core/clock.py`** is the one place that knows "today in Africa/Algiers". Tests swap in a fake clock, so time-zone and date-boundary tests are deterministic.
- **`core/storage.py`** is a small interface (`save/open/delete`) with a local-disk implementation. Moving to Azure Blob later means writing one new class.
- **Generated TS types from FastAPI's OpenAPI schema** mean the frontend and backend can't silently drift apart. CI will check that the types are up to date.

**Stack details:**
- **Synchronous SQLAlchemy + psycopg 3.** For one user, async adds complexity without benefit (FastAPI runs sync endpoints in a threadpool).
- **uv** manages Python deps: it's fast, uses a lockfile, and gives reproducible Docker builds.
- **Postgres 17.**

---

## 2. Data model

Conventions:
- UUID primary keys.
- `created_at` / `updated_at` are `timestamptz`, stored in UTC.
- Plain dates use the `date` type.
- Status-like fields are `text` + `CHECK` constraints, not native Postgres enums. Changing a native enum in a migration is painful, while a CHECK is easy to alter.
- Ordering uses a `position int` column. Reorder endpoints receive the full ordered id list.

### Spaces & structure
| table | fields | constraints / relations |
|---|---|---|
| **spaces** | id, name, color (palette token, e.g. `indigo`), icon (emoji or lucide name), position, archived_at null, created_at, updated_at | unique `lower(name)` |
| **departments** | id, space_id, name, position, timestamps | FK space ON DELETE CASCADE; unique (space_id, lower(name)); unique (id, space_id) for the composite FK below |

### Tasks
| table | fields | constraints / relations |
|---|---|---|
| **tasks** | id, space_id, department_id null, title, description, due_date null, priority (`low/medium/high`), status (`todo/in_progress/waiting/done`), progress smallint (cached step-based value), completed_at null, waiting_on_person_id null, waiting_on_text null, nudge_on null, is_recurring bool, source_idea_id null, position, timestamps | FK space CASCADE. **Composite FK (department_id, space_id) → departments(id, space_id) ON DELETE SET NULL (department_id)**: Postgres 15+ can null just one column, so a task can never point at another space's department, and deleting a department moves its tasks to "No department" at the DB level. CHECK: no waiting fields unless status = waiting; not both person and text set; recurring ⇒ due_date null. Indexes: (space_id, status), (due_date), (nudge_on) |
| **steps** | id, task_id, title, weight smallint (1/2/3), done bool, done_at null, due_date null, position, timestamps | FK task CASCADE; CHECK weight IN (1,2,3) |
| **task_people** | task_id, person_id | PK both; both FKs CASCADE |
| **recurrence_rules** | task_id (PK), frequency (`daily/weekly/monthly`), weekdays smallint[] (ISO 1=Mon…7=Sun), month_day smallint null, start_date null, end_date null | FK task CASCADE. CHECK: weekly ⇒ weekdays not empty; monthly ⇒ month_day 1–31; end ≥ start |
| **recurring_occurrences** | id, task_id, date, done bool, completed_at null | FK task CASCADE; unique (task_id, date) |

### Today
| table | fields | constraints / relations |
|---|---|---|
| **pins** | id, date, task_id null, step_id null, position, created_at | FKs CASCADE; CHECK exactly one of task_id/step_id; partial unique (date, task_id) and (date, step_id); "done" is derived (decision 11) |
| **events** | id, title, date, start_time time, end_time null, location, notes, space_id null, timestamps | FK space **ON DELETE SET NULL**; index (date, start_time) |
| **event_people** | event_id, person_id | PK both; CASCADE both |

### Ideas
| table | fields | constraints / relations |
|---|---|---|
| **ideas** | id, text, space_id null, status (`open/archived/converted`), converted_task_id null, timestamps | FK space CASCADE (the spec deletes a space's ideas with it); converted_task_id SET NULL |

### People
| table | fields | constraints / relations |
|---|---|---|
| **people** | id, full_name, nickname, birth_day null, birth_month null, birth_year null, photo_key null, notes, timestamps | CHECK day/month both null or both set, month 1–12, day 1–31 (full validity incl. Feb 29 checked in Pydantic); pg_trgm index on name |
| **person_contacts** | id, person_id, kind (`email/phone`), label, value, value_e164 null, is_main, position | CASCADE; **partial unique (person_id, kind) WHERE is_main**, so only one main email and one main phone |
| **person_family** | id, person_id, name, relation (`father/mother/brother/sister/spouse/child/other`), position | CASCADE |
| **person_tags** | id, person_id, kind (`hobby/like/dislike`), value | CASCADE; unique (person_id, kind, lower(value)); index (kind, lower(value)) for the tag filter + autocomplete |
| **person_custom_fields** | id, person_id, label, value, position | CASCADE |
| **person_spaces** | person_id, space_id | PK both; CASCADE both. No rows means the person is "Personal" |
| **contact_logs** | id, person_id, date, text, created_at | CASCADE; index (person_id, date desc). "Last contacted" = max(date) |

### Auth
| table | fields | notes |
|---|---|---|
| **auth_sessions** | id, token_hash (sha256), created_at, expires_at, last_seen_at, user_agent | The cookie holds a random token. Only its hash is stored, so a DB leak doesn't leak live sessions. Logout deletes the row (real revocation, which a signed-cookie-only session can't do). |

### Rules the schema can't express (enforced in `services/`, all tested)
- **Progress.**
  - `step_progress` = round-half-up(sum of done weights / sum of all weights × 100).
  - A task with no steps has 0 (or 100 if it's done).
  - The progress shown on screen is **100 if status = done, otherwise `step_progress`**.
- **Auto-done.** Only inside "check a step": if progress was below 100 before and is 100 after, and the task isn't done yet, it becomes done and `completed_at` is set to now. Nothing else triggers it.
- **Delete a space:** the DB cascades everything listed in the spec. Events are set to null. The person links are removed by cascade. Before deleting, `GET /spaces/{id}/delete-preview` returns the task, step and idea counts for the confirmation dialog.
- **Delete a person**, in one transaction:
  1. Copy the person's name into `waiting_on_text` on every task waiting on them, and clear `waiting_on_person_id`.
  2. Delete the person (task and event links are removed by cascade).
  3. Delete the photo file.
- **Recurrence:**
  - daily, specific weekdays, or monthly on day N. If the month is shorter than N, it falls on the last day (`min(N, days_in_month)`).
  - start and end dates are inclusive.
  - **a recurring task can't have steps** (adding a step is rejected, and so is converting a task that has steps).
- **Birthdays.** Compute the next occurrence on or after today. Feb 29 falls on Feb 28 in non-leap years. A birthday early next year counts if it's within the 7-day window (year-end wrap).

---

## 3. API endpoints

Next.js forwards `/api/*` to FastAPI, so the browser only ever talks to one origin: no CORS, and the cookie can be `SameSite=Lax`. Every route requires a session except the two marked 🔓.

Mutating requests also check the `Origin` header as CSRF protection, on top of SameSite. Pydantic validates every body. Mutations return the updated entity (for steps, also the parent task's new progress and status), so the UI can reconcile its optimistic update.

**System / auth**
- `GET /health` 🔓: process up + DB ping
- `POST /api/auth/login` 🔓: rate-limited to 5/min per IP (slowapi). Sets an httpOnly, Secure, SameSite=Lax cookie
- `POST /api/auth/logout` · `GET /api/auth/me`
- `GET /api/meta`: timezone, week_start, server "today". The frontend uses this instead of the device clock, so a phone set to another time zone still shows the right day.

**Dashboard / search**
- `GET /api/dashboard?space_id=`: overdue, today, this week, waiting (with an `is_late` flag), active tasks, birthdays, space summaries and a Today preview, all in one request. This is a "backend-for-frontend" endpoint: one round-trip for Home, so it renders fast on a phone.
- `GET /api/search?q=`: results grouped as tasks / spaces / people / ideas / events (pg_trgm)

**Spaces & departments**
- `GET /api/spaces?include_archived=` · `POST /api/spaces` · `GET /api/spaces/{id}` (departments, task groups, ideas, people, progress) · `PATCH /api/spaces/{id}`
- `POST /api/spaces/{id}/archive` · `POST /api/spaces/{id}/unarchive` · `GET /api/spaces/{id}/delete-preview` · `DELETE /api/spaces/{id}` · `PUT /api/spaces/order`
- `POST /api/spaces/{id}/departments` · `PATCH /api/departments/{id}` · `DELETE /api/departments/{id}` · `PUT /api/spaces/{id}/departments/order`

**Tasks & steps**
- `GET /api/tasks?space_id=&department_id=&status=&person_id=&due_from=&due_to=` · `POST /api/tasks` · `GET /api/tasks/{id}` · `PATCH /api/tasks/{id}` · `DELETE /api/tasks/{id}`
- `POST /api/tasks/{id}/complete` · `POST /api/tasks/{id}/reopen` · `POST /api/tasks/{id}/move` `{space_id, department_id?}` · `PUT /api/tasks/order` `{space_id, department_id, ids}`
- `PUT /api/tasks/{id}/people` `{person_ids}`
- `PUT /api/tasks/{id}/recurrence` · `DELETE /api/tasks/{id}/recurrence` · `PUT /api/tasks/{id}/occurrences/{date}` `{done}`
- `POST /api/tasks/{id}/steps` · `PATCH /api/steps/{id}` (title, weight, done, due_date) · `DELETE /api/steps/{id}` · `PUT /api/tasks/{id}/steps/order`
- `progress` is never accepted from the client. The response schemas simply don't contain it on the input side.

**Today / agenda**
- `GET /api/agenda?date=`: events, birthdays, recurring occurrences, pins with their targets, and the due-today suggestions
- `GET /api/agenda/overview?start=&days=7`: counts per day for the date chips
- `POST /api/pins` `{date, task_id | step_id}` · `PATCH /api/pins/{id}` `{done?, date?}`. Setting done toggles the target, which can trigger auto-done.
- `DELETE /api/pins/{id}` · `PUT /api/pins/order` `{date, ids}` · `POST /api/pins/carry-over` `{from_date}`

**Events**
- `GET /api/events?from=&to=&space_id=&person_id=` · `POST /api/events` · `GET|PATCH|DELETE /api/events/{id}` · `PUT /api/events/{id}/people`

**Ideas**
- `GET /api/ideas?space_id=&status=` · `POST /api/ideas` · `PATCH /api/ideas/{id}` (text, space, archive) · `DELETE /api/ideas/{id}` · `POST /api/ideas/{id}/convert` `{space_id, department_id?, title?}`

**People**
- `GET /api/people?q=&space_id=&tag=&tag_kind=&sort=name|birthday|last_contacted` · `POST /api/people` · `GET /api/people/{id}` (full profile + linked tasks and events) · `PATCH /api/people/{id}` · `DELETE /api/people/{id}`
- Whole-list replace for the small collections: `PUT /api/people/{id}/contacts | family | tags | custom-fields | spaces`. Simple and atomic; it fits edit-in-place chip editors.
- `POST /api/people/{id}/logs` · `PATCH /api/contact-logs/{id}` · `DELETE /api/contact-logs/{id}`
- `PUT /api/people/{id}/photo` (multipart) · `DELETE /api/people/{id}/photo` · `GET /api/people/{id}/photo` (protected, ETag caching)
- `GET /api/people/tags?kind=&q=`: tag autocomplete

---

## 4. UI plan

### Architecture
- The App Router handles routing and layouts. Pages are mostly **client components that fetch through TanStack Query**: the data sits behind login and is all personal, so server rendering doesn't buy much.
- TanStack Query gives caching, background refetch and **optimistic updates**: change the cache right away, send the request, roll back and show a toast if it fails.
- A Next.js `middleware.ts` redirects to `/login` when there's no session cookie. The API is still the real gate.
- **Responsive panel.** The same `<DetailPanel>` renders as a right-side sheet on desktop (≥1024 px) and a bottom sheet on phone (shadcn Drawer/vaul). The URL carries `?task=<id>`, so panels can be linked to and the back button closes them.

### Design system
- **Colors.** Defined as CSS variables, with separately tuned light and dark values. Dark mode isn't an inversion: it uses lighter *surfaces* and subtle borders instead of shadows, which are invisible on dark backgrounds.
  - Neutrals: `bg`, `surface`, `surface-raised`, `border-subtle`, `text`, `text-muted`, `text-faint`, built on a slightly warm neutral scale (stone/zinc).
  - Accent `primary`: indigo, used for focus rings, the primary button and selection.
  - Semantic colors, reserved for their meaning only: `danger` red (overdue, late nudge, destructive actions), `waiting` amber, `success` green (done, completion).
  - **Space palette, 10 tokens: slate, blue, sky, cyan, teal, indigo, violet, purple, fuchsia, pink.** Red, green and amber are deliberately left out, so a space color never reads as "overdue", "done" or "waiting". Each token has light and dark variants. The DB stores the token name, not a hex, so both themes work.
- **Typography.** Geist Sans, served locally by `next/font`, with tabular numbers for dates and percentages.
  - Page title: 28/34 semibold (24 on phone)
  - Section: 17/24 semibold
  - Body: 15/22
  - Meta: 13/18 muted
  - Micro (pills): 12/16 medium
- **Spacing.** 4 px grid.
  - Page gutters 16 px on phone, 32 px on desktop.
  - Card padding 16, gaps 12/16, sections 32 apart.
  - Touch targets ≥ 44 px.
- **Shape and depth.** Cards 14 px radius, inputs and buttons 10 px, pills fully rounded. Two shadow levels (`sm` for cards, `lg` for panels and the palette).
- **Motion.** Motion (Framer Motion) at 150–250 ms ease-out, springs for drag.
  - Step check: the check draws, the bar animates.
  - Task done: a small burst + "Done ✓" toast.
  - Panels slide; reordering uses layout animation.
  - `prefers-reduced-motion` turns everything into opacity fades.
- **Icons.** lucide-react. Every icon button gets an `aria-label`. Focus rings are always visible (`focus-visible`).

### Component inventory
- **Shell:** AppShell, Sidebar (desktop), BottomNav (phone), PageHeader, DetailPanel (Sheet/Drawer), CommandPalette (cmdk), ShortcutsDialog ("?").
- **Data display:** ProgressBar (slim, space-colored), ProgressRing, StatusPill, PriorityPill (flag icon, 3 intensities), DueChip (red when overdue), WeightChip (S/M/L), SpaceDot / SpaceBadge, Avatar (photo or colored initials) + AvatarStack, TagChip (hobby/like/dislike tints), RepeatIcon, SkeletonCard.
- **Cards:** TaskCard, StepRow, PinCard, EventRow, OccurrenceRow, BirthdayCard, WaitingCard, SpaceSummaryCard, PersonCard, IdeaCard.
- **Editing:** InlineText, InlineDate (chips: today / tomorrow / next week + calendar), InlineSelect, TagInput, KeyValueEditor, SortableList (dnd-kit), KanbanBoard, SwipeableRow, ConfirmDialog, toasts (sonner, with an `undo` action).
- **States:** EmptyState (icon + one-line hint + action button).

### Screens
- **Home:**
  - Greeting + date.
  - **Focus strip:** three tappable counters (Overdue in red, Today, Waiting late) plus a space filter. Tapping a counter expands that section.
  - Main column: **Overdue → Today → This week** (task and step cards), then **Active tasks** with progress bars.
  - Side column on desktop (stacked on phone): **Today's list preview** (next event + first 3 pins), **Waiting** (late nudges in red at the top), **Birthdays** (avatar, name, "turns 23 · Fri").
  - Bottom: **Space cards** with progress ring, open-task count and space color accent.
- **Today:**
  - **Date chips** (Today, Tomorrow, then the next 5 days, swipeable on phone).
  - A timeline rail with **events** (time on the left), the day's **birthdays**, the **Routine** group (recurring items, repeat icon), then the **pinned list** (draggable, checkable cards with space dot and parent task for steps).
  - The **Due today – pin?** tray, and the **Move unfinished to tomorrow** button.
- **Space:**
  - Header in the space color, with icon, name (edit in place), overall progress ring, and add department / task / idea buttons.
  - **Kanban columns per department** + "No department" on desktop, collapsible sections on phone.
  - Task cards show title, progress bar, due chip, priority pill, status, avatar stack.
  - Below: a **Recurring** strip, **Ideas** for the space, **People** avatars. An overflow menu holds Archive and Delete.
- **Task panel:**
  - Big editable title, live progress bar, and a pill row (status, priority, due date, space/department, people, recurrence).
  - Waiting block (on whom + nudge date) when the status is waiting.
  - **Steps checklist** with drag handles and S/M/L weight chips, an "Add step" input (Enter adds the next one), and notes.
  - Footer actions: Reopen (when done), Move, Pin to today, Delete.
- **Ideas:** a capture box at the top (Enter saves, optional space chip), then a masonry grid of sticky-note cards tinted with their space color. Each card has a hover/long-press menu: Convert, Archive, Delete. A filter offers all / per space / archived.
- **People list:** search, space filter, tag filter and sort selector. Then a grid of PersonCards: avatar, name/nickname, call/email/WhatsApp buttons, next birthday, space dots and "last contacted 12 d ago".
- **Person page:** a profile layout.
  - Header: large avatar, name, quick actions.
  - Sections:
    - Contact (emails/phones with labels, main starred)
    - Family
    - Likes / Dislikes / Hobbies as colored chips
    - Custom fields
    - **Contact log timeline** (add an entry inline)
    - Linked tasks and events
- **Command palette** (Ctrl/Cmd+K, `/`): instant grouped search + recent items. Typing a prefix switches to quick-add (`t ` task, `s ` step, `e ` event, `i ` idea, `p ` person). Light parsing: `#space`, `!high`, `today/tomorrow/fri`.
- **Shortcuts:** `N` new task · `T` Today · `H` Home · `P` People · `I` Ideas · `/` search · `?` cheat sheet.
- **Login:** a centered card, password field only, and the app mark.
- **Phone extras:**
  - PWA manifest (standalone display, theme color per scheme, icons 192/512 + maskable). Installable; no offline mode in v1.
  - Bottom nav: Home / Today / + / People / Spaces.
  - Swipe gestures (decision 29). Bottom sheets everywhere instead of modals.

We'll also add a **`/design` route** (dev only) that renders every token and component in both themes. It's the reference page for the ui-reviewer subagent and for screenshots.

---

## 5. Phase-by-phase build plan

Each phase is split into features. Every feature gets **its own branch, small commits, and a stop for you to test**. Commit messages follow Conventional Commits (`feat(tasks): auto-done on last step`).

### Phase 0: Setup
**What gets done:**
1. You move the folder out of OneDrive (decision 1).
2. `git init`, plus a `.gitignore` covering `.env*` (except `.env.example`), `uploads/`, `node_modules`, `.venv`, `.next`, `__pycache__` and `.claude/settings.local.json`.
3. **You run `/init`**. It reads the repo and improves the draft CLAUDE.md. Then we add the rules below.
4. **You create `.claude/settings.json`** with the permissions below (I'll give you the file content). We check it with `/permissions`.
5. First commit, then `gh repo create` (you confirm public or private).

**Claude Code features:**
- **CLAUDE.md:** project memory loaded into every session. It's how rules like "stop after each phase" survive across sessions.
- **Permissions:** allow-lists remove repetitive prompts for safe commands; deny rules protect secrets.
- Plan mode was used for this proposal.

**CLAUDE.md (proposed content):**
```markdown
# Organizy
Single-user personal productivity app (spaces → departments → tasks → steps, Today planner, recurring tasks, ideas, people).
Full spec: @docs/SPEC.md (source of truth; ask before deviating).

## Stack
Backend: FastAPI · Python 3.12 · SQLAlchemy 2.0 (sync, psycopg 3) · Pydantic v2 · Alembic · PostgreSQL 17 · uv
Frontend: Next.js App Router (TS) · Tailwind · shadcn/ui · lucide-react · Motion · dnd-kit · cmdk · sonner · TanStack Query

## Commands
- DB (dev): `docker compose -f docker-compose.dev.yml up -d`
- Backend: `cd backend && uv run fastapi dev app/main.py` · tests `uv run pytest` · lint `uv run ruff check . && uv run black --check .`
- Migrations: `uv run alembic revision --autogenerate -m "..."` then `uv run alembic upgrade head`
- Frontend: `cd frontend && npm run dev` · `npm run lint` · `npm run typecheck` · `npm test` · `npm run gen:api` (regenerate API types)
- Full stack (Phase 3+): `docker compose up --build`

## Architecture rules
- Business rules live in backend/app/services, never in routers or the frontend.
- "Today"/dates always come from app/core/clock.py (TZ from env). Never use date.today() or datetime.now() directly.
- Progress is computed server-side only. Clients never send it.
- Status/kind fields are text + CHECK constraints, not Postgres enums.
- Frontend calls the API only through src/lib/api with generated types. Mutations are optimistic via TanStack Query.
- UI: no tables or grids; use cards/lists; design tokens only (no raw hex); both themes; respect reduced motion.

## Privacy
- People data is real personal data: never put real names, emails or phones in code, seeds, tests, fixtures or commit messages. Fake people only (example.com).
- Never read or print .env files or secrets.

## Workflow
- I'm learning Claude Code: briefly explain each decision and name the Claude Code feature we're using.
- One feature per branch, small Conventional Commits, show me the diff before committing.
- Write failing tests first for business rules, then implement.
- Stop at the end of each phase (and each feature) so I can test. Give a recap: "Claude Code features used" + one tip.
- Ask before adding a dependency or changing the stack.
```

**`.claude/settings.json` (committed, shared). Personal overrides go in `settings.local.json`, which is gitignored:**
```json
{
  "permissions": {
    "allow": [
      "Bash(uv run pytest:*)", "Bash(uv run ruff:*)", "Bash(uv run black:*)",
      "Bash(uv run alembic upgrade:*)", "Bash(uv run alembic revision:*)", "Bash(uv run alembic current:*)",
      "Bash(npm run lint:*)", "Bash(npm run typecheck:*)", "Bash(npm test:*)", "Bash(npm run test:*)",
      "Bash(npm run build:*)", "Bash(npm run gen:api:*)",
      "Bash(docker compose ps:*)", "Bash(docker compose logs:*)", "Bash(docker compose up:*)",
      "Bash(docker compose -f docker-compose.dev.yml up:*)", "Bash(docker compose build:*)",
      "Bash(git status:*)", "Bash(git diff:*)", "Bash(git log:*)", "Bash(git branch:*)", "Bash(git switch:*)",
      "Bash(gh pr view:*)", "Bash(gh run view:*)", "Bash(gh run list:*)", "Bash(gh pr checks:*)"
    ],
    "ask": [
      "Bash(git commit:*)", "Bash(git push:*)", "Bash(git merge:*)", "Bash(git rebase:*)",
      "Bash(uv add:*)", "Bash(npm install:*)", "Bash(npx:*)",
      "Bash(uv run alembic downgrade:*)", "Bash(docker compose down:*)", "Bash(docker volume:*)",
      "Bash(gh pr create:*)", "Bash(gh repo:*)"
    ],
    "deny": [
      "Read(./.env)", "Read(./**/.env)", "Read(./**/.env.*.local)",
      "Bash(git push --force:*)", "Bash(git reset --hard:*)", "Bash(rm -rf:*)",
      "Bash(docker compose down -v:*)"
    ]
  }
}
```

**Why these rules:**
- Read-only and test commands run freely.
- Anything that rewrites git history, installs dependencies, or **deletes the Postgres volume** (`down -v` would wipe your contacts) asks first or is denied.
- Claude Code here also has a PowerShell tool. In Phase 0 we confirm with `/permissions` how its rules are written and add the same entries for it.

### Phase 1: Backend
**Order of work** (one branch per item; tests come before code wherever there's a rule):
1. **Skeleton:**
   - `docker-compose.dev.yml` (Postgres 17 + named volume + healthcheck, plus a second `organizy_test` DB)
   - `core/config.py`, `core/db.py`, `core/clock.py`
   - `/health`, `.env.example`
   - ruff/black/pytest config
2. **Models + first Alembic migration** (all tables above; we review the autogenerated migration together).
3. **Auth:**
   - argon2 hash in `ADMIN_PASSWORD_HASH`, generated with `uv run python -m app.cli hash-password`. Gotcha: argon2 hashes contain `$`, which must be written as `$$` in docker-compose env files.
   - sessions table, `require_session` dependency, slowapi rate limit, Origin check.
4. Spaces + departments (incl. the delete-preview/cascade tests).
5. **Tasks + steps, test-first:**
   - progress math and rounding
   - auto-done only on the transition
   - reopen
   - manual done shows 100
   - adding/unchecking a step doesn't change status
   - move between departments and spaces
   - department delete → "No department"
6. **Recurring + agenda + pins, test-first:**
   - daily, weekdays and monthly cases (31st → Feb 28/29, Apr 30)
   - start/end dates
   - Today in Algiers at 23:30 UTC (already tomorrow there)
   - week boundaries with WEEK_START
   - carry-over skips occurrences
   - checking a pinned step updates its task
7. Events, ideas (convert).
8. **People, test-first:**
   - birthdays (Feb 29, year-end wrap, age)
   - delete keeps "waiting on" as text
   - one main contact per kind
   - photo upload validation + EXIF strip, protected photo route
9. Dashboard + search.
10. Seed CLI (`seed base`, `seed demo`), then a README backend section.

**Claude Code features:**
- **Hooks.** A `PostToolUse` hook in `.claude/settings.json` (matcher `Edit|Write`) runs `.claude/hooks/format_python.py`. The script reads the edited file path from the hook's JSON input and runs `ruff check --fix` + `black` on `.py` files. A hook is deterministic: Claude can't forget to format.
- **Checkpoints / rewind.** Press `Esc Esc` or run `/rewind` to roll the conversation and/or code back to before a prompt. We'll try it on purpose once. It's local undo; git remains the real history.
- **Test-first.** I'll write the failing rule tests, show you them going red, then make them pass. You'll see how precise acceptance criteria steer Claude.

### Phase 2: Frontend
**Order of work:**
1. Scaffold:
   - Next.js + TS + Tailwind + shadcn init
   - ESLint/Prettier, Vitest + Testing Library
   - `/api` rewrite, `gen:api` script
   - **Live preview setup**: the `/dev/preview` phone frames, and testing USB port forwarding to your Android phone
2. **Design system:** tokens in globals.css, light/dark themes (next-themes, system default), the primitives above, and the `/design` page.
3. App shell (sidebar, bottom nav, theme), login, the auth middleware, the TanStack Query setup with error toasts.
4. Home.
5. Space page (Kanban + dnd).
6. Task panel (steps, live progress, celebration).
7. Today (chips, timeline, pins, carry-over).
8. Ideas.
9. People list + person page (+ photo upload).
10. Command palette, quick add, shortcuts, recently viewed, Undo toasts.
11. PWA manifest/icons, swipe gestures, phone polish, empty states and skeletons everywhere.
12. Frontend tests: progress/date utilities, a couple of component tests (TaskCard, StepRow), and an optimistic-update hook test.

**Claude Code features:**
- **Subagents.** We create `.claude/agents/code-reviewer.md` (checks correctness, spec rules, security and tests on the diff) and `.claude/agents/ui-reviewer.md` (checks against the design principles: tokens, both themes, touch targets, a11y, empty and loading states). Each runs in its own context window, so its review doesn't fill up our main conversation. We run them before each commit.
- **Screenshots.** You paste a screenshot (or drag it in) and say "this card feels cramped, fix spacing". This is the fastest design-fix loop.
- **Context management:**
  - `/clear` between unrelated features: a fresh context, with CLAUDE.md still loaded.
  - `/compact` partway through one long feature: it summarizes and keeps going.
  - `/context` shows what is using the context window.

### Phase 3: Docker
**What gets done:**
- **Backend Dockerfile:**
  - multi-stage: a `uv` builder stage installs from `uv.lock` into `/app/.venv`
  - runtime stage is `python:3.12-slim` with only the venv and app code, running as a non-root `app` user with a `HEALTHCHECK`
- **Frontend Dockerfile:**
  - multi-stage: deps → build with Next.js `output: "standalone"` → `node:alpine` runtime
  - only `.next/standalone` + static files are copied, running as a non-root user
  - this typically gets the image from ~1 GB down to ~150 MB
- **`docker-compose.yml`:**
  - `postgres` (volume `pgdata`, healthcheck)
  - a one-shot **`migrate`** service (`alembic upgrade head && python -m app.cli seed base`)
  - `backend` (waits for `migrate` to complete successfully, volume `uploads`)
  - `frontend` (proxies `/api` to `backend` over the internal network, the only published port)
- Why a separate migrate step: migrations shouldn't race when you scale backend replicas. The same pattern maps to an Azure Container Apps *job* later.
- `.dockerignore` files, and the README run instructions.

**Claude Code feature: Skills / custom slash commands.** You create `.claude/skills/phase-check/SKILL.md`, which defines `/phase-check`:
1. run backend lint + tests
2. run frontend lint + typecheck + tests
3. `docker compose up -d --build`
4. poll `/health`
5. report a pass/fail summary

It encodes a repeatable workflow once, and you trigger it with one word.

### Phase 4: CI
**What gets done:**
- **`.github/workflows/ci.yml`**, on push and PR:
  - jobs `backend` (uv cache → ruff → black --check → pytest against a `postgres` service container)
  - `frontend` (npm ci → lint → typecheck → test → check that the generated API types are up to date)
  - `docker` (`needs: [backend, frontend]`, buildx with GitHub Actions cache, builds both images)
  - Optional: push images to GHCR on `main`, ready for Azure later.
- Dependabot for pip, npm, actions and docker.
- Branch protection on `main` requiring CI.
- README: architecture diagram (Mermaid), setup, env vars, screenshots (light + dark, desktop + phone).

**Claude Code features:**
- **GitHub via `gh` CLI or the GitHub MCP server.** Claude opens PRs, reads failing CI logs (`gh run view --log-failed`) and fixes them. MCP is the general mechanism for giving Claude tools for external systems.
- **Claude Code GitHub Actions.** Run `/install-github-app`, then mention `@claude` in a PR comment to get a review or a fix pushed to the branch.

**Throughout:**
- One feature per prompt with acceptance criteria.
- `@file` references.
- Review every diff before accepting.
- One branch per feature.

---

## Verification (how each phase is checked)
- **Phase 0:** `git status` is clean. `/permissions` shows the rules. `/memory` shows CLAUDE.md loaded.
- **Phase 1:** `docker compose -f docker-compose.dev.yml up -d` → `uv run alembic upgrade head` → `uv run pytest` is green (rule tests cover every case listed in the spec's Tests line). Swagger UI at `/docs`:
  - login, then a step check auto-completes the English Coffee task
  - a request without a cookie gets 401
  - the 6th login attempt in a minute gets 429
- **Phase 2:**
  - `npm run lint && npm run typecheck && npm test`
  - a manual walkthrough of every screen, in both themes, at desktop and phone width (Chrome devtools)
  - install the PWA on your phone over the LAN
  - ui-reviewer subagent pass
- **Phase 3:**
  - `docker compose up --build` from a clean clone works with only `.env` filled in
  - the containers run as non-root (`docker compose exec backend id`)
  - image sizes are checked with `docker images`
  - `/phase-check` passes
- **Phase 4:** a PR shows all CI jobs green. A deliberately broken test turns CI red, and Claude fixes it from the CI log.
