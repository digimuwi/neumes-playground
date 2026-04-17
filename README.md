# neumes-playground

## Frontend development

The Vite dev server proxies `/api/*` requests to the Python backend to avoid browser CORS issues during development.

By default the proxy target is:

```bash
http://127.0.0.1:8000
```

You can override it with an environment variable:

```bash
VITE_HTR_PROXY_TARGET=http://134.2.227.44:8000
```

You can also bypass the proxy entirely and point the frontend directly at a backend:

```bash
VITE_HTR_BASE_URL=http://134.2.227.44:8000
```

`VITE_HTR_BASE_URL` takes precedence over the dev proxy.

## Running locally

### Backend

```bash
cd backend
.venv/bin/python -m htr_service
```

The service listens on `http://localhost:8000`. With default env, auth is
disabled and every request is attributed to a synthetic `local-dev` user.

### Frontend

```bash
npm run dev
```

### Training (standalone CLI)

Training is no longer exposed as an API endpoint. Run it from the command line
against the current contributions:

```bash
cd backend
.venv/bin/python -m htr_service.training --type both
# or: --type neumes | --type segmentation
# tune with: --epochs N --imgsz N --seg-epochs N --from-scratch
```

## GitHub OAuth (optional, for shared deployments)

Local dev works without registering an OAuth app. To exercise the real sign-in
flow:

1. Create a GitHub OAuth App under the `digimuwi` org:
   - Homepage URL: `http://localhost:5173`
   - Authorization callback URL: `http://localhost:8000/auth/callback`
2. Export the secrets before starting the backend:

   ```bash
   export AUTH_ENABLED=true
   export GITHUB_CLIENT_ID=...
   export GITHUB_CLIENT_SECRET=...
   export GITHUB_ALLOWED_ORG=digimuwi
   export SESSION_SECRET=$(python -c 'import secrets; print(secrets.token_urlsafe(32))')
   export FRONTEND_URL=http://localhost:5173
   export BACKEND_URL=http://localhost:8000
   ```

3. Start backend and frontend as above. The frontend will show a login screen
   and redirect to GitHub. Users outside the `digimuwi` org are rejected.

## Git-backed storage (optional)

Every contribution save, annotation update, neume relabel, and neume-class
change can be committed to the current git working copy automatically:

```bash
export DATA_GIT_ENABLED=true
# Optional: also push to the remote after each commit
export DATA_GIT_PUSH=true
export DATA_GIT_REMOTE=origin
export DATA_GIT_BRANCH=main
```

Commits are authored as the signed-in GitHub user (or `local-dev` when auth is
disabled). Failures are logged and never break the API response.

## Environment variable reference

| Variable | Purpose | Default |
| --- | --- | --- |
| `AUTH_ENABLED` | Require GitHub OAuth sign-in | `false` |
| `GITHUB_CLIENT_ID` / `GITHUB_CLIENT_SECRET` | OAuth app credentials | — |
| `GITHUB_ALLOWED_ORG` | Only members of this org may sign in | `digimuwi` |
| `SESSION_SECRET` | Signs session cookies | dev placeholder |
| `FRONTEND_URL` | Public URL of the SPA (post-login redirect target) | `http://localhost:5173` |
| `BACKEND_URL` | Public URL of this service (used for OAuth callback) | `http://localhost:8000` |
| `DATA_GIT_ENABLED` | Commit contributions/registry writes to git | `false` |
| `DATA_GIT_PUSH` | Also push after each commit | `false` |
| `DATA_GIT_REMOTE` | Git remote to push to | `origin` |
| `DATA_GIT_BRANCH` | Branch to push | current branch |
| `DATA_REPO_ROOT` | Working copy to operate on | repo root |

