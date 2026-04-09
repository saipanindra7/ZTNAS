#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if [ ! -f ".env.prod" ]; then
  echo "Missing .env.prod file in project root."
  echo "Create it with production secrets before deploying."
  exit 1
fi

echo "Deploying ZTNAS using docker-compose.prod.yml..."
docker compose --env-file .env.prod -f docker-compose.prod.yml pull
docker compose --env-file .env.prod -f docker-compose.prod.yml up -d --build

echo "Deployment complete."
docker compose --env-file .env.prod -f docker-compose.prod.yml ps
