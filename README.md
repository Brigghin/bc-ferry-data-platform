# BC Ferry Data Platform (WIP)

This is a learning project for exploring Python API development with FastAPI, dependency management with uv, Docker, and release automation. The backend currently retrieves and serves BC Ferries sailing schedules from the BC Ferries API.

## Repository layout

- `backend/` contains the Python API service, its dependencies, and backend-specific documentation.
- `DockerFile` defines a container image for the backend.
- `.github/workflows/release-please.yml` runs Release Please on pushes to `main`.

For endpoint details and an example response, see the [backend README](backend/README.md).

## Run the backend locally

Requirements: Python 3.14 and [uv](https://docs.astral.sh/uv/).

From the repository root:

```sh
cd backend
uv sync --locked
uv run fastapi dev
```

The API is available at <http://127.0.0.1:8000>. Interactive API documentation is available at <http://127.0.0.1:8000/docs>.

## Releases

Release Please runs on pushes to `main` and creates or updates a release pull request based on [Conventional Commit](https://www.conventionalcommits.org/) messages. For example, `fix: correct sailing time parsing` indicates a patch-level change, while `feat: add route filtering` indicates a minor change.
