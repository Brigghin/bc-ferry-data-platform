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

Release pull requests are configured for squash auto-merge after required checks and reviews pass. The App token lets Release Please trigger CI on its pull requests and lets the merged release trigger the workflow that creates the GitHub release. The **CI result** check must remain required; otherwise a release could merge before CI finishes.

Before merging the App-based workflow, create and configure a GitHub App:

1. Open [GitHub App settings](https://github.com/settings/apps), select **New GitHub App**, and choose a unique name. Use your repository URL as the homepage, turn off **Active** under Webhook, and choose **Only on this account**.
2. Under **Repository permissions**, grant **Contents: Read and write**, **Issues: Read and write**, and **Pull requests: Read and write**. Leave other permissions at their defaults, then create the App.
3. On the App's settings page, copy its **Client ID**. Generate and download a private key, and keep it private.
4. Select **Install App**, install it on your account, and grant access to this repository.
5. In this repository, open **Settings > Secrets and variables > Actions**. Under **Variables**, add `RELEASE_PLEASE_APP_CLIENT_ID` with the Client ID. Under **Secrets**, add `RELEASE_PLEASE_APP_PRIVATE_KEY` with the entire contents of the downloaded private key file. Do not commit the key.
6. Merge the workflow change into `main`. The workflow also supports manual execution from the Actions tab. Confirm that a release PR runs CI, enables auto-merge, and creates a GitHub release after merging.

Without these App credentials and installation, Release Please will fail rather than create releases. GitHub may require an approval before running CI for a new App's first pull request. Required reviews and branch rules still apply; the workflow does not bypass them.

## Dependabot auto-merge

The Dependabot workflow requests squash auto-merge for Dependabot pull requests targeting `main`; it does not approve them. Before enabling the workflow, enable auto-merge in repository settings and configure branch protection or a ruleset for `main` to require **CI result**. This aggregate check passes only if Pytest, Pylint, ESLint, and Hadolint all pass. Auto-merge only waits for required checks and reviews; without that rule, a pull request could merge before tests finish. Replace any previous required check names with the new reusable-workflow check names or the aggregate **CI result** check.

The CI workflow runs these checks on pull requests to `main`. Afterward, a separate reporting workflow comments with each result, a bounded excerpt of its output, and a link to the full logs. If a check fails before producing output, the comment directs readers to the workflow logs. The reporting workflow does not check out or execute pull request code.

If branch protection requires reviews, an independent approval is still needed. The workflow token must have permission to merge pull requests. A merge queue may require a GitHub App or personal access token instead of `GITHUB_TOKEN`. A merge performed with `GITHUB_TOKEN` generally does not trigger other workflows on the resulting push, including `DockerBuild`; use a GitHub App or personal access token if that build must run for these merges.
