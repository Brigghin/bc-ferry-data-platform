# Plan: bring the READMEs up to date

Audience: developers visiting the repo (and the owner coming back later). Keep each README concise; fix what is wrong or missing, keep sections that are still accurate. Verify every claim against the code/config before writing it. Do not invent hosts, URLs, or features. Do not commit.

## Step 1 — Root `README.md`

- Describe the whole project: FastAPI backend + React/Vite frontend ("Coastline"). Drop "(WIP)" unless the owner's wording elsewhere suggests keeping it — keep it if unsure.
- Add a short "How it works" data flow: BC Ferries API (`https://www.bcferriesapi.ca/v2/`) → `POST /ferries/refresh` (called every 10 minutes by an external cron service, cron-job.org, with the `X-Refresh-Token` header) → Neon Postgres → `GET /ferries/` → frontend. Backend is hosted on Render at `https://bc-ferry-data-platform.onrender.com` (free tier: it sleeps when idle and cold-starts in up to ~1 minute). Do not name a frontend host (unknown).
- Fix repository layout: `backend/`, `frontend/`, `Dockerfile` (not `DockerFile`; backend image — check its base Python version), `neon.ts` (Neon config), `.github/workflows/` (CI: Pytest, Pylint, ESLint, Hadolint, aggregate CI result + PR comment; Docker build; Release Please; Dependabot auto-merge; manual `refresh-ferries`). Verify against `ls .github/workflows`. `compose.yaml` is being deleted — don't mention it.
- "Run locally": backend and frontend quick start (frontend dev server proxies to the hosted backend, so a local backend is optional), linking to each sub-README.
- Keep the Releases and Dependabot auto-merge sections; only fix factual errors.

Acceptance: every file/workflow named exists; commands match `backend/pyproject.toml` / `frontend/package.json`.

## Step 2 — `frontend/README.md`

- Replace "with date, route, and text filters" (wrong) with what the app actually does, verified in `frontend/src/App.tsx`:
  - pick origin and destination terminals (with swap);
  - one day at a time, ‹ / › buttons beside the date step through the days the API returns (today plus any next-day sailings in the feed);
  - columns: departure (actual, with scheduled time shown when it differs), arrival (actual, or an "ETA" = departure + route sailing duration when upstream gives none), ferry, fill % meter;
  - arrived sailings are greyed out — status `arrived`, or `departed` with a passed ETA, because upstream never marks Swartz Bay departures arrived;
  - cancelled sailings: struck-through time, red "Cancelled" label, fill shown as 0%;
  - a "Waking up the server…" message if loading takes over 3 seconds (Render cold start).
- Use `sh` code blocks instead of `powershell` (commands are the same).
- Check the CORS sentence against the backend (grep for CORS in `backend/src`); keep, fix, or drop accordingly.

Acceptance: each described behaviour exists in `App.tsx`; no mention of features that don't exist.

## Step 3 — `backend/README.md`

- Verify the Python version (`backend/.python-version`, `pyproject.toml` `requires-python`) and fix if it is no longer 3.14.
- Endpoints: verify against `backend/src/bc_ferry_data_platform/routers/`. Update the `GET /ferries/` example so timestamps match what the API really returns (UTC `Z` strings, e.g. `"2026-11-25T14:00:00Z"`, and `observedAt` as a UTC timestamp).
- Rewrite "Automatic refresh": the 10-minute schedule now runs on cron-job.org (POST to `https://bc-ferry-data-platform.onrender.com/ferries/refresh`, header `X-Refresh-Token`). The GitHub `refresh-ferries` workflow is manual-only (`workflow_dispatch`), still using the `FERRY_REFRESH_URL` variable and `FERRY_REFRESH_TOKEN` secret. Add token rotation: generate with `python3 -c "import secrets; print(secrets.token_urlsafe(32))"`, then update `REFRESH_TOKEN` on Render, the cron-job.org header, and the GitHub secret. Note cold starts can exceed cron-job.org's 30 s timeout occasionally.
- Add a short "Upstream data quirks" note: Swartz Bay departures (e.g. SWB→TSA) stay `departed` and never get `actualArrivalTime`; the frontend estimates arrival from the route duration.
- Use `sh` code blocks except where the commands are PowerShell-specific (the Alembic env-var snippet) — for that one, add an equivalent `sh` version and keep the PowerShell one.

Acceptance: README matches the routers, settings and workflow file; no secrets or token values included.

## Step 5 — Root README intro rework (owner request)

Edit only `README.md`. The owner is a DevOps-focused engineer; the full-stack app exists to give the automation something real to run. Readers are recruiters/engineers evaluating DevOps skill.

- Delete the whole "## Repository layout" section.
- Intro (keep the owner's current first sentence wording style; drop nothing else they wrote): say what each piece runs on — frontend: React + Vite on a **Render static site**; backend: FastAPI (uv, Docker) on a **Render web service** (`https://bc-ferry-data-platform.onrender.com`, free tier, cold starts); database: **Neon** serverless Postgres (managed by `neon.ts`; check what its branch policy does and mention it if notable). Don't invent a frontend URL or a Neon region.
- Add a "## Automation" section (one solid paragraph, or a short paragraph + tight bullets), framed from a DevOps perspective: this is the main point of the project, the app is the workload. Verify every claim by reading `.github/workflows/*`, `Dockerfile`, `release-please-config.json`, `neon.ts`. Cover what is actually there, e.g.: CI on PRs (Pytest, Pylint, ESLint, Hadolint) with an aggregate required "CI result" gate; PR result comments posted by a separate workflow that never checks out/executes PR code; Docker build (what it builds/pushes, where — check); multi-stage, non-root, pinned Docker image; Release Please with a GitHub App token, Conventional Commits, auto-merged release PRs; Dependabot updates auto-merged only after CI passes; scheduled data refresh via external cron (cron-job.org) hitting a token-protected endpoint, with a manual GitHub workflow fallback; Neon branch policy. Confident, plain, no marketing fluff.
- Keep "How it works", "Run locally", "Releases", "Dependabot auto-merge" sections; remove any now-duplicated sentence. Leave the "(WIP)" title alone.

Acceptance: every automation claim traceable to a file; no repository-layout section; no invented URLs.

## Step 4 — Review

Send `reviewer` this file and the three changed READMEs.
