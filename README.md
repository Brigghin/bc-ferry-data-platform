# BC Ferry Data Platform

A full-stack app that collects BC Ferries sailing data and shows it in a web app ("Coastline"), with automated CI, releases, container builds and dependency updates.

- **Frontend:** React + Vite on a Render static site at <https://bc-ferry-data-platform-frontend.onrender.com>.
- **Backend:** FastAPI (managed with uv, packaged with Docker) on a Render web service at `https://bc-ferry-data-platform.onrender.com`.
- **Database:** [Neon](https://neon.com) serverless Postgres, with branch settings managed in `neon.ts`.

## How it works

1. The [BC Ferries API](https://www.bcferriesapi.ca/v2/) is the upstream data source.
2. An external cron service ([cron-job.org](https://cron-job.org)) calls `POST /ferries/refresh` every 10 minutes, sending the `X-Refresh-Token` header.
3. The backend fetches the upstream data and stores it in a Neon Postgres database.
4. The frontend reads it from `GET /ferries/`.

The backend runs on Render's free tier, so it sleeps when idle and a cold start can take up to about a minute.

## Automation

Everything below lives in this repository.

- **CI on pull requests.** `CI.yaml` runs Pytest, Pylint, ESLint, and Hadolint as reusable workflows, then an aggregate **CI result** job that fails unless all four succeeded. Mark that single check as required in branch protection.
- **PR result comments.** `CI-comment.yaml` runs on `workflow_run` after CI, downloads the check outputs as artifacts, and comments a truncated excerpt per check. It never checks out or executes pull request code.
- **Container image.** The `Dockerfile` is multi-stage (build stage with a `uv sync --locked` install, slim runtime stage), pins the base image (`python:3.15.2-slim-trixie`) and uv (`0.12.15`), and runs as a non-root user (uid 10001). Render builds and deploys the backend from this `Dockerfile`; Hadolint checks it in CI.
- **Releases.** `release-please.yml` runs Release Please on `main` using a GitHub App token (so its pull requests trigger CI), driven by [Conventional Commits](https://www.conventionalcommits.org/). It requests squash auto-merge on the release PR it opens; the merge itself waits for the required checks.
- **Dependency updates.** Dependabot covers Docker, GitHub Actions, uv (backend), and npm (frontend). `Dependabot-auto.yaml` requests squash auto-merge on its pull requests; with **CI result** required, they merge only once CI passes.
- **Security scanning.** GitHub code scanning (CodeQL) and secret scanning are enabled on the repository, alongside the lint checks in CI.
- **Data refresh.** cron-job.org calls the token-protected `POST /ferries/refresh` every 10 minutes. `refresh-ferries.yaml` is a manual (`workflow_dispatch`) fallback that calls the same endpoint with the same header.
- **Database branches.** `neon.ts` gives new non-default Neon branches a 7-day TTL so they clean themselves up; the default branch is left alone.

## Run locally

Requirements: Python 3.11 or newer with [uv](https://docs.astral.sh/uv/) for the backend, and Node.js with npm for the frontend.

Backend, from the repository root:

```sh
cd backend
uv sync --locked
uv run fastapi dev
```

The API is available at <http://127.0.0.1:8000>, with interactive docs at <http://127.0.0.1:8000/docs>. See the [backend README](backend/README.md) for configuration and endpoints.

Frontend, from the repository root:

```sh
cd frontend
npm ci
npm run dev
```

The Vite dev server proxies `/api` requests to the hosted backend, so running the backend locally is optional. See the [frontend README](frontend/README.md) for details.
