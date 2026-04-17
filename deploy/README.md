# Deploying to Hetzner

## Prerequisites

- A Hetzner VPS with Docker and Docker Compose installed
- A domain pointing to the server's IP (A record)
- A GitHub deploy key or PAT with push access to the repo (for git-backed storage)

## First-time setup

```bash
# 1. SSH into the server
ssh root@your-server-ip

# 2. Clone this repo (or just the deploy/ dir)
git clone git@github.com:digimuwi/neumes-playground.git
cd neumes-playground/deploy

# 3. Create .env from the example
cp .env.example .env
# Edit .env — fill in all values

# 4. Clone the data repo for git-backed storage
git clone git@github.com:digimuwi/neumes-playground.git /var/lib/neumes-data
# Ensure the deploy key can push to this repo

# 5. Start everything
docker compose up -d --build

# 6. Verify
curl https://your-domain/health
```

## Updating

```bash
cd neumes-playground
git pull
cd deploy
docker compose up -d --build
```

## Logs

```bash
docker compose logs -f backend
docker compose logs -f caddy
```
