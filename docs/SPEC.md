# Project: Organizy — personal productivity app

## Context
I'm a 4th-year Cloud & DevOps engineering student, President of Horizon's Club (a student club at my school, ENSTTIC), and community manager at Yacine Academy. I work on many things at once. I want ONE personal app (single user: only me) to organize everything I work on, each in its own space, with a daily view of what I need to do, and to keep track of the people I work and live with.

This is also a DevOps portfolio project, so I want clean architecture, Docker, CI/CD, and deployment-ready code.

## My two goals
1. BUILD THE APP: a real app I use every day, with a beautiful design and production-quality code.
2. LEARN CLAUDE CODE: use this project to learn how to work with Claude Code properly (planning, CLAUDE.md, permissions, hooks, subagents, skills/slash commands, context management, checkpoints, MCP, GitHub integration).
Both goals matter equally. Don't just do the work: teach me the Claude Code feature that fits each step (see "Learning Claude Code" at the end).

## Core structure
Space → Department → Task → Step
People are a separate section, linked to spaces, tasks and events.

### Space
- Anything I work on, each in its own box (e.g. Horizon, Yacine Academy, Studies, Career)
- I can create, rename, archive, unarchive, delete and reorder spaces
- Each space has a name, color and icon/emoji
- Each space has its own page showing its departments, tasks, progress, ideas and people
- Archive is the main action in the UI (hides the space, keeps all its data)
- Delete is permanent: it deletes the space with all its departments, tasks, steps, ideas and pins, after a confirmation dialog that shows how many tasks will be deleted
- Linked events are NOT deleted; their space link is set to empty
- Linked people are NOT deleted; only their link to that space is removed

### Department
- Sub-areas inside a space. NOTHING is hardcoded.
- Any space can have departments. I add them manually from the UI (add / rename / reorder / delete)
- A space can have zero departments
- Examples: Horizon → its departments; Yacine Academy → Instagram, Club; Studies → AZ-104, TPs
- Deleting a department never deletes its tasks; they move to "No department" in the same space

### Task
- Belongs to a space, optionally to a department
- Fields: title, description/notes, due date (optional), priority (low / medium / high), status (todo / in progress / waiting / done), progress %, created/updated/completed timestamps
- "Waiting" status = blocked on someone else (admin reply, partner answer):
  - stores "waiting on" and a "nudge on" date
  - "waiting on" is either a linked person (from People) or free text (e.g. an organization like "LabLabee")
  - flagged red on the dashboard when the nudge date has passed
- A task can be linked to people (optional, many-to-many), e.g. the people involved in it
- A task can be moved to another department in the same space
- A task can be moved to another space: its department resets to "No department"
- A task can be recurring (see Recurring tasks)

### Step
- Checklist items inside a task
- Fields: title, weight, done (bool), optional due date, order
- Weight: Small (1), Medium (2), Large (3)
- Steps can be reordered with drag & drop

### Progress and status rules
- Progress of a task = sum of weights of done steps ÷ total weight × 100 (rounded to an integer)
- A task with no steps: progress is 0% or 100% depending on done status
- Progress is computed by the backend, never sent by the client
- Auto-done: when checking a step makes progress go from below 100% to 100%, the task becomes "done" and completed_at is set
- Auto-done only fires on that transition (a step check), not continuously. So:
  - Reopening a task whose steps are all done sets it to "in progress" and it STAYS open
  - Adding a new step to a done task does not reopen it automatically
- Unchecking a step on a done task does not reopen it automatically (I reopen it myself)
- Marking a task "done" manually while some steps are unchecked:
  - the steps are left as they are
  - the task displays 100% while its status is "done"
- Reopening a task (done → todo / in progress) clears completed_at; progress returns to the step-based value

## Features

### 1. Home dashboard (all spaces)
- Sections: Overdue / Today / This week
- Waiting items, with overdue nudges highlighted in red
- Active tasks with progress bars
- Upcoming birthdays (next 7 days), with the person's name and age if the birth year is known
- Summary cards per space (number of open tasks, average progress)
- Filter by space
- Archived spaces and their tasks are hidden from the dashboard

### 2. Space page
- Shows departments as columns or groups, with their tasks, plus a "No department" group
- Each task shows its progress bar, due date, priority and status
- Space-specific ideas list
- People linked to this space
- Button to add a department, task or idea directly in this space

### 3. Task detail
- Edit all fields
- Manage steps: add, check, set weight, reorder, delete
- Live progress bar
- Link / unlink people
- Move to another department or space
- Reopen button when the task is done

### 4. Today (daily schedule)
- NOT time blocks: an ordered list of the tasks or single steps I pin to a day
- A pin = (date, task OR step, order, done)
- I can reorder the list (drag & drop) and check items off
- Checking off a pinned step also checks that step in its task (and updates progress)
- Checking off a pinned task marks the task done
- Timed events: meetings or events with a specific time (e.g. 14:00 meeting), with title, date, time, optional location/notes, an optional linked space and optional linked people. Shown at the top of Today, sorted by time
- Events are one-off only in v1 (no recurring events)
- Birthdays of the day are shown at the top of Today
- Recurring task occurrences automatically appear on their days
- "Move unfinished to tomorrow" button: moves unfinished PINS to tomorrow in one click
  - It does NOT move recurring occurrences: a missed occurrence stays missed on its own day
- I can view and plan upcoming days (tomorrow, the next 7 days)

### 5. Recurring tasks
- Stored as one template task + an occurrences table (one row per date, with done status)
- Occurrences are generated for the days being displayed (no need to pre-create them for the future)
- Repeat options:
  - daily
  - specific weekdays (e.g. Mon/Wed/Fri; picking one weekday = weekly)
  - monthly on day N (if the month is shorter, e.g. day 31 in February, it falls on the last day of the month)
- Optional start date and end date
- Examples: "AZ-104 study" every day, "Instagram post" Mon/Wed/Fri
- Each occurrence can be checked off independently
- Recurring tasks have NO steps in v1 (progress is not used for them)

### 6. Ideas inbox
- Quick capture: text + optional space
- Global inbox + per-space ideas
- Convert an idea into a task in one click (choose space/department)
- Archive or delete ideas

### 7. Quick add
- Global quick-add bar (keyboard shortcut, e.g. Ctrl+K) to add a task, step, event, idea or person fast

### 8. People
A personal contacts book for everyone I deal with: club members, Yacine Academy contacts, partners, friends and family.

Person fields:
- Basics: full name, nickname (optional), email, phone, birthday, photo (optional), notes
  - Birthday: day and month required, year optional (age is shown only if the year is known)
  - A Feb 29 birthday is shown on Feb 28 in non-leap years
  - A person can have several emails/phones, each with a label (personal, work…), one marked as main
- Family: a list of entries, each with a name and a relation (father, mother, brother, sister, spouse, child, other); covers parents and siblings with no fixed limit
- Hobbies: tag list
- Likes: tag list (e.g. food they prefer)
- Dislikes: tag list (e.g. food they hate)
- Custom fields: label + value pairs, for anything else (e.g. "Study year: 3rd", "Instagram: @…"), so new info doesn't need a database change
- Spaces: a person can be linked to zero or more spaces (e.g. Horizon, Yacine Academy); people with no space are "Personal"

Contact log:
- Short dated notes per person (date + text), e.g. "Nov 20 — talked about the LabLabee partnership"
- "Last contacted" date = date of the latest log entry, shown on the person card

People pages:
- People list: search by name, filter by space, filter by tag (hobby/like/dislike), sort by name / upcoming birthday / last contacted
- Person page: all fields, family, tags, custom fields, contact log, and the tasks and events linked to this person
- Add / edit / delete a person (delete asks for confirmation; tasks and events are kept and only lose the link; a task "waiting on" that person keeps the person's name as free text)

Privacy:
- People data is real personal data about others: it lives only in my database, behind login, never in the repo
- Seed data and tests use fake people only

## Dates and time zone
- Time zone comes from env: TZ=Africa/Algiers
- The backend computes "today", "this week", overdue, nudge dates and birthdays in that time zone, never in UTC
- Timestamps (created/updated/completed) are stored in UTC and shown in local time
- Due dates, nudge dates and birthdays are plain dates (no time)
- A week starts on Sunday by default (configurable via env WEEK_START)

## UI / UX — design is a priority
The app must look beautiful and modern, and let me find any information in seconds. NO data tables, NO admin-panel look, NO spreadsheet-style grids anywhere. Think of polished apps like Linear, Things 3, Todoist or Notion Calendar, not a CRUD back-office.

### Design principles
- Cards, lists and visual blocks instead of tables
- Information at a glance: the most important thing on each screen is the biggest and first (what's overdue, what's next, who's waiting)
- Anything reachable in 2 taps/clicks max from Home
- Edit in place: click a title, date, priority or tag to change it directly, no separate "edit form" pages for small changes
- Progressive disclosure: cards show the essentials; details open in a side panel (desktop) or bottom sheet (phone) without leaving the page
- Calm, not cluttered: generous spacing, few borders, soft shadows, rounded corners (12–16px)
- Color with meaning: each space's color is used consistently (sidebar dot, card accent, progress bar); red only for overdue / late nudges; amber for waiting; green for done
- Consistent visual language for status and priority (small colored pills/icons, not text columns)

### Visual style
- Modern typography (Inter or Geist), clear size hierarchy (page title / section title / body / meta)
- Neutral background with the space colors as accents
- Icons everywhere they help scanning (lucide icons)
- Progress shown as slim progress bars on cards and progress rings on space summary cards
- Avatars (photo or colored initials) for people
- Friendly empty states (illustration or icon + one-line hint + action button), never a blank screen
- Skeleton loaders instead of spinners
- Subtle, fast animations (150–250ms): checking a step, completing a task (small celebration), opening panels, reordering. Respect "reduce motion"
- Dark mode + light mode, both designed properly (not just inverted), following the system setting by default

### Screen-by-screen
- Home: greeting + date, then "Focus" strip (overdue + today count), then cards: Today's list preview, Waiting (late nudges in red), Upcoming birthdays, Space cards with progress rings and open-task counts
- Today: vertical timeline feel — events with their time at the top, then the ordered list of pinned items as checkable cards, recurring items marked with a small repeat icon; a day switcher (today / tomorrow / next 7 days) as swipeable date chips
- Space page: header with the space color, icon and overall progress; departments as Kanban-style columns on desktop, collapsible sections on phone; task cards show title, progress bar, due date, priority pill, status, linked people avatars
- Task detail: side panel / bottom sheet with big title, live progress bar, steps checklist with weight chips (S/M/L), drag handles to reorder
- Ideas: masonry or sticky-note style cards, quick capture box at the top
- People: grid of person cards (avatar, name, main contact buttons, next birthday, space colors); person page as a profile: header with avatar and quick actions (call / email / WhatsApp link), then sections for family, likes/dislikes/hobbies as colored tag chips, custom fields, contact log as a timeline, linked tasks and events

### Fast access
- Command palette (Ctrl+K / Cmd+K): search everything (tasks, spaces, people, ideas) AND quick-add from the same box
- Keyboard shortcuts on desktop (e.g. N = new task, T = go to Today, / = search), with a "?" cheat sheet
- Global search with instant results grouped by type
- Recently viewed items for quick return
- Optimistic UI: changes appear instantly, saved in the background, with a toast and Undo for deletes/moves

### Phone (first-class, not an afterthought)
- Organizy is mainly an ANDROID phone app: an installable PWA (Chrome WebAPK), designed phone-first (412×915), with desktop as the secondary layout. Decided 2026-11-27.
- Android extras: the back gesture closes sheets and panels, safe areas, a status-bar color per theme, app shortcuts (Today / Quick add / New idea), a share target (share text from any app into Ideas), haptics on check/complete, touch targets of at least 48dp
- Live preview during development: hot reload, a dev-only /dev/preview page with phone frames, and the real phone through USB port forwarding
- PWA: installable on my phone's home screen (web app manifest, app icons, theme color, standalone display). No offline mode in v1
- Bottom navigation: Home, Today, People, Spaces, + (quick add)
- Floating "+" button for quick add
- Swipe gestures on task cards: swipe right = done, swipe left = pin to today / move
- Large touch targets (min 44px), bottom sheets instead of modals, tap-to-call / tap-to-email
- Sidebar on desktop: Home, Today, Ideas, People, then the list of spaces (with their colors)

### Feedback
- Toasts for feedback (with Undo where it makes sense)
- Confirmation dialogs only for permanent deletes
- Accessible: good contrast in both themes, visible keyboard focus, labels on icon buttons

## Tech stack
- Backend: FastAPI (Python 3.12), SQLAlchemy 2.0, Pydantic v2, PostgreSQL, Alembic migrations
- Frontend: Next.js (App Router, TypeScript), Tailwind CSS
- UI libraries: shadcn/ui (components), lucide-react (icons), Framer Motion (animations), dnd-kit (drag & drop), cmdk (command palette), sonner (toasts), TanStack Query (data fetching + optimistic updates)
- Photo uploads: stored on a mounted volume locally (designed so it can move to Azure Blob Storage later); size limit and image type check
- Auth:
  - single user, password login (bcrypt/argon2 hashed password from env)
  - session in an httpOnly, Secure, SameSite cookie (no token in localStorage)
  - rate limiting on the login route (e.g. 5 attempts per minute)
  - every API route protected except /health and /auth/login (photos are served through a protected route too)
- Tests: pytest for the backend (especially progress calculation, auto-done/reopen rules, recurring logic incl. month-end cases, time zone "today" logic, department deletion behavior, upcoming-birthday logic incl. Feb 29 and year-end wrap, and person deletion behavior); basic frontend tests
- Code quality: ruff + black (Python), ESLint + Prettier (TS)

## DevOps
- Monorepo: /backend, /frontend, docker-compose.yml, .github/workflows
- Dockerfiles for backend and frontend (multi-stage, small images, non-root user)
- Phase 1 uses a small docker-compose.dev.yml with only PostgreSQL (with volume); the backend runs locally
- Phase 3 adds the full docker-compose: backend, frontend, postgres (with volume), uploads volume
- Config through environment variables, with a .env.example
- GitHub Actions CI: lint → tests → build Docker images on every push/PR
- Health check endpoint (/health)
- Deployment-ready for Azure later (I'll decide the service: App Service / Container Apps); don't deploy yet
- Clear README: setup, run locally, env vars, architecture diagram, screenshots of the UI (light + dark, desktop + phone)

## Seed data (for first run)
- Spaces:
  - Horizon (no departments yet, I'll add them)
  - Yacine Academy (departments: Instagram, Club)
  - Studies (departments: AZ-104, TPs)
  - Career (no departments)
- Tasks in Horizon:
  - "English Coffee" event, due Dec 3 2026, with weighted steps:
    authorization (Large), room booking (Medium), poster (Small), announcement (Small), recap post (Small)
  - "LabLabee partnership", status waiting (proposal sent), waiting on LabLabee
  - "Metwork partnership", status waiting (WhatsApp message sent), waiting on Metwork
- Recurring task in Studies / AZ-104: "AZ-104 study", daily
- People: 3 FAKE people (made-up names, example.com emails, fake phones), with family, tags, custom fields and a contact log entry; one with a birthday in the next 7 days so the dashboard shows it
- Seeding runs only once (only if the database is empty)

## Out of scope for now (design so they can be added later)
- Instagram content calendar (posts, captions, max 5 hashtags per post)
- Stats: completed tasks per week per space, progress charts
- Notifications/reminders (including birthday reminders)
- Recurring events, steps on recurring tasks, offline mode
- Importing contacts from my phone / exporting people (vCard/CSV)

## How I want to work with you
1. First propose: the folder structure, the data model (tables, fields, relations), the API endpoints, AND the UI plan (layout of each screen + the design system: colors, typography, spacing, components). WAIT for my OK before writing code.
2. Then build step by step, and stop after each phase so I can test:
   - Phase 0: setup (repo, CLAUDE.md, permissions)
   - Phase 1: backend (models, migrations, API, auth, tests) + Postgres in docker-compose.dev.yml
   - Phase 2: frontend (design system first, then pages, components, API integration, PWA)
   - Phase 3: Docker + full docker-compose
   - Phase 4: GitHub Actions CI
3. Briefly explain DevOps and architecture decisions so I learn from them.
4. Use clear git commits per feature.

## Learning Claude Code (goal 2)
At each phase, teach me the Claude Code feature listed below: explain in 2–3 lines what it is and why it fits here, show me the exact command or file, and let ME run or create it when it's a one-time setup step. At the end of each phase, give me a short recap: "Claude Code features you used in this phase" + one tip.

- Phase 0 — Setup
  - CLAUDE.md: run /init, then add project rules (stack, commands, conventions, "stop after each phase", "explain decisions")
  - Keep this spec in the repo as docs/SPEC.md and reference it from CLAUDE.md
  - Permissions / settings: allow safe commands (pytest, ruff, npm run lint, docker compose) without asking every time; keep risky ones on "ask"
- Proposal step — Plan mode
  - Use plan mode (Shift+Tab) for the proposal: Claude Code plans without editing files until I approve
- Phase 1 — Backend
  - Hooks: auto-run ruff/black after Python files are edited
  - Checkpoints / rewind: how to undo a bad change
  - Test-first workflow: ask Claude Code to write failing tests for the progress and recurring rules, then make them pass
- Phase 2 — Frontend
  - Subagents: create a "code-reviewer" (and maybe a "ui-reviewer") agent in .claude/agents to review each feature before committing
  - Pasting screenshots of the UI to Claude Code to fix design issues
  - Context management: when to use /compact and when to use /clear between features
- Phase 3 — Docker
  - Skills / custom slash commands: create my own command (e.g. /phase-check that runs lint + tests + docker compose up and reports the result)
- Phase 4 — CI
  - MCP: connect GitHub (or use the gh CLI) so Claude Code can open PRs and read CI results
  - Claude Code GitHub Actions: try mentioning @claude on a pull request
- Throughout
  - Writing good prompts: one feature per prompt, clear acceptance criteria, reference files with @
  - Git workflow with Claude Code: one branch per feature, small commits, reviewing diffs before accepting
