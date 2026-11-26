# Plan: Claude auto-fix for failed CI on pull requests

Goal: when the `CI` workflow fails on a pull request, a Claude Code agent reads the failure, fixes it, pushes one commit to the PR branch, and comments on the PR explaining what it changed. Do not commit; the owner will.

Existing pieces to reuse:
- `.github/workflows/CI.yaml` (workflow name `CI`; jobs Pytest, Pylint, ESLint, Hadolint, aggregate "CI result").
- `.github/workflows/claude-code-review.yml` / `claude.yml`: already use `anthropics/claude-code-action@v1` with `secrets.CLAUDE_CODE_OAUTH_TOKEN`.
- `.github/workflows/release-please.yml`: mints a GitHub App token with `actions/create-github-app-token@v3`, `client-id: ${{ vars.RELEASE_PLEASE_APP_CLIENT_ID }}`, `private-key: ${{ secrets.RELEASE_PLEASE_APP_PRIVATE_KEY }}`. Reuse the same App so the pushed commit triggers CI again (pushes made with `GITHUB_TOKEN` do not).
- Backend: Python via uv (`backend/`, `uv sync --locked`, pytest, pylint — check Pytest.yaml / Pylint.yaml for exact commands). Frontend: `frontend/`, `npm ci`, `npm run lint`, `npm run build` (check ESlint.yaml). Hadolint on `Dockerfile` (check hadolint.yaml).

## Step 1 — Verify the action's interface

Before writing YAML, read the current docs for `anthropics/claude-code-action` v1: README, `docs/usage.md`, `docs/configuration.md` (or equivalent), and its CI-failure auto-fix example under `examples/` if present. Confirm: input names (`prompt`, `claude_args`, `claude_code_oauth_token`, `github_token`), how to allow tools (`--allowedTools` syntax incl. Bash patterns), `--max-turns`, whether `id-token: write` is needed when `github_token` is supplied, and how the example gets failure logs and PR number. Prefer the example's structure where it fits this plan.

## Step 2 — `.github/workflows/claude-ci-fix.yml`

- `on: workflow_run` for workflows `["CI"]`, `types: [completed]`.
- Job `if:` ALL of:
  - `github.event.workflow_run.conclusion == 'failure'`
  - `github.event.workflow_run.event == 'pull_request'`
  - `github.event.workflow_run.head_repository.full_name == github.repository` (never run on forks: the agent holds a write token and reads untrusted code/logs)
  - `!contains(github.event.workflow_run.head_commit.message, '[claude-ci-fix]')` (loop guard: at most one fix attempt per failing push)
  - head branch is not `main`.
- `concurrency: { group: claude-ci-fix-${{ github.event.workflow_run.head_branch }}, cancel-in-progress: true }`.
- Minimal `permissions:` (e.g. `actions: read`, `contents: read`, `pull-requests: read`, plus `id-token: write` only if Step 1 says it's required). Writes go through the App token.
- `timeout-minutes: 20`.
- Steps:
  1. Mint App token (same inputs as release-please.yml) with `permission-contents: write`, `permission-pull-requests: write`, `permission-actions: read`.
  2. Checkout `github.event.workflow_run.head_branch` with that token (full enough history to commit and push).
  3. Toolchains so the agent can re-run checks: `astral-sh/setup-uv` (pin like the other workflows do), `actions/setup-node` (version as in ESlint.yaml). Match versions/pins used by the existing CI workflows.
  4. Resolve the PR number (`github.event.workflow_run.pull_requests[0].number`; fall back to `gh pr list --head <branch>` if empty).
  5. Run `anthropics/claude-code-action@v1` with `claude_code_oauth_token`, `github_token` = App token, a `prompt`, and `claude_args` with `--max-turns` (~30) and an `--allowedTools` allow-list: Read/Edit/Write/Glob/Grep, `gh run view` (logs), `gh pr comment`, `git add/commit/push/diff/status/log`, and the check commands (`uv run pytest`, `uv run pylint`, `uv sync`, `npm ci`, `npm run lint`, `npm run build`, `hadolint` if installed). No other network or shell access.
- Prompt (write it clearly; pass run id, run URL, PR number, branch via `${{ }}`):
  1. Fetch failed job logs (`gh run view <run id> --log-failed`), find the root cause.
  2. If the failure is flaky/infra/external (runner, network, upstream API, secrets) or the fix would need a design decision, push nothing; post a PR comment with the diagnosis and stop.
  3. Otherwise make the smallest fix; do not weaken checks (no disabling lint rules, skipping/deleting tests, loosening config) unless that is genuinely the correct fix and the comment says so.
  4. Re-run the failing check(s) locally and confirm they pass.
  5. Commit once with a message starting `fix(ci): ` and containing `[claude-ci-fix]`; push to the PR branch.
  6. Comment on the PR: which check failed, root cause, what changed (files), how it was verified, link to the failed run.

Acceptance: YAML parses (`python3 -c "import yaml,sys; yaml.safe_load(open(sys.argv[1]))" <file>`); if `actionlint` is available run it; all inputs match Step 1's docs; every guard above present; no secrets inlined.

## Step 3 — README

In root `README.md` "## Automation", add one bullet **CI auto-fix** describing the above in one or two sentences (trigger, same-repo PRs only, one attempt, commits + PR comment, uses the GitHub App token so CI re-runs). Mention the existing Claude PR review workflow in the same bullet if it fits.

## Step 4 — Review

Send `reviewer` this file and the changed files.

## Owner setup (not for workers)

- GitHub App `bc-ferry-automation` must have Contents, Pull requests: write and Actions: read, and be installed on the repo.
- `CLAUDE_CODE_OAUTH_TOKEN` secret must exist (it does if claude-code-review.yml runs).
